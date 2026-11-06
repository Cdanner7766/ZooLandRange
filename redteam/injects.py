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

ACCESS MODEL -- this matters for what blue team is supposed to see:

  --via network (default): logs in over the actual VLAN like a real
  attacker and runs the command there. This is what makes the inject
  detectable: a real SSH or WinRM session, a real login event, a real
  child process spawned by sudo / the command shell. It uses credentials
  that mirror an actual compromise path already in this range:
    - Linux targets: the Ludus default `localuser` account (passwordless
      sudo) over SSH. None of the documented low-privilege weak accounts
      (admin/admin, ftpuser/ftpuser, mail/mail, dbadmin/password, ...)
      have sudo rights, so they can't actually stop a systemd service or
      container -- using them here would just fail. `localuser` stands in
      for "the attacker already has a privileged foothold" (e.g. a reused
      key or a completed privilege escalation), which is a fair assumption
      for an inject rather than a full exploit chain.
    - Windows targets: the `domainadmin` domain admin account over WinRM
      (HTTPS 5986, NTLM) -- the direct, intended payoff of this range's
      weak AD password policy vulnerability (see README.md). Domain
      Admins are local admins on every domain-joined box, so this one
      account reaches GIRAFFE, MEERKAT and ZEBRA.
  If blue team detects and locks out this account (rotates the password,
  firewalls SSH/WinRM, disables the account), the network-mode inject
  starts failing -- that is success, not a bug in this tool.

  --via guest-agent: the ORIGINAL mechanism (sudo qm guest exec on the
  Ludus host, over the QEMU guest agent channel). This leaves no network
  trace and no login event, so it does not simulate an attacker. Use it
  only as a white-cell/instructor override -- e.g. to force restore-all
  at the end of a session even if blue team successfully cut off the
  simulated attacker's access.

Run from the Ludus host:

    python3 redteam/injects.py list
    python3 redteam/injects.py status                       # all scenarios
    python3 redteam/injects.py status giraffe-dns-stop
    python3 redteam/injects.py apply giraffe-dns-stop
    python3 redteam/injects.py restore giraffe-dns-stop
    python3 redteam/injects.py restore-all                   # end-of-session reset
    python3 redteam/injects.py random                        # 1 random inject
    python3 redteam/injects.py random -n 3 --hide            # 3 injects, don't say which
    python3 redteam/injects.py apply hippo-mysql-stop --via guest-agent   # white-cell override

Network mode needs `sshpass` (Linux targets) and the `winrm` Python
package / pywinrm (Windows targets) -- the same optional tools
tests/check.py already uses, with the same SKIP-if-missing behavior
rather than a crash. Guest-agent mode needs `sudo qm list` / `sudo qm
guest exec` rights on the Ludus host, per CLAUDE.md.

Range IPs are auto-detected the same way tests/check.py does (10.<X>.99.*
on this host -> range X), or pass --range. If blue team rotates the
attacker credentials as part of hardening, override them with
REDTEAM_LINUX_PW / REDTEAM_WIN_USER / REDTEAM_WIN_PW env vars instead of
editing this file.

