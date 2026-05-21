# ZooLandRange — Red Team

## Proxmox

| Account | Username | Password |
|---------|----------|----------|
| Proxmox | `RedTeam` | `RedTeam!` |

---

## Scope

**In scope:** `10.1.x.x`

**Out of scope:** The range router and the scoring server — do not attack or disrupt these.

---

## Known Vulnerabilities

- Default and weak credentials
- Cleartext protocols (no encryption in transit)
- SMBv1
- Anonymous FTP access
- Open SMTP relay
- SQL injection
- Unauthenticated debug endpoint
- DNS zone transfer
- Open recursive DNS resolver
- Database exposed to all network interfaces
- Guest SMB access
- Credentials in plaintext files
- No host-based firewalls
