# PROGRESS

## Current step
Cycle 2: re-running `ludus range deploy -t user-defined-roles` after DNS fix (commit 223051d).

## Done
- Read CLAUDE.md + README.md; wrote tests/check.py (commit 1f415cf). Not yet run against the range.
- Git identity set repo-local: Claude <noreply@anthropic.com>.
- Preflight: all 5 required templates BUILT; all ludus_ccdc_* roles registered; range config set from range-config.yaml.

## Decisions
- Range ID is CLAUDEAGENT, network 10.1.0.0/16 (X=1).
- check.py SKIPs checks whose tool is missing; use `--strict` for the definition-of-done run.

## Next
- When deploy ends: `ludus range errors`, `ludus range logs`, then `python3 tests/check.py` (from JAGUAR via qm guest exec or direct if routable).

## Findings
- Cycle 1 (full deploy, ~03:50-05:15) ended ERROR. Root cause: Ludus router AdGuard DNS (10.1.10.254) is unreachable from range VMs because Ludus default rule `-s 10.1.0.0/16 -d 10.0.0.0/8 REJECT` also hits INPUT to the router. apt hung on PENGUIN; FLAMINGO/HIPPO failed Ludus's python3-apt prereq; PENGUIN apt cache update failed. ZEBRA WinRM error was rescued (not a failure).
- Fix: first task in every Linux role sets 1.1.1.1/8.8.8.8 (commit 223051d). Also set live on the 6 Linux VMs via qm guest exec. Not touching Ludus/router config.
- LESSON: `ludus ansible role add -d` does NOT overwrite a registered role; always use `-f`.
- Access: `sudo qm guest exec <vmid> --timeout 30 -- /bin/bash -c '...'` works (vmids 113 router,114 GIRAFFE,115 MEERKAT,116 ZEBRA,117 PENGUIN,118 OTTER,119 FLAMINGO,120 HIPPO,121 JAGUAR,122 SCORESVR).

## BLOCKED
- None. (ludus_ccdc_blueteam_access was blocked on admin-only pveum; resolved by the user running the steps manually as admin, see Log.)

