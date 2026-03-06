---
title: "--last flag fails without subnet argument"
category: logic-errors
component: argument-parsing
tags: [argparse, cli, caching]
date: 2026-03-06
severity: minor
---

# `--last` flag fails without subnet argument

## Symptom

Running `pingsweep --last` or `pingsweep -last` (single dash) fails immediately:

```
pingsweep.py: error: the following arguments are required: subnet
```

The `--last` flag was designed to show cached results without scanning, but it could never execute because argparse rejected the command first.

## Root Cause

The `subnet` positional argument was defined as mandatory:

```python
parser.add_argument('subnet', help='Subnet to scan (e.g., 192.168.1.0/24)')
```

Argparse validates positional arguments during `parse_args()` before any application logic runs. The `--last` handler was unreachable without a subnet.

A secondary issue: `-last` (single dash) is interpreted by argparse as `-l -a -s -t`, not as `--last`. There was no `-l` short flag defined.

## Solution

### 1. Make `subnet` optional at the argparse level

```python
parser.add_argument('subnet', nargs='?', default=None,
                   help='Subnet to scan (e.g., 192.168.1.0/24)')
```

### 2. Add `-l` short flag

```python
parser.add_argument('-l', '--last', action='store_true',
                   help='Show results from the last sweep(s) without scanning')
```

### 3. Handle `--last` with or without subnet

- With subnet: show cached results for that subnet only
- Without subnet: enumerate all cache files under `~/.config/pingsweep/cache/` and display all cached results

### 4. Enforce subnet requirement for other modes

After the `--last` early exit, manually validate:

```python
if not args.subnet:
    parser.error("the following arguments are required: subnet")
```

### 5. Fix usage line

Added custom usage string showing both patterns:

```python
usage='%(prog)s [options] subnet\n       %(prog)s -l [subnet]'
```

## Prevention

This is a standard argparse pattern for commands with modal flags that don't need all arguments. When adding flags that bypass normal execution flow:

1. Consider whether all positional arguments are needed for that mode
2. Use `nargs='?'` for conditionally-required positional args
3. Move validation to application code where conditional logic can apply
4. Always add short flags for frequently-used options

## Related

- `docs/plans/2026-02-27-feat-cached-scan-results-plan.md` - Original cache feature plan
- README.md - Does not yet document the `--last` / `-l` flag
