CLAUDE.md: ZooLandRange

ZooLandRange is a Ludus cyber range for CCDC practice. It has 9 VMs across 2 VLANs, a Windows AD domain (zooland.local), and a scoring engine. Every VM is intentionally vulnerable.

Mission

Deploy the range, test it, and fix deployment problems until everything works. Run the loop below on your own for hours without user input. The user is not watching: do not ask questions and do not wait for approval.

The vulnerabilities are intentional. Never fix or harden them. Your job is to fix things that are broken (failed Ansible tasks, services that don't start, wrong IPs, scoring checks that fail). Before changing any setting that looks like a security hole, check the vulnerability tables in README.md. If it is listed there, it must stay.

Autonomy
Work without asking the user anything. When something is ambiguous, pick the most reasonable option, record the decision in PROGRESS.md, and continue.
Keep a running log in PROGRESS.md: what you tried, what failed, what you changed, the current step, and what is next. Update it after every deploy/test cycle. Your context will fill up over a long run, so at the start of every session (and after any context reset) read PROGRESS.md first and resume from it.
Keep long commands from hanging forever. Wrap them in timeout. Note that `ludus range deploy` returns as soon as the deploy starts, so the timeout does not cap the deploy itself: poll `ludus range status` every 60 seconds with an overall cap of about 2 hours. A full deploy takes about 45 minutes and a roles-only redeploy up to an hour. Do not use ludus range logs -f or other follow commands, which never exit. Read ludus range logs once the deploy ends. A recap line `failed=0` per host is the real success signal.
Some things only the user can do (see "What you cannot do"). When you hit one, write it under a BLOCKED heading in PROGRESS.md, work on anything else that is not blocked, and stop only when nothing else is left.
Stop when the definition of done is met, or after 5 failed attempts at the same problem. Then write the final report to REPORT.md.
Being unattended does not widen your limits. The Rules section still applies.
Environment
You run as Linux user claude on the Ludus server (a homelab VM, safe to rebuild; the user snapshots it before runs).
The Ludus CLI is authenticated as Ludus user CLAUDEAGENT (non-admin) through LUDUS_API_KEY. LUDUS_URL is https://127.0.0.1:8080. Never print, log, or commit the API key.
Range number: 1. Range network 10.1.0.0/16. Every IP below is 10.1.<vlan>.<last octet>.
VM names in Proxmox start with the range ID, for example CLAUDEAGENT-GIRAFFE. Confirm with sudo qm list.
Range config: `range-config.yaml` in this repo.
Other docs in the repo: README.md (full details and vulnerability tables), SETUP.md, ARCHITECTURE.md, DEMO.md, BLUETEAM.md, WAZUH.md.
Ludus flags vary by version. If a command fails, run it with --help.
What you cannot do
You are a non-admin Ludus user. You cannot build or add Ludus templates, add sources, or manage users. If a template shows BUILT: FALSE in ludus templates list, record it under BLOCKED and tell the user which one to build as admin.
Your sudo access is limited to sudo qm list, sudo qm status *, sudo qm guest exec *, and sudo qm monitor *. Other qm commands and other sudo commands fail. Do not try to work around this.
You do not have the Proxmox host's iptables or systemd.
Range layout
VM	OS	IP	Ansible role	Services
GIRAFFE	Windows Server 2022	10.1.10.7	ludus_ccdc_domain_users	AD, DNS 53, Kerberos 88, LDAP 389, SMB 445
MEERKAT	Windows 11	10.1.10.12	ludus_ccdc_workstation	RDP 3389
ZEBRA	Windows Server 2022	10.1.10.15	ludus_ccdc_file_server	SMB 445/139
PENGUIN	Ubuntu 22.04	10.1.10.23	ludus_ccdc_web_server	HTTP 80, API 5000 (Docker), SSH 22
OTTER	Ubuntu 22.04	10.1.10.29	ludus_ccdc_ftp_server	FTP 21, passive 40000-40100, SSH 22
FLAMINGO	Debian 12	10.1.10.38	ludus_ccdc_mail_server	SMTP 25, POP3 110, IMAP 143, SSH 22
HIPPO	Debian 12	10.1.10.41	ludus_ccdc_db_server	MariaDB 3306, SSH 22
JAGUAR	Kali	10.1.99.34	ludus_ccdc_kali_setup	Red team box
SCORESVR	Ubuntu 22.04 + XFCE	10.1.99.17	ludus_ubuntu_desktop, ludus_ccdc_scoring_engine, ludus_ccdc_blueteam_access	Scoring dashboard 8080

Required templates (must show BUILT: TRUE): win2022-server-x64-template, win11-22h2-x64-enterprise-template, ubuntu-22.04-x64-server-template, debian-12-x64-server-template, kali-x64-desktop-template.

Domain controller GIRAFFE must be healthy before the domain-joined VMs (MEERKAT, ZEBRA) can join. If those fail, check GIRAFFE first.

Firewall rules: VLAN 10 to VLAN 99 allows only TCP 80, 443, 8080. VLAN 99 to VLAN 10 allows everything. All other inter-VLAN traffic is rejected. JAGUAR and SCORESVR (VLAN 99) can therefore reach every corporate VM.

Credentials (lab only, intentionally weak)
Where	Account	Password
Windows local admin	Administrator	ZooTime!
Domain admin	ZOOLAND\domainadmin	ZooTime!
Domain employees (15 documented)	jsmith, bwilson, mchen, mlopez, rthomas, and others	ZooLand2025!
Linux root (PENGUIN, OTTER, FLAMINGO, HIPPO)	root	ZooTime! (SSH root password login is refused by sshd defaults; use localuser + sudo)
Linux weak users	admin / admin, ftpuser / ftpuser, mail / mail, webadmin / password, dbadmin / password, user / password	see left
Ludus Linux default	localuser	password (passwordless sudo; debian/debian does not work)
Kali	kali	kali
MariaDB	root / password, admin / admin, dbuser / dbuser, testuser / testuser	see left
CrazyRhino app	admin / admin123, johndoe / password123	see left
Proxmox blue team	BlueTeam@pve	BlueTeam

If Windows login fails before the roles have run, try the Ludus defaults (localuser / password, domainadmin / password) and check whether the role changed them.

Deploy and debug loop
bash
ludus range config set -f <range-config>.yaml
timeout 3600 ludus range deploy                           # full deploy
timeout 1800 ludus range deploy -t user-defined-roles     # re-run roles only (faster)
ludus range status
ludus range errors                                        # first stop when a deploy fails
ludus range logs                                          # full Ansible output
Before the first deploy, check ludus templates list (all five required templates built) and ludus ansible roles list (all ludus_ccdc_* roles present). If a role is missing and its folder is in roles/, register it with ludus ansible role add -d roles/<role-name>.
tests/check.py already exists (see Definition of done); run it after each deploy.
If a deploy fails, read ludus range errors, then ludus range logs, and find the failing Ansible task.
Fix the cause in the YAML or the ludus_ccdc_* role. After editing a role, re-register it with ludus ansible role add -d <role-dir> and redeploy with -t user-defined-roles.
Run python3 tests/check.py.
Commit the fix, update PROGRESS.md, and repeat from step 3.

Prefer partial redeploys over full ones; for a single role use `-t user-defined-roles -l CLAUDEAGENT-<VM> --only-roles <role>`. A full destroy and redeploy can still surface bugs that partial runs hide, so do one before declaring done. Do a full destroy and rebuild only when a VM definition changed (template, RAM, CPUs, IP, VLAN) or the range is badly broken, and note it in PROGRESS.md.

Reaching the VMs

Range VMs sit behind a Ludus router, so the Ludus host may not reach them directly. Try these in order and record what works in the Notes section at the bottom:

QEMU guest agent (works with no networking):
bash
   sudo qm list
   sudo qm guest exec <vmid> -- <command>

The agent may not answer while a VM is still booting. Wait and retry. 2. Run tests from JAGUAR. VLAN 99 can reach all of VLAN 10, so run the checks on JAGUAR through qm guest exec or SSH. 3. Direct from this host (works here, try this first): ssh for Linux and pywinrm over HTTPS port 5986 for Windows, if ping 10.1.10.7 works. 4. Screen problems (Windows login screens, hung installers):

bash
   echo "screendump /tmp/screen.ppm" | sudo qm monitor <vmid>
   convert /tmp/screen.ppm /tmp/screen.png

Then view the PNG. Delete the image files afterward; do not commit them.

Definition of done

All of these must be true:

ludus range deploy completes with no errors. (A skip warning from ludus_ccdc_blueteam_access counts as clean for a non-admin deploy, but real blue team access still needs an admin.)
All 15 scoring checks pass (900 points per round, listed below).
Every intentional vulnerability in the next section is still present.
python3 tests/check.py exits 0.

tests/check.py exists; extend it when checks change. `python3 tests/check.py --strict` (SKIP counts as failure) is the done check. It should check the 15 scoring services and confirm each intentional vulnerability exists, print which check failed, and exit non-zero on any failure.

Scoring engine checks

The engine on SCORESVR polls every 30 seconds. Dashboard: http://10.1.99.17:8080/. It is a Flask app (scoring_engine.service, user scoring, code in /opt/scoring_engine) with its database at /opt/scoring_engine/scores.db. Credentialed checks rotate accounts round-robin, one per round; each account's password can be set from the dashboard key button.

Check	Points
HTTP CrazyRhino (PENGUIN:80)	100
LDAP (GIRAFFE:389)	100
Kerberos (GIRAFFE:88)	100
DNS resolution (GIRAFFE:53)	100
SMTP open relay (FLAMINGO:25)	75
MySQL (HIPPO:3306)	75
IMAP login, rotates jsmith/bwilson/mchen (FLAMINGO:143)	50
POP3 banner (FLAMINGO:110)	50
SMB (ZEBRA:445)	50
FTP login, rotates mlopez/rthomas (OTTER:21)	50
RDP, rotates jsmith/bwilson/mchen/mlopez/rthomas (MEERKAT:3389)	50
SSH banner on PENGUIN, HIPPO, FLAMINGO, OTTER (:22)	25 each
Vulnerabilities that must stay
GIRAFFE: DNS zone transfer (AXFR) allowed to anyone, recursion open, no DNSSEC, DNS logging off. The 12 hidden AD accounts exist (check.py reports 13 undocumented, because domainadmin counts too).
ZEBRA: SMBv1 on, Everyone Full Control on Public and Shared, guest access on, firewall off, credential files in the shares.
PENGUIN: /api/debug leaks env vars, SQL injection in ?search=, admin / admin123, IDOR on /api/orders/:orderNumber, no rate limiting, HTTP only, X-Powered-By: Express, /opt/crazyrhino/backup_credentials.txt, UFW off.
OTTER: anonymous FTP with upload, no TLS, no chroot, world-writable FTP dirs (/srv/ftp/pub, upload, incoming are 777; /srv/ftp itself must stay root-owned because vsftpd refuses an anonymous chroot root that is writable), vsftpd version in banner, iptables open.
FLAMINGO: open SMTP relay, no SMTP auth, no TLS on Postfix or Dovecot, mynetworks = 0.0.0.0/0, plaintext IMAP/POP3 auth, iptables open.
HIPPO: MariaDB bound to 0.0.0.0, root@% login with password password, LOAD DATA LOCAL enabled, open test database (testuser / testuser has ALL on test.* from any host), PII in ccdc_company.employees, iptables open.
Rules
Do not change Proxmox networking, iptables on the Proxmox host, or Ludus server config.
Do not run ludus user, ludus-admin, or any command that affects other users' ranges.
The ludus_ccdc_blueteam_access role runs against the Proxmox host (creates the BlueTeam@pve user and grants PVEVMUser on each blue team VM; no pool, see Notes). Only touch it if it is the cause of a failure.
Do not remove or weaken a vulnerability to make a test pass. If a check fails because of a vulnerability, record it in REPORT.md instead.
Do not edit files outside this repo, except temporary files in /tmp.
Do not use rm -rf, force-push, or modify other users' home directories. `ludus range rm` on your own range is allowed when a full rebuild is needed.
Never git push: no credentials are configured here and the user pushes manually.
If a user is interactively present in the session, ask before outward-facing or hard-to-reverse actions (push, deleting things). Unattended runs follow the Autonomy rules and do not ask.
Do not paste the Ludus API key into any file, log, or commit.
Git
Work on the claude-tuning branch. Never commit to main and never force-push.
One commit per fix, with a message that names the VM or role and the problem.
Commit PROGRESS.md and REPORT.md. Never commit API keys, tokens, screenshots, or __pycache__.
Final report (REPORT.md)

When done or stopped, write REPORT.md with:

Pass/fail status of every scoring check and vulnerability check.
Each problem you found, its root cause, and the fix (commit hash).
Anything still failing, what you tried, and your best guess at the cause.
Anything BLOCKED that needs the user (for example a template that needs an admin build).
Anything you could not verify.
Notes (append what you learn here)
Range number: 1 (network 10.1.0.0/16)
Working access method to range VMs: the Ludus host reaches 10.1.10.x directly (it is not affected by the VLAN rules), and `sudo qm guest exec <vmid> --timeout N -- /bin/bash -c '...'` works (Windows: `-- powershell -NoProfile -Command ...`).
vmids: 113 router, 114 GIRAFFE, 115 MEERKAT, 116 ZEBRA, 117 PENGUIN, 118 OTTER, 119 FLAMINGO, 120 HIPPO, 121 JAGUAR, 122 SCORESVR.
Linux SSH: `localuser` / `password` with passwordless sudo (`debian`/`debian` and root password SSH do not work). Windows WinRM: HTTPS 5986 (not 5985), pywinrm ntlm, ignore cert validation.
`ludus ansible role add -d` does NOT overwrite an already-registered role; always add `-f`.
`ludus range status` can show a stale ERROR/DEPLOYING right after a deploy starts; wait before polling.
`range-config.yaml` `network.always_blocked_networks` must not cover the range's own 10.<N>.0.0/16 (Ludus emits it before the user rules and it breaks VLAN99->VLAN10 and router DNS). It lists 10/8 minus 10.1.0.0/16 and must be regenerated if the range number changes.
`ludus_ccdc_blueteam_access` needs a Proxmox admin (pveum). It grants PVEVMUser per VM (/vms/<id>); VMs already sit in the Ludus user pool, so they cannot join a second pool. Without Proxmox rights the role probes, skips and prints a WARNING, so non-admin deploys finish clean; an admin must apply the pveum steps (after a rebuild with new VM IDs, redo the ACL grant).
The scoring engine rotates accounts round-robin per round (FTP 2, IMAP 3, RDP 5); passwords for each are set from the dashboard key button.
`python3 tests/check.py --strict` is the definition-of-done check (exit 0 = 900/900 scoring, all vulnerability checks present).
Gotchas: Flask is not installed on the Ludus host; test the scoring engine in a temporary venv under /tmp. config.py guesses the range ID from the local IP, so running the engine code on the Ludus host picks the wrong network (it needs to run on SCORESVR, or patch the hosts).
In role PowerShell scripts, put passwords in single quotes: a `$` inside double quotes silently truncated one ("C00p3r$IT9"). `win_powershell` swallows non-terminating errors unless `error_action: stop` is set.
`ludus range errors` always lists a ZEBRA WinRM connection error that Ansible rescues; check the recap for failed=0 before chasing it.
