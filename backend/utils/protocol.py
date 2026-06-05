import json
import struct
import socket
from typing import Any, Optional

# Batas maksimum ukuran payload per pesan (1 MB).
# Klien jahat yang mengirim header palsu (misal 4GB) akan langsung diputus.
MAX_PAYLOAD_BYTES = 1 * 1024 * 1024  # 1 MB


def send_message(sock: socket.socket, data: Any):
    """
    Packs data into a length-prefixed JSON byte string and sends it.
    [ 4 Bytes Length ] [ JSON Payload ]
    """
    payload = json.dumps(data).encode('utf-8')
    length = len(payload)
    header = struct.pack('>I', length)
    sock.sendall(header + payload)


def receive_message(sock: socket.socket) -> Optional[dict]:
    """
    Reads a length-prefixed JSON message from a blocking socket.
    Returns None jika koneksi terputus, timeout, atau payload melebihi batas.
    """
    try:
        # Baca 4-byte header
        header = b''
        while len(header) < 4:
            chunk = sock.recv(4 - len(header))
            if not chunk:
                return None
            header += chunk

        length = struct.unpack('>I', header)[0]

        # Tolak pesan yang terlalu besar untuk mencegah DoS
        if length > MAX_PAYLOAD_BYTES:
            return None

        # Baca payload
        payload = b''
        while len(payload) < length:
            chunk = sock.recv(length - len(payload))
            if not chunk:
                return None
            payload += chunk

        return json.loads(payload.decode('utf-8'))
    except (socket.error, socket.timeout, json.JSONDecodeError, struct.error):
        return None

