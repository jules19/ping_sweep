#!/usr/bin/env python3
import ipaddress
import subprocess
import concurrent.futures
import time
import sys
import threading
import re
import json
import requests
from collections import defaultdict
import os
import signal
import argparse
from tqdm import tqdm

# Configuration
DEFAULT_MAX_WORKERS = 50
DEFAULT_TIMEOUT = 1000
DEFAULT_COUNT = 1
SENETAS_OUI = "00d01f"

class MACVendorLookup:
    """Handles MAC address vendor identification using multiple methods"""
    
    def __init__(self, verbose=False):
        self.oui_database = {}
        self.verbose = verbose
        self.load_local_database()
    
    def load_local_database(self):
        """Load IEEE OUI database from local file or download if needed"""
        # Use XDG config directory
        config_dir = os.path.expanduser("~/.config/pingsweep")
        os.makedirs(config_dir, exist_ok=True)
        oui_file = os.path.join(config_dir, "oui_database.json")
        
        if os.path.exists(oui_file):
            try:
                with open(oui_file, 'r', encoding='utf-8') as f:
                    self.oui_database = json.load(f)
                if self.verbose:
                    print(f"📚 Loaded {len(self.oui_database)} OUI entries from local database")
                return
            except Exception as e:
                if self.verbose:
                    print(f"⚠️  Error loading local OUI database: {e}")
        
        # Download and create local database
        self.download_oui_database(oui_file)
    
    def download_oui_database(self, filename):
        """Download IEEE OUI database and create local lookup file"""
        if self.verbose:
            print("🌐 Downloading IEEE OUI database...")
        
        try:
            # IEEE OUI database URL
            url = "http://standards-oui.ieee.org/oui/oui.txt"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse the OUI file
            oui_pattern = re.compile(r'^([0-9A-F]{6})\s+\(base 16\)\s+(.+)$', re.MULTILINE)
            matches = oui_pattern.findall(response.text)
            
            for oui, vendor in matches:
                # Store as lowercase for consistent lookup
                self.oui_database[oui.lower()] = vendor.strip()
            
            # Save to local file for future use
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.oui_database, f, indent=2)
            
            if self.verbose:
                print(f"✅ Downloaded and cached {len(self.oui_database)} OUI entries")
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Failed to download OUI database: {e}")
            # Use minimal built-in database as fallback
            self.oui_database = self.get_minimal_oui_database()
    
    def get_minimal_oui_database(self):
        """Fallback minimal OUI database with common vendors"""
        return {
            "000000": "Xerox Corporation",
            "00000c": "Cisco Systems, Inc",
            "00000f": "NeXT Computer, Inc",
            "000010": "Sytek Inc",
            "00001b": "Novell Inc",
            "00001d": "Cabletron Systems Inc",
            "000020": "DIAB Data AB",
            "000022": "Visual Technology Inc",
            "000024": "Connect AS",
            "00002a": "TRW Inc",
            "00003c": "Auspex Systems Inc",
            "00005e": "IANA",
            "00006b": "MIPS Computer Systems Inc",
            "000094": "Asante Technologies",
            "0000a2": "Wellfleet Communications Inc",
            "0000a3": "Network Application Technology",
            "0000a6": "Network General Corporation",
            "0000a7": "NCD X-terminals",
            "0000a9": "Network Systems Corporation",
            "0000aa": "Xerox Xerox machines",
            "0000b7": "Dove Computer Corporation",
            "0000bb": "TRI-DATA Systems Inc",
            "0000bc": "Allen-Bradley",
            "0000c0": "Western Digital Corporation",
            "0000c9": "Emulex Corporation",
            "0000f8": "DEC",
            "00d01f": "Senetas Corporation Ltd",
            "001cf0": "Dell Inc",
            "00d861": "Giga-byte Technology Co Ltd",
            "2c600c": "Huawei Technologies Co Ltd",
            "b499ba": "Circle Media Inc",
            "001b63": "Apple, Inc",
            "28f076": "Apple, Inc",
            "7c7a91": "Apple, Inc",
            "a4c361": "Apple, Inc",
        }
    
    def lookup_vendor(self, mac_address):
        """Look up vendor name from MAC address"""
        if not mac_address:
            return "Unknown"
        
        # Extract OUI (first 6 hex digits)
        mac_clean = mac_address.replace(":", "").replace("-", "").lower()
        if len(mac_clean) < 6:
            return "Invalid MAC"
        
        oui = mac_clean[:6]
        vendor = self.oui_database.get(oui, "Unknown Vendor")
        
        if self.verbose:
            print(f"DEBUG - MAC: {mac_address}, OUI: {oui}, Vendor: {vendor}")
        return vendor
    
    def classify_device_type(self, vendor, hostname=None):
        """Classify device type based on vendor and hostname"""
        vendor_lower = vendor.lower()
        hostname_lower = (hostname or "").lower()

        # Encryption appliances
        if 'senetas' in vendor_lower:
            return "🔐 Encryptor"

        # Network infrastructure
        if any(keyword in vendor_lower for keyword in ['cisco', 'juniper', 'netgear', 'linksys', 'tp-link', 'asus router', 'mikrotik']):
            return "🌐 Network Equipment"
        
        # Mobile devices
        if any(keyword in vendor_lower for keyword in ['apple', 'samsung', 'huawei', 'xiaomi', 'lg electronics']):
            return "📱 Mobile Device"
        
        # Computers
        if any(keyword in vendor_lower for keyword in ['dell', 'hp', 'lenovo', 'asus', 'msi', 'gigabyte', 'intel']):
            return "💻 Computer"
        
        # IoT and Smart devices
        if any(keyword in vendor_lower for keyword in ['amazon', 'google', 'nest', 'philips', 'samsung smart', 'lg smart']):
            return "🏠 IoT Device"
        
        # Printers
        if any(keyword in vendor_lower for keyword in ['canon', 'epson', 'brother', 'xerox', 'ricoh']):
            return "🖨️ Printer"
        
        # Gaming consoles
        if any(keyword in vendor_lower for keyword in ['sony', 'microsoft', 'nintendo']):
            return "🎮 Gaming Console"
        
        # Based on hostname patterns
        if hostname_lower:
            if any(keyword in hostname_lower for keyword in ['router', 'gateway', 'switch']):
                return "🌐 Network Equipment"
            elif any(keyword in hostname_lower for keyword in ['printer', 'print']):
                return "🖨️ Printer"
            elif any(keyword in hostname_lower for keyword in ['camera', 'cam']):
                return "📹 Camera"
        
        return "❓ Unknown Device"

