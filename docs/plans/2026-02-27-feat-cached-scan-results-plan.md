---
title: "feat: Cache scan results for faster repeat scans"
type: feat
date: 2026-02-27
brainstorm: docs/brainstorms/2026-02-27-cached-scan-results-brainstorm.md
---

# feat: Cache Scan Results for Faster Repeat Scans

On repeat scans of the same subnet, check previously discovered devices first for instant feedback, then continue with the full sweep.

## Approach

Two-pass scan: verify cached IPs first (fast), then sweep remaining IPs. Cache is one JSON file per subnet, stored alongside the existing OUI database.

### Cache storage

- Location: `~/.config/pingsweep/cache/`
- Two subdirs: `cache/ping/` and `cache/encryptors/`
- Filename: normalized subnet with `/` replaced by `_` (e.g., `192.168.1.0_24.json`)
- Subnet is normalized via `str(ipaddress.ip_network(subnet, strict=False))` before keying, so `192.168.1.5/24` and `192.168.1.0/24` hit the same cache
- Format: same JSON structure as `--export` (no new schema)

### Cache-check phase (runs before main sweep)

1. Load cache file for this subnet. If missing or corrupt, skip to full sweep with a warning.
2. Extract IPs from cached results.
3. **Encryptor mode:** ARP the cached IPs individually (single `srp()` call with a list of targets). Display hits immediately.
4. **Ping sweep mode:** Ping cached IPs using the existing `ping_and_analyze_host()` in a small thread pool. Display hits immediately.
5. Collect confirmed-alive IPs into a `skip_set`.

### Full sweep phase

6. Run the normal scan but skip IPs already in `skip_set`.
7. For encryptor mode: filter cached IPs out of each chunk's target range — or simply skip duplicates when processing responses.
8. For ping sweep mode: filter `network.hosts()` through `skip_set` before submitting to the executor.

### Cache write

9. After scan completes, write all results (cache-verified + newly found) to the cache file.
10. **Interrupted scans (Ctrl+C): do not write cache.** Partial results would cause missed devices on next run.

### `--no-cache` flag

11. Skips cache read (forces clean scan). Still writes results to cache at the end so subsequent runs benefit.

## Acceptance Criteria

- [ ] Repeat scan of same subnet shows cached devices within seconds before full sweep begins
- [ ] Full sweep still finds new devices not in cache
- [ ] Cache file created at `~/.config/pingsweep/cache/{ping,encryptors}/<subnet>.json`
- [ ] Works for both `--find-encryptors` and regular ping sweep modes
- [ ] Corrupt/missing cache degrades gracefully (warning + full scan)
- [ ] Interrupted scan does not write cache
- [ ] `--no-cache` flag skips cache read but still writes
- [ ] Equivalent subnet notations (e.g., `192.168.1.5/24` vs `192.168.1.0/24`) share cache

## Key edge cases

| Case | Behavior |
|------|----------|
| First scan (no cache) | Normal full sweep, write cache at end |
| Corrupt cache file | Print warning, run full sweep |
| Cached device now offline | Silently excluded from results and new cache |
| Scan interrupted (Ctrl+C) | Do not overwrite cache file |
| `--no-cache` | Skip read, still write |
| Overlapping subnets (/24 then /16) | Exact-match cache keys only — no subset/superset reuse |

## Files to modify

### `pingsweep.py`

- Add `load_cache(subnet, mode)` helper — returns list of dicts or `[]`
- Add `save_cache(subnet, mode, results)` helper — writes JSON
- Modify `find_encryptors()`: load cache → verify cached IPs → set skip logic → save cache (unless interrupted)
- Modify `EnhancedPingSweep.scan_subnet()`: load cache → verify cached IPs → filter `network.hosts()` → save cache
- Add `--no-cache` argument to argparse
- Pass `no_cache` flag through to scan functions

## References

- Brainstorm: `docs/brainstorms/2026-02-27-cached-scan-results-brainstorm.md`
- OUI cache pattern (model to follow): `pingsweep.py:30-49`
- Export JSON format (reuse for cache): `pingsweep.py:640-648` (encryptors), `pingsweep.py:677-685` (ping)
- Config dir: `~/.config/pingsweep/` (`pingsweep.py:34`)
