---
title: "feat: Fast Senetas Encryptor Discovery Mode"
type: feat
date: 2026-02-26
status: reviewed-and-simplified
---

# Fast Senetas Encryptor Discovery Mode

## Overview

Add a `--find-encryptors` flag to `pingsweep.py` that rapidly identifies Senetas encryptors (OUI prefix `00:d0:1f`) via Scapy ARP sweep. One new dependency, one new function, ~60 lines of code.

**Target performance**: /24 in <5s, /16 in <60s (vs 20+ minutes with current subprocess approach).

## Problem Statement

The current tool pings every host via subprocess, then runs `arp` and `nslookup` subprocesses per alive host. On a /16 (65,534 hosts), this takes 20+ minutes. When the user only needs to find Senetas encryptors by MAC prefix, a full network inventory is wasteful.

## Proposed Solution

ARP sweep the target subnet with Scapy. Filter responses for MAC prefix `00:d0:1f`. Print results.

ARP is L2 — it only reaches the local broadcast domain, so non-local IPs simply won't get a response. The OUI filter handles any gateway MAC responses. No routing table parsing needed.

### Implementation

Add to `pingsweep.py`:

```python
SENETAS_OUI = "00d01f"

def find_encryptors(subnet, timeout=2, verbose=False):
    """ARP sweep for Senetas encryptors (OUI 00:d0:1f)."""
    from scapy.all import srp, Ether, ARP, conf
    conf.verb = 0

    network = ipaddress.ip_network(subnet, strict=False)
    total = network.num_addresses - 2 if network.prefixlen < 31 else network.num_addresses

    print(f"Scanning for Senetas encryptors in {subnet} ({total} hosts)...")

    # For large subnets, chunk into /24s to avoid memory issues
    if network.prefixlen < 24:
        chunks = list(network.subnets(new_prefix=24))
    else:
        chunks = [network]

    encryptors = []
    for chunk in chunks:
        pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=str(chunk))
        ans, _ = srp(pkt, timeout=timeout, verbose=False)

        for sent, received in ans:
            mac = received.hwsrc.replace(":", "").lower()
            if mac[:6] == SENETAS_OUI:
                encryptors.append({
                    'ip': received.psrc,
                    'mac': received.hwsrc,
                })

    return encryptors
```

Wire into `main()`:

```python
if args.find_encryptors:
    # Root check
    if sys.platform != 'win32' and os.geteuid() != 0:
        print("Error: --find-encryptors requires root. Run with sudo.")
        sys.exit(1)

    # Dependency check
    try:
        from scapy.all import srp, Ether, ARP, conf
    except ImportError:
        print("Error: --find-encryptors requires scapy: pip install scapy")
        sys.exit(1)

    start = time.time()
    encryptors = find_encryptors(args.subnet, timeout=args.timeout // 1000, verbose=args.verbose)

    if encryptors:
        print(f"\nFound {len(encryptors)} encryptor(s):")
        for e in sorted(encryptors, key=lambda x: ipaddress.ip_address(x['ip'])):
            print(f"  {e['ip']:<15} {e['mac']}")
    else:
        print("\nNo Senetas encryptors found.")

    print(f"Scan complete in {time.time() - start:.1f}s")

    # Export if requested
    if args.export and encryptors:
        filename = f"encryptors_{args.subnet.replace('/', '_')}_{int(time.time())}.json"
        with open(filename, 'w') as f:
            json.dump({
                'scan_info': {
                    'mode': 'find-encryptors',
                    'subnet': args.subnet,
                    'scan_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'encryptors_found': len(encryptors),
                },
                'encryptors': encryptors
            }, f, indent=2)
        print(f"Results exported to {filename}")

    sys.exit(0)
```

### New CLI Argument

```python
parser.add_argument('--find-encryptors', action='store_true',
                   help='Fast ARP scan to find Senetas encryptors by MAC prefix (requires root)')
```

### Output Format

```
Scanning for Senetas encryptors in 192.168.1.0/24 (254 hosts)...

Found 2 encryptor(s):
  192.168.1.50    00:d0:1f:09:82:f4
  192.168.1.51    00:d0:1f:09:82:f5

Scan complete in 3.2s
```

## Implementation Checklist

- [ ] Add `SENETAS_OUI` constant — `pingsweep.py`
- [ ] Add `--find-encryptors` CLI argument — `pingsweep.py`
- [ ] Add root check and Scapy dependency check in `main()` — `pingsweep.py`
- [ ] Add `find_encryptors()` function with ARP sweep — `pingsweep.py`
- [ ] Add output formatting and JSON export support — `pingsweep.py`
- [ ] Fix existing macOS ARP bug: `arp -n` → `arp -a` on darwin — `pingsweep.py:241`
- [ ] Add "Encryptor" device type to `classify_device_type()` for Senetas — `pingsweep.py:139`
- [ ] Update README — `README.md`

## Acceptance Criteria

- [ ] `sudo python pingsweep.py --find-encryptors 192.168.1.0/24` finds Senetas devices by MAC
- [ ] /24 completes in <5 seconds
- [ ] /16 completes in <60 seconds (chunked into /24s)
- [ ] Running without root prints a clear error
- [ ] Running without Scapy prints install instructions
- [ ] `--export` produces JSON with encryptor list
- [ ] Existing functionality is completely unaffected (lazy import)

## Dependencies

**New**: `scapy` (lazy-imported only when `--find-encryptors` is used)

No other new dependencies.

## What Was Cut (and Why)

Per reviewer feedback (DHH, Kieran, Simplicity), the following were removed from the original plan:

| Cut | Reason |
|---|---|
| `PrivilegeManager` class | Replaced with 3-line `if` check |
| `EncryptorDiscovery` class | Replaced with single function |
| Phase 2 (async ICMP/icmplib) | Solves hypothetical routed-segment problem; not needed for v1 |
| `get_local_subnets()` routing parser | Not needed without Phase 2 |
| UDP/161 SNMP heuristic | False positive factory; any SNMP device triggers it |
| Confidence levels | Only existed to support the heuristic |
| `icmplib` dependency | Not needed without Phase 2 |
| `--rate` flag | Premature; default Scapy ARP is production-safe |
| Flag interaction table | Irrelevant when feature is self-contained |
| 4 implementation phases | Collapsed to 1 |

## Future Enhancements (if needed)

1. **Routed segment scanning**: Add async ICMP probing + SNMPv3 credential-based identification when there's a proven need
2. **`--rate` flag**: Add inter-packet delay control if anyone reports IDS/IPS issues
3. **`--interface` flag**: Add explicit NIC selection for multi-homed hosts
4. **Multiple subnet support**: Accept multiple positional subnet arguments
5. **`--quiet` mode**: Output only IPs for scripting/piping

## References

- Brainstorm: `docs/brainstorms/2026-02-26-fast-encryptor-discovery-brainstorm.md`
- Senetas OUI entry: `pingsweep.py:111` (`"00d01f": "Senetas Corporation Ltd"`)
- macOS ARP bug: `pingsweep.py:241` (uses `arp -n` which macOS doesn't support)
- Scapy docs: https://scapy.readthedocs.io/en/latest/usage.html
