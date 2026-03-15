# ZooLandRange — CCDC Practice Environment

> **Documentation:**
> - **[ARCHITECTURE.md](ARCHITECTURE.md)** — Competition environment design rationale, network diagram, VM architecture, Ansible automation overview, and deployment summary
> - **[SETUP.md](SETUP.md)** — Step-by-step deployment instructions
> - **[BLUETEAM.md](BLUETEAM.md)** — Quick-reference credential sheet
> - **[WAZUH.md](WAZUH.md)** — Optional Wazuh SIEM integration

---

## Overview

This Ludus range deploys a full Active Directory environment with **9 virtual machines** across 2 VLANs for CCDC (Collegiate Cyber Defense Competition) practice. All VMs are named after zoo animals and contain intentional vulnerabilities that blue teams must identify and remediate while maintaining service availability.

**Domain:** `zooland.local`
**Company:** ZooLand Inc.
**Network:** `10.{RANGE_ID}.0.0/16` (VLAN determines third octet)

---

## Network Architecture

```
VLAN 10 - Corporate Network (10.X.10.0/24)
├── GIRAFFE   (.7)   - Domain Controller + DNS (Windows Server 2022)
├── MEERKAT   (.12)  - Workstation (Windows 11 Enterprise)
├── ZEBRA     (.15)  - File Server (Windows Server 2022)
├── PENGUIN   (.23)  - Web Server / CrazyRhino Store (Ubuntu 22.04)
├── OTTER     (.29)  - FTP Server (Ubuntu 22.04)
├── FLAMINGO  (.38)  - Mail Server (Debian 12)
└── HIPPO     (.41)  - Database Server (Debian 12)

VLAN 99 - Attacker Network (10.X.99.0/24)
├── JAGUAR    (.34)  - Kali Linux (Red Team)
└── SCORESVR  (.17)  - Scoring Engine (Ubuntu 22.04 + XFCE)
```

### Firewall Rules

| Direction | Protocol | Ports | Action |
|-----------|----------|-------|--------|
| VLAN 10 -> VLAN 99 | TCP | 80, 443, 8080 only | ACCEPT |
| VLAN 99 -> VLAN 10 | ALL | ALL | ACCEPT |
| All other inter-VLAN | ALL | ALL | REJECT |

---

## Machine Details

### 1. Domain Controller (GIRAFFE)

| Property | Value |
|----------|-------|
| Hostname | `{RANGE_ID}-GIRAFFE` |
| OS | Windows Server 2022 |
| IP | `10.X.10.7` |
| RAM / CPUs | 8 GB / 4 |
| Domain Role | Primary DC for `zooland.local` |
| Ports | 53/tcp+udp (DNS), 88/tcp (Kerberos), 389/tcp (LDAP), 445/tcp (SMB) |

**Credentials:**

| Account | Username | Password |
|---------|----------|----------|
| Local Administrator | `Administrator` | `password` |
| Domain Admin | `ZOOLAND\domainadmin` | `password` |
| Domain User | `ZOOLAND\domainuser` | `password` |

**ZooLand Inc. employee accounts** (created by `ludus_ccdc_domain_users` role):

| Display Name | Username | Password | Department |
|-------------|----------|----------|------------|
| John Smith | `jsmith` | `ZooLand2025!` | IT Support *(IMAP scoring account on FLAMINGO)* |
| Barbara Wilson | `bwilson` | `ZooLand2025!` | HR |
| Michelle Chen | `mchen` | `ZooLand2025!` | Finance |
| Maria Lopez | `mlopez` | `ZooLand2025!` | Logistics *(FTP scoring account on OTTER)* |
| Robert Thomas | `rthomas` | `ZooLand2025!` | Warehouse |

**Services:** Active Directory, DNS (AD-integrated zone, scored), DHCP, Group Policy, Kerberos, LDAP

**DNS Records (zooland.local AD-integrated zone):**

| Record | Type | Value |
|--------|------|-------|
| `web.zooland.local` | A | `10.X.10.23` |
| `db.zooland.local` | A | `10.X.10.41` |
| `files.zooland.local` | A | `10.X.10.15` |
| `mail.zooland.local` | A | `10.X.10.38` |
| `ftp.zooland.local` | A | `10.X.10.29` |
| `zooland.local` | MX | `mail.zooland.local` (priority 10) |

