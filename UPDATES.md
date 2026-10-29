# ZooLandRange — Update Log

Chronological record of all changes made to the range after initial deployment.

---

## 2026-10-23

### Fix: Internet DNS Failure on Domain Members (Chocolatey Download Failed on MEERKAT)
**Files:** `roles/ludus_ccdc_domain_users/tasks/main.yml`, `roles/ludus_ccdc_workstation/tasks/main.yml`, `SETUP.md`

MEERKAT could not resolve `community.chocolatey.org`. Domain members use GIRAFFE
for DNS, and GIRAFFE's only forwarder was the Ludus router (`x.x.x.254`), which was
not answering. Direct queries to `1.1.1.1` worked, so the internet path was fine.

- **ludus_ccdc_domain_users** — GIRAFFE now sets public DNS forwarders
  (`1.1.1.1`, `8.8.8.8`, root hints kept) so lookups no longer depend on the router.
- **ludus_ccdc_workstation** — new task before the Chocolatey bootstrap waits up to
  2 minutes for internet DNS to resolve. If the DC still cannot resolve, it adds
  `1.1.1.1` as a secondary DNS server (DC stays primary so AD keeps working).
- **SETUP.md** — added a DNS troubleshooting note.

---

## 2026-05-21 (continued)

### New: `VULNERABILITIES.md` — Full Vulnerability Reference for Blue Team VMs
**Files:** `VULNERABILITIES.md`

Created a dedicated vulnerability reference listing all intentional misconfigurations
across the 7 blue team VMs (GIRAFFE, MEERKAT, ZEBRA, PENGUIN, OTTER, FLAMINGO, HIPPO).
Excludes the Debian router, JAGUAR, and SCORESVR.

---

### New: Network Isolation — Host Firewall Rules and `always_blocked_networks`
**Files:** `SETUP.md`, `range-config.yaml`

Added two-layer RFC 1918 isolation to prevent range VMs from reaching the Ludus
management network, other ranges, or the broader LAN:

- **`range-config.yaml`** — added `always_blocked_networks` (`10.0.0.0/8`,
  `172.16.0.0/12`, `192.168.0.0/16`) to the `network:` block. The Debian router
  enforces these blocks automatically on every `ludus range deploy`.
- **`SETUP.md`** — added new Step 4 with the host-level `iptables` commands
  (`br_netfilter`, intra-range ACCEPT, three RFC 1918 DROPs, `netfilter-persistent save`)
  that enforce the same isolation at the Proxmox hypervisor FORWARD chain. Renumbered
  old Steps 4 and 5 to 5 and 6.

---

## 2026-05-21 (continued)

### Docs: BlueTeam Proxmox Access Documented Across All Relevant Files
**Files:** `README.md`, `ARCHITECTURE.md`, `BLUETEAM.md`

Updated documentation to reflect the new `ludus_ccdc_blueteam_access` role:

- **ARCHITECTURE.md** — Added role to the Custom Ansible Roles table and to the Role File Structure and File Map sections.
- **README.md** — Added a "Proxmox Console Access" block to the SCORESVR section documenting the `BlueTeam@pve` user, `ZooLand-BlueTeam` pool, pool members, and `PVEVMUser` permission.
- **BLUETEAM.md** — Added a minimal "Proxmox" credential row (`BlueTeam@pve` / `BlueTeam`) to the credential sheet.

---

### New: `ludus_ccdc_blueteam_access` Role — BlueTeam Proxmox User and Pool
**Files:** `roles/ludus_ccdc_blueteam_access/tasks/main.yml`,
`roles/ludus_ccdc_blueteam_access/defaults/main.yml`,
`roles/ludus_ccdc_blueteam_access/meta/main.yml`,
`range-config.yaml`, `SETUP.md`

Added a new Ansible role that provisions Proxmox-level access for the blue team:

1. **Creates the `ZooLand-BlueTeam` Proxmox pool** — a logical container for all blue team VMs.
2. **Creates the `BlueTeam@pve` Proxmox user** (password: `BlueTeam`) — a PVE-realm account stored in Proxmox's own credential store (not Linux PAM).
3. **Resolves VM IDs dynamically** by querying `/cluster/resources` at deploy time, then adds GIRAFFE, MEERKAT, ZEBRA, PENGUIN, OTTER, FLAMINGO, and HIPPO to the pool. JAGUAR (red team) and SCORESVR (admin infra) are excluded.
4. **Grants `PVEVMUser`** to `BlueTeam@pve` on the pool — allows start/stop/reboot and console access to all pool members; does not allow config changes, cloning, or snapshot management.

