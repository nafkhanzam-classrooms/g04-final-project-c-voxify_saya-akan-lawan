export class VoxifyNetworkClient {
  constructor(url = "ws://127.0.0.1:8000") {
    this.url = url;
    this.socket = null;
    this.isConnected = false;
    this.messageHandlers = new Map();
  }

  connect(onOpenCallback, onDisconnectCallback) {
    try {
      this.socket = new WebSocket(this.url);

      this.socket.onopen = () => {
        this.isConnected = true;
        onOpenCallback();
      };

      this.socket.onmessage = (event) => {
        const packet = JSON.parse(event.data);
        if (packet.type && this.messageHandlers.has(packet.type)) {
          this.messageHandlers.get(packet.type)(packet.data);
        } else if (packet.status) {
          if (this.messageHandlers.has(packet.action)) {
            this.messageHandlers.get(packet.action)(packet);
          }
        }
      };

      this.socket.onclose = () => {
        this.isConnected = false;
        onDisconnectCallback();
      };
    } catch (error) {
      this.isConnected = false;
    }
  }

  registerHandler(type, callback) {
    this.messageHandlers.set(type, callback);
  }

  sendPacket(action, data = {}) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) return;
    const token = localStorage.getItem("voxify_token");
    const packet = {
      action: action,
      token: token,
      data: data,
    };
    this.socket.send(JSON.stringify(packet));
  }
}