class EnhancedPingSweep:
    """Enhanced ping sweep with MAC address lookup and device classification"""
    
    def __init__(self, max_workers=DEFAULT_MAX_WORKERS, timeout=DEFAULT_TIMEOUT, count=DEFAULT_COUNT, verbose=False):
        self.max_workers = max_workers
        self.timeout = timeout
        self.count = count
        self.verbose = verbose
        self.alive_hosts = []
        self.lock = threading.Lock()
        self.stats = defaultdict(int)
        self.mac_lookup = MACVendorLookup(verbose=verbose)
        
    def normalize_mac_address(self, mac_raw):
        """Normalize MAC address to standard format with leading zeros"""
        if not mac_raw:
            return None
        
        # Remove common separators and convert to lowercase
        mac_clean = mac_raw.replace(':', '').replace('-', '').replace('.', '').lower()
        
        # Handle cases where hex digits don't have leading zeros
        # Split into pairs and ensure each pair has 2 digits
        if len(mac_clean) == 12:
            # Already in correct format
            normalized = mac_clean
        else:
            # Handle format like "0:d0:1f:9:82:f4" -> "00d01f098f4"
            parts = mac_raw.replace('-', ':').split(':')
            if len(parts) == 6:
                # Ensure each part is 2 digits with leading zero if needed
                normalized_parts = [part.zfill(2).lower() for part in parts]
                normalized = ''.join(normalized_parts)
            else:
                return None
        
        if len(normalized) == 12 and all(c in '0123456789abcdef' for c in normalized):
            return ':'.join([normalized[i:i+2] for i in range(0, 12, 2)])
        
        return None
    
    def get_mac_address(self, ip):
        """Get MAC address for an IP using ARP table"""
        try:
            if sys.platform.startswith('win'):
                # Windows ARP command
                result = subprocess.run(['arp', '-a', ip], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    if self.verbose:
                        print(f"DEBUG - Windows ARP output: {result.stdout}")
                    # Parse Windows ARP output
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if ip in line:
                            # More flexible MAC address extraction for Windows
                            mac_match = re.search(r'([0-9a-fA-F]{1,2}[:-]){5}[0-9a-fA-F]{1,2}', line)
                            if mac_match:
                                raw_mac = mac_match.group()
                                return self.normalize_mac_address(raw_mac)
            else:
                # Unix/Linux/macOS ARP command
                result = subprocess.run(['arp', '-n', ip],
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    if self.verbose:
                        print(f"DEBUG - Unix ARP output: {result.stdout}")
                    # Parse Unix ARP output
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if ip in line and 'incomplete' not in line.lower():
                            # More flexible MAC address extraction - handle single digit hex
                            mac_match = re.search(r'([0-9a-fA-F]{1,2}[:-]){5}[0-9a-fA-F]{1,2}', line)
                            if mac_match:
                                raw_mac = mac_match.group()
                                normalized = self.normalize_mac_address(raw_mac)
                                if self.verbose:
                                    print(f"DEBUG - Raw MAC: {raw_mac}, Normalized: {normalized}")
                                return normalized
        except Exception as e:
            if self.verbose:
                print(f"DEBUG - ARP lookup error: {e}")
        
        return None
    
    def get_hostname(self, ip):
        """Attempt to get hostname via reverse DNS lookup"""
        try:
            result = subprocess.run(['nslookup', ip], 
                                  capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                # Parse nslookup output for hostname
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'name =' in line.lower():
                        hostname = line.split('=')[1].strip().rstrip('.')
                        return hostname
        except Exception:
            pass
        
        return None
    
    def ping_and_analyze_host(self, ip, pbar=None):
        """Enhanced ping with MAC lookup and device classification"""
        ip_str = str(ip)
        start_time = time.time()
        
        try:
            # Platform-specific ping command
            if sys.platform.startswith('win'):
                cmd = ['ping', '-n', str(self.count), '-w', str(self.timeout), ip_str]
            else:
                cmd = ['ping', '-c', str(self.count), '-W', str(self.timeout // 1000), '-n', ip_str]
            
            response = subprocess.run(cmd, 
                                    stdout=subprocess.DEVNULL, 
                                    stderr=subprocess.DEVNULL,
                                    timeout=5)
            
            response_time = (time.time() - start_time) * 1000
            
            with self.lock:
                if response.returncode == 0:
                    # Host is alive - gather additional information
                    mac_address = self.get_mac_address(ip_str)
                    hostname = self.get_hostname(ip_str)
                    
                    vendor = "Unknown"
                    device_type = "❓ Unknown Device"
                    
                    if mac_address:
                        vendor = self.mac_lookup.lookup_vendor(mac_address)
                        device_type = self.mac_lookup.classify_device_type(vendor, hostname)
                    
                    host_info = {
                        'ip': ip_str,
                        'response_time': response_time,
                        'mac_address': mac_address or 'N/A',
                        'vendor': vendor,
                        'device_type': device_type,
                        'hostname': hostname or 'N/A'
                    }
                    
                    self.alive_hosts.append(host_info)
                    self.stats['alive'] += 1
                    
                    # Store results for display after progress update
                    if self.verbose:
                        # Verbose output with device info
                        result_line = f"✓ {ip_str:<15} ({response_time:.1f}ms) - {device_type} - {vendor}"
                    else:
                        # Concise output: IP, response time, vendor  
                        result_line = f"{ip_str:<15} {response_time:>6.1f}ms  {vendor}"
                    
                    # Show result cleanly
                    if self.verbose:
                        print(result_line)
                    else:
                        # For non-verbose, use tqdm.write to avoid progress bar interference
                        if pbar:
                            pbar.write(result_line)
                        else:
                            print(result_line)
                    
                else:
                    self.stats['down'] += 1
                
            # Update progress bar
            if pbar:
                pbar.update(1)
                pbar.set_postfix(alive=self.stats['alive'], down=self.stats['down'])
                    
        except subprocess.TimeoutExpired:
            with self.lock:
                self.stats['timeout'] += 1
            if pbar:
                pbar.update(1)
                pbar.set_postfix(alive=self.stats['alive'], down=self.stats['down'])
        except Exception as e:
            with self.lock:
                self.stats['error'] += 1
            if pbar:
                pbar.update(1)
                pbar.set_postfix(alive=self.stats['alive'], down=self.stats['down'])
    
    def scan_subnet(self, subnet, use_cache=True):
        """Scan subnet with enhanced device information"""
        try:
            network = ipaddress.ip_network(subnet, strict=False)
        except ValueError as e:
            print(f"❌ Invalid subnet: {e}")
            return []

        total_hosts = network.num_addresses - 2 if network.prefixlen < 31 else network.num_addresses
        if total_hosts <= 0:
            print("❌ No hosts to scan in this subnet")
            return []

        skip_ips = set()

        # Cache check phase — verify previously found devices first
        if use_cache:
            cached = load_cache(subnet, "ping")
            if cached:
                cached_ips = [entry['ip'] for entry in cached]
                print(f"Checking {len(cached_ips)} cached device(s)...")
                cache_workers = min(len(cached_ips), self.max_workers)
                with concurrent.futures.ThreadPoolExecutor(max_workers=cache_workers) as executor:
                    futures = {executor.submit(self.ping_and_analyze_host, ip): ip for ip in cached_ips}
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            future.result()
                        except Exception:
                            pass
                skip_ips = {host['ip'] for host in self.alive_hosts}
                if skip_ips:
                    print(f"  {len(skip_ips)}/{len(cached_ips)} cached device(s) still alive\n")

        remaining_hosts = [ip for ip in network.hosts() if str(ip) not in skip_ips]
        remaining = len(remaining_hosts)

        if self.verbose:
            print(f"🔍 Scanning {remaining} hosts in {subnet}")
            print(f"⚙️  Using {self.max_workers} threads, {self.timeout}ms timeout")
            print(f"📚 MAC vendor database loaded with {len(self.mac_lookup.oui_database)} entries\n")
        else:
            print(f"Scanning {remaining} hosts in {subnet}")
            print(f"{'IP Address':<15} {'Time':<8} Vendor")
            print("-" * 50)

        start_time = time.time()
        actual_workers = min(self.max_workers, remaining) if remaining > 0 else 1

        # Use tqdm progress bar (disable in verbose mode to avoid interference)
        if remaining > 0:
            with tqdm(total=remaining, desc="Scanning", unit="host",
                      disable=self.verbose, leave=True, position=0) as pbar:

                with concurrent.futures.ThreadPoolExecutor(max_workers=actual_workers) as executor:
                    futures = {executor.submit(self.ping_and_analyze_host, ip, pbar): ip for ip in remaining_hosts}

                    for future in concurrent.futures.as_completed(futures):
                        try:
                            future.result()
                        except Exception as e:
                            with self.lock:
                                self.stats['error'] += 1

        scan_time = time.time() - start_time

        if self.verbose:
            self.display_enhanced_results(scan_time, total_hosts)
        else:
            self.display_simple_results(scan_time, total_hosts)

        if use_cache:
            save_cache(subnet, "ping", self.alive_hosts)

        return self.alive_hosts
    
    def display_simple_results(self, scan_time, total_hosts):
        """Display simple summary results"""
        alive_count = len(self.alive_hosts)
        
        print(f"\nScan complete: {alive_count}/{total_hosts} hosts alive ({scan_time:.1f}s)")
        
        if self.stats['timeout'] or self.stats['error']:
            print(f"Timeouts: {self.stats['timeout']}, Errors: {self.stats['error']}")
    
    def display_enhanced_results(self, scan_time, total_hosts):
        """Display enhanced results with device classification"""
        alive_count = len(self.alive_hosts)
        
        print(f"\n{'='*80}")
        print(f"📊 ENHANCED SCAN COMPLETE")
        print(f"{'='*80}")
        print(f"⏱️  Scan time: {scan_time:.2f} seconds")
        print(f"📈 Hosts scanned: {total_hosts}")
        print(f"✅ Alive: {self.stats['alive']}")
        print(f"❌ Down: {self.stats['down']}")
        if self.stats['timeout']:
            print(f"⏰ Timeouts: {self.stats['timeout']}")
        if self.stats['error']:
            print(f"🚫 Errors: {self.stats['error']}")
        
        if self.alive_hosts:
            print(f"\n🌐 DISCOVERED DEVICES ({alive_count}):")
            print("-" * 80)
            
            # Sort by IP address
            sorted_hosts = sorted(self.alive_hosts, key=lambda x: ipaddress.ip_address(x['ip']))
            
            # Display detailed information
            for host in sorted_hosts:
                print(f"📍 {host['ip']:<15} ({host['response_time']:.1f}ms)")
                print(f"   🏷️  Device Type: {host['device_type']}")
                print(f"   🏭 Vendor: {host['vendor']}")
                if host['mac_address'] != 'N/A':
                    print(f"   🔗 MAC Address: {host['mac_address']}")
                if host['hostname'] != 'N/A':
                    print(f"   🏠 Hostname: {host['hostname']}")
                print()
            
            # Device type summary
            device_types = defaultdict(int)
            for host in self.alive_hosts:
                device_types[host['device_type']] += 1
            
            print("📊 DEVICE TYPE SUMMARY:")
            print("-" * 30)
            for device_type, count in sorted(device_types.items()):
                print(f"   {device_type}: {count}")
                
        else:
            print("\n💀 No alive hosts found")

def normalize_mac(mac_raw):
    """Normalize a MAC address to 12-char lowercase hex (e.g., '00d01f098008').

    Handles short-form MACs like '0:d0:1f:9:80:8' by zero-padding each octet.
    """
    parts = mac_raw.replace("-", ":").split(":")
    if len(parts) == 6:
        return "".join(p.zfill(2).lower() for p in parts)
    # Already separator-free or unexpected format
    clean = mac_raw.replace(":", "").replace("-", "").replace(".", "").lower()
    return clean if len(clean) == 12 else ""


def _cache_path(subnet, mode):
    """Return cache file path for a subnet. Mode is 'ping' or 'encryptors'."""
    network = ipaddress.ip_network(subnet, strict=False)
    cache_dir = os.path.expanduser(f"~/.config/pingsweep/cache/{mode}")
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, str(network).replace("/", "_") + ".json")


def load_cache(subnet, mode):
    """Load cached scan results. Returns list of dicts or []."""
    path = _cache_path(subnet, mode)
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return []


def save_cache(subnet, mode, results):
    """Save scan results to cache."""
    try:
        path = _cache_path(subnet, mode)
        with open(path, 'w') as f:
            json.dump(results, f, indent=2)
    except Exception:
        pass


def find_encryptors(subnet, timeout=2, verbose=False, iface=None, use_cache=True):
    """ARP sweep for Senetas encryptors (OUI 00:d0:1f).

    Uses Scapy to send ARP requests and filters responses
    for the Senetas MAC prefix. Requires root privileges.
    """
    from scapy.all import srp, Ether, ARP, conf
    conf.verb = 0

    network = ipaddress.ip_network(subnet, strict=False)
    total = network.num_addresses - 2 if network.prefixlen < 31 else network.num_addresses

    if total <= 0:
        print("No hosts to scan in this subnet")
        return []

    # Auto-detect interface from Scapy's routing table if not specified
    if iface is None:
        first_host = str(next(network.hosts()))
        iface, _, _ = conf.route.route(first_host)

    print(f"Scanning for Senetas encryptors in {subnet} ({total} hosts) on {iface}...")

    encryptors = []
    found_ips = set()
    srp_kwargs = {"timeout": timeout, "verbose": False}
    if iface:
        srp_kwargs["iface"] = iface

    # Cache check phase — verify previously found encryptors first
    if use_cache:
        cached = load_cache(subnet, "encryptors")
        if cached:
            cached_ips = [e['ip'] for e in cached]
            print(f"Checking {len(cached_ips)} previously found encryptor(s)...")
            pkt = [Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip) for ip in cached_ips]
            try:
                ans, _ = srp(pkt, timeout=1, verbose=False,
                             **({"iface": iface} if iface else {}))
                for sent, received in ans:
                    mac_norm = normalize_mac(received.hwsrc)
                    if mac_norm[:6] == SENETAS_OUI:
                        entry = {
                            'ip': received.psrc,
                            'mac': ':'.join(mac_norm[i:i+2] for i in range(0, 12, 2)),
                        }
                        encryptors.append(entry)
                        found_ips.add(received.psrc)
                        print(f"  Found (cached): {entry['ip']:<15} {entry['mac']}")
            except Exception:
                pass
            if found_ips:
                print(f"  {len(found_ips)}/{len(cached_ips)} cached encryptor(s) still alive")

    # For large subnets, chunk into /24s to avoid memory issues
    if network.prefixlen < 24:
        chunks = list(network.subnets(new_prefix=24))
    else:
        chunks = [network]

    # Reliable Ctrl+C: first press requests stop, second press force-quits.
    # Scapy overrides SIGINT during srp(), so a simple flag won't work.
    interrupted = False
    old_handler = signal.getsignal(signal.SIGINT)

    def on_sigint(signum, frame):
        nonlocal interrupted
        if interrupted:
            print("\nForce quit.")
            os._exit(1)
        interrupted = True
        print("\nStopping after current chunk (Ctrl+C again to force quit)...")

    signal.signal(signal.SIGINT, on_sigint)

    try:
        with tqdm(total=len(chunks), desc="ARP sweep", unit="chunk",
                  disable=verbose, leave=True) as pbar:
            for chunk in chunks:
                if interrupted:
                    break

                pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=str(chunk))
                try:
                    ans, _ = srp(pkt, **srp_kwargs)
                except KeyboardInterrupt:
                    break

                if interrupted:
                    break

                for sent, received in ans:
                    if received.psrc in found_ips:
                        continue
                    mac_norm = normalize_mac(received.hwsrc)
                    if verbose:
                        print(f"  ARP reply: {received.psrc:<15} {received.hwsrc} (normalized: {mac_norm})")
                    if mac_norm[:6] == SENETAS_OUI:
                        encryptors.append({
                            'ip': received.psrc,
                            'mac': ':'.join(mac_norm[i:i+2] for i in range(0, 12, 2)),
                        })
                        found_ips.add(received.psrc)
                        msg = f"  Found: {received.psrc:<15} {encryptors[-1]['mac']}"
                        if pbar.disable:
                            print(msg)
                        else:
                            pbar.write(msg)

                pbar.update(1)

            if interrupted:
                print(f"\nScan interrupted. Scanned {pbar.n}/{len(chunks)} chunks.")
    finally:
        signal.signal(signal.SIGINT, old_handler)

    if not interrupted and use_cache:
        save_cache(subnet, "encryptors", encryptors)

    return encryptors


def main():
    parser = argparse.ArgumentParser(
        description='Enhanced Network Discovery Tool with MAC lookup and device classification',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pingsweep.py 192.168.1.0/24
  python pingsweep.py -v 10.0.0.0/24
  python pingsweep.py --verbose --workers 20 --timeout 500 192.168.1.0/24
  sudo python pingsweep.py --find-encryptors 10.0.0.0/16
        """
    )
    
    parser.add_argument('subnet', help='Subnet to scan (e.g., 192.168.1.0/24)')
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='Enable verbose output with detailed device information')
    parser.add_argument('-w', '--workers', type=int, default=DEFAULT_MAX_WORKERS,
                       help=f'Number of worker threads (default: {DEFAULT_MAX_WORKERS})')
    parser.add_argument('-t', '--timeout', type=int, default=DEFAULT_TIMEOUT,
                       help=f'Ping timeout in milliseconds (default: {DEFAULT_TIMEOUT})')
    parser.add_argument('-c', '--count', type=int, default=DEFAULT_COUNT,
                       help=f'Number of ping packets per host (default: {DEFAULT_COUNT})')
    parser.add_argument('--export', action='store_true',
                       help='Export results to JSON file')
    parser.add_argument('--find-encryptors', action='store_true',
                       help='Fast ARP scan to find Senetas encryptors by MAC prefix (requires root and scapy)')
    parser.add_argument('--iface', type=str, default=None,
                       help='Network interface to use for ARP scan (e.g., en8)')
    parser.add_argument('--no-cache', action='store_true',
                       help='Skip cached results and force a clean scan')

    args = parser.parse_args()

    # Fast encryptor discovery mode
    if args.find_encryptors:
        try:
            # Root check (Unix only)
            if sys.platform != 'win32' and os.geteuid() != 0:
                print("Error: --find-encryptors requires root. Run with sudo.")
                sys.exit(1)

            # Dependency check
            try:
                from scapy.all import srp  # noqa: F401
            except ImportError:
                print("Error: --find-encryptors requires scapy: pip install scapy")
                sys.exit(1)

            start = time.time()
            timeout_sec = max(1, args.timeout // 1000)
            use_cache = not args.no_cache
            encryptors = find_encryptors(args.subnet, timeout=timeout_sec, verbose=args.verbose, iface=args.iface, use_cache=use_cache)

            if encryptors:
                sorted_results = sorted(encryptors, key=lambda x: ipaddress.ip_address(x['ip']))
                print(f"\nFound {len(encryptors)} encryptor(s):")
                for e in sorted_results:
                    print(f"  {e['ip']:<15} {e['mac']}")
            else:
                print("\nNo Senetas encryptors found.")

            print(f"Scan complete in {time.time() - start:.1f}s")

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

        except KeyboardInterrupt:
            print("\n\nScan interrupted by user")
        except Exception as e:
            print(f"\nError: {e}")
        sys.exit(0)

    try:
        if args.verbose:
            print("🏓 ENHANCED NETWORK DISCOVERY TOOL")
            print("=" * 50)
            print("Features: Ping Sweep + MAC Lookup + Device Classification")
            print()
        
        print(f"🚀 Starting {'enhanced ' if args.verbose else ''}scan...")
        scanner = EnhancedPingSweep(
            max_workers=args.workers, 
            timeout=args.timeout,
            count=args.count,
            verbose=args.verbose
        )
        use_cache = not args.no_cache
        alive_hosts = scanner.scan_subnet(args.subnet, use_cache=use_cache)
        
        # Export option with enhanced data
        if args.export and alive_hosts:
            filename = f"network_discovery_{args.subnet.replace('/', '_')}_{int(time.time())}.json"
            with open(filename, 'w') as f:
                json.dump({
                    'scan_info': {
                        'subnet': args.subnet,
                        'scan_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'total_discovered': len(alive_hosts),
                        'verbose_mode': args.verbose
                    },
                    'devices': alive_hosts
                }, f, indent=2)
            print(f"✅ Results exported to {filename}")
        
    except KeyboardInterrupt:
        print("\n\n🛑 Scan interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()