All tasks delegate to `localhost` (the Proxmox host) and run once. The role is idempotent — re-deploying will not error if the user or pool already exists. Assigned to SCORESVR so it fires last, after all blue team VMs are provisioned.

---

## 2026-05-21

### Fix: RDP Scoring — Grant Domain Users Remote Desktop Access on MEERKAT
**Files:** `roles/ludus_ccdc_workstation/tasks/main.yml`

Added a PowerShell task that adds `ZOOLAND\Domain Users` to the `Remote Desktop Users`
local group on MEERKAT. Without this, domain accounts (including `jsmith`, the RDP scoring
account) could not authenticate via NLA, causing the RDP scoring check to fail every round.

---

### Fix: Replace `kali-linux-default` with Targeted Tool Set on JAGUAR
**Files:** `roles/ludus_ccdc_kali_setup/tasks/main.yml`

`kali-linux-default` (~2.4 GB, 1413 packages) consistently failed because several
required packages (`dbd`, `hyperion`, `windows-binaries`, `python3-masky`) are hosted
exclusively on Cloudflare CDN (`kali.download` / `104.17.253.239`) which is unreachable
from the Ludus host. The `netexec → python3-masky` dependency chain caused the entire
install to abort. Also switched mirror from `http.kali.org` (CDN load balancer) to
`archive-4.kali.org` (direct archive, no CDN). A targeted set of ~40 CCDC-relevant
tools is now installed instead.

---

### Change: Admin and Root Passwords Updated to `ZooTime!`
**Files:** `roles/ludus_ccdc_workstation/tasks/main.yml`,
`roles/ludus_ccdc_file_server/tasks/main.yml`,
`roles/ludus_ccdc_domain_users/tasks/main.yml`,
`roles/ludus_ccdc_web_server/tasks/main.yml`,
`roles/ludus_ccdc_db_server/tasks/main.yml`,
`roles/ludus_ccdc_mail_server/tasks/main.yml`,
`roles/ludus_ccdc_ftp_server/tasks/main.yml`,
`BLUETEAM.md`, `README.md`, `DEMO.md`, `WAZUH.md`

All admin and root credentials given to blue team updated from their previous values
(`password` for Windows admin accounts, `toor` for Linux root) to `ZooTime!`.

| Account | Previous | New |
|---|---|---|
| Windows `Administrator` (GIRAFFE, MEERKAT, ZEBRA) | `password` | `ZooTime!` |
| `ZOOLAND\domainadmin` | `password` (stale — account now explicitly created) | `ZooTime!` |
| Linux `root` (PENGUIN, OTTER, FLAMINGO, HIPPO) | `toor` | `ZooTime!` |

---

### New: `domainadmin` Account Explicitly Created
**Files:** `roles/ludus_ccdc_domain_users/tasks/main.yml`

`domainadmin` was referenced in documentation but never explicitly provisioned by any
role. Added a PowerShell task to create the account with `ZooTime!` and add it to
`Domain Admins`. Task is idempotent — resets password if account already exists.

---

### New: 25 Additional Domain Accounts Added
**Files:** `roles/ludus_ccdc_domain_users/tasks/main.yml`

Added two batches of new employee accounts to `zooland.local`:

**10 standard employees** (all `ZooLand2025!`, visible in README.md):
`ajohnson`, `tlee`, `swilliams`, `pgarcia`, `kbrown`, `lmartinez`, `djones`,
`nanderson`, `cwilson`, `emiller`

**12 hidden employees** (individual passwords, not in BLUETEAM.md — for red team discovery):
- 9 regular users with mixed weak/mid-strength passwords:
  `dwhite`, `hlee`, `rjohnson`, `asmith`, `bgarcia`, `cjones`, `pmiller`, `ltaylor`, `kwilliams`
- 3 Domain Admins: `scooper`, `jharris`, `mrobinson`

Password tiers for hidden accounts:

