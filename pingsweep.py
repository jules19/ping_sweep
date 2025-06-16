import ipaddress
import subprocess
import concurrent.futures
import time
import sys
import threading
from collections import defaultdict

# Configuration
DEFAULT_MAX_WORKERS = 50  # Reduced from 70 for better system stability
DEFAULT_TIMEOUT = 1000    # ms - more reasonable timeout
DEFAULT_COUNT = 1

class PingSweep:
    def __init__(self, max_workers=DEFAULT_MAX_WORKERS, timeout=DEFAULT_TIMEOUT, count=DEFAULT_COUNT):
        self.max_workers = max_workers
        self.timeout = timeout
        self.count = count
        self.alive_hosts = []
        self.lock = threading.Lock()
        self.stats = defaultdict(int)
        
    def ping_host(self, ip):
        ip_str = str(ip)
        start_time = time.time()
        
        try:
            # Platform-specific ping command optimization
            if sys.platform.startswith('win'):
                cmd = ['ping', '-n', str(self.count), '-w', str(self.timeout), ip_str]
            else:
                # Unix/Linux/macOS - use faster timeout and disable DNS resolution
                cmd = ['ping', '-c', str(self.count), '-W', str(self.timeout // 1000), '-n', ip_str]
            
            response = subprocess.run(cmd, 
                                    stdout=subprocess.DEVNULL, 
                                    stderr=subprocess.DEVNULL,
                                    timeout=5)  # Hard timeout as fallback
            
            response_time = (time.time() - start_time) * 1000
            
            with self.lock:
                if response.returncode == 0:
                    self.alive_hosts.append((ip_str, response_time))
                    self.stats['alive'] += 1
                    print(f"✓ {ip_str} ({response_time:.1f}ms)")
                else:
                    self.stats['down'] += 1
                    
        except subprocess.TimeoutExpired:
            with self.lock:
                self.stats['timeout'] += 1
        except Exception as e:
            with self.lock:
                self.stats['error'] += 1
    
    def scan_subnet(self, subnet):
        try:
            network = ipaddress.ip_network(subnet, strict=False)
        except ValueError as e:
            print(f"❌ Invalid subnet: {e}")
            return []
        
        # Calculate and display scan info
        total_hosts = network.num_addresses - 2 if network.prefixlen < 31 else network.num_addresses
        if total_hosts <= 0:
            print("❌ No hosts to scan in this subnet")
            return []
            
        print(f"🔍 Scanning {total_hosts} hosts in {subnet}")
        print(f"⚙️  Using {self.max_workers} threads, {self.timeout}ms timeout\n")
        
        start_time = time.time()
        
        # Use appropriate number of workers (don't exceed host count)
        actual_workers = min(self.max_workers, total_hosts)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=actual_workers) as executor:
            # Submit all tasks
            futures = {executor.submit(self.ping_host, ip): ip for ip in network.hosts()}
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    with self.lock:
                        self.stats['error'] += 1
        
        scan_time = time.time() - start_time
        
        # Display results
        self.display_results(scan_time, total_hosts)
        return self.alive_hosts
    
    def display_results(self, scan_time, total_hosts):
        alive_count = len(self.alive_hosts)
        
        print(f"\n{'='*50}")
        print(f"📊 SCAN COMPLETE")
        print(f"{'='*50}")
        print(f"⏱️  Scan time: {scan_time:.2f} seconds")
        print(f"📈 Hosts scanned: {total_hosts}")
        print(f"✅ Alive: {self.stats['alive']}")
        print(f"❌ Down: {self.stats['down']}")
        if self.stats['timeout']:
            print(f"⏰ Timeouts: {self.stats['timeout']}")
        if self.stats['error']:
            print(f"🚫 Errors: {self.stats['error']}")
        
        if self.alive_hosts:
            print(f"\n🌐 ALIVE HOSTS ({alive_count}):")
            print("-" * 30)
            # Sort by IP address for better readability
            sorted_hosts = sorted(self.alive_hosts, key=lambda x: ipaddress.ip_address(x[0]))
            for host, response_time in sorted_hosts:
                print(f"  {host:<15} ({response_time:.1f}ms)")
        else:
            print("\n💀 No alive hosts found")

def get_user_input():
    """Enhanced input collection with validation and defaults"""
    print("🔧 PING SWEEP CONFIGURATION")
    print("=" * 30)
    
    # Get subnet
    while True:
        subnet = input("Enter subnet (e.g., 192.168.1.0/24): ").strip()
        if subnet:
            try:
                ipaddress.ip_network(subnet, strict=False)
                break
            except ValueError:
                print("❌ Invalid subnet format. Please try again.")
        else:
            print("❌ Subnet cannot be empty.")
    
    # Get optional parameters
    print("\n⚙️ Optional settings (press Enter for defaults):")
    
    # Max workers
    while True:
        workers_input = input(f"Max threads (default {DEFAULT_MAX_WORKERS}): ").strip()
        if not workers_input:
            max_workers = DEFAULT_MAX_WORKERS
            break
        try:
            max_workers = int(workers_input)
            if 1 <= max_workers <= 200:
                break
            else:
                print("❌ Please enter a number between 1 and 200.")
        except ValueError:
            print("❌ Please enter a valid number.")
    
    # Timeout
    while True:
        timeout_input = input(f"Timeout in ms (default {DEFAULT_TIMEOUT}): ").strip()
        if not timeout_input:
            timeout = DEFAULT_TIMEOUT
            break
        try:
            timeout = int(timeout_input)
            if 100 <= timeout <= 10000:
                break
            else:
                print("❌ Please enter a timeout between 100 and 10000 ms.")
        except ValueError:
            print("❌ Please enter a valid number.")
    
    return subnet, max_workers, timeout

def main():
    print("🏓 NETWORK PING SWEEP TOOL")
    print("=" * 40)
    
    try:
        subnet, max_workers, timeout = get_user_input()
        
        print(f"\n🚀 Starting scan...")
        scanner = PingSweep(max_workers=max_workers, timeout=timeout)
        alive_hosts = scanner.scan_subnet(subnet)
        
        # Export option
        if alive_hosts:
            export = input("\n💾 Export results to file? (y/N): ").strip().lower()
            if export in ['y', 'yes']:
                filename = f"ping_sweep_{subnet.replace('/', '_')}_{int(time.time())}.txt"
                with open(filename, 'w') as f:
                    f.write(f"Ping Sweep Results\n")
                    f.write(f"Subnet: {subnet}\n")
                    f.write(f"Scan Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Alive Hosts: {len(alive_hosts)}\n\n")
                    for host, response_time in sorted(alive_hosts, key=lambda x: ipaddress.ip_address(x[0])):
                        f.write(f"{host} ({response_time:.1f}ms)\n")
                print(f"✅ Results exported to {filename}")
        
    except KeyboardInterrupt:
        print("\n\n🛑 Scan interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()


