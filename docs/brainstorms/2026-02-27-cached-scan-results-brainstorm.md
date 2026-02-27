# Brainstorm: Cached Scan Results for Faster Repeat Scans

**Date:** 2026-02-27
**Status:** Decision made

## What We're Building

A cache-first scanning strategy for both `--find-encryptors` and regular ping sweep modes. On repeat scans of the same subnet, previously discovered devices are checked first and displayed immediately, giving instant feedback while the full scan continues.

## Why This Approach

The primary goal is **speed of feedback** — when scanning a subnet you've scanned before, show known devices within seconds rather than waiting for the full sweep. This is especially valuable on large subnets (/16) where a full ARP or ping sweep takes minutes.

**Not** building: change detection, historical analytics, or background refresh. Just "check the ones we found last time first."

## Key Decisions

1. **Scope: Both modes** — Cache applies to `--find-encryptors` (ARP) and regular ping sweep
2. **Goal: Speed, not change detection** — Show verified-alive cached devices fast, then continue full scan
3. **Staleness: No expiry** — Devices don't move often; any cached result is worth re-checking
4. **Approach: Check-first pass** — Verify cached IPs first (ping or ARP), display hits immediately, then run full sweep skipping already-found IPs

## Approach: Check-First Pass

- Save last scan results per subnet to `~/.config/pingsweep/cache/<subnet>.json`
- On next scan, ping/ARP those cached IPs first and display hits immediately
- Then run the full sweep, skipping IPs already confirmed alive
- Overwrite cache with new results at end of scan (cache stays fresh naturally)

### Pros
- Simple — one JSON file per subnet
- Honest — only shows verified-alive devices
- No new dependencies
- Full scan still runs, so new devices are never missed

### Cons
- Stale entries get pinged for nothing (harmless)
- Two-pass display slightly different from a clean scan

## Rejected Alternatives

- **Show cached immediately (unverified):** Misleading — could show offline devices as alive
- **SQLite history DB:** Over-engineered for the speed goal (YAGNI)

## Open Questions

- Cache file naming: sanitise subnet string (e.g., `192.168.1.0_24.json`) — straightforward
- Should `--no-cache` flag exist to force a clean scan? Probably yes, simple to add
