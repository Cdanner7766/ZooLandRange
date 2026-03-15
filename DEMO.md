# ZooLandRange — Service Demonstration Guide

This guide shows how to connect to and interact with every service in the range.
It is written from the perspective of someone who wants to verify the environment
works, demonstrate it to others, or exercise each service before a practice session.

**Replace `X` with your Ludus range ID throughout** (e.g. if your range ID is `10`,
then `10.X.10.7` becomes `10.10.10.7`).

**Best starting point:** SSH into or open a terminal on **JAGUAR** (`10.X.99.34`),
the Kali Linux VM. It has full access to all corporate services and ships with every
tool used in this guide.

```bash
# Connect to JAGUAR from the Ludus host
ssh kali@10.X.99.34
# Password: kali
```

---

## Table of Contents

1. [Scoring Dashboard](#1-scoring-dashboard)
2. [Web Application — CrazyRhino Store](#2-web-application--crazyrhino-store)
3. [Email — Sending Mail Between Employees](#3-email--sending-mail-between-employees)
4. [Email — Reading Mail via IMAP and POP3](#4-email--reading-mail-via-imap-and-pop3)
5. [Database — Connecting to MySQL and Querying Data](#5-database--connecting-to-mysql-and-querying-data)
6. [FTP — Browsing and Transferring Files](#6-ftp--browsing-and-transferring-files)
7. [SMB File Shares — Accessing Windows Shares](#7-smb-file-shares--accessing-windows-shares)
8. [RDP — Remote Desktop to the Workstation](#8-rdp--remote-desktop-to-the-workstation)
9. [DNS — Resolving Hostnames and Zone Transfer](#9-dns--resolving-hostnames-and-zone-transfer)
10. [Active Directory — LDAP Queries](#10-active-directory--ldap-queries)
11. [SSH — Accessing Linux Servers](#11-ssh--accessing-linux-servers)
12. [Validation Script — Test Everything at Once](#12-validation-script--test-everything-at-once)

---

## 1. Scoring Dashboard

The scoring engine runs on **SCORESVR** and polls all services every 30 seconds.
The live dashboard is reachable from any corporate (VLAN 10) machine and from JAGUAR.

**From JAGUAR or MEERKAT — open a browser:**
```
http://10.X.99.17:8080/
```

The dashboard shows:
- Current UP/DOWN status for every service
- Historical uptime percentage per service
- Countdown to the next check round
- Credential update fields for services that use login checks

**From JAGUAR — check the dashboard via curl:**
```bash
curl -s http://10.X.99.17:8080/api/status | python3 -m json.tool
```

Expected output (abbreviated):
```json
{
    "last_check_time": "2025-04-01 14:32:01",
    "next_check_in": 18,
    "round_count": 47,
    "services": {
        "http":    { "name": "HTTP Web Store",          "up": true,  "uptime_pct": 100.0 },
        "ftp":     { "name": "FTP Server",              "up": true,  "uptime_pct": 98.0  },
        "smtp":    { "name": "SMTP (Mail)",             "up": true,  "uptime_pct": 100.0 },
        "dns":     { "name": "DNS Server",              "up": true,  "uptime_pct": 100.0 },
        "mysql":   { "name": "MySQL Database",          "up": true,  "uptime_pct": 100.0 },
        "smb":     { "name": "SMB File Share",          "up": true,  "uptime_pct": 100.0 },
        "ldap":    { "name": "LDAP (Active Directory)", "up": true,  "uptime_pct": 100.0 }
    }
}
```

---

## 2. Web Application — CrazyRhino Store

**Server:** PENGUIN (`10.X.10.23`)
**URL:** `http://10.X.10.23/`

### Open the store in a browser

From JAGUAR's desktop or MEERKAT:
```
http://10.X.10.23/
```

You should see the CrazyRhino Wildlife Supply e-commerce storefront with animal products listed.

### Browse the store via curl (from terminal)

```bash
# Check the store loads
curl -s http://10.X.10.23/ | grep -i "crazyrhino\|zoo\|wild"

# Check the API health endpoint
curl -s http://10.X.10.23:5000/api/health

# List products
curl -s http://10.X.10.23:5000/api/products | python3 -m json.tool
```

### Log in as the admin account

```bash
curl -s -X POST http://10.X.10.23:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | python3 -m json.tool
```

Expected: JSON response containing a JWT token.

### Log in as a regular employee

```bash
curl -s -X POST http://10.X.10.23:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"johndoe","password":"password123"}' | python3 -m json.tool
```

### Register a new user account

```bash
curl -s -X POST http://10.X.10.23:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@zooland.local","password":"testpass1"}' \
  | python3 -m json.tool
```

---

## 3. Email — Sending Mail Between Employees

**Server:** FLAMINGO (`10.X.10.38`)
**Ports:** SMTP 25

The mail server runs Postfix configured as an **open relay** — it will accept and
deliver mail from any sender to any recipient without authentication.

### Send an email using `swaks` (recommended — from JAGUAR)

`swaks` (Swiss Army Knife SMTP) is pre-installed on Kali and makes SMTP testing easy.

```bash
# Send from mlopez (Logistics) to jsmith (IT Support)
swaks \
  --to jsmith@zooland.local \
  --from mlopez@zooland.local \
  --server 10.X.10.38 \
  --port 25 \
  --body "Hi John, please check the new file on the FTP server. - Maria"

# Send from an external address (demonstrates open relay)
swaks \
  --to jsmith@zooland.local \
  --from anyone@external.com \
  --server 10.X.10.38 \
  --port 25 \
  --body "This message came from outside the organization."
```

Expected output (last few lines):
```
<-  220 FLAMINGO ESMTP Postfix
 -> EHLO ...
<-  250-FLAMINGO
<-  250 Ok
<-  354 End data with <CR><LF>.<CR><LF>
 -> .
<-  250 2.0.0 Ok: queued as ...
```

### Send an email using raw SMTP (telnet / netcat)

This demonstrates the raw SMTP protocol step-by-step:

```bash
telnet 10.X.10.38 25
```

Then type each line and press Enter:
```
EHLO zooland.local
MAIL FROM:<bwilson@zooland.local>
RCPT TO:<mchen@zooland.local>
DATA
Subject: Q3 Finance Report

Hi Michelle, the Q3 report is ready for your review.
.
QUIT
```

### Send an email using Python (from JAGUAR or any Linux VM)

```bash
python3 - <<'EOF'
import smtplib
from email.mime.text import MIMEText

msg = MIMEText("Hi Robert, the shipment documents are on the FTP server.")
msg["Subject"] = "Shipment Update"
msg["From"]    = "mlopez@zooland.local"
msg["To"]      = "rthomas@zooland.local"

with smtplib.SMTP("10.X.10.38", 25) as smtp:
    smtp.sendmail("mlopez@zooland.local", ["rthomas@zooland.local"], msg.as_string())
    print("Mail sent successfully.")
EOF
```

---

## 4. Email — Reading Mail via IMAP and POP3

**Server:** FLAMINGO (`10.X.10.38`)
**Ports:** IMAP 143, POP3 110

### Read email via IMAP using raw telnet

```bash
telnet 10.X.10.38 143
```

Then type each line (the `a` prefix is the IMAP tag — required):
```
a LOGIN jsmith ZooLand2025!
a SELECT INBOX
a FETCH 1 BODY[TEXT]
a LOGOUT
```

Expected output after LOGIN:
```
* OK [CAPABILITY ...] Dovecot ready.
a OK [CAPABILITY ...] Logged in
* 1 EXISTS
* 0 RECENT
```

### Read email via POP3 using raw telnet

```bash
telnet 10.X.10.38 110
```

Then:
```
USER jsmith
PASS ZooLand2025!
LIST
RETR 1
QUIT
```

Expected output after PASS:
```
+OK Logged in.
+OK 1 messages:
1 342
```

### Read email using Python (from JAGUAR)

```bash
python3 - <<'EOF'
import imaplib, email

M = imaplib.IMAP4("10.X.10.38", 143)
M.login("jsmith", "ZooLand2025!")
M.select("INBOX")

status, data = M.search(None, "ALL")
for num in data[0].split():
    status, msg_data = M.fetch(num, "(RFC822)")
    msg = email.message_from_bytes(msg_data[0][1])
    print(f"From: {msg['From']}")
    print(f"Subject: {msg['Subject']}")
    print("---")
M.logout()
EOF
```

---

## 5. Database — Connecting to MySQL and Querying Data

**Server:** HIPPO (`10.X.10.41`)
**Port:** 3306

### Connect with the MySQL client (from JAGUAR)

```bash
# Connect as root (password: password)
mysql -h 10.X.10.41 -u root -ppassword
```

### Useful MySQL commands once connected

```sql
-- List all databases
SHOW DATABASES;

-- Open the company database
USE ccdc_company;

-- List tables
SHOW TABLES;

-- View all employee records (includes SSNs and salaries)
SELECT * FROM employees;

-- Find a specific employee
SELECT name, email, salary FROM employees WHERE name LIKE '%Smith%';

-- List all MySQL user accounts and their privileges
SELECT user, host FROM mysql.user;
SHOW GRANTS FOR 'root'@'%';
```

### One-liner queries (without entering interactive mode)

```bash
# List all databases
mysql -h 10.X.10.41 -u root -ppassword -e "SHOW DATABASES;"

# Dump the employees table
mysql -h 10.X.10.41 -u root -ppassword -e "SELECT * FROM ccdc_company.employees;"

# Connect as the application user instead
mysql -h 10.X.10.41 -u dbuser -pdbuser -e "SHOW DATABASES;"

# Connect as the admin user
mysql -h 10.X.10.41 -u admin -padmin -e "SELECT user,host FROM mysql.user;"
```

### Connect using Python (from JAGUAR)

```bash
python3 - <<'EOF'
import pymysql

conn = pymysql.connect(host="10.X.10.41", user="root", password="password", database="ccdc_company")
cursor = conn.cursor()
cursor.execute("SELECT id, name, email, ssn, salary FROM employees")
for row in cursor.fetchall():
    print(row)
conn.close()
EOF
```

---

## 6. FTP — Browsing and Transferring Files

**Server:** OTTER (`10.X.10.29`)
**Port:** 21 (control), 40000–40100 (passive data)

### Anonymous FTP (no credentials required)

```bash
ftp 10.X.10.29
# Name: anonymous
# Password: (press Enter or type any email)
```

FTP commands once connected:
```
ls              # list files in current directory
cd pub          # enter the pub directory
ls              # list pub contents
get readme.txt  # download a file
get backup_notes.txt
bye             # disconnect
```

### Log in as an employee account

```bash
ftp 10.X.10.29
# Name: mlopez
# Password: ZooLand2025!
```

```
ls              # list home directory
put testfile.txt  # upload a file (demonstrates write access)
bye
```

### Use `lftp` for a full-featured client (from JAGUAR)

```bash
# Anonymous session with full directory listing
lftp -u anonymous, 10.X.10.29
ls -la
mirror pub/ /tmp/ftp-pub/   # download the entire pub/ directory
quit
```

```bash
# Employee login
lftp -u mlopez,ZooLand2025! 10.X.10.29
ls
put /etc/hostname uploaded_hostname.txt
quit
```

### Download a file without an interactive client

```bash
# Download backup_notes.txt anonymously (contains credential list)
wget ftp://anonymous:@10.X.10.29/pub/backup_notes.txt
cat backup_notes.txt

# Or use curl
curl ftp://10.X.10.29/pub/readme.txt
curl ftp://10.X.10.29/pub/backup_notes.txt
```

---

## 7. SMB File Shares — Accessing Windows Shares

**Server:** ZEBRA (`10.X.10.15`)
**Port:** 445
**Shares:** `Public`, `Shared`

### List available shares (from JAGUAR)

```bash
# List shares — no credentials (Guest/anonymous access)
smbclient -L //10.X.10.15 -N

# List shares with domain user credentials
smbclient -L //10.X.10.15 -U "zooland.local\\jsmith%ZooLand2025!"
```

Expected output:
```
Sharename    Type  Comment
---------    ----  -------
Public       Disk
Shared       Disk
IPC$         IPC   Remote IPC
```

### Browse the Public share (no credentials)

```bash
smbclient //10.X.10.15/Public -N
```

SMB shell commands:
```
ls                      # list files
get readme.txt          # download readme.txt
get backup_notes.txt    # download the credential file (if present)
put /etc/hostname test.txt  # upload a file (demonstrates write access)
exit
```

### Browse the Shared (IT) share

```bash
# As a domain user
smbclient //10.X.10.15/Shared -U "zooland.local\\jsmith%ZooLand2025!"

# As the domain admin
smbclient //10.X.10.15/Shared -U "zooland.local\\domainadmin%password"
```

SMB shell commands:
```
ls
get IT_Notes.txt   # download the IT notes file containing server passwords
exit
```

### Mount the share as a filesystem (from JAGUAR)

```bash
sudo mkdir -p /mnt/zebra-public
sudo mount -t cifs //10.X.10.15/Public /mnt/zebra-public -o guest

ls /mnt/zebra-public
cat /mnt/zebra-public/readme.txt

sudo umount /mnt/zebra-public
```

### Access shares from MEERKAT (Windows)

Open **File Explorer** on MEERKAT and type in the address bar:
```
\\ZEBRA\Public
```
or:
```
\\10.X.10.15\Public
```

Since the shares allow Guest access and `MEERKAT` is domain-joined, no credentials
prompt should appear. Files in the share will be visible and editable.

---

## 8. RDP — Remote Desktop to the Workstation

**Server:** MEERKAT (`10.X.10.12`)
**Port:** 3389
**Domain:** `zooland.local`

### Connect from JAGUAR using xfreerdp

```bash
# Log in as domain employee jsmith
xfreerdp /v:10.X.10.12 /u:jsmith /p:'ZooLand2025!' /d:zooland /cert:ignore

# Log in as domain admin
xfreerdp /v:10.X.10.12 /u:domainadmin /p:password /d:zooland /cert:ignore

# Log in as local Administrator
xfreerdp /v:10.X.10.12 /u:Administrator /p:password /cert:ignore

# Useful display options
xfreerdp /v:10.X.10.12 /u:jsmith /p:'ZooLand2025!' /d:zooland \
  /cert:ignore /w:1280 /h:800 /dynamic-resolution
```

Once connected you will see a Windows 11 desktop. The machine has the following
tools installed (via Chocolatey) for blue team use:
- Wireshark, Process Hacker, Network Monitor
- Burp Suite Free
- 7-Zip, Croc
- ILSpy, Explorer Suite
- Firefox

### Verify RDP is open (without connecting)

```bash
# Quick port check
nc -zv 10.X.10.12 3389

# Or use nmap
nmap -p 3389 --open 10.X.10.12
```

### Connect from another Windows machine (mstsc)

On any Windows machine in the range (e.g. MEERKAT itself or ZEBRA), press
`Win+R` and run:
```
mstsc /v:10.X.10.12
```

Enter credentials: `zooland\jsmith` / `ZooLand2025!`

---

## 9. DNS — Resolving Hostnames and Zone Transfer

**Server:** GIRAFFE (`10.X.10.7`)
**Port:** 53

### Basic hostname resolution

```bash
# Resolve a service hostname
nslookup web.zooland.local 10.X.10.7
nslookup mail.zooland.local 10.X.10.7
nslookup db.zooland.local 10.X.10.7
nslookup ftp.zooland.local 10.X.10.7
nslookup files.zooland.local 10.X.10.7

# Same with dig
dig web.zooland.local @10.X.10.7
dig mail.zooland.local @10.X.10.7 +short
```

Expected output for `web.zooland.local`:
```
Name:   web.zooland.local
Address: 10.X.10.23
```

### Look up the MX record (mail exchanger)

```bash
dig MX zooland.local @10.X.10.7
```

Expected:
```
zooland.local.   600  IN  MX  10 mail.zooland.local.
```

### Perform a zone transfer (AXFR — dumps every record in the zone)

```bash
dig axfr zooland.local @10.X.10.7
```

This returns all DNS records in the `zooland.local` zone — A records, MX records,
SOA, NS, and any host entries created when machines joined the domain. In a real
environment zone transfers would be restricted; here they are intentionally open.

Expected output (abbreviated):
```
zooland.local.      SOA   GIRAFFE.zooland.local. ...
zooland.local.      NS    GIRAFFE.zooland.local.
zooland.local.      MX    10 mail.zooland.local.
GIRAFFE.zooland.local.  A     10.X.10.7
MEERKAT.zooland.local.  A     10.X.10.12
ZEBRA.zooland.local.    A     10.X.10.15
web.zooland.local.      A     10.X.10.23
ftp.zooland.local.      A     10.X.10.29
mail.zooland.local.     A     10.X.10.38
db.zooland.local.       A     10.X.10.41
```

### Reverse lookup

```bash
# Find what hostname owns an IP
dig -x 10.X.10.23 @10.X.10.7
```

---

## 10. Active Directory — LDAP Queries

**Server:** GIRAFFE (`10.X.10.7`)
**Port:** 389 (LDAP), 88 (Kerberos)

### Anonymous LDAP bind and query

```bash
# Test that LDAP is responding
ldapsearch -x -H ldap://10.X.10.7 -b "" -s base

# Query all user accounts in the domain (anonymous bind)
ldapsearch -x \
  -H ldap://10.X.10.7 \
  -b "DC=zooland,DC=local" \
  "(objectClass=user)" \
  sAMAccountName displayName description
```

Expected output (one entry shown):
```
# jsmith, Users, zooland.local
dn: CN=John Smith,CN=Users,DC=zooland,DC=local
sAMAccountName: jsmith
displayName: John Smith
description: IT Support
```

### Query with domain credentials (authenticated bind)

```bash
ldapsearch -x \
  -H ldap://10.X.10.7 \
  -D "CN=jsmith,CN=Users,DC=zooland,DC=local" \
  -w 'ZooLand2025!' \
  -b "DC=zooland,DC=local" \
  "(objectClass=user)" \
  sAMAccountName mail department
```

### List all domain groups

```bash
ldapsearch -x \
  -H ldap://10.X.10.7 \
  -b "DC=zooland,DC=local" \
  "(objectClass=group)" \
  cn description
```

### Check Kerberos is running (KDC port)

```bash
# Quick TCP check — should connect and immediately close
nc -zv 10.X.10.7 88

# Or with nmap
nmap -p 88 --open 10.X.10.7
```

---

## 11. SSH — Accessing Linux Servers

All four Linux servers (PENGUIN, OTTER, FLAMINGO, HIPPO) have SSH running on port 22.
Each has weak OS accounts created by their respective Ansible roles.

### Connect to each server

```bash
# Web server (PENGUIN)
ssh root@10.X.10.23          # password: toor
ssh admin@10.X.10.23         # password: admin
ssh webadmin@10.X.10.23      # password: password

# FTP server (OTTER)
ssh root@10.X.10.29          # password: toor
ssh mlopez@10.X.10.29        # password: ZooLand2025!

# Mail server (FLAMINGO)
ssh root@10.X.10.38          # password: toor
ssh jsmith@10.X.10.38        # password: ZooLand2025!

# Database server (HIPPO)
ssh root@10.X.10.41          # password: toor
ssh admin@10.X.10.41         # password: admin
```

### Check what's running on a server after SSH

```bash
# On PENGUIN — verify Docker containers are up
ssh root@10.X.10.23 "docker ps"

# On OTTER — verify vsftpd is running
ssh root@10.X.10.29 "systemctl status vsftpd"

# On FLAMINGO — verify Postfix and Dovecot are running
ssh root@10.X.10.38 "systemctl status postfix dovecot"

# On HIPPO — verify MariaDB is running and listening
ssh root@10.X.10.41 "systemctl status mariadb && ss -tlnp | grep 3306"
```

### Scan all SSH banners at once (from JAGUAR)

```bash
for ip in 10.X.10.23 10.X.10.29 10.X.10.38 10.X.10.41; do
  echo -n "$ip: "
  nc -w2 $ip 22 2>/dev/null | head -1
done
```

---

## 12. Validation Script — Test Everything at Once

A pre-built validation script lives at `scripts/test_range.sh`. It runs from
**JAGUAR** and checks every service automatically, printing a pass/fail summary.

### Copy the script to JAGUAR (run from the Ludus host)

```bash
scp ~/ZooLandRange/scripts/test_range.sh kali@10.X.99.34:~/
```

### Run the script

```bash
ssh kali@10.X.99.34
chmod +x ~/test_range.sh
./test_range.sh
```

The script tests:
- **Connectivity:** ICMP ping to all 7 corporate VMs
- **Web (PENGUIN):** HTTP 200, CrazyRhino content, API `/health`, admin login
- **Database (HIPPO):** Port open, weak credential login, `ccdc_company` query
- **SMB (ZEBRA):** Port open, anonymous share listing, file read
- **Mail (FLAMINGO):** Ports 25/110/143 open, SMTP relay, POP3 banner
- **DNS (GIRAFFE):** All A record lookups, MX record, AXFR zone transfer
- **FTP (OTTER):** Port open, banner read, anonymous file download
- **Domain Controller (GIRAFFE):** Ports 53/88/389/445

---

## Quick Reference — All Services at a Glance

| Service | VM | IP | Port | Demo Command |
|---------|----|----|------|-------------|
| Web Store | PENGUIN | `10.X.10.23` | 80 | `curl http://10.X.10.23/` |
| Web API | PENGUIN | `10.X.10.23` | 5000 | `curl http://10.X.10.23:5000/api/health` |
| FTP | OTTER | `10.X.10.29` | 21 | `ftp 10.X.10.29` (user: `anonymous`) |
| SMTP | FLAMINGO | `10.X.10.38` | 25 | `swaks --to jsmith@zooland.local --from mlopez@zooland.local --server 10.X.10.38` |
| IMAP | FLAMINGO | `10.X.10.38` | 143 | `telnet 10.X.10.38 143` then `a LOGIN jsmith ZooLand2025!` |
| POP3 | FLAMINGO | `10.X.10.38` | 110 | `telnet 10.X.10.38 110` then `USER jsmith` |
| MySQL | HIPPO | `10.X.10.41` | 3306 | `mysql -h 10.X.10.41 -u root -ppassword` |
| SMB Public | ZEBRA | `10.X.10.15` | 445 | `smbclient //10.X.10.15/Public -N` |
| SMB Shared | ZEBRA | `10.X.10.15` | 445 | `smbclient //10.X.10.15/Shared -U "zooland.local\\jsmith%ZooLand2025!"` |
| RDP | MEERKAT | `10.X.10.12` | 3389 | `xfreerdp /v:10.X.10.12 /u:jsmith /p:'ZooLand2025!' /d:zooland /cert:ignore` |
| DNS | GIRAFFE | `10.X.10.7` | 53 | `dig web.zooland.local @10.X.10.7` |
| LDAP | GIRAFFE | `10.X.10.7` | 389 | `ldapsearch -x -H ldap://10.X.10.7 -b "DC=zooland,DC=local" "(objectClass=user)"` |
| Kerberos | GIRAFFE | `10.X.10.7` | 88 | `nc -zv 10.X.10.7 88` |
| SSH — Web | PENGUIN | `10.X.10.23` | 22 | `ssh root@10.X.10.23` (pw: `toor`) |
| SSH — DB | HIPPO | `10.X.10.41` | 22 | `ssh root@10.X.10.41` (pw: `toor`) |
| SSH — Mail | FLAMINGO | `10.X.10.38` | 22 | `ssh root@10.X.10.38` (pw: `toor`) |
| SSH — FTP | OTTER | `10.X.10.29` | 22 | `ssh root@10.X.10.29` (pw: `toor`) |
| Scoring Dashboard | SCORESVR | `10.X.99.17` | 8080 | `curl http://10.X.99.17:8080/api/status` |