| Tier | Accounts | Passwords |
|---|---|---|
| Weak (plain wordlists) | `hlee`, `bgarcia`, `cjones`, `ltaylor`, `kwilliams`, `jharris` (DA) | `Password1`, `Welcome1!`, `Zooland1`, `Summer24!`, `Qwerty123`, `Admin123!` |
| Mid (rules required) | `dwhite`, `rjohnson`, `asmith`, `pmiller`, `scooper` (DA), `mrobinson` (DA) | `Wh1te2024$`, `F1nanc3!99`, `Sm1th#HR2!`, `Z00Keep3r!`, `C00p3r$IT9`, `N3tw0rk@1` |

---

### Fix: Remove Stale `domainuser` References from Documentation
**Files:** `README.md`, `ARCHITECTURE.md`

`ZOOLAND\domainuser` was listed as an autologon credential on MEERKAT and ZEBRA in
README.md. No role ever created this account. All references removed; credential rows
replaced with actual provisioned accounts (`domainadmin`, `Administrator`).

---

### Fix: Stale IP Addresses in WAZUH.md
**Files:** `WAZUH.md`

WAZUH.md referenced OTTER at `10.X.10.81` (old IP from before range redesign).
Corrected to `10.X.10.29` throughout (3 occurrences in the example config).

---

### Fix: Old VM Name References in WAZUH.md
**Files:** `WAZUH.md`

- ToC anchor link `#part-1--install-the-wazuh-server-ftp01` updated to `#...-otter`
- `GIRAFFE, MEERKAT, ZEBRA, and GIRAFFE` (duplicate) corrected to `GIRAFFE, MEERKAT, and ZEBRA`
- `wazuh@ftp01.zooland.local` updated to `wazuh@otter.zooland.local`

---

### New: Template Build Commands Added to SETUP.md
**Files:** `SETUP.md`

Added Step 0 covering Ludus template management. Documents all 5 required templates
with the correct commands (`ludus templates build -n <name>`, `ludus templates list`,
`ludus templates logs -f`) and a table mapping each template to the VMs that use it.
Previous SETUP.md only listed prerequisites without build instructions.

---

### Fix: Service Count Corrections
**Files:** `README.md`, `ARCHITECTURE.md`

- README.md scoring table: was missing 4 SSH banner checks; updated count from 11 → 15
  services and added SSH entries for PENGUIN, HIPPO, FLAMINGO, OTTER (25 pts each)
- Max points per round updated from 800 → 900
- ARCHITECTURE.md: corrected "14 services" → "15 services"

---

### Fix: Employee Account Documentation Updated
**Files:** `README.md`, `range-config.yaml`, `roles/ludus_ccdc_domain_users/tasks/main.yml`

- README.md GIRAFFE section now lists all 15 standard employees (previously showed 5)
- range-config.yaml GIRAFFE comment updated to reference all employee batches
- domain_users role header comment updated from "15 employees" to accurate 27-account count

---

### New: `UPDATES.md` Created
**Files:** `UPDATES.md` (this file)

Established this log to track all changes to the range going forward.

---

## 2026-10-28

Fresh-deploy test pass on a non-admin Ludus user. Everything below is on branch `claude-tuning`; earlier entries that mention a `ZooLand-BlueTeam` pool or a plain `10.0.0.0/8` block are superseded by this entry.

### Fix: `always_blocked_networks` blocked the range's own network
**Files:** `range-config.yaml`
`10.0.0.0/8` covered `10.1.0.0/16`, so VLAN 99 -> VLAN 10 traffic and router DNS were rejected (scoring engine saw 0/15). The list now covers 10/8 except the range's own /16.

### Fix: roles
- `ludus_ccdc_domain_users` (GIRAFFE): `New-ADUser` needed `-Name`, errors were swallowed, and `C00p3r$IT9` lost `$IT9` in a double-quoted string (now single quotes).
- `ludus_ccdc_file_server` (ZEBRA): reboot so the SMBv1 driver exists before enabling it.
- `ludus_ccdc_mail_server` (FLAMINGO): `smtpd_relay_restrictions = permit_mynetworks, reject_unauth_destination` (docs previously claimed `permit_all` plus a recipient-restrictions setting the role never had; a bare `permit` crashed smtpd); `mynetworks = 0.0.0.0/0` keeps it an open relay.
- `ludus_ccdc_ftp_server` (OTTER): `/srv/ftp` is root-owned (vsftpd refuses a writable anonymous root); pub/upload/incoming stay 777.
- `ludus_ccdc_web_server` (PENGUIN): frontend build runs with `DISABLE_ESLINT_PLUGIN=true`.
- Linux roles set public DNS first (now redundant after the network fix, harmless).