Every apply/restore is appended to redteam/inject_log.jsonl so an
instructor (or the student, afterward) can see exactly what was done,
when, and by which access path.
"""
import argparse
import json
import os
import random as _random
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

LOG_PATH = Path(__file__).parent / "inject_log.jsonl"

# --------------------------------------------------------------------------
# "Attacker" credentials for --via network -- see the ACCESS MODEL note
# above for why these specific accounts, not the documented low-priv ones.
# --------------------------------------------------------------------------
LINUX_SSH_USERS = (
    (os.environ.get("REDTEAM_LINUX_USER", "localuser"),
     os.environ.get("REDTEAM_LINUX_PW", "password")),
)
WIN_USER = os.environ.get("REDTEAM_WIN_USER", "ZOOLAND\\domainadmin")
WIN_PW = os.environ.get("REDTEAM_WIN_PW", "ZooTime!")

# Each scenario is ONE reversible action against ONE (or two, when a real
# Windows service legitimately backs two checks) of the 15 scored checks.
# "host" is the last IP octet (10.<range>.10.<host>); "vm" is the Ludus VM
# name substring, used only by --via guest-agent.
SCENARIOS = {
    "giraffe-dns-stop": {
        "vm": "GIRAFFE", "host": 7, "os": "windows",
        "checks": ["DNS resolution (GIRAFFE:53) - 100 pts"],
        "apply": "Stop-Service DNS -Force",
        "restore": "Start-Service DNS",
        "verify": "(Get-Service DNS).Status",
    },
    "giraffe-ldap-kerberos-stop": {
        "vm": "GIRAFFE", "host": 7, "os": "windows",
        "checks": [
            "LDAP (GIRAFFE:389) - 100 pts",
            "Kerberos (GIRAFFE:88) - 100 pts",
        ],
        "apply": "Stop-Service NTDS -Force",
        "restore": "Start-Service NTDS",
        "verify": "(Get-Service NTDS).Status",
    },
    "meerkat-rdp-stop": {
        "vm": "MEERKAT", "host": 12, "os": "windows",
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
        "vm": "ZEBRA", "host": 15, "os": "windows",
        "checks": ["SMB (ZEBRA:445) - 50 pts"],
        "apply": "Stop-Service LanmanServer -Force",
        "restore": "Start-Service LanmanServer",
        "verify": "(Get-Service LanmanServer).Status",
    },
    "penguin-http-stop": {
        "vm": "PENGUIN", "host": 23, "os": "linux",
        "checks": ["HTTP CrazyRhino (PENGUIN:80) - 100 pts"],
        "apply": "cd /opt/crazyrhino && docker compose stop frontend",
        "restore": "cd /opt/crazyrhino && docker compose start frontend",
        "verify": "cd /opt/crazyrhino && docker compose ps frontend --format '{{.Status}}'",
    },
    "penguin-ssh-stop": {
        "vm": "PENGUIN", "host": 23, "os": "linux",
        "checks": ["SSH banner PENGUIN (:22) - 25 pts"],
        "apply": "systemctl stop ssh",
        "restore": "systemctl start ssh",
        "verify": "systemctl is-active ssh",
    },
    "otter-ftp-stop": {
        "vm": "OTTER", "host": 29, "os": "linux",
        "checks": ["FTP login (OTTER:21) - 50 pts"],
        "apply": "systemctl stop vsftpd",
        "restore": "systemctl start vsftpd",
        "verify": "systemctl is-active vsftpd",
    },
    "otter-ssh-stop": {
        "vm": "OTTER", "host": 29, "os": "linux",
        "checks": ["SSH banner OTTER (:22) - 25 pts"],
        "apply": "systemctl stop ssh",
        "restore": "systemctl start ssh",
        "verify": "systemctl is-active ssh",
    },
    "flamingo-smtp-stop": {
        "vm": "FLAMINGO", "host": 38, "os": "linux",
        "checks": ["SMTP open relay (FLAMINGO:25) - 75 pts"],
        "apply": "systemctl stop postfix",
        "restore": "systemctl start postfix",
        "verify": "systemctl is-active postfix",
    },
    "flamingo-imap-pop3-stop": {
        "vm": "FLAMINGO", "host": 38, "os": "linux",
        "checks": [
            "IMAP login (FLAMINGO:143) - 50 pts",
            "POP3 banner (FLAMINGO:110) - 50 pts",
        ],
        "apply": "systemctl stop dovecot",
        "restore": "systemctl start dovecot",
        "verify": "systemctl is-active dovecot",
    },
    "flamingo-ssh-stop": {
        "vm": "FLAMINGO", "host": 38, "os": "linux",
        "checks": ["SSH banner FLAMINGO (:22) - 25 pts"],
        "apply": "systemctl stop ssh",
        "restore": "systemctl start ssh",
        "verify": "systemctl is-active ssh",
    },
    "hippo-mysql-stop": {
        "vm": "HIPPO", "host": 41, "os": "linux",
        "checks": ["MySQL (HIPPO:3306) - 75 pts"],
        "apply": "systemctl stop mariadb",
        "restore": "systemctl start mariadb",
        "verify": "systemctl is-active mariadb",
    },
    "hippo-ssh-stop": {
        "vm": "HIPPO", "host": 41, "os": "linux",
        "checks": ["SSH banner HIPPO (:22) - 25 pts"],
        "apply": "systemctl stop ssh",
        "restore": "systemctl start ssh",
        "verify": "systemctl is-active ssh",
    },
}


# --------------------------------------------------------------------------
# Range / IP resolution -- mirrors tests/check.py's detect_range()
# --------------------------------------------------------------------------
def detect_range():
    try:
        out = subprocess.run(["ip", "-4", "addr"], capture_output=True, text=True).stdout
        m = re.search(r"10\.(\d+)\.99\.\d+", out)
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return 1


def host_ip(range_num, last_octet):
    return f"10.{range_num}.10.{last_octet}"


# --------------------------------------------------------------------------
# --via network: SSH (Linux) / WinRM (Windows) -- mirrors tests/check.py's
# ssh_root() and winrm() helpers so this tool behaves the same way as the
# rest of the project's tooling.
# --------------------------------------------------------------------------
def have(tool):
    import shutil
    return shutil.which(tool) is not None


def ssh_exec(host, cmd, timeout=30):
    """Run cmd as root over SSH (attacker foothold account + sudo).
    Returns (rc, output), or None if sshpass isn't installed."""
    if not have("sshpass"):
        return None
    out = ""
    for user, pw in LINUX_SSH_USERS:
        p = subprocess.run(
            ["sshpass", "-p", pw, "ssh", "-o", "StrictHostKeyChecking=no",
             "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=8",
             "-o", "LogLevel=ERROR", f"{user}@{host}",
             "sudo -n sh -c " + shlex.quote(cmd)],
            capture_output=True, text=True, timeout=timeout,
        )
        out = p.stdout + p.stderr
        if "Permission denied" not in out:
            return p.returncode, out
    return 255, out


