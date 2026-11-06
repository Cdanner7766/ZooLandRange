# Red-team injects

A practice tool for PRCCDC-style play on ZooLandRange: each "inject" is one
small, reversible disruption to a scored service -- the same pattern as a
real competition, where a red team member stops AD DS on the DC to drop
LDAP, or disables RDP on a workstation. Blue team's job is to notice the
scoring dashboard drop, **and to catch the attacker doing it** -- the
unusual network session, the login event, the command that ran -- the
same way they'd catch a real intrusion.

This is **not** an exploit toolkit and it is **not** a denial-of-service
script. Every scenario:

- Changes exactly one service or setting.
- Has a matching restore command that undoes it exactly.
- Never deletes data, corrupts a config file, or touches the VM outside
  the one service being tested.
- Never weakens or removes an intentional vulnerability from
  README.md / VULNERABILITIES.md -- it only interrupts a service that is
  already running.

## Access model -- this is the part that matters for training

By default (`--via network`), the tool logs in over the actual VLAN like
a real attacker and runs the command there, so blue team has something
real to detect:

| Target | Login path | What it generates |
|---|---|---|
| Windows (GIRAFFE, MEERKAT, ZEBRA) | WinRM (HTTPS 5986, NTLM) as `ZOOLAND\domainadmin` | A real network session to 5986, a Windows Security logon event (4624, type 3) for `domainadmin`, and the service-control event for whatever got stopped |
| Linux (PENGUIN, OTTER, FLAMINGO, HIPPO) | SSH as `localuser` + `sudo` | A real SSH session (`sshd`/`auth.log` entry), and a `sudo` child process running the stop command |

These accounts aren't arbitrary. `domainadmin` is the direct payoff of
this range's weak AD password policy vulnerability (see README.md) --
using it here *is* the "attacker already compromised a domain admin"
scenario, not a shortcut around it. `localuser` stands in for "the
attacker already has a privileged foothold": none of the documented
low-privilege weak accounts (`admin`/`admin`, `ftpuser`/`ftpuser`,
`mail`/`mail`, `dbadmin`/`password`, ...) have sudo rights, so they
can't actually stop a systemd service or container -- this tool doesn't
pretend otherwise.

**If blue team detects and locks out the attacker** -- rotates
`domainadmin`'s password, firewalls off WinRM/SSH, disables the account
-- `--via network` injects start failing. That's the system working as
intended, not a bug to work around.

`--via guest-agent` is the original mechanism (`sudo qm guest exec` on
the Ludus host, over the QEMU guest agent). It leaves **no network trace
and no login event**, so it does not simulate an attacker. Use it only as
a white-cell/instructor override -- most commonly, to force `restore-all`
at the end of a session even if blue team successfully cut the simulated
attacker's access.

## Requirements

Run from the Ludus host.

- **`--via network`** (default): needs `sshpass` for the Linux targets
  and the `winrm` Python package (`pip install pywinrm`) for the Windows
  targets -- the same optional tools `tests/check.py` already uses, with
  the same behavior if one is missing: that scenario reports an error
  telling you what to install, or you can fall back to `--via
  guest-agent` for that one call.
- **`--via guest-agent`**: needs the `sudo qm list` / `sudo qm guest exec`
  rights documented in `CLAUDE.md`.

```bash
python3 redteam/injects.py list
```

## Usage

```bash
# See every available inject and which scored check(s) it hits
python3 redteam/injects.py list

# Check current live state of every service this tool knows about
python3 redteam/injects.py status

# Check one
python3 redteam/injects.py status giraffe-dns-stop

# Apply one inject over the network (default) -- generates a real
# domainadmin WinRM logon or localuser SSH session for blue team to catch
python3 redteam/injects.py apply giraffe-dns-stop

# Undo it
python3 redteam/injects.py restore giraffe-dns-stop

# Apply 3 random injects without saying which (self-practice: find them
# via monitoring / the scoring dashboard / tests/check.py, not this log)
python3 redteam/injects.py random -n 3 --hide

# End of session: put everything back over the network
python3 redteam/injects.py restore-all

# If blue team locked the attacker out and restore-all over the network
# can't get back in, force cleanup via the guest agent instead:
python3 redteam/injects.py restore-all --via guest-agent
```

