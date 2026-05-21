# ZooLandRange — Vulnerability Reference

All intentional misconfigurations across the 7 blue team VMs. Each entry includes the
vulnerability name, the technical detail (what was actually configured), and where in the
system the setting lives.

---

## GIRAFFE — Domain Controller / DNS (Windows Server 2022)

| # | Vulnerability | Technical Detail | Config Location |
|---|---------------|------------------|-----------------|
| 1 | **Zone transfers to anyone** | `SecureSecondaries = TransferAnyServer` — AXFR dumps full zone to any requester | `Set-DnsServerPrimaryZone` |
| 2 | **Open recursive resolver** | Recursion enabled globally — DNS amplification attack vector | `Set-DnsServerRecursion -Enable $true` |
| 3 | **No DNSSEC** | No DNSSEC validation — DNS cache poisoning possible | DNS server settings |
| 4 | **DNS logging disabled** | `Set-DnsServerDiagnostics -All $false` — no audit trail for queries | DNS diagnostics |

---

## MEERKAT — Workstation (Windows 11 Enterprise)

| # | Vulnerability | Technical Detail | Config Location |
|---|---------------|------------------|-----------------|
| 1 | **Windows Firewall disabled** | All profiles (Domain, Public, Private) disabled | `Set-NetFirewallProfile -Enabled False` |
| 2 | **Domain Users can RDP** | `Remote Desktop Users` group includes `Domain Users` — any domain account can log in remotely | Local group membership |

---

## ZEBRA — File Server (Windows Server 2022)

| # | Vulnerability | Technical Detail | Config Location |
|---|---------------|------------------|-----------------|
| 1 | **SMBv1 enabled** | Vulnerable to MS17-010 (EternalBlue) | `Enable-WindowsOptionalFeature -FeatureName SMB1Protocol` |
| 2 | **Everyone Full Control on shares** | All shares grant Full Control to Everyone | `New-SmbShare -FullAccess "Everyone"` |
| 3 | **Guest access enabled** | Guest account active with full share access | `net user Guest /active:yes` |
| 4 | **Unencrypted SMB** | `RejectUnencryptedAccess = $false` — credentials sent in cleartext | `Set-SmbServerConfiguration` |
| 5 | **Insecure guest auth** | `AllowInsecureGuestAuth = 1` — guest fallback allowed | `HKLM:\...\LanmanWorkstation\Parameters` |
| 6 | **Credentials in shares** | Plaintext passwords in `readme.txt` (`\\ZEBRA\Public`) and `IT_Notes.txt` (`\\ZEBRA\Shared`) | Share contents |
| 7 | **Windows Firewall disabled** | All profiles (Domain, Public, Private) disabled | `Set-NetFirewallProfile -Enabled False` |
| 8 | **NTFS permissions wide open** | `FileSystemAccessRule("Everyone","FullControl")` on share directories | NTFS ACLs |

---

## PENGUIN — Web Server / CrazyRhino Store (Ubuntu 22.04)

| # | Vulnerability | Technical Detail | Config Location |
|---|---------------|------------------|-----------------|
| 1 | **Weak JWT secret** | `JWT_SECRET=wild-kingdom-zoo-secret-2024` hardcoded — tokens forgeable | `docker-compose.yml` env var |
| 2 | **Default admin credentials** | `admin` / `admin123` — unchanged from deployment default | CrazyRhino database seed |
| 3 | **Debug endpoint (no auth)** | `GET /api/debug` returns all environment variables including JWT secret | `backend/server.js` |
| 4 | **SQL injection — product search** | `?search=` concatenated into raw SQL — union-based extraction possible | `backend/routes/products.js` |
| 5 | **IDOR — order lookup** | `GET /api/orders/:orderNumber` returns any order without verifying ownership | `backend/routes/orders.js` |
| 6 | **No rate limiting** | No `express-rate-limit` — brute force of login/API endpoints possible | `backend/server.js` |
| 7 | **No HTTPS** | All traffic served over HTTP — credentials and tokens in cleartext | `docker-compose.yml` port mapping |
| 8 | **Credentials in plaintext file** | `/opt/crazyrhino/backup_credentials.txt` contains admin creds and JWT secret | Ansible deployment |
| 9 | **Server header disclosure** | `X-Powered-By: Express` reveals backend framework | Default Express config |
| 10 | **Firewall disabled** | UFW completely disabled and reset | `ufw disable && ufw --force reset` |
| 11 | **Weak password policy** | Minimum length 6, no complexity — weak passwords accepted on registration | `backend/routes/auth.js` |
| 12 | **Weak OS accounts** | `admin:admin`, `webadmin:password`, `root:ZooTime!` | `/etc/shadow` |

---

## OTTER — FTP Server (Ubuntu 22.04)

