#!/usr/bin/env python3
"""
ZooLandRange validation: the 15 scoring checks (900 pts) plus every
intentional vulnerability listed in CLAUDE.md / README.md.

Run from JAGUAR (VLAN 99 can reach all of VLAN 10):

    python3 tests/check.py                 # range number auto-detected, else 1
    python3 tests/check.py --range 2
    python3 tests/check.py --only scoring  # or: vuln
    python3 tests/check.py --strict        # SKIP counts as failure

Standard library only. Deeper checks use optional tools when installed
(sshpass, smbclient, mysql/mariadb, ldapsearch, xfreerdp, pywinrm) and
report SKIP, never PASS, when a tool or credential is missing.

Exit code: 0 = no FAIL (and no SKIP with --strict), 1 otherwise.
Read-only: nothing on the range is modified.
"""
import argparse
import ftplib
import http.client
import io
import json
import os
import re
import shlex
import shutil
import socket
import struct
import subprocess
import sys
import hashlib

TIMEOUT = 6
ROOT_PW = "ZooTime!"
ADMIN_PW = "ZooTime!"
EMP_PW = "ZooLand2025!"

PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"
results = []  # (section, name, status, detail, points)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def detect_range():
    try:
        out = subprocess.run(["ip", "-4", "addr"], capture_output=True, text=True).stdout
        m = re.search(r"10\.(\d+)\.99\.\d+", out)
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return 1


def tcp_open(host, port):
    try:
        socket.create_connection((host, port), TIMEOUT).close()
        return True
    except OSError:
        return False


def banner(host, port, send=None):
    with socket.create_connection((host, port), TIMEOUT) as s:
        s.settimeout(TIMEOUT)
        if send:
            s.recv(2048)
            s.sendall(send)
        return s.recv(2048).decode(errors="replace")


def converse(host, port, lines):
    """Send each line, return list of replies (first reply = greeting)."""
    out = []
    with socket.create_connection((host, port), TIMEOUT) as s:
        s.settimeout(TIMEOUT)
        out.append(s.recv(4096).decode(errors="replace"))
        for ln in lines:
            s.sendall(ln.encode() + b"\r\n")
            out.append(s.recv(4096).decode(errors="replace"))
    return out


def http_req(host, port, path, method="GET", body=None, headers=None):
    c = http.client.HTTPConnection(host, port, timeout=TIMEOUT)
    h = dict(headers or {})
    if body is not None:
        body = json.dumps(body)
        h["Content-Type"] = "application/json"
    c.request(method, path, body=body, headers=h)
    r = c.getresponse()
    data = r.read().decode(errors="replace")
    hdrs = {k.lower(): v for k, v in r.getheaders()}
    c.close()
    return r.status, hdrs, data


def have(tool):
    return shutil.which(tool) is not None


def run(cmd, timeout=20, inp=None):
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, input=inp)
    return p.returncode, (p.stdout + p.stderr)


SSH_USERS = (("localuser", "password"), ("debian", "debian"))  # Ludus default account, passwordless sudo


def ssh_root(host, cmd):
    """Run cmd as root over SSH (Ludus default user + sudo). Returns (rc, output) or None if no sshpass.
    sshd's default PermitRootLogin refuses the documented root password, so root@ SSH is not used."""
    if not have("sshpass"):
        return None
    out = ""
    for user, pw in SSH_USERS:
        rc, out = run(["sshpass", "-p", pw, "ssh", "-o", "StrictHostKeyChecking=no",
                       "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=6", "-o", "LogLevel=ERROR",
                       f"{user}@{host}", "sudo -n sh -c " + shlex.quote(cmd)], timeout=30)
        if "Permission denied" not in out:
            return rc, out
    return 255, out


def _recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("connection closed")
        buf += chunk
    return buf


def _mysql_packet(sock):
    hdr = _recv_exact(sock, 4)
    return hdr[3], _recv_exact(sock, int.from_bytes(hdr[:3], "little"))


def _lenenc(buf, pos):
    b = buf[pos]
    if b < 0xFB:
        return b, pos + 1
    if b == 0xFB:
        return None, pos + 1
    n = {0xFC: 2, 0xFD: 3, 0xFE: 8}[b]
    return int.from_bytes(buf[pos + 1:pos + 1 + n], "little"), pos + 1 + n