## Log
- 03:50 full deploy started.
- ~05:20 cycle 1 ended ERROR (DNS). Fix committed 223051d; roles re-registered; starting roles redeploy.
- 05:25 roles re-added with -f (DNS task + frontend ESLint fix 1e6ded7); redeploying roles.
- 05:28 GIRAFFE found powered off (unknown cause); ludus power on. FLAMINGO/HIPPO still on DHCP IPs (.212/.180) -> need full deploy.
- 06:25 full deploy: only SCORESVR failed (pip DNS). Ludus re-applies router DNS via /etc/network/interfaces + resolved.conf; role now edits both (commit after 1e6ded7). Redeploying roles.
- 06:27 roles redeploy: DNS fix confirmed; only error left is the BLOCKED blueteam_access role. Next: run tests/check.py.
- 06:50 First check.py run: 625/900. Fixes: GIRAFFE New-ADUser -Name (588f3ea), ZEBRA SMB1 reboot, FLAMINGO postfix 'permit, reject', OTTER chown root /srv/ftp. HIPPO test DB: role uses testuser not anon ''@'%' (doc mismatch; left as is, test accepts either). Next: force re-add roles, redeploy roles, rerun check.
- 06:55 check run 2: 775/900, vulns 29/31. Left: SMTP timeout (FLAMINGO), RDP jsmith auth rejected, IDOR skip (no orders).
- 07:05 RDP: engine CredSSP pubKeyAuth was unsealed -> correct creds got TLS alert. Implemented NTLM sealing in scoring_engine/checks.py (+role copy). Verified from host: jsmith OK, wrong pw fails. NLA experiment on MEERKAT reverted to 0. FLAMINGO postfix needs 'permit_mynetworks, reject_unauth_destination' (60fe1a1). Redeploying roles.
- 07:20 ROOT CAUSE of engine 0/15 + router DNS: range-config always_blocked_networks 10.0.0.0/8 includes own 10.1.0.0/16; Ludus emits it before user rules. Replaced by 10/8 minus 10.1/16. Applying with deploy -t network.
- 07:35 DONE except BLOCKED pveum. check.py --strict exit 0 (900/900, 31/31). Engine dashboard 15/15 UP. REPORT.md written.
- Later: user ran pveum steps as admin on the Proxmox host. User BlueTeam@pve created. `pvesh set /pools/ZooLand-BlueTeam -vms ...` failed: "VM 114 belongs already to pool 'CLAUDEAGENT' and 'allow-move' is not set" (a VM can be in one pool only; moving would risk the Ludus user's access). Decision: grant PVEVMUser per VM (/vms/114-120) instead. Verified via `pveum acl list`. Role rewritten to do the same (no pool); README/SETUP/ARCHITECTURE updated. The empty ZooLand-BlueTeam pool left on the host is unused (pveum pool delete ZooLand-BlueTeam to remove).
- Not re-run: the rewritten role has not been deployed (non-admin cannot run it); it mirrors the commands that worked manually.
- Scoring engine now rotates accounts round-robin per round (ftp: mlopez/rthomas; imap: jsmith/bwilson/mchen; rdp: jsmith/bwilson/mchen/mlopez/rthomas). Dashboard key modal lists every rotation account with its own password field; API: GET /api/credentials/<svc> -> {users}, POST {username,password} (must be in rotation); new table service_user_credentials (legacy single-account row still honoured). Verified all 10 accounts log in on the live range from the Ludus host; API/rotation tested in a temp venv. NOT yet deployed to SCORESVR (needs `ludus ansible role add -f -d roles/ludus_ccdc_scoring_engine` + roles redeploy).
- 13:40 FRESH-DEPLOY TEST: all roles re-added -f, config set; destroying range (ludus range rm) then full deploy.
- 14:25 Fresh full deploy ended ERROR: GIRAFFE scooper/jharris/mrobinson not created ('C00p3r$IT9' in double quotes -> $IT9 empty -> complexity fail). ZEBRA WinRM error is the known rescued one (failed=0). Fixed (single quotes); redeploying roles only.
- 15:25 FRESH-DEPLOY RESULT: range destroyed, full deploy (13:41-14:24) + roles-only redeploy (14:25-15:21) after fixing GIRAFFE (a0e6ea6). All hosts failed=0 except SCORESVR's ludus_ccdc_blueteam_access (admin-only, known). check.py --strict exit 0 (900/900, 31/31). Engine rotating live (ftp mlopez/rthomas, imap jsmith/bwilson/mchen, rdp 5 users), 15/15 UP. VM ids unchanged (114-120) so the admin-applied per-VM ACLs still match.
- 17:21 blueteam_access now probes for Proxmox rights and skips with a WARNING (bbc7f79). Limited deploy (-l SCORESVR --only-roles) ended SUCCESS, failed=0, no errors. Non-admin deploys no longer report an error; admin still has to apply the ACLs.
- 23:24 HIPPO test DB decision: follow the role (testuser/testuser). README, CLAUDE.md and check.py (now requires testuser) updated; vuln checks 31/31 live.
- 23:27 Docs audit: README, SETUP (scoring total was 800, SSH rows missing), ARCHITECTURE, VULNERABILITIES, UPDATES updated for rotation, SMTP relay config, FTP dirs, testuser, always_blocked_networks, blueteam ACLs.
- 23:32 DEMO.md reviewed: section 1 (rotation, key button), 11 + quick ref (root SSH password login is refused; use weak users or localuser+sudo), 12 (test_range.sh verified: 0 failed, 1 warn; check.py mention). README OS root row fixed.
- 23:39 FTP and IMAP rotations now 5 accounts each (same 5 as RDP). New OS accounts jsmith/bwilson/mchen on OTTER, mlopez/rthomas on FLAMINGO (ZooLand2025!). check.py has per-account rotation section (15/15 live). Limited deploy of ftp/mail/scoring roles on OTTER/FLAMINGO/SCORESVR failed=0. Docs updated.
- 23:48 Employee passwords: each of 15 domain employees now has its own basic weak password (see UPDATES.md / README); ZooTime! only for root/Administrator/domainadmin. Roles redeployed on GIRAFFE/MEERKAT/OTTER/FLAMINGO/SCORESVR failed=0. check.py --strict exit 0 (900/900, 31/31, rotation 15/15). Old password still works for RDP up to 60 min (NTLM old-password window).
- 23:56 Weak domain password policy set in domain_users role (min 5, complexity off, lockout 0). ajohnson/sunny, tlee/dragon, kbrown/letmein. New vuln check; GIRAFFE role deploy failed=0. check.py --strict exit 0 (900/900, 32/32, rotation 15/15).
- 00:22 Added public 'Meet the Team' page (/team, GET /api/team) on CrazyRhino (PENGUIN): staff directory with name/department/email, found via normal browsing (nav+footer link), teaches real-world username-convention OSINT before AD password spray. Not a vuln table entry. Deployed to PENGUIN failed=0; verified live from JAGUAR. check.py --strict exit 0 (900/900, 32/32, rotation 15/15).
- 00:24 FRESH-DEPLOY TEST #2: destroying range (ludus range rm) to test all session's changes (rotation, weak passwords, policy, team page) from scratch.
- 02:06 FRESH-DEPLOY #2 RESULT: full destroy (ludus range rm) + full deploy (00:25-02:06, ~1h41m). `ludus range errors` returned NOTHING — first fully clean deploy this session (blueteam_access now warns+skips instead of erroring). All hosts failed=0. check.py --strict exit 0 (900/900, 32/32, rotation 15/15). Team page (/team, /api/team) verified live from JAGUAR: 15 employees, HTTP 200. Weak AD password policy (complexity off, min 5, lockout 0) confirmed live on GIRAFFE. Every change made this session survives a from-scratch deploy. VM ids unchanged (114-120) so admin-applied BlueTeam ACLs still match.
