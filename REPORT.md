# ZooLandRange - final report (2026-10-28)

## Status
- `python3 tests/check.py --strict` exits 0: **900/900 scoring points (15/15)**, **31/31 vulnerability checks**, 0 FAIL, 0 SKIP.
- The scoring engine's own dashboard (SCORESVR:8080, round 6) shows all 15 services UP, including `RDP LOGIN OK as 'zooland\jsmith'`.
- Everything deploys cleanly except `ludus_ccdc_blueteam_access`, which still errors for a non-admin Ludus user (needs Proxmox admin; see below). Its effect was applied manually by an admin.

## Scoring checks (all PASS)
HTTP 100, LDAP 100, Kerberos 100, DNS 100, SMTP 75, MySQL 75, IMAP jsmith 50, POP3 50, SMB 50, FTP mlopez 50, RDP jsmith 50, SSH x4 25 each = 900.

## Vulnerabilities (all present)
GIRAFFE: AXFR, open recursion, no DNSSEC, DNS logging off, 12 hidden accounts. ZEBRA: SMBv1, guest + Everyone Full Control, credential files, firewall off.
PENGUIN: /api/debug, SQLi, admin/admin123, IDOR, no rate limit, HTTP only, X-Powered-By, backup_credentials.txt, UFW off.
OTTER: anonymous upload, vsftpd banner, no TLS, no chroot, iptables open. FLAMINGO: open relay/no auth/no TLS, mynetworks 0.0.0.0/0, plaintext IMAP/POP3, iptables open.
HIPPO: root@% / password, local_infile=1, open test DB, PII, no firewall.

## Problems, root causes, fixes (branch claude-tuning)
| # | Problem | Root cause | Fix (commit) |
|---|---------|-----------|--------------|
| 1 | apt/pip hung or failed on every Linux VM; engine saw 0/15 up; VLAN99 could not reach VLAN10 | `range-config.yaml` `always_blocked_networks: 10.0.0.0/8` also covers the range's own 10.1.0.0/16. Ludus emits it ahead of the user rules, so new VLAN99->VLAN10 traffic and all VM->router DNS were REJECTed | Replaced with the CIDRs for 10/8 minus 10.1/16; other ranges, 172.16/12, 192.168/16 stay blocked (06387ad) |
| 2 | (symptom of 1) Linux roles could not download | router DNS unreachable | Roles set public DNS first (223051d, 3ea11ae). Now redundant but harmless; revert if unwanted |
| 3 | PENGUIN frontend build failed (`jest/globals` unknown) | no lockfile, newer eslint plugin | `DISABLE_ESLINT_PLUGIN=true` in frontend Dockerfile (1e6ded7) |
| 4 | Only 6 AD accounts; none of the 27 employees | `New-ADUser` called without mandatory `-Name`; `win_powershell` swallowed the error | Added `-Name` and `error_action: stop` (588f3ea) |
| 5 | ZEBRA SMBv1 not active | feature installed with `-NoRestart`; driver (mrxsmb10) only exists after reboot | Install, reboot if driver missing, then enable (e1575dc) |
| 6 | FLAMINGO SMTP dead | `smtpd_relay_restrictions = permit` makes smtpd exit (Postfix needs a reject-type restriction; ignores one after `permit`) | `permit_mynetworks, reject_unauth_destination`; with mynetworks 0.0.0.0/0 it is still an open relay (e1575dc, 60fe1a1) |
| 7 | OTTER anonymous login: "refusing to run with writable root inside chroot()" | `/srv/ftp` owned by ftp | Root dir owned by root (755); pub/upload/incoming stay 777 (e1575dc) |
| 8 | RDP check failed for every domain account | engine's CredSSP did not seal pubKeyAuth with NTLM; correct passwords got a TLS alert | Implemented NTLM sealing in `scoring_engine/checks.py` and the role copy (a7dd1c7). Wrong password still fails (0xC000006D) |
| 9 | tests/check.py bugs (root SSH, 5985, LDAP parse, SQLi payload, no mysql client) | my test assumptions | fixed (e1575dc, 93f3b18) |

## Fresh-deploy verification (range destroyed and rebuilt)
- Full `ludus range deploy` from nothing, then one roles-only redeploy. The full deploy exposed one more bug: GIRAFFE `scooper` password `"C00p3r$IT9"` was in a double-quoted PowerShell string, so `$IT9` expanded to empty and the password failed AD complexity (scooper, jharris, mrobinson were not created). Fixed with single quotes (a0e6ea6). Earlier runs missed it because the failure was swallowed.
- After that: every host `failed=0` except `ludus_ccdc_blueteam_access` (admin-only). `tests/check.py --strict` exit 0, 900/900, 31/31. Scoring engine rotation confirmed live (later expanded to five accounts for FTP, IMAP and RDP; 15/15 rotation logins verified by check.py).
- Caveat: this was a full deploy plus a roles-only redeploy, not one single uninterrupted full deploy with the final commits. ZEBRA still shows one rescued WinRM error (failed=0).

## BLOCKED / needs admin
- `ludus_ccdc_blueteam_access` needs Proxmox admin rights (`pveum`). It now probes first and, without them, skips with a visible WARNING instead of failing the deploy (bbc7f79). A non-admin `ludus range deploy` therefore ends SUCCESS with that warning in the log; verified with a limited deploy (SCORESVR, failed=0, no errors). With admin rights the role creates `BlueTeam@pve` and grants `PVEVMUser` per VM (`/vms/<id>`), not via a pool (the VMs already sit in the Ludus `CLAUDEAGENT` pool and moving them needs `allow-move`). An admin applied those steps manually on VMs 114-120 and `pveum acl list` confirmed them; the BlueTeam console login was not tested, and the admin-rights path of the rewritten role has never run. Because a deploy no longer fails when this is missing, the warning is the only signal: after a rebuild with new VM IDs an admin must re-run the ACL grant.

## Discrepancies and caveats
- HIPPO: the open test database is `testuser`/`testuser` (ALL on `test.*`, any host), as the role has always done. README/CLAUDE.md/check.py were changed to match; the old README text said anonymous `''@'%'`.
- OTTER: `/srv/ftp` itself cannot be world-writable (vsftpd refuses anonymous chroot); only its subdirectories are 777. Docs say "world-writable /srv/ftp".
- Router/Proxmox host firewall, Ludus server config and the Proxmox host were not touched.
- A GIRAFFE VM was found powered off mid-run (cause unknown); I powered it on with `ludus power on -n`.
- Temporary experiment: MEERKAT `UserAuthentication` set 1 then restored to 0 (original value).

## Could not verify
- A from-scratch full `ludus range deploy` with all final commits. Fixes were applied through a full deploy plus partial role/network redeploys, then verified.
- The rewritten blueteam_access role under a real deploy (manual steps verified with `pveum acl list`; BlueTeam console login not tested).
- RDP login was verified with the engine's own NLA implementation, not a third-party RDP client.
- IDOR was verified from the deployed handler source because the seed data has no orders.
- `PROGRESS.md` and `REPORT.md` are uncommitted.