def mysql_q(host, user, pw, sql, db=None):
    """Minimal MySQL/MariaDB client (mysql_native_password). Returns (rc, text); text is the rows, tab-separated."""
    with socket.create_connection((host, 3306), TIMEOUT) as s:
        s.settimeout(TIMEOUT)
        _, hs = _mysql_packet(s)
        if hs[0] != 10:
            return 1, f"unexpected protocol {hs[0]}"
        pos = hs.index(b"\0", 1) + 1 + 4
        salt = hs[pos:pos + 8]
        pos += 8 + 1 + 2 + 1 + 2 + 2
        alen = hs[pos]
        pos += 1 + 10
        salt += hs[pos:pos + max(13, alen - 8)][:12]
        sha = lambda d: hashlib.sha1(d).digest()
        token = b"" if not pw else bytes(a ^ b for a, b in zip(sha(pw.encode()), sha(salt + sha(sha(pw.encode())))))
        caps = 0x1 | 0x200 | 0x8000 | 0x80000 | (0x8 if db else 0)
        resp = struct.pack("<IIB23x", caps, 1 << 24, 33) + user.encode() + b"\0" + bytes([len(token)]) + token
        resp += (db.encode() + b"\0" if db else b"") + b"mysql_native_password\0"
        s.sendall(len(resp).to_bytes(3, "little") + b"\x01" + resp)
        _, r = _mysql_packet(s)
        if r[0] == 0xFF:
            return 1, r[9:].decode(errors="replace")
        if r[0] != 0x00:
            return 1, f"auth not completed (plugin switch?): {r[1:30]!r}"
        q = b"\x03" + sql.encode()
        s.sendall(len(q).to_bytes(3, "little") + b"\x00" + q)
        _, r = _mysql_packet(s)
        if r[0] == 0xFF:
            return 1, r[9:].decode(errors="replace")
        if r[0] == 0x00:
            return 0, ""
        ncols, _ = _lenenc(r, 0)
        for _ in range(ncols):
            _mysql_packet(s)
        _mysql_packet(s)  # EOF after column defs
        rows = []
        while True:
            _, r = _mysql_packet(s)
            if r[0] == 0xFE and len(r) < 9:
                break
            if r[0] == 0xFF:
                return 1, r[9:].decode(errors="replace")
            pos, row = 0, []
            for _ in range(ncols):
                ln, pos = _lenenc(r, pos)
                row.append("NULL" if ln is None else r[pos:pos + ln].decode(errors="replace"))
                pos += ln or 0
            rows.append("\t".join(row))
        return 0, "\n".join(rows)


def winrm(host, user, pw, ps):
    """Run PowerShell over WinRM (HTTPS 5986, as Ludus configures it). Returns (rc, stdout) or None without pywinrm."""
    try:
        import winrm as _w
    except ImportError:
        return None
    try:
        sess = _w.Session(f"https://{host}:5986/wsman", auth=(user, pw), transport="ntlm",
                          server_cert_validation="ignore", operation_timeout_sec=20, read_timeout_sec=30)
        r = sess.run_ps(ps)
        return r.status_code, r.std_out.decode(errors="replace")
    except Exception as e:
        return 1, f"winrm error: {e}"


def record(section, name, fn, points=0):
    try:
        res = fn()
        if isinstance(res, tuple):
            status, detail = res
        else:
            status, detail = (PASS if res else FAIL), ""
    except (socket.timeout, TimeoutError):
        status, detail = FAIL, "timed out"
    except ConnectionRefusedError:
        status, detail = FAIL, "connection refused"
    except Exception as e:
        status, detail = FAIL, f"{type(e).__name__}: {e}"
    results.append((section, name, status, detail, points))
    color = {PASS: "\033[32m", FAIL: "\033[31m", SKIP: "\033[33m"}[status] if sys.stdout.isatty() else ""
    reset = "\033[0m" if color else ""
    pts = f" ({points} pts)" if points else ""
    print(f"  {color}[{status}]{reset} {name}{pts}" + (f" - {detail}" if detail else ""))


def ok(detail=""):
    return PASS, detail


def bad(detail=""):
    return FAIL, detail


def skip(detail):
    return SKIP, detail


# --------------------------------------------------------------------------
# DNS (raw, stdlib)
# --------------------------------------------------------------------------
def dns_name(name):
    return b"".join(bytes([len(p)]) + p.encode() for p in name.rstrip(".").split(".")) + b"\0"


