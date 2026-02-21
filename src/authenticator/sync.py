import json
import socket
import threading
import time
import random
from rich.console import Console
import questionary

console = Console()

def wireless_sync(keys, role, port=9999):
    if role == "sender":
        wireless_sender(keys, port)
    elif role == "receiver":
        wireless_receiver(port)


def wireless_sender(keys, port):
    # 生成6位数字密钥
    pin = str(random.randint(100000, 999999))
    console.print(f"[cyan]PIN Code: [bold]{pin}[/bold][/cyan]")
    console.print("[yellow]Waiting for receiver to connect...[/yellow]")

    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', port))
        server_socket.listen(1)
        
        # 创建广播线程（UDP 广播设备信息）
        broadcast_thread = threading.Thread(
            target=_broadcast_device,
            args=(pin, port),
            daemon=True
        )
        broadcast_thread.start()
        
        # 等待连接
        client_socket, client_address = server_socket.accept()
        console.print(f"[green]✓ Receiver connected from {client_address[0]}[/green]")
        
        # 接收 PIN 验证
        received_pin = client_socket.recv(1024).decode('utf-8').strip()
        if received_pin != pin:
            console.print(f"[red]✗ PIN mismatch! Expected {pin}, got {received_pin}[/red]")
            client_socket.close()
            return
        
        console.print("[green]✓ PIN verified[/green]")

        # 发送密钥数据
        keys_json = json.dumps(keys)
        client_socket.send(keys_json.encode('utf-8'))
        console.print(f"[green]✓ Sent {len(keys)} keys successfully[/green]")
        
        client_socket.close()
        server_socket.close()
        
    except Exception as e:
        console.print(f"[red]✗ Sender error: {e}[/red]")


def wireless_receiver(port):
    """接收端：发现设备并连接"""
    console.print("[yellow]Scanning for devices...[/yellow]")
    
    devices = []
    
    def _scan_devices():
        """扫描局域网设备"""
        try:
            # 监听 UDP 广播
            receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            receiver_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            receiver_socket.bind(('0.0.0.0', 9998))
            receiver_socket.settimeout(5)
            
            while len(devices) < 5:  # 最多扫描5个设备
                try:
                    data, addr = receiver_socket.recvfrom(1024)
                    device_info = json.loads(data.decode('utf-8'))
                    entry = {
                        'ip': addr[0],
                        'name': device_info.get('name', 'Authenticator Sync'),
                        'port': device_info['port']
                    }
                    if entry not in devices:
                        devices.append(entry)
                except socket.timeout:
                    break
            
            receiver_socket.close()
        except Exception as e:
            console.print(f"[red]Scan error: {e}[/red]")
    
    scan_thread = threading.Thread(target=_scan_devices, daemon=True)
    scan_thread.start()
    scan_thread.join(timeout=6)
    
    if not devices:
        console.print("[red]✗ No devices found[/red]")
        return
    
    # 选择设备
    choices = [f"{i+1}. {d['ip']} ({d['name']})" for i, d in enumerate(devices)]
    device_idx = questionary.select(
        "Select device:",
        choices=choices,
        use_arrow_keys=True
        ).ask()
    
    selected_device = devices[int(device_idx.split('.')[0]) - 1]
    
    # 输入 PIN
    pin = questionary.text("Enter PIN code:").ask()
    
    # 连接并接收
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((selected_device['ip'], selected_device['port']))
        
        # 发送 PIN
        client_socket.send(pin.encode('utf-8'))
        
        # 接收密钥
        keys_json = client_socket.recv(65536).decode('utf-8')
        keys = json.loads(keys_json)
        
        client_socket.close()
        
        console.print(f"[green]✓ Received {len(keys)} keys[/green]")
        return keys
        
    except Exception as e:
        console.print(f"[red]✗ Receiver error: {e}[/red]")
        return None


def _broadcast_device(pin, port):
    """广播设备信息到局域网"""
    try:
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        device_info = {
            'port': port,
            'name': 'Authenticator Sync'
        }
        
        # 广播 10 秒
        for _ in range(10):
            broadcast_socket.sendto(
                json.dumps(device_info).encode('utf-8'),
                ('<broadcast>', 9998)
            )
            time.sleep(1)
        
        broadcast_socket.close()
    except Exception as e:
        console.print(f"[red]Broadcast error: {e}[/red]")