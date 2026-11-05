#!/usr/bin/env python3
"""
ZooLandRange red-team injects: single, reversible disruptions to the 15
scored services, for PRCCDC-style blue team practice.

Each inject is ONE small, non-destructive change (stop a service, flip one
setting) with a matching restore command -- the same pattern as a red team
member stopping AD DS to drop LDAP on a real CCDC box. Nothing here deletes
data, corrupts a VM, or touches anything outside the service being tested.
It never weakens or removes the intentional vulnerabilities in README.md;
it only interrupts the service that is already running.

Run from the Ludus host (needs `sudo qm guest exec`, which works even
without range networking):

    python3 redteam/injects.py list
    python3 redteam/injects.py status                    # all scenarios
    python3 redteam/injects.py status giraffe-dns-stop
    python3 redteam/injects.py apply giraffe-dns-stop
    python3 redteam/injects.py restore giraffe-dns-stop
    python3 redteam/injects.py restore-all                # end-of-session reset
    python3 redteam/injects.py random                     # 1 random inject
    python3 redteam/injects.py random -n 3 --hide          # 3 injects, don't say which

Standard library only. VM IDs are resolved by name at run time via
`sudo qm list`, so this works under any Ludus username prefix (CD-GIRAFFE,
CLAUDEAGENT-GIRAFFE, etc.) -- just set the match text in each scenario's
"vm" field to the part of the name after the prefix.

Every apply/restore is appended to redteam/inject_log.jsonl so an
instructor (or the student, afterward) can see exactly what was done and
when, and so restore-all has a record to work from.
"""
import argparse
import json
import random as _random
import re
import subprocess
import sys
import time
from pathlib import Path

LOG_PATH = Path(__file__).parent / "inject_log.jsonl"

# Each scenario is ONE reversible action against ONE (or two, when a real
# Windows service legitimately backs two checks) of the 15 scored checks.
SCENARIOS = {
    "giraffe-dns-stop": {
        "vm": "GIRAFFE", "os": "windows",
        "checks": ["DNS resolution (GIRAFFE:53) - 100 pts"],
        "apply": "Stop-Service DNS -Force",
        "restore": "Start-Service DNS",
        "verify": "(Get-Service DNS).Status",
    },
    "giraffe-ldap-kerberos-stop": {
        "vm": "GIRAFFE", "os": "windows",
        "checks": [
            "LDAP (GIRAFFE:389) - 100 pts",
            "Kerberos (GIRAFFE:88) - 100 pts",
        ],
        "apply": "Stop-Service NTDS -Force",
        "restore": "Start-Service NTDS",
        "verify": "(Get-Service NTDS).Status",
    },
    "meerkat-rdp-stop": {
        "vm": "MEERKAT", "os": "windows",
        "checks": ["RDP (MEERKAT:3389) - 50 pts"],
        "apply": (
            "Set-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server' "
            "-Name fDenyTSConnections -Value 1; Stop-Service TermService -Force"
        ),
        "restore": (
            "Set-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server' "
            "-Name fDenyTSConnections -Value 0; Start-Service TermService"
        ),
        "verify": "(Get-Service TermService).Status",
    },
    "zebra-smb-stop": {
        "vm": "ZEBRA", "os": "windows",
        "checks": ["SMB (ZEBRA:445) - 50 pts"],
        "apply": "Stop-Service LanmanServer -Force",
        "restore": "Start-Service LanmanServer",
        "verify": "(Get-Service LanmanServer).Status",
    },
    "penguin-http-stop": {
        "vm": "PENGUIN", "os": "linux",
        "checks": ["HTTP CrazyRhino (PENGUIN:80) - 100 pts"],
        "apply": "cd /opt/crazyrhino && docker compose stop frontend",
        "restore": "cd /opt/crazyrhino && docker compose start frontend",
        "verify": "cd /opt/crazyrhino && docker compose ps frontend --format '{{.Status}}'",
    },
    "penguin-ssh-stop": {
        "vm": "PENGUIN", "os": "linux",
        "checks": ["SSH banner PENGUIN (:22) - 25 pts"],
        "apply": "systemctl stop ssh",
        "restore": "systemctl start ssh",
        "verify": "systemctl is-active ssh",
    },
    "otter-ftp-stop": {
        "vm": "OTTER", "os": "linux",
        "checks": ["FTP login (OTTER:21) - 50 pts"],
        "apply": "systemctl stop vsftpd",
        "restore": "systemctl start vsftpd",
        "verify": "systemctl is-active vsftpd",
    },
    "otter-ssh-stop": {
        "vm": "OTTER", "os": "linux",
        "checks": ["SSH banner OTTER (:22) - 25 pts"],
        "apply": "systemctl stop ssh",
        "restore": "systemctl start ssh",
        "verify": "systemctl is-active ssh",
    },
    "flamingo-smtp-stop": {
        "vm": "FLAMINGO", "os": "linux",
        "checks": ["SMTP open relay (FLAMINGO:25) - 75 pts"],
        "apply": "systemctl stop postfix",
        "restore": "systemctl start postfix",
        "verify": "systemctl is-active postfix",
    },
    "flamingo-imap-pop3-stop": {
        "vm": "FLAMINGO", "os": "linux",
        "checks": [
            "IMAP login (FLAMINGO:143) - 50 pts",
            "POP3 banner (FLAMINGO:110) - 50 pts",
        ],
        "apply": "systemctl stop dovecot",
        "restore": "systemctl start dovecot",
        "verify": "systemctl is-active dovecot",
    },
    "flamingo-ssh-stop": {
        "vm": "FLAMINGO", "os": "linux",
        "checks": ["SSH banner FLAMINGO (:22) - 25 pts"],
        "apply": "systemctl stop ssh",
        "restore": "systemctl start ssh",
        "verify": "systemctl is-active ssh",
    },
    "hippo-mysql-stop": {
        "vm": "HIPPO", "os": "linux",
        "checks": ["MySQL (HIPPO:3306) - 75 pts"],
        "apply": "systemctl stop mariadb",
        "restore": "systemctl start mariadb",
        "verify": "systemctl is-active mariadb",
    },
    "hippo-ssh-stop": {
        "vm": "HIPPO", "os": "linux",
        "checks": ["SSH banner HIPPO (:22) - 25 pts"],
        "apply": "systemctl stop ssh",
        "restore": "systemctl start ssh",
        "verify": "systemctl is-active ssh",
    },
}


