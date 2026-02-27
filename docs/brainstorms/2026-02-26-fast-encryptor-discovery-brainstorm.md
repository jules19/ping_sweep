# Fast Encryptor Discovery on Large Subnets

**Date**: 2026-02-26
**Status**: Ready for planning

## What We're Building

A new `--find-encryptors` mode in pingsweep.py that rapidly identifies Senetas encryptors (OUI prefix `00:d0:1f`) across large subnets (up to /16 = 65,534 hosts). The mode is purpose-built for speed — it only cares about finding Senetas devices, not a full network inventory.

### Target Performance

- /24 (254 hosts): under 5 seconds
- /16 (65,534 hosts): under 2 minutes
- Current tool on a /16: 20+ minutes

## Why This Approach (Hybrid Two-Phase Scan)

### The Problem with the Current Approach

The existing tool pings every host via subprocess (`ping -c 1`), then runs `arp` and `nslookup` subprocesses for each alive host. On a /16:
- 65,534 subprocess calls for ping alone
- Additional subprocess calls for ARP and nslookup per alive host
- Even with 50 threads, subprocess overhead dominates
- Timeout waiting for dead hosts is the biggest time sink

### Chosen Approach: Hybrid Two-Phase Scan + Rate Limiting

**Phase 1 — ARP Sweep (local L2 segments)**:
- Use Scapy to send raw ARP requests for all IPs in range
- ARP responses contain MAC addresses directly
- Filter for `00:d0:1f` prefix → instant identification
- Completes in seconds even for a /16
- Negligible network impact (~1.8 MB of broadcast traffic)

**Phase 2 — Async Network Probing (routed segments)**:
- Use asyncio with raw sockets for massively parallel ICMP echo or UDP-161 probes
- No subprocess overhead — direct socket operations
- For responding hosts on local segments: check ARP cache for MAC
- For routed hosts: attempt device fingerprinting (SNMP, TLS cert, or other distinguishing characteristic)
- Rate-limited to avoid triggering IDS/IPS alerts

**Why hybrid**: Encryptors can be on the same L2 segment (ARP works) or across routers (ARP won't see real MACs). The two-phase approach covers both cases optimally.

## Key Decisions

1. **Integration**: New `--find-encryptors` flag in existing pingsweep.py (not a separate script)
2. **MAC prefix**: Senetas OUI is `00:d0:1f` — the primary identification mechanism
3. **SNMP**: Encryptors run SNMPv3 on UDP/161 — can be used for fingerprinting routed devices, but requires auth credentials (username, auth/priv protocols and keys)
4. **Rate limiting**: Include `--rate` flag (packets/sec) for operator control on sensitive production networks
5. **Root required**: ARP scanning and raw ICMP sockets require root/admin privileges (acceptable for this tool's use case)
6. **Dependency**: Scapy library will be needed for ARP scanning

## Network Impact Assessment

- ARP scan of /16: ~1.8 MB broadcast traffic (negligible)
- ICMP probing of /16: ~4 MB (negligible)
- Both are less impactful than the current subprocess-based approach
- Rate limiting provides operator control for sensitive environments
- Standard enterprise IDS may flag rapid scans — rate limiting mitigates this

## Open Questions

1. **SNMPv3 credentials**: Should the tool accept SNMPv3 auth parameters (--snmp-user, --snmp-auth, etc.) to positively identify encryptors on routed segments? Or is "host responds on UDP/161" sufficient as a heuristic?
2. **Additional fingerprinting**: Beyond MAC prefix and SNMP, are there other unique identifiers for Senetas encryptors (e.g., specific TLS certificate patterns on a management port, unique TCP fingerprint)?
3. **Output format**: For `--find-encryptors` mode, should output be minimal (just IP + MAC) or include response time, hostname, etc.?
4. **Scapy vs raw sockets**: Scapy is convenient but heavy (~20 MB). Could use raw sockets directly for ARP if we want to minimize dependencies. Trade-off: complexity vs dependency size.

## Technical Notes

- Python's `asyncio` can handle 10,000+ concurrent connections efficiently
- Scapy's `srp()` function can send/receive ARP at line rate
- ARP only works within broadcast domains; routers don't forward ARP
- SNMPv3 adds authentication overhead but is the standard for enterprise devices
- The existing `MACVendorLookup` class already handles the `00:d0:1f` → Senetas mapping
