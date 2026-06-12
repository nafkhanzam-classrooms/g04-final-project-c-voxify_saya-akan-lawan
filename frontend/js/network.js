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
        if (packet.action && this.messageHandlers.has(packet.action)) {
          this.messageHandlers.get(packet.action)(packet);
        } else if (packet.type && this.messageHandlers.has(packet.type)) {
          this.messageHandlers.get(packet.type)(packet);
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

  registerHandler(action, callback) {
    this.messageHandlers.set(action, callback);
  }

  sendPacket(action, data = {}) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) return;
    const token = localStorage.getItem("voxify_token");
    const packet = {
      action: action,
      data: data,
      token: token || null,
    };
    this.socket.send(JSON.stringify(packet));
  }
}
