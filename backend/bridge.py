import asyncio
import socket
import websockets
import json
import struct
from utils.protocol import send_message, receive_message

# TCP Server Configuration
TCP_HOST = '127.0.0.1'
TCP_PORT = 8000

# Bridge WebSocket Configuration
WS_HOST = '0.0.0.0'
WS_PORT = 8080

async def bridge_handler(websocket):
    """
    Handles a single WebSocket connection from the browser and
    proxies it to the Raw TCP Server.
    """
    print(f"[*] Browser connected via WebSocket")
    
    # Create a TCP connection to the backend server
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Connect is blocking, but short. For robustness we could use loop.run_in_executor
        tcp_sock.connect((TCP_HOST, TCP_PORT))
        loop = asyncio.get_event_loop()
        
        async def ws_to_tcp():
            """Relays messages from Browser -> TCP Server"""
            try:
                async for message in websocket:
                    data = json.loads(message)
                    print(f"[WS -> TCP] Action: {data.get('action')}")
                    # Relay to TCP server (Blocking call in executor)
                    await loop.run_in_executor(None, send_message, tcp_sock, data)
            except Exception as e:
                print(f"[*] WS to TCP closed: {e}")

        async def tcp_to_ws():
            """Relays messages from TCP Server -> Browser"""
            try:
                while True:
                    # Blocking receive from TCP server (Blocking call in executor)
                    data = await loop.run_in_executor(None, receive_message, tcp_sock)
                    if data is None:
                        print("[*] TCP Server closed connection")
                        break
                    
                    print(f"[TCP -> WS] Response Status: {data.get('status')}")
                    # Send to Browser
                    await websocket.send(json.dumps(data))
            except Exception as e:
                print(f"[*] TCP to WS closed: {e}")

        # Run both relay tasks concurrently
        await asyncio.gather(ws_to_tcp(), tcp_to_ws())

    except ConnectionRefusedError:
        print("[!] Could not connect to TCP Server. Is it running?")
        await websocket.send(json.dumps({"status": "error", "message": "Backend server is offline"}))
    except Exception as e:
        print(f"[!] Bridge error: {e}")
    finally:
        tcp_sock.close()
        print("[*] WebSocket connection closed")

async def main():
    print(f"[*] WebSocket Bridge starting on {WS_HOST}:{WS_PORT}...")
    print(f"[*] Proxying to Raw TCP Server at {TCP_HOST}:{TCP_PORT}")
    async with websockets.serve(bridge_handler, WS_HOST, WS_PORT):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] Shutting down bridge...")
