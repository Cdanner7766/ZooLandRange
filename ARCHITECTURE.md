# ZooLandRange — Competition Environment Design & Architecture

## What is CCDC?

The **Collegiate Cyber Defense Competition (CCDC)** is a national collegiate competition where teams of students defend a pre-built corporate IT infrastructure against a professional red team for several hours. Blue teams inherit a network full of services they must keep running and secure, while a red team (hired professionals) actively attacks those services throughout the event.

The scoring system rewards blue teams for **service availability**: a scoring engine polls key services every 30–90 seconds and awards points for each successful check. Downtime costs points. Misconfigurations that let the red team in also cost points via injects and penalties.

This practice range is designed to replicate the structure, service mix, and vulnerability profile of a typical CCDC environment so that students can practice:
- Initial incident response on a network they've never seen before
- Identifying and remediating common misconfigurations under time pressure
- Balancing service hardening against keeping services up (if you harden wrong, you break scoring)

---

## Why These Services?

Every service in this range was chosen because it appears in real CCDC competitions and teaches a specific class of defensive skill. The table below explains each inclusion:

| Service | VM | Justification |
|---------|-----|---------------|
| **Active Directory Domain Controller** | GIRAFFE | AD is the cornerstone of almost every CCDC environment. Blue teams must manage domain accounts, DNS, Group Policy, and Kerberos. AD compromise (credential theft, DC replication, Golden Ticket) is a primary red team objective. |
| **Windows Workstation** | MEERKAT | CCDC environments always include at least one end-user workstation joined to the domain. It simulates a real employee machine, creates an RDP scoring target, and gives the red team a lateral movement path from a low-privilege account to the domain. |
| **Windows SMB File Server** | ZEBRA | File servers (SMB shares) are a fixture of corporate CCDC environments. They introduce SMBv1/EternalBlue exposure, Guest access risks, and information disclosure via files left on shares — all common real-world findings. |
| **Web Application Server** | PENGUIN | Web services appear in every CCDC. This range uses a custom e-commerce store (CrazyRhino) to introduce realistic web vulnerabilities: SQL injection, IDOR, JWT weaknesses, and debug endpoints — matching the OWASP Top 10 issues typically seen in competition. |
| **Database Server** | HIPPO | Databases back the web application and represent a high-value target (PII exfiltration). CCDC blue teams must secure remote database access, manage credentials, and prevent SQL-based attacks. |
| **Mail Server** | FLAMINGO | Email (SMTP + IMAP/POP3) is a traditional CCDC service. Open relays allow the red team to send phishing mail internally. Cleartext IMAP is a common credential capture vector. Mail servers also introduce SPF/DKIM/DMARC hardening opportunities. |
| **FTP Server** | OTTER | Legacy file transfer services appear frequently in CCDC to simulate an older corporate infrastructure. Anonymous FTP, no TLS, and directory traversal are introduced intentionally, matching vulnerability classes commonly seen in competition injections. |
| **Scoring Engine** | SCORESVR | Mirrors the real CCDC scoring infrastructure. The engine polls all services every 30 seconds and provides a live dashboard. This teaches blue teams to verify that hardening changes have not accidentally broken a scored service. |
| **Red Team Machine** | JAGUAR | The Kali Linux VM gives students a dedicated attack platform (separate VLAN) to practice red team techniques against their own environment. It ships with the full `kali-linux-default` tool suite. |

Together these services represent a **realistic small-to-medium corporate environment**: a Windows domain, three Linux back-end servers, a file server, an e-commerce application, and the supporting network infrastructure that a blue team would be handed at the start of a competition.

---

## VM Architecture

The range deploys **9 virtual machines** across two isolated VLANs.

### Corporate Network (VLAN 10)

| # | Name | OS | Role | IP (.10.x) | RAM | CPUs |
|---|------|----|------|-----------|-----|------|
| 1 | **GIRAFFE** | Windows Server 2022 | Primary Domain Controller, AD DNS, DHCP, Group Policy | `.7` | 8 GB | 4 |
| 2 | **MEERKAT** | Windows 11 Enterprise | Domain-joined workstation, RDP scoring target | `.12` | 8 GB | 4 |
| 3 | **ZEBRA** | Windows Server 2022 | SMB file server (`\\ZEBRA\Public`, `\\ZEBRA\Shared`) | `.15` | 4 GB | 2 |
| 4 | **PENGUIN** | Ubuntu 22.04 | Web server — CrazyRhino e-commerce store (Docker: React + Node.js) | `.23` | 4 GB | 2 |
| 5 | **OTTER** | Ubuntu 22.04 | FTP server (vsftpd) | `.29` | 4 GB | 2 |
| 6 | **FLAMINGO** | Debian 12 | Mail server (Postfix SMTP + Dovecot IMAP/POP3) | `.38` | 4 GB | 2 |
| 7 | **HIPPO** | Debian 12 | Database server (MariaDB/MySQL) | `.41` | 4 GB | 2 |