**Vulnerabilities (DNS — applied by `ludus_ccdc_domain_users` role):**

| # | Vulnerability | Technical Detail | Config Location |
|---|---------------|------------------|-----------------|
| 1 | **Zone transfers to anyone** | `SecureSecondaries = TransferAnyServer` — AXFR dumps full zone to any requester | `Set-DnsServerPrimaryZone` |
| 2 | **Recursion enabled globally** | Open recursive resolver — DNS amplification attack vector | `Set-DnsServerRecursion -Enable $true` |
| 3 | **No DNSSEC** | No DNSSEC validation — DNS cache poisoning possible | DNS server settings |
| 4 | **DNS logging disabled** | `Set-DnsServerDiagnostics -All $false` — no audit trail for queries | DNS diagnostics |

---

### 2. Windows 11 Workstation (MEERKAT)

| Property | Value |
|----------|-------|
| Hostname | `{RANGE_ID}-MEERKAT` |
| OS | Windows 11 22H2 Enterprise |
| IP | `10.X.10.12` |
| RAM / CPUs | 8 GB / 4 |
| Domain Role | Member of `zooland.local` |

**Credentials:**

| Account | Username | Password |
|---------|----------|----------|
| Domain User (autologon) | `ZOOLAND\domainuser` | `password` |
| Domain Admin | `ZOOLAND\domainadmin` | `password` |
| Local Administrator | `Administrator` | `password` |

**Installed Software:** Firefox, Burp Suite, 7zip, Process Hacker, Wireshark, ILSpy, NetworkMonitor, ExplorerSuite, Croc

**Desktop:** Solid dark blue background (no Ludus wallpaper)

---

### 3. File Server (ZEBRA)

| Property | Value |
|----------|-------|
| Hostname | `{RANGE_ID}-ZEBRA` |
| OS | Windows Server 2022 |
| IP | `10.X.10.15` |
| RAM / CPUs | 4 GB / 2 |
| Domain Role | Member of `zooland.local` |
| Service | SMB File Shares |
| Ports | 445/tcp (SMB), 139/tcp (NetBIOS) |

**Credentials:**

| Account | Username | Password |
|---------|----------|----------|
| Local Administrator | `Administrator` | `password` |
| Domain Admin | `ZOOLAND\domainadmin` | `password` |
| Domain User | `ZOOLAND\domainuser` | `password` |

**SMB Shares:**

| Share | Path | Permissions |
|-------|------|-------------|
| `\\ZEBRA\Public` | `C:\Shares\Public` | Everyone: Full Control, Guest: Full Control |
| `\\ZEBRA\Shared` | `C:\Shares\Shared` | Everyone: Full Control, Guest: Full Control |

**Sensitive Files in Shares:**

| File | Location | Contents |
|------|----------|----------|
| `readme.txt` | `\\ZEBRA\Public\` | Network credentials (`admin/admin`), WiFi password (`CompanyWifi123`) |
| `IT_Notes.txt` | `\\ZEBRA\Shared\` | Server passwords, default admin password (`P@ssw0rd!`), DB root password |

**Desktop:** Solid dark blue background (no Ludus wallpaper)

**Vulnerabilities:**

| # | Vulnerability | Technical Detail | Config Location |
|---|---------------|------------------|-----------------|
| 1 | **SMBv1 enabled** | Vulnerable to MS17-010 (EternalBlue) | `Enable-WindowsOptionalFeature -FeatureName SMB1Protocol` |
| 2 | **Everyone Full Control** | All shares grant Full Control to Everyone | `New-SmbShare -FullAccess "Everyone"` |
| 3 | **Guest access enabled** | Guest account active with full share access | `net user Guest /active:yes` |
| 4 | **Unencrypted SMB** | `RejectUnencryptedAccess = $false` — credentials sent in cleartext | `Set-SmbServerConfiguration` |
| 5 | **Insecure guest auth** | `AllowInsecureGuestAuth = 1` registry value enables guest fallback | `HKLM:\...\LanmanWorkstation\Parameters` |
| 6 | **Credentials in shares** | Plaintext passwords in `readme.txt` and `IT_Notes.txt` | `C:\Shares\Public\`, `C:\Shares\Shared\` |
| 7 | **Windows Firewall disabled** | All profiles (Domain, Public, Private) disabled | `Set-NetFirewallProfile -Enabled False` |
| 8 | **NTFS permissions wide open** | `FileSystemAccessRule("Everyone","FullControl")` on share directories | NTFS ACLs |

---

### 4. Web Server / CrazyRhino Store (PENGUIN)

| Property | Value |
|----------|-------|
| Hostname | `{RANGE_ID}-PENGUIN` |
| OS | Ubuntu 22.04 Server |
| IP | `10.X.10.23` |
| RAM / CPUs | 4 GB / 2 |
| Service | CrazyRhino e-commerce store (Docker: React + Node.js) |
| Ports | 80/tcp (HTTP frontend), 5000/tcp (API backend) |
| Store URL | `http://10.X.10.23/` |
| API URL | `http://10.X.10.23:5000/api/` |

