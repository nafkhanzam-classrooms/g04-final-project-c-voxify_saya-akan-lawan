import asyncio
import socket
import websockets
import json
import struct
from utils.protocol import send_message, receive_message

TCP_HOST = '127.0.0.1'
TCP_PORT = 8000

WS_HOST = '0.0.0.0'
WS_PORT = 8080

async def bridge_handler(websocket):
    print(f"[*] Browser connected via WebSocket")
    
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        tcp_sock.connect((TCP_HOST, TCP_PORT))
        loop = asyncio.get_event_loop()
        
        async def ws_to_tcp():
            try:
                async for message in websocket:
                    data = json.loads(message)
                    print(f"[WS -> TCP] Action: {data.get('action')}")
                    await loop.run_in_executor(None, send_message, tcp_sock, data)
            except Exception as e:
                print(f"[*] WS to TCP closed: {e}")

        async def tcp_to_ws():
            try:
                while True:
                    data = await loop.run_in_executor(None, receive_message, tcp_sock)
                    if data is None:
                        print("[*] TCP Server closed connection")
                        break
                    
                    print(f"[TCP -> WS] Response Status: {data.get('status')}")
                    await websocket.send(json.dumps(data))
            except Exception as e:
                print(f"[*] TCP to WS closed: {e}")
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
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] Shutting down bridge...")