**Total corporate network: 7 VMs — 36 GB RAM, 20 vCPUs**

### Attacker/Scoring Network (VLAN 99)

| # | Name | OS | Role | IP (.99.x) | RAM | CPUs |
|---|------|----|------|-----------|-----|------|
| 8 | **JAGUAR** | Kali Linux | Red team attack platform (`kali-linux-default`) | `.34` | 8 GB | 4 |
| 9 | **SCORESVR** | Ubuntu 22.04 + XFCE | Scoring engine dashboard (Flask + SQLite, systemd service) | `.17` | 4 GB | 2 |

**Total attacker network: 2 VMs — 12 GB RAM, 6 vCPUs**

**Grand total: 9 VMs — 48 GB RAM, 26 vCPUs**

---

## Network Topology

```
                        LUDUS HOST
                            │
              ┌─────────────┴─────────────┐
              │                           │
    ┌─────────▼─────────┐     ┌──────────▼──────────┐
    │   VLAN 10          │     │   VLAN 99            │
    │  10.X.10.0/24      │     │  10.X.99.0/24        │
    │  Corporate Network │     │  Attacker Network    │
    │                    │     │                      │
    │  .7  GIRAFFE  [DC] │     │  .17  SCORESVR       │
    │  .12 MEERKAT  [WS] │     │  .34  JAGUAR  [Kali] │
    │  .15 ZEBRA   [SMB] │     │                      │
    │  .23 PENGUIN [WEB] │     └──────────────────────┘
    │  .29 OTTER   [FTP] │
    │  .38 FLAMINGO[MAIL]│
    │  .41 HIPPO   [DB]  │
    └────────────────────┘
```

### Inter-VLAN Firewall Rules

Traffic between VLANs is blocked by default. The following rules apply:

```
Default policy between all VLANs:  REJECT

Exceptions:
  VLAN 10 → VLAN 99   TCP  80, 443, 8080   ACCEPT  (blue team reaches scoring dashboard)
  VLAN 99 → VLAN 10   ALL  ALL             ACCEPT  (red team/scorer reaches all services)
```

**Why this topology?**
The VLAN separation mirrors a real CCDC network where the scoring engine and red team machines live outside the corporate network perimeter. The one-way firewall rules mean:
- Blue team VMs can reach the scoring dashboard (port 8080) to check their score
- The scoring engine on SCORESVR can reach all services to perform checks
- The red team on JAGUAR has full access to all corporate services (simulating an external attacker)
- Corporate machines cannot reach JAGUAR on arbitrary ports (simulating no egress to the attacker machine)

### DNS (AD-Integrated Zone: `zooland.local`)

All service hostnames are registered as A records in the AD-integrated DNS zone hosted on GIRAFFE. The records are created by the `ludus_ccdc_domain_users` Ansible role:

```
web.zooland.local   →  10.X.10.23  (PENGUIN)
db.zooland.local    →  10.X.10.41  (HIPPO)
files.zooland.local →  10.X.10.15  (ZEBRA)
mail.zooland.local  →  10.X.10.38  (FLAMINGO)
ftp.zooland.local   →  10.X.10.29  (OTTER)
MX  zooland.local   →  mail.zooland.local (priority 10)
```

The `X` in all IPs is the Ludus **range ID** — an integer that Ludus assigns per user. This is auto-detected at runtime so the range works for any range ID without changing any config.

---

## Ansible Automation