**Credentials:**

| Account | Username | Password | Notes |
|---------|----------|----------|-------|
| OS root | `root` | `toor` | VULN: weak root |
| OS local user | `admin` | `admin` | VULN: weak account |
| OS local user | `webadmin` | `password` | VULN: weak account |
| App admin | `admin` | `admin123` | CrazyRhino admin panel |
| App demo user | `johndoe` | `password123` | CrazyRhino regular user |

**Vulnerabilities:**

| # | Vulnerability | Technical Detail | Config Location |
|---|---------------|------------------|-----------------|
| 1 | **Weak JWT secret** | `JWT_SECRET=wild-kingdom-zoo-secret-2024` hardcoded in environment — tokens forgeable | `docker-compose.yml` env var |
| 2 | **Default admin credentials** | `admin` / `admin123` — unchanged from deployment default | CrazyRhino database seed |
| 3 | **Debug endpoint (no auth)** | `GET /api/debug` returns all environment variables including JWT secret | `backend/server.js` |
| 4 | **SQL injection — product search** | `?search=` concatenated into raw SQL — union-based extraction possible | `backend/routes/products.js` |
| 5 | **IDOR — order lookup** | `GET /api/orders/:orderNumber` returns any order without verifying ownership | `backend/routes/orders.js` |
| 6 | **No rate limiting** | No `express-rate-limit` — brute force of login/API endpoints possible | `backend/server.js` |
| 7 | **No HTTPS** | All traffic served over HTTP — credentials and tokens in cleartext | `docker-compose.yml` port mapping |
| 8 | **Credentials in plaintext file** | `/opt/crazyrhino/backup_credentials.txt` contains admin creds and JWT secret | Ansible deployment |
| 9 | **Server header disclosure** | `X-Powered-By: Express` reveals backend framework | Default Express config |
| 10 | **Firewall disabled** | UFW completely disabled and reset | `ufw disable && ufw --force reset` |
| 11 | **Minimum password length only 6** | `password.length < 6` — weak passwords accepted on registration | `backend/routes/auth.js` |
| 12 | **Weak OS accounts** | `admin:admin`, `webadmin:password`, `root:toor` | `/etc/shadow` |

**CrazyRhino Exploit Examples:**

```bash
# 1. Dump JWT secret via debug endpoint (no auth)
curl http://10.X.10.23:5000/api/debug | jq '.env.JWT_SECRET'

# 2. SQL injection in product search — extract all users
curl "http://10.X.10.23:5000/api/products?search=x%27%20UNION%20SELECT%201,username,password_hash,email,5,6,7%20FROM%20users--"

# 3. Log in as admin with default credentials
curl -X POST http://10.X.10.23:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 4. IDOR — access another user's order (enumerate WKZ- prefixed order numbers)
curl http://10.X.10.23:5000/api/orders/WKZ-XXXXXX-XXXX \
  -H "Authorization: Bearer <your_token>"
```

---

### 5. FTP Server (OTTER)

| Property | Value |
|----------|-------|
| Hostname | `{RANGE_ID}-OTTER` |
| OS | Ubuntu 22.04 Server |
| IP | `10.X.10.29` |
| RAM / CPUs | 4 GB / 2 |
| Service | vsftpd 3.0.5 |
| Ports | 21/tcp (FTP), 40000-40100/tcp (passive) |

**Credentials:**

