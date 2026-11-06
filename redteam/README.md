# Red-team injects

A practice tool for PRCCDC-style play on ZooLandRange: each "inject" is one
small, reversible disruption to a scored service -- the same pattern as a
real competition, where a red team member stops AD DS on the DC to drop
LDAP, or disables RDP on a workstation. Blue team's job is to notice the
scoring dashboard drop and fix the *specific* thing that changed.

This is **not** an exploit toolkit and it is **not** a denial-of-service
script. Every scenario:

- Changes exactly one service or setting.
- Has a matching restore command that undoes it exactly.
- Never deletes data, corrupts a config file, or touches the VM outside
  the one service being tested.
- Never weakens or removes an intentional vulnerability from
  README.md / VULNERABILITIES.md -- it only interrupts a service that is
  already running.

## Requirements

Run from the Ludus host, as the `claude` user (or whichever account has
the `sudo qm guest exec` / `sudo qm list` grants). This uses the QEMU
guest agent, so it works even if range networking is broken -- the same
access path documented in `CLAUDE.md` / `PROGRESS.md`.

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

# Apply one inject (prints which check(s) it affects and how to undo it)
python3 redteam/injects.py apply giraffe-dns-stop

# Undo it
python3 redteam/injects.py restore giraffe-dns-stop

# Apply 3 random injects without saying which (self-practice: find them
# via the scoring dashboard / tests/check.py, not this log)
python3 redteam/injects.py random -n 3 --hide

# End of session: put everything back
python3 redteam/injects.py restore-all
```

Every apply/restore is appended to `redteam/inject_log.jsonl` (gitignored,
local only) with a timestamp, so you can always see exactly what was done
-- useful for an instructor, or for grading yourself afterward even when
you ran `--hide`.

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

## Why this is safe for the range

- `qm guest exec` goes through the QEMU guest agent, not the service being
  disrupted, so a stopped SSH/RDP/SMB service never locks this tool out of
  the VM.
- Every `apply` command is a plain service stop or a single, documented
  registry/setting flip (e.g. `fDenyTSConnections`), reversed by the exact
  paired `restore` command -- nothing destructive, nothing that needs a
  rebuild.
- VM IDs are resolved by name match at run time (`sudo qm list`), so this
  works under any range/user prefix without editing the script.
- `restore-all` is idempotent and safe to run even if nothing was ever
  applied -- useful as a "reset before I hand this off" step.