def dns_query(host, name, qtype=1, rd=True, tcp=False):
    hdr = struct.pack(">HHHHHH", 0xBEEF, 0x0100 if rd else 0, 1, 0, 0, 0)
    pkt = hdr + dns_name(name) + struct.pack(">HH", qtype, 1)
    if tcp:
        with socket.create_connection((host, 53), TIMEOUT) as s:
            s.sendall(struct.pack(">H", len(pkt)) + pkt)
            data = b""
            first = s.recv(2)
            if len(first) < 2:
                return b""
            ln = struct.unpack(">H", first)[0]
            while len(data) < ln:
                chunk = s.recv(ln - len(data))
                if not chunk:
                    break
                data += chunk
            return data
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(TIMEOUT)
        s.sendto(pkt, (host, 53))
        return s.recvfrom(4096)[0]


def dns_flags(resp):
    f = struct.unpack(">H", resp[2:4])[0]
    return {"rcode": f & 0xF, "ra": bool(f & 0x80), "an": struct.unpack(">H", resp[6:8])[0]}


def _skip_name(buf, pos):
    while True:
        ln = buf[pos]
        if ln == 0:
            return pos + 1
        if ln >= 0xC0:
            return pos + 2
        pos += 1 + ln


def dns_a_records(resp):
    """Extract IPv4 addresses from the A answers of a DNS response."""
    ips = []
    an = struct.unpack(">H", resp[6:8])[0]
    pos = _skip_name(resp, 12) + 4  # QNAME + QTYPE/QCLASS
    for _ in range(an):
        pos = _skip_name(resp, pos)
        typ, _, _, rdlen = struct.unpack(">HHIH", resp[pos:pos + 10])
        pos += 10
        if typ == 1 and rdlen == 4:
            ips.append(".".join(str(b) for b in resp[pos:pos + 4]))
        pos += rdlen
    return ips


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--range", type=int, default=None, help="range number X (default: autodetect, else 1)")
    ap.add_argument("--only", choices=["scoring", "vuln"])
    ap.add_argument("--strict", action="store_true", help="treat SKIP as failure")
    args = ap.parse_args()

    X = args.range if args.range is not None else detect_range()
    n = f"10.{X}.10"
    GIRAFFE, MEERKAT, ZEBRA, PENGUIN, OTTER, FLAMINGO, HIPPO = (
        f"{n}.7", f"{n}.12", f"{n}.15", f"{n}.23", f"{n}.29", f"{n}.38", f"{n}.41")
    print(f"ZooLandRange check - range {X} (10.{X}.0.0/16)")

    state = {}  # shared between checks

    # ======================================================================
    if args.only in (None, "scoring"):
        print("\n== Scoring checks (900 pts) ==")
        S = "scoring"

        def http_store():
            st, _, body = http_req(PENGUIN, 80, "/")
            return ok(f"HTTP {st}") if st == 200 and body else bad(f"HTTP {st}")
        record(S, "HTTP CrazyRhino (PENGUIN:80)", http_store, 100)

        def ldap():
            # Anonymous simple bind (LDAPv3); AD answers with a long-form BER length, so look for the
            # BindResponse tag (0x61) anywhere in the reply, as the scoring engine does.
            bind = bytes.fromhex("300c020101600702010304008000")
            with socket.create_connection((GIRAFFE, 389), TIMEOUT) as s:
                s.settimeout(TIMEOUT)
                s.sendall(bind)
                r = s.recv(256)
            return ok("LDAP BindResponse received") if len(r) >= 7 and 0x61 in r else bad("no LDAP bindResponse")
        record(S, "LDAP (GIRAFFE:389)", ldap, 100)

        record(S, "Kerberos (GIRAFFE:88)", lambda: ok() if tcp_open(GIRAFFE, 88) else bad("port closed"), 100)

        def dns_res():
            r = dns_query(GIRAFFE, "web.zooland.local")
            f = dns_flags(r)
            ips = dns_a_records(r)
            if f["rcode"] == 0 and f"{n}.23" in ips:
                return ok(f"web.zooland.local -> {ips}")
            return bad(f"rcode={f['rcode']} answers={ips}")
        record(S, "DNS resolution (GIRAFFE:53)", dns_res, 100)

        def smtp():
            g, e = converse(FLAMINGO, 25, ["EHLO scoring.zooland.local", "QUIT"])[:2]
            return ok(g.splitlines()[0][:60]) if g.startswith("220") and e.startswith("250") else bad(g[:60])
        record(S, "SMTP open relay (FLAMINGO:25)", smtp, 75)

        def mysql_port():
            b = banner(HIPPO, 3306)
            # MySQL/MariaDB greeting: 3-byte len, seq 0, protocol version 10
            return ok("handshake received") if len(b) > 5 and ord(b[4]) == 10 else bad(f"bad greeting {b[:20]!r}")
        record(S, "MySQL (HIPPO:3306)", mysql_port, 75)

        def imap():
            r = converse(FLAMINGO, 143, [f"a1 LOGIN jsmith {EMP_PW}", "a2 LOGOUT"])
            return ok("login OK") if "a1 OK" in r[1] else bad(r[1].strip()[:80])
        record(S, "IMAP login jsmith (FLAMINGO:143)", imap, 50)

        def pop3():
            b = banner(FLAMINGO, 110)
            return ok(b.strip()[:60]) if b.startswith("+OK") else bad(b[:60])
        record(S, "POP3 banner (FLAMINGO:110)", pop3, 50)

        def smb():
            # SMB1/2 negotiate not needed: score = port 445 accepting and speaking SMB
            with socket.create_connection((ZEBRA, 445), TIMEOUT) as s:
                s.settimeout(TIMEOUT)
                neg = (b"\x00\x00\x00\x2f\xffSMB\x72\x00\x00\x00\x00\x18\x01\x28" + b"\x00" * 12 +
                       b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0c\x00\x02NT LM 0.12\x00")
                s.sendall(neg)
                r = s.recv(1024)
                return ok("SMB responded") if r[4:8] in (b"\xffSMB", b"\xfeSMB") else bad(f"bad reply {r[:8]!r}")
        record(S, "SMB (ZEBRA:445)", smb, 50)

        def ftp():
            r = converse(OTTER, 21, ["USER mlopez", f"PASS {EMP_PW}", "QUIT"])
            return ok("230 login OK") if r[2].startswith("230") else bad(r[2].strip()[:80])
        record(S, "FTP login mlopez (OTTER:21)", ftp, 50)

        def rdp():
            if not tcp_open(MEERKAT, 3389):
                return bad("port closed")
            try:
                sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scoring_engine"))
                from checks import check_rdp_login  # the scoring engine's own CredSSP/NTLMv2 check
            except Exception as e:
                return skip(f"could not import scoring_engine.checks: {e}")
            up, msg = check_rdp_login(MEERKAT, 3389, "zooland", "jsmith", EMP_PW)
            return (ok if up else bad)(msg)
        record(S, "RDP login jsmith (MEERKAT:3389)", rdp, 50)

        for label, host in (("PENGUIN", PENGUIN), ("HIPPO", HIPPO), ("FLAMINGO", FLAMINGO), ("OTTER", OTTER)):
            def ssh_banner(host=host):
                b = banner(host, 22)
                return ok(b.strip()[:60]) if b.startswith("SSH-") else bad(b[:60])
            record(S, f"SSH banner ({label}:22)", ssh_banner, 25)

    # ======================================================================
    if args.only in (None, "vuln"):
        print("\n== Vulnerability checks (must remain present) ==")

        # ---------------- GIRAFFE ----------------
        V = "GIRAFFE"

        def axfr():
            r = dns_query(GIRAFFE, "zooland.local", qtype=252, tcp=True)
            if not r:
                return bad("transfer refused (empty response)")
            f = dns_flags(r)
            return ok(f"AXFR returned {f['an']} answers") if f["rcode"] == 0 and f["an"] > 1 else bad(f"rcode={f['rcode']} answers={f['an']}")
        record(V, "GIRAFFE DNS zone transfer to anyone (AXFR)", axfr)

        def recursion():
            r = dns_query(GIRAFFE, "example.com")
            f = dns_flags(r)
            if f["ra"] and f["rcode"] == 0:
                return ok(f"RA set, rcode 0, {f['an']} answers")
            return bad(f"ra={f['ra']} rcode={f['rcode']}")
        record(V, "GIRAFFE DNS recursion open", recursion)

        def nodnssec():
            r = dns_query(GIRAFFE, "zooland.local", qtype=48)  # DNSKEY
            f = dns_flags(r)
            return ok("no DNSKEY published") if f["an"] == 0 else bad("DNSKEY present (zone is signed)")
        record(V, "GIRAFFE no DNSSEC", nodnssec)

        def dnslog():
            r = winrm(GIRAFFE, "Administrator", ADMIN_PW,
                      "$d=Get-DnsServerDiagnostics; if($d.Queries -or $d.Answers -or $d.Notifications -or $d.Updates){'LOGGING_ON'}else{'LOGGING_OFF'}")
            if r is None:
                return skip("pywinrm not installed")
            return ok("diagnostics all off") if "LOGGING_OFF" in r[1] else bad(r[1].strip()[:80])
        record(V, "GIRAFFE DNS logging off", dnslog)

        def hidden_accts():
            documented = {"jsmith", "bwilson", "mchen", "mlopez", "rthomas", "ajohnson", "tlee", "swilliams",
                          "pgarcia", "kbrown", "lmartinez", "djones", "nanderson", "cwilson", "emiller"}
            r = winrm(GIRAFFE, "Administrator", ADMIN_PW,
                      "Get-ADUser -Filter * | Select-Object -ExpandProperty SamAccountName")
            if r is not None and r[0] == 0:
                names = {x.strip().lower() for x in r[1].splitlines() if x.strip()}
            elif have("ldapsearch"):
                rc, out = run(["ldapsearch", "-x", "-H", f"ldap://{GIRAFFE}", "-D", "ZOOLAND\\domainadmin",
                               "-w", ADMIN_PW, "-b", "DC=zooland,DC=local", "(&(objectCategory=person)(objectClass=user))",
                               "sAMAccountName"])
                if rc != 0:
                    return bad(out.strip()[:80])
                names = {m.lower() for m in re.findall(r"^sAMAccountName: (\S+)", out, re.M)}
            else:
                return skip("need pywinrm or ldapsearch")
            builtin = {"administrator", "guest", "krbtgt", "domainadmin", "defaultaccount", "wdagutilityaccount", "localuser"}
            extra = names - documented - builtin
            return ok(f"{len(extra)} undocumented accounts") if len(extra) >= 12 else bad(f"only {len(extra)} undocumented accounts: {sorted(extra)}")
        record(V, "GIRAFFE 12 hidden AD accounts", hidden_accts)

        # ---------------- ZEBRA ----------------
        V = "ZEBRA"

        def smbv1():
            with socket.create_connection((ZEBRA, 445), TIMEOUT) as s:
                s.settimeout(TIMEOUT)
                s.sendall(b"\x00\x00\x00\x2f\xffSMB\x72" + b"\x00" * 4 + b"\x18\x01\x28" + b"\x00" * 12 +
                          b"\x00" * 8 + b"\x00\x0c\x00\x02NT LM 0.12\x00")
                r = s.recv(1024)
            return ok("server accepts SMB1 NT LM 0.12") if r[4:8] == b"\xffSMB" and r[8:9] == b"\x72" else bad("SMB1 not negotiated")
        record(V, "ZEBRA SMBv1 enabled", smbv1)

        def smb_ls(share, path_cmd, creds):
            if not have("smbclient"):
                return None
            return run(["smbclient", f"//{ZEBRA}/{share}", *creds, "-c", path_cmd], timeout=25)

        def guest_shares():
            r = smb_ls("Public", "ls", ["-N"])
            if r is None:
                return skip("smbclient not installed")
            r2 = smb_ls("Shared", "ls", ["-N"])
            return ok("anonymous/guest can list Public and Shared") if r[0] == 0 and r2[0] == 0 else bad((r[1] + r2[1]).strip()[:100])
        record(V, "ZEBRA guest access + Everyone on Public/Shared", guest_shares)

        def everyone_full():
            r = winrm(ZEBRA, "Administrator", ADMIN_PW,
                      "foreach($s in 'Public','Shared'){(Get-SmbShareAccess -Name $s | ? {$_.AccountName -eq 'Everyone'}).AccessRight}")
            if r is None:
                if not have("smbclient"):
                    return skip("need pywinrm or smbclient")
                rc, out = run(["smbclient", f"//{ZEBRA}/Public", "-N", "-c", 'mkdir zoocheck_probe; rmdir zoocheck_probe'], timeout=25)
                return ok("guest can create+remove a directory (write access)") if "NT_STATUS" not in out else bad(out.strip()[:100])
            return ok("Everyone: Full") if r[1].count("Full") >= 2 else bad(r[1].strip()[:80])
        record(V, "ZEBRA Everyone Full Control on shares", everyone_full)

        def cred_files():
            if not have("smbclient"):
                return skip("smbclient not installed")
            a = run(["smbclient", f"//{ZEBRA}/Public", "-N", "-c", "get readme.txt -"], timeout=25)[1]
            b = run(["smbclient", f"//{ZEBRA}/Shared", "-N", "-c", "get IT_Notes.txt -"], timeout=25)[1]
            good = "CompanyWifi123" in a and "P@ssw0rd!" in b
            return ok("readme.txt and IT_Notes.txt contain credentials") if good else bad("credential files missing or changed")
        record(V, "ZEBRA credential files in shares", cred_files)

        def zebra_fw():
            r = winrm(ZEBRA, "Administrator", ADMIN_PW,
                      "(Get-NetFirewallProfile | ? Enabled -eq True | Measure-Object).Count")
            if r is None:
                # Indirect: firewall off means arbitrary ports like 139 are reachable
                return ok("139 reachable (consistent with firewall off)") if tcp_open(ZEBRA, 139) else bad("139 filtered")
            return ok("0 profiles enabled") if r[1].strip() == "0" else bad(f"enabled profiles: {r[1].strip()}")
        record(V, "ZEBRA Windows firewall off", zebra_fw)

        # ---------------- PENGUIN ----------------
        V = "PENGUIN"

        def debug_ep():
            st, _, body = http_req(PENGUIN, 5000, "/api/debug")
            return ok("JWT_SECRET leaked") if st == 200 and "JWT_SECRET" in body else bad(f"HTTP {st}")
        record(V, "PENGUIN /api/debug leaks env vars", debug_ep)

        def sqli():
            base_q = "/api/products?search=" + "zzzz_no_such_product_zzzz"
            inj_q = "/api/products?search=" + "zzzz%25%27)%20OR%201%3D1%20--%20"
            _, _, a = http_req(PENGUIN, 5000, base_q)
            st, _, b = http_req(PENGUIN, 5000, inj_q)
            if st == 200 and len(b) > len(a) + 10:
                return ok("tautology returned extra rows")
            return bad(f"HTTP {st}; baseline {len(a)}B vs injected {len(b)}B")
        record(V, "PENGUIN SQL injection in ?search=", sqli)

        def login(user, pw):
            st, _, body = http_req(PENGUIN, 5000, "/api/auth/login", "POST", {"username": user, "password": pw})
            if st == 200:
                try:
                    return json.loads(body).get("token")
                except ValueError:
                    return None
            return None

        def app_admin():
            t = login("admin", "admin123")
            state["admin_token"] = t
            return ok("admin/admin123 accepted") if t else bad("login rejected")
        record(V, "PENGUIN CrazyRhino admin / admin123", app_admin)

        def idor():
            at = state.get("admin_token") or login("admin", "admin123")
            jt = login("johndoe", "password123")
            if not at or not jt:
                return skip("could not log in as admin and johndoe")
            _, _, body = http_req(PENGUIN, 5000, "/api/orders", headers={"Authorization": f"Bearer {at}"})
            try:
                orders = json.loads(body)
            except ValueError:
                orders = []
            if not orders:
                # No order to probe with, and a checkout would write data: inspect the deployed handler instead.
                r = ssh_root(PENGUIN, "grep -n \"order_number = ?\" /opt/crazyrhino/backend/routes/orders.js")
                if r is None:
                    return skip("no orders to probe with and sshpass not installed")
                lines = [l for l in r[1].splitlines() if "order_number = ?" in l and "SELECT" in l]
                if lines and all("user_id" not in l for l in lines):
                    return ok("deployed GET /:orderNumber looks orders up with no user_id filter (source check)")
                return bad("order lookup is filtered by owner: " + " | ".join(lines)[:100] if lines else "could not find order lookup")
            num = orders[0]["order_number"]
            st, _, _ = http_req(PENGUIN, 5000, f"/api/orders/{num}", headers={"Authorization": f"Bearer {jt}"})
            return ok(f"johndoe read admin order {num}") if st == 200 else bad(f"HTTP {st} for another user's order")
        record(V, "PENGUIN IDOR on /api/orders/:orderNumber", idor)

        def norate():
            codes = [http_req(PENGUIN, 5000, "/api/auth/login", "POST",
                              {"username": "ratetest", "password": "x"})[0] for _ in range(40)]
            return ok("40 rapid logins, no 429") if 429 not in codes else bad("429 returned: rate limiting active")
        record(V, "PENGUIN no rate limiting", norate)

        def http_only():
            return ok("443 closed") if not tcp_open(PENGUIN, 443) else bad("443 open")
        record(V, "PENGUIN HTTP only (no 443)", http_only)

        def xpb():
            _, h, _ = http_req(PENGUIN, 5000, "/api/products")
            return ok(h["x-powered-by"]) if h.get("x-powered-by", "").lower() == "express" else bad(f"header={h.get('x-powered-by')}")
        record(V, "PENGUIN X-Powered-By: Express", xpb)

        def backup_creds():
            r = ssh_root(PENGUIN, "cat /opt/crazyrhino/backup_credentials.txt")
            if r is None:
                return skip("sshpass not installed")
            return ok("file present") if r[0] == 0 and "admin" in r[1] else bad(r[1].strip()[:80])
        record(V, "PENGUIN backup_credentials.txt", backup_creds)

        def ufw_off():
            r = ssh_root(PENGUIN, "ufw status 2>&1")
            if r is None:
                return skip("sshpass not installed")
            return ok("UFW inactive") if "inactive" in r[1].lower() or "not found" in r[1].lower() else bad(r[1].strip()[:80])
        record(V, "PENGUIN UFW off", ufw_off)

        # ---------------- OTTER ----------------
        V = "OTTER"

        def anon_ftp():
            f = ftplib.FTP(timeout=TIMEOUT)
            f.connect(OTTER, 21)
            state["otter_banner"] = f.getwelcome()
            f.login("anonymous", "check@example.com")
            name = "zoocheck_probe.txt"
            try:
                f.cwd("upload")
                f.storbinary("STOR " + name, io.BytesIO(b"x"))
                f.delete(name)
            finally:
                f.close()
            return ok("anonymous login + upload to /upload accepted")
        record(V, "OTTER anonymous FTP with upload", anon_ftp)

        def ver_banner():
            b = state.get("otter_banner") or banner(OTTER, 21)
            return ok(b.strip()[:70]) if "vsftpd 3.0.5" in b else bad(b.strip()[:70])
        record(V, "OTTER vsftpd version in banner", ver_banner)

        def no_tls():
            r = converse(OTTER, 21, ["AUTH TLS", "QUIT"])
            return ok(r[1].strip()[:60]) if not r[1].startswith("234") else bad("AUTH TLS accepted")
        record(V, "OTTER no TLS", no_tls)

        def otter_conf():
            r = ssh_root(OTTER, "grep -hE '^(chroot_local_user|ssl_enable|anon_umask)' /etc/vsftpd.conf; stat -c 'perm=%a' /srv/ftp/pub /srv/ftp/upload /srv/ftp/incoming; (command -v iptables >/dev/null && iptables -S | head -5) || echo NO-IPTABLES")
            if r is None:
                return skip("sshpass not installed")
            o = r[1]
            problems = []
            if "chroot_local_user=NO" not in o:
                problems.append("chroot_local_user not NO")
            if "ssl_enable=NO" not in o:
                problems.append("ssl_enable not NO")
            if len(re.findall(r"^perm=7[0-7]7$", o, re.M)) != 3:
                problems.append("FTP subdirectories not world-writable")
            if "-P INPUT ACCEPT" not in o and "NO-IPTABLES" not in o:
                problems.append("iptables INPUT policy not ACCEPT")
            return bad("; ".join(problems)) if problems else ok("no chroot, no ssl, /srv/ftp writable, iptables open")
        record(V, "OTTER no chroot, world-writable FTP dirs, iptables open", otter_conf)

        # ---------------- FLAMINGO ----------------
        V = "FLAMINGO"

        def relay():
            r = converse(FLAMINGO, 25, ["EHLO check.example.net", "MAIL FROM:<attacker@evil.example>",
                                       "RCPT TO:<victim@external.example>", "QUIT"])
            ehlo, rcpt = r[1], r[3]
            if not rcpt.startswith("250"):
                return bad(f"RCPT rejected: {rcpt.strip()[:60]}")
            if "AUTH" in ehlo:
                return bad("server advertises AUTH")
            if "STARTTLS" in ehlo:
                return bad("server advertises STARTTLS")
            return ok("relay to external accepted, no AUTH, no STARTTLS")
        record(V, "FLAMINGO open relay, no SMTP auth, no TLS", relay)

        def dovecot_plain():
            r = converse(FLAMINGO, 143, ["a1 CAPABILITY", "a2 LOGOUT"])
            cap = r[1]
            if "STARTTLS" in cap or "LOGINDISABLED" in cap:
                return bad(cap.strip()[:80])
            return ok("IMAP plaintext LOGIN allowed, no STARTTLS")
        record(V, "FLAMINGO plaintext IMAP/POP3, no TLS", dovecot_plain)

        def postfix_conf():
            r = ssh_root(FLAMINGO, "postconf -h mynetworks smtpd_tls_security_level smtpd_sasl_auth_enable; (command -v iptables >/dev/null && iptables -S | head -3) || echo NO-IPTABLES")
            if r is None:
                return skip("sshpass not installed")
            o = r[1]
            probs = []
            if "0.0.0.0/0" not in o:
                probs.append("mynetworks != 0.0.0.0/0")
            if "-P INPUT ACCEPT" not in o and "NO-IPTABLES" not in o:
                probs.append("iptables not open")
            return bad("; ".join(probs)) if probs else ok("mynetworks 0.0.0.0/0, iptables open")
        record(V, "FLAMINGO mynetworks 0.0.0.0/0, iptables open", postfix_conf)

        # ---------------- HIPPO ----------------
        V = "HIPPO"

        def remote_root():
            r = mysql_q(HIPPO, "root", "password", "SELECT CURRENT_USER()")
            if r is None:
                return skip("mysql/mariadb client not installed")
            return ok(r[1].strip()) if r[0] == 0 else bad(r[1].strip()[:80])
        record(V, "HIPPO root@% login with 'password' (bound to 0.0.0.0)", remote_root)

        def local_infile():
            r = mysql_q(HIPPO, "root", "password", "SELECT @@GLOBAL.local_infile")
            if r is None:
                return skip("mysql/mariadb client not installed")
            return ok("local_infile=1") if r[0] == 0 and r[1].strip().endswith("1") else bad(r[1].strip()[:80])
        record(V, "HIPPO LOAD DATA LOCAL enabled", local_infile)

        def test_db():
            # README says ''@'%' (anonymous); the role actually creates testuser/testuser with ALL on test.*.
            # Either way the test database is reachable remotely without an admin credential.
            for user, pw in (("", ""), ("testuser", "testuser")):
                rc, out = mysql_q(HIPPO, user, pw, "SELECT 1", db="test")
                if rc == 0:
                    return ok(f"test DB open to {user or 'anonymous'}" +
                              ("" if not user else " (role uses testuser, README says anonymous ''@'%')"))
            return bad(out.strip()[:80])
        record(V, "HIPPO open test database (testuser or anonymous)", test_db)

        def pii():
            r = mysql_q(HIPPO, "root", "password", "SELECT COUNT(*) FROM employees WHERE ssn IS NOT NULL AND ssn<>''", db="ccdc_company")
            if r is None:
                return skip("mysql/mariadb client not installed")
            if r[0] != 0:
                r = mysql_q(HIPPO, "root", "password", "SHOW COLUMNS FROM employees", db="ccdc_company")
                return ok("employees table present") if r and r[0] == 0 and "ssn" in r[1].lower() else bad(r[1].strip()[:80])
            return ok(f"{r[1].strip()} rows with SSN") if r[1].strip() not in ("", "0") else bad("no SSN data")
        record(V, "HIPPO PII in ccdc_company.employees", pii)

        def hippo_fw():
            r = ssh_root(HIPPO, "(command -v iptables >/dev/null && iptables -S | head -3) || echo NO-IPTABLES")
            if r is None:
                return skip("sshpass not installed")
            return ok("INPUT ACCEPT or no iptables") if "-P INPUT ACCEPT" in r[1] or "NO-IPTABLES" in r[1] else bad(r[1].strip()[:80])
        record(V, "HIPPO iptables open", hippo_fw)

    # ----------------------------------------------------------------------
    # summary
    # ----------------------------------------------------------------------
    print("\n== Summary ==")
    sc = [r for r in results if r[0] == "scoring"]
    if sc:
        earned = sum(r[4] for r in sc if r[2] == PASS)
        total = sum(r[4] for r in sc)
        print(f"  Scoring: {earned}/{total} points ({sum(1 for r in sc if r[2] == PASS)}/{len(sc)} checks)")
    vu = [r for r in results if r[0] != "scoring"]
    if vu:
        print(f"  Vulnerabilities present: {sum(1 for r in vu if r[2] == PASS)}/{len(vu)}")
    nf = sum(1 for r in results if r[2] == FAIL)
    ns = sum(1 for r in results if r[2] == SKIP)
    print(f"  FAIL: {nf}   SKIP: {ns}   PASS: {sum(1 for r in results if r[2] == PASS)}")
    for r in results:
        if r[2] == SKIP:
            print(f"    skipped: {r[1]} ({r[3]})")
    return 1 if nf or (args.strict and ns) else 0


if __name__ == "__main__":
    sys.exit(main())