| Account | Username | Password | Notes |
|---------|----------|----------|-------|
| OS / FTP user | `ftpuser` | `ftpuser` | VULN: weak account |
| OS / FTP user | `admin` | `admin` | VULN: weak account |
| OS root | `root` | `toor` | VULN: weak root |
| FTP anonymous | `anonymous` | (any password) | VULN: anonymous upload |
| Ludus default | `debian` | `debian` | |
| Employee (Logistics) | `mlopez` | `ZooLand2025!` | **Scoring engine FTP account** |
| Employee (Warehouse) | `rthomas` | `ZooLand2025!` | |

**FTP Directory Structure:**

```
/srv/ftp/               (anonymous root, world-writable)
├── pub/
│   ├── readme.txt      ("Public FTP files - CCDC Practice Range")
│   └── backup_notes.txt ("Backup credentials - admin:admin, root:toor, ftpuser:ftpuser")
├── upload/
│   └── readme.txt      ("Upload directory - anonymous uploads allowed")
└── incoming/
```

**Vulnerabilities:**

| # | Vulnerability | Technical Detail | Config Location |
|---|---------------|------------------|-----------------|
| 1 | **Anonymous access enabled** | `anonymous_enable=YES` with upload, mkdir, and delete permissions | `/etc/vsftpd.conf` |
| 2 | **No TLS/SSL** | `ssl_enable=NO` — credentials transmitted in cleartext | `/etc/vsftpd.conf` |
| 3 | **No chroot** | `chroot_local_user=NO` — users can traverse entire filesystem | `/etc/vsftpd.conf` |
| 4 | **World-writable FTP root** | `chmod -R 777 /srv/ftp` | Directory permissions |
| 5 | **umask 000** | `anon_umask=000`, `local_umask=000` — all new files are world-writable | `/etc/vsftpd.conf` |
| 6 | **FTP bounce enabled** | `pasv_promiscuous=YES`, `port_promiscuous=YES` | `/etc/vsftpd.conf` |
| 7 | **Version in banner** | `ftpd_banner=Welcome to CCDC Practice FTP Server (vsftpd 3.0.5)` | `/etc/vsftpd.conf` |
| 8 | **Credentials in share** | `backup_notes.txt` contains plaintext passwords | `/srv/ftp/pub/backup_notes.txt` |
| 9 | **Weak user accounts** | `ftpuser:ftpuser`, `admin:admin`, `root:toor` | `/etc/shadow` |
| 10 | **Firewall disabled** | iptables flushed, all policies set to ACCEPT | iptables rules |

---

### 6. Mail Server (FLAMINGO)

| Property | Value |
|----------|-------|
| Hostname | `{RANGE_ID}-FLAMINGO` |
| OS | Debian 12 Server |
| IP | `10.X.10.38` |
| RAM / CPUs | 4 GB / 2 |
| Services | Postfix (SMTP), Dovecot (IMAP/POP3) |
| Ports | 25/tcp (SMTP), 110/tcp (POP3), 143/tcp (IMAP) |

**Credentials:**

| Account | Username | Password | Notes |
|---------|----------|----------|-------|
| OS / mail user | `mail` | `mail` | VULN: weak account |
| OS / mail user | `admin` | `admin` | VULN: weak account |
| OS / mail user | `user` | `password` | VULN: weak account |
| OS root | `root` | `toor` | VULN: weak root |
| Ludus default | `debian` | `debian` | |
| Employee (IT Support) | `jsmith` | `ZooLand2025!` | **Scoring engine IMAP account** |
| Employee (HR) | `bwilson` | `ZooLand2025!` | |
| Employee (Finance) | `mchen` | `ZooLand2025!` | |

**Vulnerabilities:**

| # | Vulnerability | Technical Detail | Config Location |
|---|---------------|------------------|-----------------|
| 1 | **Open SMTP relay** | `smtpd_relay_restrictions = permit_all`, `smtpd_recipient_restrictions = permit_all` — accepts and relays mail from anyone | `/etc/postfix/main.cf` |
| 2 | **No SMTP authentication** | `smtpd_sasl_auth_enable = no` — no auth required to send mail | `/etc/postfix/main.cf` |
| 3 | **No TLS (Postfix)** | `smtpd_tls_security_level = none` — all SMTP traffic in cleartext | `/etc/postfix/main.cf` |
| 4 | **mynetworks = 0.0.0.0/0** | Treats the entire internet as a trusted network | `/etc/postfix/main.cf` |
| 5 | **Plaintext IMAP/POP3 auth** | `disable_plaintext_auth = no` — credentials sent in clear | `/etc/dovecot/dovecot.conf` |
| 6 | **No SSL (Dovecot)** | `ssl = no` — no encryption on IMAP/POP3 | `/etc/dovecot/dovecot.conf` |
| 7 | **No SPF/DKIM/DMARC** | No email authentication records — spoofing possible | DNS records |
| 8 | **Weak user accounts** | `mail:mail`, `admin:admin`, `user:password`, `root:toor` | `/etc/shadow` |
| 9 | **Firewall disabled** | iptables flushed, all policies set to ACCEPT | iptables rules |