def resolve_vmid(vm_suffix):
    """Find the VM ID whose name contains vm_suffix, independent of the
    Ludus username prefix (CD-GIRAFFE, CLAUDEAGENT-GIRAFFE, ...)."""
    out = subprocess.run(
        ["sudo", "qm", "list"], capture_output=True, text=True, timeout=30
    )
    if out.returncode != 0:
        raise RuntimeError(f"sudo qm list failed: {out.stderr.strip()}")
    matches = []
    for line in out.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 2:
            continue
        vmid, name = parts[0], parts[1]
        if vm_suffix.upper() in name.upper():
            matches.append((vmid, name))
    if not matches:
        raise RuntimeError(f"No VM found matching '{vm_suffix}' in `qm list`")
    if len(matches) > 1:
        names = ", ".join(n for _, n in matches)
        raise RuntimeError(f"'{vm_suffix}' matched more than one VM: {names}")
    return matches[0]


def qm_exec(vmid, os_type, command, timeout=30):
    if os_type == "windows":
        cmd = [
            "sudo", "qm", "guest", "exec", str(vmid),
            "--timeout", str(timeout),
            "--", "powershell", "-NoProfile", "-Command", command,
        ]
    else:
        cmd = [
            "sudo", "qm", "guest", "exec", str(vmid),
            "--timeout", str(timeout),
            "--", "/bin/bash", "-c", command,
        ]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 15)