| # | Vulnerability | Technical Detail | Config Location |
|---|---------------|------------------|-----------------|
| 1 | **Anonymous access enabled** | `anonymous_enable=YES` with upload, mkdir, and delete permissions | `/etc/vsftpd.conf` |
| 2 | **No TLS/SSL** | `ssl_enable=NO` — credentials transmitted in cleartext | `/etc/vsftpd.conf` |
| 3 | **No chroot** | `chroot_local_user=NO` — users can traverse entire filesystem | `/etc/vsftpd.conf` |
| 4 | **World-writable FTP root** | `chmod -R 777 /srv/ftp` | Directory permissions |
| 5 | **umask 000** | `anon_umask=000`, `local_umask=000` — all new files are world-writable | `/etc/vsftpd.conf` |
| 6 | **FTP bounce enabled** | `pasv_promiscuous=YES`, `port_promiscuous=YES` | `/etc/vsftpd.conf` |
| 7 | **Version in banner** | `ftpd_banner` discloses `vsftpd 3.0.5` | `/etc/vsftpd.conf` |
| 8 | **Credentials in share** | `backup_notes.txt` contains plaintext passwords | `/srv/ftp/pub/backup_notes.txt` |
| 9 | **Weak user accounts** | `ftpuser:ftpuser`, `admin:admin`, `root:ZooTime!` | `/etc/shadow` |
| 10 | **Firewall disabled** | iptables flushed, all policies set to ACCEPT | iptables rules |

---

## FLAMINGO — Mail Server (Debian 12)

| # | Vulnerability | Technical Detail | Config Location |
|---|---------------|------------------|-----------------|
| 1 | **Open SMTP relay** | `smtpd_relay_restrictions = permit_all`, `smtpd_recipient_restrictions = permit_all` — accepts and relays mail from anyone | `/etc/postfix/main.cf` |
| 2 | **No SMTP authentication** | `smtpd_sasl_auth_enable = no` — no auth required to send mail | `/etc/postfix/main.cf` |
| 3 | **No TLS (Postfix)** | `smtpd_tls_security_level = none` — all SMTP traffic in cleartext | `/etc/postfix/main.cf` |
| 4 | **mynetworks = 0.0.0.0/0** | Entire internet treated as a trusted network | `/etc/postfix/main.cf` |
| 5 | **Plaintext IMAP/POP3 auth** | `disable_plaintext_auth = no` — credentials sent in clear | `/etc/dovecot/dovecot.conf` |
| 6 | **No SSL (Dovecot)** | `ssl = no` — no encryption on IMAP/POP3 | `/etc/dovecot/dovecot.conf` |
| 7 | **No SPF/DKIM/DMARC** | No email authentication records — spoofing possible | DNS records |
| 8 | **Weak user accounts** | `mail:mail`, `admin:admin`, `user:password`, `root:ZooTime!` | `/etc/shadow` |
| 9 | **Firewall disabled** | iptables flushed, all policies set to ACCEPT | iptables rules |

---

## HIPPO — Database Server (Debian 12)

| # | Vulnerability | Technical Detail | Config Location |
|---|---------------|------------------|-----------------|
| 1 | **MySQL bound to 0.0.0.0** | Accessible from all network interfaces, not just localhost | `/etc/mysql/mariadb.conf.d/99-insecure.cnf` (`bind-address = 0.0.0.0`) |
| 2 | **Remote root login** | `root@%` with `GRANT OPTION` allows root from any host | MySQL user grants |
| 3 | **Weak root password** | Root password is `password` | `ALTER USER 'root'@'localhost'` |
| 4 | **Weak admin account** | `admin:admin` with `ALL PRIVILEGES` and `GRANT OPTION` | MySQL user grants |
| 5 | **Weak app user** | `dbuser:dbuser` with `ALL PRIVILEGES` on everything | MySQL user grants |
| 6 | **LOAD DATA LOCAL enabled** | `local-infile = 1` — server-side file reads via SQL | `/etc/mysql/mariadb.conf.d/99-insecure.cnf` |
| 7 | **Test database open** | `test` database with `GRANT ALL` to anonymous users (`''@'%'`) | MySQL user grants |
| 8 | **PII in database** | SSNs and salaries stored in plaintext in `ccdc_company.employees` | `ccdc_company` database |
| 9 | **Firewall disabled** | iptables flushed, all policies set to ACCEPT | iptables rules |
| 10 | **Weak OS accounts** | `admin:admin`, `dbadmin:password`, `root:ZooTime!` | `/etc/shadow` |

---

## Summary

| VM | OS | Vuln Count |
|----|-----|:----------:|
| GIRAFFE | Windows Server 2022 | 4 |
| MEERKAT | Windows 11 Enterprise | 2 |
| ZEBRA | Windows Server 2022 | 8 |
| PENGUIN | Ubuntu 22.04 | 12 |
| OTTER | Ubuntu 22.04 | 10 |
| FLAMINGO | Debian 12 | 9 |
| HIPPO | Debian 12 | 10 |
| **Total** | | **55** |
