from server import ThreadedTCPServer

if __name__ == "__main__":
    # You can change host/port via env variables or hardcoded
    server = ThreadedTCPServer(host="0.0.0.0", port=8000)
    server.start()