Range IPs are auto-detected the same way `tests/check.py` does (reads
this host's own `10.<X>.99.*` address); pass `--range X` to override.

If blue team rotates the attacker credentials as part of hardening
(which is realistic and expected), set `REDTEAM_LINUX_PW`,
`REDTEAM_WIN_USER`, or `REDTEAM_WIN_PW` in the environment instead of
editing the script.

Every apply/restore is appended to `redteam/inject_log.jsonl` (gitignored,
local only) with a timestamp and which access path was used -- useful for
an instructor, or for grading yourself afterward even when you ran
`--hide`.

## Scenarios and the scored checks they hit

| Scenario | VM | Scored check(s) | Points at risk |
|---|---|---|---|
| `giraffe-dns-stop` | GIRAFFE | DNS resolution (53) | 100 |
| `giraffe-ldap-kerberos-stop` | GIRAFFE | LDAP (389) + Kerberos (88) | 200 |
| `meerkat-rdp-stop` | MEERKAT | RDP (3389) | 50 |
| `zebra-smb-stop` | ZEBRA | SMB (445) | 50 |
| `penguin-http-stop` | PENGUIN | HTTP CrazyRhino (80) | 100 |
| `penguin-ssh-stop` | PENGUIN | SSH banner (22) | 25 |
| `otter-ftp-stop` | OTTER | FTP login (21) | 50 |
| `otter-ssh-stop` | OTTER | SSH banner (22) | 25 |
| `flamingo-smtp-stop` | FLAMINGO | SMTP relay (25) | 75 |
| `flamingo-imap-pop3-stop` | FLAMINGO | IMAP (143) + POP3 (110) | 100 |
| `flamingo-ssh-stop` | FLAMINGO | SSH banner (22) | 25 |
| `hippo-mysql-stop` | HIPPO | MySQL (3306) | 75 |
| `hippo-ssh-stop` | HIPPO | SSH banner (22) | 25 |

`giraffe-ldap-kerberos-stop` and `flamingo-imap-pop3-stop` hit two checks
at once because that's realistic: NTDS backs both LDAP and Kerberos on a
real DC, and Dovecot backs both IMAP and POP3 on a real mail server. A red
team doesn't usually get to pick just one.

## What blue team should look for

- **Windows**: Security Event ID 4624 (logon type 3, network) for
  `domainadmin` from an unexpected source IP (the Ludus host, not a
  normal admin workstation), followed by a Service Control Manager event
  (7036/7040) for the service that stopped. If Wazuh is deployed
  (`WAZUH.md`) these should show up as alerts; otherwise `Get-WinEvent`
  or Event Viewer on the target VM.
- **Linux**: an `sshd` "Accepted password for localuser" line in
  `/var/log/auth.log` (or `journalctl -u ssh`) from an unexpected source,
  followed by a `sudo` entry running the stop command. A packet capture
  on VLAN 10 shows the actual SSH/WinRM TCP session.
- **Either way**: the scoring dashboard drop itself (from VLAN 99 --
  see README.md's Firewall Rules) is the downstream symptom; the login
  and command are the upstream intrusion blue team is really being
  trained to catch.

## Why this is safe for the range

- Network mode uses real but already-privileged accounts this range
  already documents (`domainadmin`, `localuser`); it never brute-forces,
  guesses, or creates new credentials, and it never touches an account
  tied to a documented vulnerability's own scoring/demo path.
- Every `apply` command is a plain service stop or a single, documented
  registry/setting flip (e.g. `fDenyTSConnections`), reversed by the exact
  paired `restore` command -- nothing destructive, nothing that needs a
  rebuild.
- Guest-agent mode goes through the QEMU guest agent, not the service
  being disrupted, so a stopped SSH/RDP/SMB service never locks that
  fallback out of the VM -- which is exactly why it's reserved for
  instructor cleanup, not for the graded exercise itself.
- `restore-all` is idempotent and safe to run even if nothing was ever
  applied -- useful as a "reset before I hand this off" step.