---

### 7. Database Server (HIPPO)

| Property | Value |
|----------|-------|
| Hostname | `{RANGE_ID}-HIPPO` |
| OS | Debian 12 Server |
| IP | `10.X.10.41` |
| RAM / CPUs | 4 GB / 2 |
| Service | MariaDB (MySQL-compatible) |
| Ports | 3306/tcp (MySQL) |

**Credentials:**

| Account | Username | Password | Scope |
|---------|----------|----------|-------|
| MySQL root (local) | `root` | `password` | `root@localhost` |
| MySQL root (remote) | `root` | `password` | `root@%` (any host) |
| MySQL admin | `admin` | `admin` | `admin@%` (any host) |
| MySQL app user | `dbuser` | `dbuser` | `dbuser@%` (any host) |
| OS root | `root` | `toor` | SSH/console |
| OS local user | `admin` | `admin` | SSH/console |
| OS local user | `dbadmin` | `password` | SSH/console |
| Ludus default | `debian` | `debian` | SSH/console |

**Databases:**

| Database | Contents |
|----------|----------|
| `ccdc_company` | `employees` table with names, emails, SSNs, salaries (PII) |
| `test` | Empty test database accessible to anonymous users |

**Vulnerabilities:**

| # | Vulnerability | Technical Detail | Config Location |
|---|---------------|------------------|-----------------|
| 1 | **MySQL bound to 0.0.0.0** | Accessible from all network interfaces, not just localhost | `/etc/mysql/mariadb.conf.d/99-insecure.cnf` (`bind-address = 0.0.0.0`) |
| 2 | **Remote root login** | `root@%` with `GRANT OPTION` allows root from any host | MySQL user grants |
| 3 | **Weak root password** | Root password is `password` | `ALTER USER 'root'@'localhost'` |
| 4 | **Weak admin account** | `admin:admin` with `ALL PRIVILEGES` and `GRANT OPTION` | MySQL user grants |
| 5 | **Weak app user** | `dbuser:dbuser` with `ALL PRIVILEGES` on everything | MySQL user grants |
| 6 | **LOAD DATA LOCAL enabled** | `local-infile = 1` allows reading server-side files via SQL | `/etc/mysql/mariadb.conf.d/99-insecure.cnf` |
| 7 | **Test database open** | `test` database with `GRANT ALL` to anonymous users (`''@'%'`) | MySQL user grants |
| 8 | **PII in database** | SSNs and salaries stored in plaintext in `ccdc_company.employees` | `ccdc_company` database |
| 9 | **Firewall disabled** | iptables flushed, all policies set to ACCEPT | iptables rules |
| 10 | **Weak OS accounts** | `admin:admin`, `dbadmin:password`, `root:toor` | `/etc/shadow` |

---

### 8. Kali Linux (JAGUAR — Red Team)

| Property | Value |
|----------|-------|
| Hostname | `{RANGE_ID}-JAGUAR` |
| OS | Kali Linux |
| IP | `10.X.99.34` |
| RAM / CPUs | 8 GB / 4 |
| VLAN | 99 (Attacker Network) |
| Tools | `kali-linux-default` (installed via `ludus_ccdc_kali_setup` role) |

**Credentials:**

| Account | Username | Password |
|---------|----------|----------|
| Default user | `kali` | `kali` |

---

### 9. Scoring Engine (SCORESVR)

| Property | Value |
|----------|-------|
| Hostname | `{RANGE_ID}-SCORESVR` |
| OS | Ubuntu 22.04 Server + XFCE4 desktop |
| IP | `10.X.99.17` |
| RAM / CPUs | 4 GB / 2 |
| VLAN | 99 (Attacker Network) |
| Purpose | Hosts the CCDC Blue Team Scoring Engine |
| Dashboard | `http://10.X.99.17:8080/` |

**Credentials:**