def winrm_exec(host, user, pw, ps, timeout=30):
    """Run PowerShell over WinRM (HTTPS 5986, NTLM, as Ludus configures it).
    Returns (rc, stdout), or None if pywinrm isn't installed."""
    try:
        import winrm as _w
    except ImportError:
        return None
    try:
        sess = _w.Session(
            f"https://{host}:5986/wsman", auth=(user, pw), transport="ntlm",
            server_cert_validation="ignore", operation_timeout_sec=timeout,
            read_timeout_sec=timeout + 10,
        )
        r = sess.run_ps(ps)
        return r.status_code, (r.std_out + r.std_err).decode(errors="replace")
    except Exception as e:
        return 1, f"winrm error: {e}"


# --------------------------------------------------------------------------
# --via guest-agent: the original QEMU-guest-agent path. White-cell /
# instructor override only -- see ACCESS MODEL note at the top of the file.
# --------------------------------------------------------------------------
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


# --------------------------------------------------------------------------
# Dispatch
# --------------------------------------------------------------------------
def log_action(scenario_id, action, via, target, ok, detail):
    entry = {
        "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "scenario": scenario_id,
        "action": action,
        "via": via,
        "target": target,
        "ok": ok,
        "detail": detail.strip()[:500],
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def run_one(sid, action, via, range_num):
    s = SCENARIOS[sid]
    cmd = s[action]

    if via == "guest-agent":
        vmid, vm_name = resolve_vmid(s["vm"])
        result = qm_exec(vmid, s["os"], cmd)
        ok = result.returncode == 0
        detail = (result.stdout or "") + (result.stderr or "")
        log_action(sid, action, via, vm_name, ok, detail)
        return vm_name, ok, detail

    # via == "network"
    ip = host_ip(range_num, s["host"])
    if s["os"] == "windows":
        r = winrm_exec(ip, WIN_USER, WIN_PW, cmd)
        if r is None:
            raise RuntimeError(
                "pywinrm not installed (pip install pywinrm) -- "
                "or use --via guest-agent as a fallback"
            )
    else:
        r = ssh_exec(ip, cmd)
        if r is None:
            raise RuntimeError(
                "sshpass not installed -- or use --via guest-agent as a fallback"
            )
    rc, out = r
    ok = rc == 0
    log_action(sid, action, via, ip, ok, out)
    return ip, ok, out


def do_list(_args):
    print(f"{'ID':<28} {'VM':<9} {'Scored check(s)'}")
    print("-" * 80)
    for sid, s in SCENARIOS.items():
        print(f"{sid:<28} {s['vm']:<9} {'; '.join(s['checks'])}")


def do_apply(args):
    sid = args.id
    if sid not in SCENARIOS:
        sys.exit(f"Unknown scenario: {sid} (see `injects.py list`)")
    target, ok, detail = run_one(sid, "apply", args.via, args.range)
    status = "APPLIED" if ok else "FAILED"
    print(f"[{status}] {sid} on {target} (via {args.via})")
    if detail.strip():
        print(detail.strip())
    for c in SCENARIOS[sid]["checks"]:
        print(f"  affects: {c}")
    print(f"  restore with: python3 redteam/injects.py restore {sid}")


def do_restore(args):
    sid = args.id
    if sid not in SCENARIOS:
        sys.exit(f"Unknown scenario: {sid} (see `injects.py list`)")
    target, ok, detail = run_one(sid, "restore", args.via, args.range)
    status = "RESTORED" if ok else "FAILED"
    print(f"[{status}] {sid} on {target} (via {args.via})")
    if detail.strip():
        print(detail.strip())


def do_restore_all(args):
    failures = []
    for sid in SCENARIOS:
        try:
            target, ok, detail = run_one(sid, "restore", args.via, args.range)
            print(f"[{'RESTORED' if ok else 'FAILED'}] {sid} on {target} (via {args.via})")
            if not ok:
                failures.append(sid)
        except RuntimeError as e:
            print(f"[FAILED] {sid}: {e}")
            failures.append(sid)
    if failures:
        print(f"\n{len(failures)} scenario(s) did not restore cleanly: {', '.join(failures)}")
        if args.via == "network":
            print(
                "If blue team locked out the attacker account (rotated the "
                "password, blocked SSH/WinRM, disabled the account), that's "
                "a successful defense. Force cleanup with:\n"
                "  python3 redteam/injects.py restore-all --via guest-agent"
            )
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
            if args.via == "guest-agent":
                vmid, target = resolve_vmid(s["vm"])
                result = qm_exec(vmid, s["os"], s["verify"])
                state = (result.stdout or result.stderr).strip()
            else:
                target = host_ip(args.range, s["host"])
                if s["os"] == "windows":
                    r = winrm_exec(target, WIN_USER, WIN_PW, s["verify"])
                else:
                    r = ssh_exec(target, s["verify"])
                if r is None:
                    state = "error: missing sshpass/pywinrm (try --via guest-agent)"
                else:
                    state = (r[1] or "").strip()
        except RuntimeError as e:
            target, state = s["vm"], f"error: {e}"
        print(f"{sid:<28} {target:<18} {state}")


def do_random(args):
    n = min(args.n, len(SCENARIOS))
    chosen = _random.sample(list(SCENARIOS), n)
    if not args.hide:
        print(f"Applying {n} random inject(s) via {args.via}: {', '.join(chosen)}\n")
    else:
        print(f"Applying {n} random inject(s) via {args.via} (hidden) ...\n")
    for sid in chosen:
        try:
            target, ok, detail = run_one(sid, "apply", args.via, args.range)
            label = sid if not args.hide else "***"
            shown_target = target if not args.hide else "???"
            print(f"[{'APPLIED' if ok else 'FAILED'}] {label} on {shown_target}")
        except RuntimeError as e:
            print(f"[FAILED] {sid if not args.hide else '***'}: {e}")
    if args.hide:
        print(
            "\nScenario names withheld from stdout, but they are still in "
            f"{LOG_PATH} for the instructor. Blue team should find and fix "
            "the outage from monitoring / the scoring dashboard, not this log."
        )
    else:
        print(f"\nRestore any of these with: python3 redteam/injects.py restore <id>")


def add_common(sp):
    sp.add_argument("--via", choices=["network", "guest-agent"], default="network",
                     help="network (default): real SSH/WinRM login, detectable by blue "
                          "team. guest-agent: QEMU guest agent, no network trace -- "
                          "white-cell/instructor override only.")
    sp.add_argument("--range", type=int, default=None,
                     help="range number X for 10.X.10.* (default: autodetect, else 1)")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List all available injects").set_defaults(func=do_list)

    sp = sub.add_parser("status", help="Show live service state for one or all injects")
    sp.add_argument("id", nargs="?", help="Scenario id (default: all)")
    add_common(sp)
    sp.set_defaults(func=do_status)

    sp = sub.add_parser("apply", help="Apply one inject")
    sp.add_argument("id")
    add_common(sp)
    sp.set_defaults(func=do_apply)

    sp = sub.add_parser("restore", help="Undo one inject")
    sp.add_argument("id")
    add_common(sp)
    sp.set_defaults(func=do_restore)

    sp = sub.add_parser("restore-all", help="Undo every inject (end-of-session reset)")
    add_common(sp)
    sp.set_defaults(func=do_restore_all)

    sp = sub.add_parser("random", help="Apply N random injects")
    sp.add_argument("-n", type=int, default=1, help="How many to apply (default 1)")
    sp.add_argument("--hide", action="store_true", help="Don't print which scenarios were chosen")
    add_common(sp)
    sp.set_defaults(func=do_random)

    args = p.parse_args()
    if getattr(args, "range", None) is None and hasattr(args, "via"):
        args.range = detect_range()
    try:
        args.func(args)
    except RuntimeError as e:
        sys.exit(f"Error: {e}")


if __name__ == "__main__":
    main()
