# Enhanced Network Discovery Tool 🏓

A powerful Python-based network discovery tool that combines ping sweeping with MAC address lookup and intelligent device classification. Discover devices on your network and automatically identify their types, vendors, and hostnames.

## Features ✨

- **Fast Ping Sweeping**: Multi-threaded subnet scanning with configurable timeout and worker threads
- **Senetas Encryptor Discovery**: Fast ARP-based scan to find Senetas encryptors by MAC prefix on large subnets
- **MAC Address Lookup**: Automatic MAC address resolution via ARP table
- **Vendor Identification**: IEEE OUI database lookup for device manufacturer identification
- **Device Classification**: Smart device type detection based on vendor and hostname patterns
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Flexible Output**: Simple or verbose output modes
- **Export Capability**: JSON export for further analysis
- **Auto-Updating Database**: Downloads and caches IEEE OUI database automatically

## Device Types Detected 🔍

The tool can automatically classify devices into categories:

- 🔐 **Encryptors** (Senetas network encryption appliances)
- 🌐 **Network Equipment** (routers, switches, access points)
- 📱 **Mobile Devices** (phones, tablets)
- 💻 **Computers** (desktops, laptops)
- 🏠 **IoT Devices** (smart home devices)
- 🖨️ **Printers**
- 🎮 **Gaming Consoles**
- 📹 **Cameras**
- ❓ **Unknown Devices**

## Installation 📦

### Prerequisites

- Python 3.6 or higher
- `requests` library for OUI database downloads
- `tqdm` library for progress bars

### Install Dependencies

```bash
pip install requests tqdm
```

For fast encryptor discovery mode (optional):

```bash
pip install scapy
```

### Download the Script

```bash
git clone <repository-url>
cd network-discovery-tool
```

Or download `pingsweep.py` directly.

## Usage 🚀

### Basic Usage

```bash
# Simple scan with minimal output
python pingsweep.py 192.168.1.0/24

# Verbose scan with detailed device information
python pingsweep.py -v 192.168.1.0/24
```

### Senetas Encryptor Discovery

```bash
# Fast ARP scan to find Senetas encryptors (requires root and scapy)
sudo python pingsweep.py --find-encryptors 192.168.1.0/24

# Scan a large /16 subnet for encryptors
sudo python pingsweep.py --find-encryptors 10.0.0.0/16

# Export discovered encryptors to JSON
sudo python pingsweep.py --find-encryptors --export 10.0.0.0/16
```

### Advanced Options

```bash
# Custom thread count and timeout
python pingsweep.py --workers 20 --timeout 500 192.168.1.0/24

# Export results to JSON
python pingsweep.py --export -v 10.0.0.0/24

# Custom ping count
python pingsweep.py --count 3 192.168.1.0/24
```

### Command Line Arguments

| Argument    | Short | Description                             | Default  |
| ----------- | ----- | --------------------------------------- | -------- |
| `subnet`    | -     | Target subnet (e.g., 192.168.1.0/24)    | Required |
| `--verbose` | `-v`  | Enable detailed output with device info | False    |
| `--workers` | `-w`  | Number of worker threads                | 50       |
| `--timeout` | `-t`  | Ping timeout in milliseconds            | 1000     |
| `--count`   | `-c`  | Number of ping packets per host         | 1        |
| `--export`  | -     | Export results to JSON file             | False    |
| `--find-encryptors` | - | Fast ARP scan for Senetas encryptors (requires root + scapy) | False |

## Output Examples 📊

### Simple Mode Output

```
Scanning 254 hosts in 192.168.1.0/24
IP Address      Time     Vendor
--------------------------------------------------
192.168.1.1     2.3ms    Cisco Systems, Inc
192.168.1.100   15.2ms   Apple, Inc
192.168.1.105   8.7ms    Samsung Electronics Co.,Ltd

Scan complete: 3/254 hosts alive (12.4s)
```

### Verbose Mode Output

