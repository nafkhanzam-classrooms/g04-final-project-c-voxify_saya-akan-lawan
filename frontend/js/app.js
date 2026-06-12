import { VoxifyNetworkClient } from "./network.js";
import { AuthModule } from "./auth.js";
import { DashboardModule } from "./dashboard.js";

class VoxifyAppController {
  constructor() {
    this.network = new VoxifyNetworkClient("ws://127.0.0.1:8080");
    this.currentUser = null;

    this.authContainer = document.getElementById("auth-container");
    this.dashboardContainer = document.getElementById("dashboard-container");

    this.auth = new AuthModule(this);
    this.dashboard = new DashboardModule(this);

    this.initNetwork();
    this.init();
  }

  initNetwork() {
    // Handle validate_token response for session restore
    this.network.registerHandler("auth.validate_token", (response) => {
      if (response.status === "success") {
        this.currentUser = response.data.user;
        this.switchToDashboard();
      } else {
        // Token invalid/expired — clear it and stay on login
        localStorage.removeItem("voxify_token");
      }
    });
  }

  init() {
    this.network.connect(
      () => this.handleServerOpen(),
      () => this.handleServerDisconnect(),
    );
  }

  handleServerOpen() {
    const token = localStorage.getItem("voxify_token");
    if (token) {
      // Attempt to restore session with existing token
      this.network.sendPacket("auth.validate_token");
    }
  }

  handleServerDisconnect() {
    this.authContainer.classList.remove("hidden");
    this.dashboardContainer.classList.add("hidden");
  }

  switchToDashboard() {
    this.authContainer.classList.add("hidden");
    this.dashboardContainer.classList.remove("hidden");
    this.dashboard.setupUserTag();
    this.dashboard.refreshSidebar();
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.App = new VoxifyAppController();
});