The entire environment is deployed and configured using **[Ludus](https://docs.ludus.cloud/)**, a Proxmox-based cyber range automation framework. Ludus reads a single YAML configuration file (`range-config.yaml`) that describes every VM and then uses Ansible roles to configure each machine after it boots.

### How it works

```
range-config.yaml
       │
       │  Defines 9 VMs:
       │  - OS template
       │  - VLAN + IP
       │  - RAM / CPU
       │  - Ansible roles to run
       ▼
   ludus range deploy
       │
       ├─── Provisions VMs from templates in Proxmox
       ├─── Runs built-in Ludus roles (domain join, sysprep, etc.)
       └─── Runs custom CCDC roles from roles/
```

### Custom Ansible Roles

Each role is a self-contained Ansible role that configures one service and intentionally introduces CCDC-realistic vulnerabilities:

| Role | Target VM | What it does |
|------|-----------|--------------|
| `ludus_ccdc_domain_users` | GIRAFFE | Creates 5 ZooLand Inc. employee AD accounts; adds DNS A records for all services; configures DNS vulnerabilities (open zone transfer, recursion) |
| `ludus_ccdc_web_server` | PENGUIN | Installs Docker; deploys CrazyRhino React+Node.js store; creates vulnerable docker-compose with hardcoded JWT secret; disables UFW |
| `ludus_ccdc_db_server` | HIPPO | Installs MariaDB; binds to 0.0.0.0; sets weak root password; grants remote root login; creates `ccdc_company` database with employee PII |
| `ludus_ccdc_file_server` | ZEBRA | Enables SMBv1; creates Public and Shared SMB shares with Everyone Full Control; enables Guest account; disables Windows Firewall |
| `ludus_ccdc_mail_server` | FLAMINGO | Installs Postfix + Dovecot; configures open SMTP relay; disables TLS; creates employee mail accounts (jsmith, bwilson, mchen) |
| `ludus_ccdc_ftp_server` | OTTER | Installs vsftpd; enables anonymous upload; disables TLS and chroot; creates employee FTP accounts (mlopez, rthomas) |
| `ludus_ccdc_workstation` | MEERKAT | Installs blue team tools via Chocolatey (Wireshark, Burp Suite, Process Hacker, ILSpy, etc.) |
| `ludus_ccdc_scoring_engine` | SCORESVR | Deploys Flask scoring engine as systemd service; installs Python venv + dependencies; configures SQLite database |
| `ludus_ccdc_kali_setup` | JAGUAR | Installs `kali-linux-default` tool metapackage (~2–3 GB) |
| `ludus_ubuntu_desktop` | SCORESVR | Installs XFCE4 desktop environment so SCORESVR can display the scoring dashboard via browser |

### Role File Structure

```
roles/
├── ludus_ccdc_domain_users/
│   ├── tasks/main.yml        ← PowerShell tasks for AD accounts + DNS
│   ├── defaults/main.yml     ← Role variables
│   └── meta/main.yml         ← Role metadata
├── ludus_ccdc_web_server/
│   ├── tasks/main.yml        ← Docker install + CrazyRhino deploy
│   └── files/
│       └── crazyrhino/       ← React frontend + Node.js backend source
├── ludus_ccdc_scoring_engine/
│   ├── tasks/main.yml        ← Python venv + systemd service deploy
│   ├── files/                ← Scoring engine Python source (app.py, config.py, etc.)
│   ├── templates/            ← systemd unit file template
│   └── handlers/main.yml     ← "Restart scoring engine" handler
└── ... (one directory per role)
```

---

## Scoring Engine

The scoring engine is the most important piece of infrastructure for CCDC practice. It runs on SCORESVR (VLAN 99) and polls all 14 services on the corporate network (VLAN 10) every **30 seconds**, awarding pass/fail scores to each.

### Scored Services

| Service | VM | Port | Check Method |
|---------|-----|------|--------------|
| HTTP — CrazyRhino store | PENGUIN | 80 | HTTP GET, validates store content in response body |
| FTP — authenticated login | OTTER | 21 | FTP login as `mlopez` / `ZooLand2025!` |
| SMTP — mail relay | FLAMINGO | 25 | Banner read + EHLO handshake |
| IMAP — authenticated login | FLAMINGO | 143 | IMAP LOGIN as `jsmith` / `ZooLand2025!` |
| POP3 — banner | FLAMINGO | 110 | Reads `+OK` banner |
| DNS — A record resolution | GIRAFFE | 53 | Resolves `web.zooland.local`, validates expected IP |
| MySQL — TCP handshake | HIPPO | 3306 | Reads MySQL server greeting banner |
| SMB — negotiate | ZEBRA | 445 | SMB negotiate protocol response |
| LDAP — anonymous bind | GIRAFFE | 389 | LDAPv3 anonymous bind |
| Kerberos — TCP connect | GIRAFFE | 88 | TCP connection to KDC |
| RDP — NLA login | MEERKAT | 3389 | CredSSP/NTLMv2 login as `jsmith` |
| SSH — banner | PENGUIN | 22 | SSH banner read |
| SSH — banner | HIPPO | 22 | SSH banner read |
| SSH — banner | FLAMINGO | 22 | SSH banner read |
| SSH — banner | OTTER | 22 | SSH banner read |

### Dashboard

The live scoring dashboard is available at `http://10.X.99.17:8080/` and is accessible from any VLAN 10 machine (the firewall permits port 8080 from VLAN 10 to VLAN 99).

The scoring engine auto-detects the range ID from SCORESVR's own IP address (pattern `10.X.99.Y` → range ID = `X`), so no manual configuration is needed.

---

## Scripts

### `scripts/test_range.sh`

A Bash validation script designed to run from **JAGUAR (Kali)** after deployment to verify that all services are operational before a practice session begins.

The script auto-detects the range network from the Kali machine's IP and performs the following checks:

| Category | Tests Performed |
|----------|----------------|
| **Connectivity** | ICMP ping to all 7 corporate VMs |
| **Web** | HTTP 200 from PENGUIN:80, CrazyRhino content validation, API `/health` endpoint |
| **Database** | Port 3306 open on HIPPO, weak credential login, `ccdc_company` database query |
| **File Server** | SMB port 445 on ZEBRA, anonymous share listing (`\\ZEBRA\Public`), file read |
| **Mail** | Ports 25/110/143 open on FLAMINGO, SMTP relay test, banner validation |
| **DNS** | A record resolution from GIRAFFE for all service hostnames, MX lookup, zone transfer |
| **FTP** | Port 21 open on OTTER, banner read, anonymous download |
| **Domain Controller** | Ports 53/88/389/445 on GIRAFFE |

**Usage:**
```bash
# From the Ludus host, copy the script to JAGUAR
scp scripts/test_range.sh kali@10.X.99.34:~/

# SSH into JAGUAR and run it
ssh kali@10.X.99.34
chmod +x ~/test_range.sh
./test_range.sh
```

### `scoring_engine/start.sh`

A convenience script for manually starting the scoring engine outside of systemd (useful for development and debugging). It prints detected range configuration before launching:

```bash
cd scoring_engine/
./start.sh
# [*] Detected Range ID : 10
# [*] Target network    : 10.10.10.0/24
# [*] Check interval    : 30s
# [*] Services checked  : 15
# [*] Starting scoring engine...
# [*] Dashboard → http://10.10.99.17:8080/
```

> In normal operation the scoring engine is managed by systemd on SCORESVR and does not need to be started manually.

---

## Deployment Steps Summary

A full deployment requires four steps. See **[SETUP.md](SETUP.md)** for complete instructions including per-VM troubleshooting.

```
Step 1 — Clone the repository on the Ludus host
   git clone <repo-url> ~/ZooLandRange

Step 2 — Register all Ansible roles with Ludus
   ludus ansible role add -d roles/ludus_ccdc_web_server
   ludus ansible role add -d roles/ludus_ccdc_db_server
   ... (one command per role, see SETUP.md)

Step 3 — Apply the range configuration
   ludus range config set -f range-config.yaml

Step 4 — Deploy
   ludus range deploy
   (takes 30–90 minutes depending on hardware)
```

After deployment, run `scripts/test_range.sh` from JAGUAR to confirm all services are up, then open the scoring dashboard at `http://10.X.99.17:8080/` to begin a timed practice session.

---

## File Map

```
ZooLandRange/
├── range-config.yaml          ← Single-file VM and network definition for Ludus
├── ARCHITECTURE.md            ← This file — design rationale and architecture overview
├── README.md                  ← Full technical reference (credentials, vulns, service details)
├── SETUP.md                   ← Step-by-step deployment instructions
├── BLUETEAM.md                ← Quick-reference credential sheet for blue team practice
├── WAZUH.md                   ← Optional Wazuh SIEM integration guide
│
├── roles/                     ← Custom Ansible roles (one per service)
│   ├── ludus_ccdc_domain_users/    AD accounts + DNS (GIRAFFE)
│   ├── ludus_ccdc_web_server/      CrazyRhino store via Docker (PENGUIN)
│   ├── ludus_ccdc_db_server/       MariaDB with vulns (HIPPO)
│   ├── ludus_ccdc_file_server/     SMB shares with vulns (ZEBRA)
│   ├── ludus_ccdc_mail_server/     Postfix + Dovecot with vulns (FLAMINGO)
│   ├── ludus_ccdc_ftp_server/      vsftpd with vulns (OTTER)
│   ├── ludus_ccdc_workstation/     Blue team tools via Chocolatey (MEERKAT)
│   ├── ludus_ccdc_scoring_engine/  Flask scoring engine (SCORESVR)
│   ├── ludus_ccdc_kali_setup/      Kali tool metapackage (JAGUAR)
│   └── ludus_ubuntu_desktop/       XFCE desktop (SCORESVR)
│
├── scoring_engine/            ← Canonical scoring engine Python source
│   ├── app.py                 Flask web app + REST API
│   ├── config.py              Service definitions and IP addressing
│   ├── checks.py              Per-protocol check functions
│   ├── database.py            SQLite result persistence
│   ├── requirements.txt       Python dependencies
│   └── start.sh               Manual launch script (dev/debug)
│
├── scripts/
│   └── test_range.sh          Post-deployment validation script (run from JAGUAR)
│
├── CrazyRhino/                ← Web store application source (React + Node.js)
└── templates/                 ← Ansible Jinja2 templates
```