```
🏓 ENHANCED NETWORK DISCOVERY TOOL
==================================================
Features: Ping Sweep + MAC Lookup + Device Classification

🚀 Starting enhanced scan...
🔍 Scanning 254 hosts in 192.168.1.0/24
⚙️  Using 50 threads, 1000ms timeout
📚 MAC vendor database loaded with 28557 entries

✓ 192.168.1.1     (2.3ms) - 🌐 Network Equipment - Cisco Systems, Inc
✓ 192.168.1.100   (15.2ms) - 📱 Mobile Device - Apple, Inc
✓ 192.168.1.105   (8.7ms) - 📱 Mobile Device - Samsung Electronics Co.,Ltd

================================================================================
📊 ENHANCED SCAN COMPLETE
================================================================================
⏱️  Scan time: 12.45 seconds
📈 Hosts scanned: 254
✅ Alive: 3
❌ Down: 251

🌐 DISCOVERED DEVICES (3):
--------------------------------------------------------------------------------
📍 192.168.1.1     (2.3ms)
   🏷️  Device Type: 🌐 Network Equipment
   🏭 Vendor: Cisco Systems, Inc
   🔗 MAC Address: 00:0c:29:1a:2b:3c
   🏠 Hostname: router.local

📍 192.168.1.100   (15.2ms)
   🏷️  Device Type: 📱 Mobile Device
   🏭 Vendor: Apple, Inc
   🔗 MAC Address: 28:f0:76:xx:xx:xx

📊 DEVICE TYPE SUMMARY:
------------------------------
   🌐 Network Equipment: 1
   📱 Mobile Device: 2
```

## Technical Details 🔧

### MAC Address Resolution

The tool uses the system's ARP table to resolve MAC addresses for discovered devices. It supports various MAC address formats and normalizes them to a standard format.

### OUI Database

- Automatically downloads IEEE OUI database on first run
- Caches database locally at `~/.config/pingsweep/oui_database.json` for faster subsequent runs
- Falls back to minimal built-in database if download fails
- Updates can be forced by deleting `~/.config/pingsweep/oui_database.json`

### Device Classification Logic

Device types are determined by:

1. **Vendor-based classification**: Known manufacturer patterns
2. **Hostname analysis**: Device naming conventions
3. **Combined heuristics**: Multiple indicators for accuracy

### Platform Support

- **Windows**: Uses `ping -n` and `arp -a` commands
- **Linux/macOS**: Uses `ping -c` and `arp -n` commands
- **Cross-platform**: Automatic detection and appropriate command usage

## Performance Considerations ⚡

### Thread Configuration

- Default: 50 threads for balanced performance
- High-performance networks: Increase to 100+ threads
- Limited resources: Reduce to 10-20 threads
- Very large subnets: Consider breaking into smaller chunks

### Timeout Settings

- Default: 1000ms (1 second)
- Fast networks: Reduce to 200-500ms
- Slow/congested networks: Increase to 2000-5000ms
- Balance between speed and accuracy

### Memory Usage

- Minimal memory footprint
- OUI database: ~2-3MB in memory
- Scales linearly with discovered devices

## Troubleshooting 🔧

### Common Issues

**Permission Errors**

```bash
# Linux/macOS may require elevated privileges for ARP access
sudo python pingsweep.py 192.168.1.0/24
```

**OUI Database Download Fails**

- Check internet connectivity
- Verify firewall settings
- Script will use minimal built-in database as fallback

**MAC Addresses Show as "N/A"**

- ARP table may not contain entries for all devices
- Try scanning with higher ping count: `--count 3`
- Some devices may not respond to ARP requests

**Slow Performance**

- Reduce worker threads: `--workers 20`
- Increase timeout: `--timeout 2000`
- Scan smaller subnets

### Debug Mode

Enable verbose mode for detailed troubleshooting:

```bash
python pingsweep.py -v 192.168.1.0/24
```

## JSON Export Format 📄

When using `--export`, results are saved in JSON format:

```json
{
  "scan_info": {
    "subnet": "192.168.1.0/24",
    "scan_date": "2025-01-15 14:30:22",
    "total_discovered": 3,
    "verbose_mode": true
  },
  "devices": [
    {
      "ip": "192.168.1.1",
      "response_time": 2.3,
      "mac_address": "00:0c:29:1a:2b:3c",
      "vendor": "Cisco Systems, Inc",
      "device_type": "🌐 Network Equipment",
      "hostname": "router.local"
    }
  ]
}
```

## Security Considerations 🔒

### Network Scanning Ethics

- Only scan networks you own or have explicit permission to scan
- Respect network policies and terms of service
- Be aware that network scanning may trigger security alerts
- Use responsibly and legally

### Data Privacy

- Tool only collects network-visible information (IP, MAC, hostname)
- No personal data or device content is accessed
- MAC addresses can be considered personally identifiable information
- Export files may contain sensitive network topology information

## Contributing 🤝

Contributions are welcome! Areas for enhancement:

- Additional device classification patterns
- IPv6 support
- Additional vendor databases
- Performance optimizations
- GUI interface
- Network mapping features

## License 📝

This project is licensed under the MIT License. See LICENSE file for details.

## Changelog 📋

### v1.0.0

- Initial release with basic ping sweep functionality
- MAC address lookup via ARP
- IEEE OUI database integration
- Device classification system
- Cross-platform support
- JSON export capability

---

**Note**: This tool is designed for network administrators and security professionals. Always ensure you have proper authorization before scanning networks.