### Change: scoring engine rotates accounts
**Files:** `scoring_engine/*`, `roles/ludus_ccdc_scoring_engine/files/*`
IMAP, FTP and RDP checks use one account per round (IMAP 3, FTP 2, RDP 5). The dashboard key button now shows every rotation account with its own password field. RDP check implements NTLM-sealed CredSSP so correct domain logins pass on Server 2022.

### Change: `ludus_ccdc_blueteam_access`
Grants `PVEVMUser` on each blue team VM (`/vms/<id>`) instead of using a pool (the VMs already belong to the Ludus user pool). Without Proxmox admin rights it prints a warning and skips, so non-admin deploys finish clean.

### Docs
HIPPO's open test database is `testuser` / `testuser` (not anonymous). `tests/check.py` added (15 scoring checks + 31 vulnerability checks). `CLAUDE.md`, `README.md`, `SETUP.md`, `ARCHITECTURE.md` and `VULNERABILITIES.md` updated to match.

---

## 2026-10-29

### Change: FTP and IMAP scoring rotations expanded to five accounts
**Files:** `roles/ludus_ccdc_ftp_server/tasks/main.yml`, `roles/ludus_ccdc_mail_server/tasks/main.yml`, `scoring_engine/config.py` (and the role copy), `tests/check.py`, docs

The FTP (2 accounts) and IMAP (3 accounts) login checks now rotate through the same five employees as RDP: `jsmith`, `bwilson`, `mchen`, `mlopez`, `rthomas`.

- **New OS accounts** (weak shared password `ZooLand2025!`, same as the domain employees): `jsmith`, `bwilson`, `mchen` on OTTER (also removed from `/etc/ftpusers` so they can FTP in), and `mlopez`, `rthomas` on FLAMINGO (with a `Maildir`). No new usernames or passwords were introduced.
- The account-creation tasks are now loops, no longer `ignore_errors`, and idempotent.
- `tests/check.py` has a new "Scoring rotation accounts" section: it logs in as every rotation account (15 total) using the engine's own checks. It is reported separately and does not change the 900-point total or the vulnerability count.
- Updated: `README.md` (account tables, scoring table), `SETUP.md`, `ARCHITECTURE.md`, `DEMO.md`, `CLAUDE.md`. `README.md` also now lists the Ludus default account as `localuser` / `password` (was `debian` / `debian`).

---

## 2026-10-29 (later)

### Change: employee passwords are individual and basic; `ZooTime!` is admin/root only
**Files:** `roles/ludus_ccdc_domain_users`, `roles/ludus_ccdc_ftp_server`, `roles/ludus_ccdc_mail_server`, `scoring_engine/config.py` (and role copy), `tests/check.py`, `range-config.yaml` comments, docs

The 15 documented domain employees no longer share `ZooLand2025!`. Each has a different, common wordlist-style password (all meet AD complexity):

- `jsmith` / `Welcome123`
- `bwilson` / `Spring2025`
- `mchen` / `Monkey123`
- `mlopez` / `Football1`
- `rthomas` / `Baseball1`
- `ajohnson` / `Sunshine1`
- `tlee` / `Dragon123`
- `swilliams` / `Princess1`
- `pgarcia` / `Iloveyou1`
- `kbrown` / `Letmein123`
- `lmartinez` / `Soccer123`
- `djones` / `Master123`
- `nanderson` / `Shadow123`
- `cwilson` / `Winter2025`
- `emiller` / `Abc12345`

- `ZooTime!` is now used only by `Administrator`, `domainadmin` and the Linux `root` accounts (this was already the case in the roles; docs now say so). The weak `admin`, `webadmin`, `dbadmin`, `ftpuser`, `mail`, `user` and `dbuser` accounts keep their own passwords.
- The OS accounts on OTTER (FTP) and FLAMINGO (mail) for the five rotation employees use the same password as the domain account.
- The domain role used to skip accounts that already existed, so a redeploy would not change their password. It now resets the password for existing employees too.
- The scoring engine's default password for each rotation account matches; `tests/check.py` still verifies every rotation account logs in.
- The 12 hidden accounts are unchanged.
- Windows keeps accepting the *previous* password for NTLM logons (such as the RDP check) for up to 60 minutes after a reset, so on an already-deployed range the old password can still appear to work for that long.