| Account | Username | Password |
|---------|----------|----------|
| Ludus default | `debian` | `debian` |

**Scoring Engine:**

Deployed by the `ludus_ccdc_scoring_engine` Ansible role. Runs as a Python Flask application under the `scoring` system user, managed by systemd (`scoring_engine.service`). Results are stored in SQLite at `/opt/scoring_engine/scoring.db`.

- Polls all **11 services** every **30 seconds**
- Scores each check pass/fail with point values ranging from 25–100 pts
- Auto-detects the range ID from the scoring machine's `10.X.99.Y` IP
- Live dashboard available at **`http://10.X.99.17:8080/`** from VLAN 10 machines (port 8080 is permitted through the firewall)

| Service Check | Points |
|---------------|-------:|
| HTTP CrazyRhino Store (PENGUIN:80) | 100 |
| LDAP — Active Directory (GIRAFFE:389) | 100 |
| Kerberos — Active Directory (GIRAFFE:88) | 100 |
| DNS Resolution (GIRAFFE:53) | 100 |
| SMTP Open Relay (FLAMINGO:25) | 75 |
| MySQL Database (HIPPO:3306) | 75 |
| IMAP Login (FLAMINGO:143) — `jsmith` | 50 |
| POP3 Banner (FLAMINGO:110) | 50 |
| SMB File Server (ZEBRA:445) | 50 |
| FTP Login (OTTER:21) — `mlopez` | 50 |
| RDP Workstation (MEERKAT:3389) | 50 |
| **Max per round** | **800** |

---

## Vulnerability Summary by Category

### Authentication / Credentials
- 16+ accounts with weak/default passwords across all machines
- MySQL root remotely accessible with password `password`
- Anonymous FTP with full write access
- Guest SMB access enabled with no authentication
- Domain built-in accounts use default Ludus passwords (`password`)
- ZooLand Inc. employee accounts (`jsmith`, `bwilson`, `mchen`, `mlopez`, `rthomas`) use `ZooLand2025!`
- CrazyRhino admin: `admin` / `admin123` (unchanged default)

### Network / Firewall
- UFW/iptables disabled on all Linux VMs
- Windows Firewall disabled on all Windows member VMs
- MySQL bound to 0.0.0.0 (all interfaces)
- SMBv1 enabled (EternalBlue-vulnerable)
- CrazyRhino API exposed on port 5000 with no firewall

### Encryption / Transport
- No TLS on SMTP, IMAP, POP3 (all plaintext)
- No TLS on FTP (cleartext credentials)
- SMB encryption not required (`RejectUnencryptedAccess = $false`)
- CrazyRhino served over HTTP only (no HTTPS)

### Web Application (CrazyRhino)
- SQL injection in product search (`?search=` — raw string concatenation in SQLite query)
- IDOR in order lookup (`/api/orders/:orderNumber` — no ownership check)
- Debug endpoint (`/api/debug`) exposes JWT_SECRET and all env vars
- Default admin credentials (`admin` / `admin123`)
- Weak JWT secret hardcoded in environment (`wild-kingdom-zoo-secret-2024`)
- No rate limiting — brute force possible
- Credentials in plaintext backup file (`/opt/crazyrhino/backup_credentials.txt`)

### Information Disclosure
- Debug endpoint dumps all environment variables including secrets
- CrazyRhino `X-Powered-By: Express` header
- vsftpd version in FTP banner
- DNS zone transfers allowed to any host (AXFR)
- Credentials in plaintext files on FTP and SMB shares

### Access Control
- World-writable FTP root (777)
- Everyone Full Control on all SMB shares
- No chroot on FTP (full filesystem traversal)
- `LOAD DATA LOCAL` enabled in MySQL
- CrazyRhino IDOR allows any authenticated user to view other users' orders

### Logging / Monitoring
- DNS diagnostic logging disabled
- No audit trail on DNS queries
- No SPF/DKIM/DMARC for email authentication
- SMTP open relay (can send as anyone)

---

## Total Vulnerability Count

| Machine | Vulnerability Count |
|---------|:-------------------:|
| GIRAFFE (DC) | 4 |
| PENGUIN (Web/CrazyRhino) | 12 |
| HIPPO (DB) | 10 |
| ZEBRA (File) | 8 |
| FLAMINGO (Mail) | 9 |
| OTTER (FTP) | 10 |
| **Total** | **53** |
