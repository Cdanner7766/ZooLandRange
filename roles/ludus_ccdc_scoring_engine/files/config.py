"""
Scoring engine configuration.
Range ID and target IPs are auto-detected from the scoring machine's IP address.
SCORESVR lives on 10.{RANGE_ID}.99.x and services are on 10.{RANGE_ID}.10.x
"""

import os
import subprocess


def _detect_range_id():
    """
    Detect the Ludus range ID from SCORESVR's IP (10.X.99.Y pattern).
    Tries 'ip addr show' (searching common paths), then falls back to
    parsing /proc/net/if_inet6 / /proc/net/fib_trie if ip(8) is absent.
    """
    # Common locations for 'ip' on Debian/Kali/Ubuntu
    ip_candidates = [
        "ip",
        "/sbin/ip",
        "/usr/sbin/ip",
        "/bin/ip",
        "/usr/bin/ip",
    ]

    for cmd in ip_candidates:
        try:
            result = subprocess.run(
                [cmd, "addr", "show"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode != 0:
                continue
            for line in result.stdout.splitlines():
                if "inet " not in line or "127.0.0.1" in line:
                    continue
                ip = line.strip().split()[1].split("/")[0]
                parts = ip.split(".")
                if len(parts) == 4 and parts[0] == "10" and parts[2] == "99":
                    return int(parts[1])
        except (FileNotFoundError, PermissionError, subprocess.TimeoutExpired):
            continue
        except Exception:
            break

    # Fallback: parse /proc/net/fib_trie (Linux only, no external tool needed)
    try:
        with open("/proc/net/fib_trie") as f:
            for line in f:
                line = line.strip()
                if line.startswith("LOCAL") or not line[0].isdigit():
                    continue
                ip = line.split()[0]
                parts = ip.split(".")
                if (len(parts) == 4 and parts[0] == "10"
                        and parts[2] == "99" and parts[3] != "255"):
                    return int(parts[1])
    except Exception:
        pass

    return 10  # Default fallback


RANGE_ID = _detect_range_id()
BASE_NET = f"10.{RANGE_ID}.10"

# How often to run a full check round (seconds)
CHECK_INTERVAL = 30

# ------------------------------------------------------------------
# Service definitions
# Each service specifies:
#   id           - unique key used in the database
#   name         - human-readable label
#   machine      - VM hostname from range-config.yaml
#   host         - target IP
#   port         - TCP port
#   check_type   - one of: http, ftp, smtp, imap_login, banner, dns, mysql,
#                           ldap, smb, ssh, tcp, rdp_login
# ------------------------------------------------------------------
def _build_services():
    n = BASE_NET
    return [
        {
            "id": "http",
            "name": "HTTP Web Store",
            "machine": "PENGUIN",
            "host": f"{n}.23",
            "port": 80,
            "check_type": "http",
        },
        {
            "id": "ftp",
            "name": "FTP Server",
            "machine": "OTTER",
            "host": f"{n}.29",
            "port": 21,
            "check_type": "ftp",
            "has_credentials": True,
            # mlopez is a ZooLand Inc. logistics employee provisioned by the FTP
            # server role.  Update via the dashboard if blue team changes the password.
            "default_user": "mlopez",
            "default_pass": "ZooLand2025!",
        },
        {
            "id": "smtp",
            "name": "SMTP (Mail)",
            "machine": "FLAMINGO",
            "host": f"{n}.38",
            "port": 25,
            "check_type": "smtp",
        },
        {
            "id": "imap",
            "name": "IMAP (Mail)",
            "machine": "FLAMINGO",
            "host": f"{n}.38",
            "port": 143,
            "check_type": "imap_login",
            "has_credentials": True,
            # jsmith is a ZooLand Inc. IT support employee provisioned by the mail
            # server role.  Update via the dashboard if blue team changes the password.
            "default_user": "jsmith",
            "default_pass": "ZooLand2025!",
        },
        {
            "id": "pop3",
            "name": "POP3 (Mail)",
            "machine": "FLAMINGO",
            "host": f"{n}.38",
            "port": 110,
            "check_type": "banner",
            "banner_expect": "+OK",
        },
        {
            "id": "dns",
            "name": "DNS Server",
            "machine": "GIRAFFE",
            "host": f"{n}.7",
            "port": 53,
            "check_type": "dns",
            "dns_query": "web.zooland.local",
            "dns_expected_ip": f"{n}.23",
        },
        {
            "id": "mysql",
            "name": "MySQL Database",
            "machine": "HIPPO",
            "host": f"{n}.41",
            "port": 3306,
            "check_type": "mysql",
        },
        {
            "id": "smb",
            "name": "SMB File Share",
            "machine": "ZEBRA",
            "host": f"{n}.15",
            "port": 445,
            "check_type": "smb",
        },
        {
            "id": "ldap",
            "name": "LDAP (Active Directory)",
            "machine": "GIRAFFE",
            "host": f"{n}.7",
            "port": 389,
            "check_type": "ldap",
        },
        {
            "id": "kerberos",
            "name": "Kerberos (Active Directory)",
            "machine": "GIRAFFE",
            "host": f"{n}.7",
            "port": 88,
            "check_type": "tcp",
        },
        # ------------------------------------------------------------------
        # Workstation RDP — verify a domain user can authenticate via NLA
        # ------------------------------------------------------------------
        {
            "id": "rdp_meerkat",
            "name": "RDP (Workstation MEERKAT)",
            "machine": "MEERKAT",
            "host": f"{n}.12",
            "port": 3389,
            "check_type": "rdp_login",
            "rdp_domain": "zooland",
            "has_credentials": True,
            # jsmith is a ZooLand Inc. domain user. Update via dashboard if
            # blue team changes the password.
            "default_user": "jsmith",
            "default_pass": "ZooLand2025!",
        },
        # ------------------------------------------------------------------
        # SSH — admin access to every Linux server
        # ------------------------------------------------------------------
        {
            "id": "ssh_web",
            "name": "SSH (Web Server)",
            "machine": "PENGUIN",
            "host": f"{n}.23",
            "port": 22,
            "check_type": "ssh",
        },
        {
            "id": "ssh_db",
            "name": "SSH (Database Server)",
            "machine": "HIPPO",
            "host": f"{n}.41",
            "port": 22,
            "check_type": "ssh",
        },
        {
            "id": "ssh_mail",
            "name": "SSH (Mail Server)",
            "machine": "FLAMINGO",
            "host": f"{n}.38",
            "port": 22,
            "check_type": "ssh",
        },
        {
            "id": "ssh_ftp",
            "name": "SSH (FTP Server)",
            "machine": "OTTER",
            "host": f"{n}.29",
            "port": 22,
            "check_type": "ssh",
        },
    ]


SERVICES = _build_services()
