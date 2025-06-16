import ipaddress
import subprocess
import concurrent.futures

MAX_WORKERS = 70

def ping_host(ip):
    ip = str(ip)
    print(f"Trying {ip}...", end="")
    # Use subprocess.call to handle command execution
    response = subprocess.call(['ping', '-c', '1', '-t', '500', ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if response == 0:
        print(f"{ip} is alive!")
        return ip
    else:
        print(f"{ip} is down.")
        return None

def main():
    subnet = input("Enter the subnet (e.g., 192.168.1.0/24): ")
    
    try:
        network = ipaddress.ip_network(subnet, strict=False)
    except ValueError:
        print("Invalid subnet.")
        return
    
    alive_hosts = []

    print("\nStarting ping sweep...\n")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(ping_host, network.hosts())
        for result in results:
            if result:
                alive_hosts.append(result)

    if alive_hosts:
        print("\nSummary of alive hosts:")
        for host in alive_hosts:
            print(host)
    else:
        print("\nNo alive hosts found.")

if __name__ == "__main__":
    main()

