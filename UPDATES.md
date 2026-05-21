# ZooLandRange — Update Log

Chronological record of all changes made to the range after initial deployment.

---

## 2026-05-21 (continued)

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
