import json
import socket
import struct

# Konfigurasi
HOST = "127.0.0.1"
PORT = 8000


def send_request(sock, action, data):
    # Bungkus JSON
    payload = json.dumps({"action": action, "data": data}).encode("utf-8")
    # Tambahkan header 4-byte (panjang pesan)
    header = struct.pack(">I", len(payload))
    sock.sendall(header + payload)
    # Terima Balasan
    raw_header = sock.recv(4)
    if not raw_header:
        return None
    length = struct.unpack(">I", raw_header)[0]
    response = sock.recv(length).decode("utf-8")
    return json.loads(response)


# Jalankan Test
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print("[*] Terhubung ke Raw TCP Server")
    # Contoh Registrasi
    res = send_request(
        s,
        "auth.register",
        {
            "username": "budi123",
            "password": "password123",
            "email": "budi123@mail.com",
            "display_name": "Budi Anto",
        },
    )
    print(f"[*] Response Register: {res}")
    # Contoh Login
    res = send_request(
        s, "auth.login", {"username": "budi123", "password": "password123"}
    )
    print(f"[*] Response Login: {res}")
