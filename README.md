# 🏓 Network Ping Sweep Tool

A fast, multi-threaded network discovery tool that identifies active hosts within a specified IP subnet using ICMP ping requests.

## ✨ Features

- **High-Performance Scanning**: Multi-threaded execution with configurable worker threads
- **Cross-Platform**: Works on Windows, Linux, and macOS with optimized ping commands
- **Real-Time Feedback**: Live progress updates with response times
- **Comprehensive Statistics**: Detailed scan results including timing and success rates  
- **Export Functionality**: Save results to timestamped text files
- **User-Friendly Interface**: Rich visual feedback with emojis and clear formatting
- **Robust Error Handling**: Graceful handling of timeouts, interruptions, and invalid inputs
- **Configurable Parameters**: Adjustable thread count and timeout values

## 🚀 Quick Start

### Prerequisites

- Python 3.6 or higher
- Standard library modules (no additional dependencies required)
- Network connectivity to target subnet

### Installation

1. Clone or download the script:
```bash
git clone <repository-url>
# or download pingsweep2.py directly
```

2. Make it executable (Unix/Linux/macOS):
```bash
chmod +x pingsweep2.py
```

### Basic Usage

Run the script and follow the interactive prompts:

```bash
python pingsweep2.py
```

**Example Session:**
```
🏓 NETWORK PING SWEEP TOOL
========================================
🔧 PING SWEEP CONFIGURATION
==============================
Enter subnet (e.g., 192.168.1.0/24): 192.168.1.0/24

⚙️ Optional settings (press Enter for defaults):
Max threads (default 50): 
Timeout in ms (default 1000): 

🚀 Starting scan...
🔍 Scanning 254 hosts in 192.168.1.0/24
⚙️  Using 50 threads, 1000ms timeout

✓ 192.168.1.1 (15.2ms)
✓ 192.168.1.15 (23.1ms)
✓ 192.168.1.100 (12.8ms)
```

## 🛠️ Configuration Options

### Thread Count
- **Default**: 50 threads
- **Range**: 1-200 threads
- **Recommendation**: 30-70 for most networks

### Timeout
- **Default**: 1000ms (1 second)
- **Range**: 100-10000ms
- **Recommendation**: 1000-3000ms for reliable results

### Supported Subnet Formats
- CIDR notation: `192.168.1.0/24`
- Single host: `192.168.1.100/32`
- Large subnets: `10.0.0.0/16`

## 📊 Output Explanation

### Real-Time Updates
- `✓ 192.168.1.1 (15.2ms)` - Host is alive with response time
- Silent for non-responding hosts (reduces noise)

### Final Summary
```
==================================================
📊 SCAN COMPLETE
==================================================
⏱️  Scan time: 12.34 seconds
📈 Hosts scanned: 254
✅ Alive: 8
❌ Down: 240
⏰ Timeouts: 4
🚫 Errors: 2

🌐 ALIVE HOSTS (8):
------------------------------
  192.168.1.1     (15.2ms)
  192.168.1.15    (23.1ms)
  192.168.1.100   (12.8ms)
```

## 🎯 Use Cases

### Network Discovery
- Identify active devices on unknown networks
- Map network topology
- Find available IP addresses

### Network Troubleshooting
- Verify connectivity to multiple hosts
- Identify network segments with issues
- Test network performance across subnets

### Security & Inventory
- Network reconnaissance (authorized testing only)
- Asset discovery and inventory
- Monitor network changes over time

### System Administration
- Verify DHCP lease usage
- Check server availability across subnets
- Network maintenance and monitoring

## ⚡ Performance Tips

### Optimal Thread Count
- **Small subnets** (/28, /27): 10-20 threads
- **Medium subnets** (/24): 30-50 threads  
- **Large subnets** (/16, /8): 50-100 threads

### Timeout Considerations
- **Local networks**: 500-1000ms
- **Remote networks**: 2000-5000ms
- **Slow networks**: 5000ms+

### System Resources
- Monitor CPU and network usage
- Reduce threads if system becomes unresponsive
- Consider network impact on production systems

## 🔒 Security Considerations

### Authorized Use Only
- Only scan networks you own or have explicit permission to test
- Be aware that ping sweeps may trigger security alerts
- Some networks block ICMP traffic (firewalls, security policies)

### Ethical Guidelines
- Respect network policies and terms of service
- Use appropriate timing to avoid network disruption
- Document and justify scanning activities

### Detection Avoidance (For Authorized Testing)
- Use slower scan rates with higher timeouts
- Randomize scan order (not implemented in current version)
- Consider time-based delays between requests

## 🐛 Troubleshooting

### Common Issues

**No hosts found in known active subnet:**
- Check if ICMP/ping is blocked by firewalls
- Verify subnet notation is correct
- Try increasing timeout value
- Test with a single known host first

**Script hangs or becomes unresponsive:**
- Reduce thread count (try 10-20)
- Increase timeout value
- Check system resources (CPU, memory)

**Permission errors (Unix/Linux):**
- Some systems require elevated privileges for ping
- Try running with `sudo` if necessary

**High error count:**
- Check network connectivity
- Verify DNS resolution isn't interfering
- Reduce thread count to prevent overwhelming the network

### Platform-Specific Notes

**Windows:**
- Uses `ping -n 1 -w <timeout>` command
- May require firewall exceptions

**Linux/macOS:**
- Uses `ping -c 1 -W <timeout> -n` command
- The `-n` flag disables DNS resolution for speed

## 📁 File Export

Results can be exported to timestamped text files:
- Filename format: `ping_sweep_<subnet>_<timestamp>.txt`
- Contains scan parameters, timestamp, and sorted results
- Useful for documentation and comparison over time

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Additional ping methods (TCP, UDP)
- Scan result comparison features
- GUI interface
- Advanced reporting options
- IPv6 support enhancement

## 📄 License

This tool is provided for educational and authorized network administration purposes. Users are responsible for compliance with applicable laws and network policies.

## 🆘 Support

For issues, feature requests, or questions:
1. Check the troubleshooting section above
2. Review your network configuration and permissions
3. Test with a smaller subnet first
4. Consider network security policies that might block ICMP

---

**⚠️ Disclaimer**: This tool should only be used on networks you own or have explicit permission to scan. Unauthorized network scanning may violate laws, regulations, or terms of service.