def log_action(scenario_id, action, vm_name, ok, detail):
    entry = {
        "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "scenario": scenario_id,
        "action": action,
        "vm": vm_name,
        "ok": ok,
        "detail": detail.strip()[:500],
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def do_list(_args):
    print(f"{'ID':<28} {'VM':<9} {'Scored check(s)'}")
    print("-" * 80)
    for sid, s in SCENARIOS.items():
        print(f"{sid:<28} {s['vm']:<9} {'; '.join(s['checks'])}")


def run_one(sid, action):
    s = SCENARIOS[sid]
    vmid, vm_name = resolve_vmid(s["vm"])
    cmd = s[action]
    result = qm_exec(vmid, s["os"], cmd)
    ok = result.returncode == 0
    detail = (result.stdout or "") + (result.stderr or "")
    log_action(sid, action, vm_name, ok, detail)
    return vm_name, ok, detail


def do_apply(args):
    sid = args.id
    if sid not in SCENARIOS:
        sys.exit(f"Unknown scenario: {sid} (see `injects.py list`)")
    vm_name, ok, detail = run_one(sid, "apply")
    status = "APPLIED" if ok else "FAILED"
    print(f"[{status}] {sid} on {vm_name}")
    if detail.strip():
        print(detail.strip())
    for c in SCENARIOS[sid]["checks"]:
        print(f"  affects: {c}")
    print(f"  restore with: python3 redteam/injects.py restore {sid}")


def do_restore(args):
    sid = args.id
    if sid not in SCENARIOS:
        sys.exit(f"Unknown scenario: {sid} (see `injects.py list`)")
    vm_name, ok, detail = run_one(sid, "restore")
    status = "RESTORED" if ok else "FAILED"
    print(f"[{status}] {sid} on {vm_name}")
    if detail.strip():
        print(detail.strip())


def do_restore_all(_args):
    failures = []
    for sid in SCENARIOS:
        try:
            vm_name, ok, detail = run_one(sid, "restore")
            print(f"[{'RESTORED' if ok else 'FAILED'}] {sid} on {vm_name}")
            if not ok:
                failures.append(sid)
        except RuntimeError as e:
            print(f"[FAILED] {sid}: {e}")
            failures.append(sid)
    if failures:
        print(f"\n{len(failures)} scenario(s) did not restore cleanly: {', '.join(failures)}")
        sys.exit(1)
    print("\nAll scenarios restored.")


def do_status(args):
    ids = [args.id] if args.id else list(SCENARIOS)
    for sid in ids:
        if sid not in SCENARIOS:
            print(f"{sid}: unknown scenario")
            continue
        s = SCENARIOS[sid]
        try:
            vmid, vm_name = resolve_vmid(s["vm"])
            result = qm_exec(vmid, s["os"], s["verify"])
            state = (result.stdout or result.stderr).strip()
        except RuntimeError as e:
            vm_name, state = s["vm"], f"error: {e}"
        print(f"{sid:<28} {vm_name:<16} {state}")


def do_random(args):
    n = min(args.n, len(SCENARIOS))
    chosen = _random.sample(list(SCENARIOS), n)
    if not args.hide:
        print(f"Applying {n} random inject(s): {', '.join(chosen)}\n")
    else:
        print(f"Applying {n} random inject(s) (hidden) ...\n")
    for sid in chosen:
        try:
            vm_name, ok, detail = run_one(sid, "apply")
            label = sid if not args.hide else "***"
            print(f"[{'APPLIED' if ok else 'FAILED'}] {label} on {vm_name if not args.hide else '???'}")
        except RuntimeError as e:
            print(f"[FAILED] {sid if not args.hide else '***'}: {e}")
    if args.hide:
        print(
            "\nScenario names withheld from stdout, but they are still in "
            f"{LOG_PATH} for the instructor. Blue team should find and fix "
            "the outage from the scoring dashboard / service checks, not this log."
        )
    else:
        print(f"\nRestore any of these with: python3 redteam/injects.py restore <id>")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List all available injects").set_defaults(func=do_list)

    sp = sub.add_parser("status", help="Show live service state for one or all injects")
    sp.add_argument("id", nargs="?", help="Scenario id (default: all)")
    sp.set_defaults(func=do_status)

    sp = sub.add_parser("apply", help="Apply one inject")
    sp.add_argument("id")
    sp.set_defaults(func=do_apply)

    sp = sub.add_parser("restore", help="Undo one inject")
    sp.add_argument("id")
    sp.set_defaults(func=do_restore)

    sub.add_parser("restore-all", help="Undo every inject (end-of-session reset)").set_defaults(func=do_restore_all)

    sp = sub.add_parser("random", help="Apply N random injects")
    sp.add_argument("-n", type=int, default=1, help="How many to apply (default 1)")
    sp.add_argument("--hide", action="store_true", help="Don't print which scenarios were chosen")
    sp.set_defaults(func=do_random)

    args = p.parse_args()
    try:
        args.func(args)
    except RuntimeError as e:
        sys.exit(f"Error: {e}")


if __name__ == "__main__":
    main()
