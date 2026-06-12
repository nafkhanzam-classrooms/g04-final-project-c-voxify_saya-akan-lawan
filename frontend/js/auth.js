export class AuthModule {
  constructor(appController) {
    this.app = appController;
    this.loginView = document.getElementById("auth-login-view");
    this.registerView = document.getElementById("auth-register-view");
    this.loginUsername = document.getElementById("login-username");
    this.loginPassword = document.getElementById("login-password");
    this.btnExecuteLogin = document.getElementById("btn-execute-login");
    this.regUsername = document.getElementById("reg-username");
    this.regEmail = document.getElementById("reg-email");
    this.regDisplay = document.getElementById("reg-display");
    this.regPassword = document.getElementById("reg-password");
    this.btnExecuteRegister = document.getElementById("btn-execute-register");
    this.linkToRegister = document.getElementById("link-to-register");
    this.linkToLogin = document.getElementById("link-to-login");

    this.initEvents();
    this.initNetwork();
  }

  initEvents() {
    this.linkToRegister.addEventListener("click", () => this.toggleView(false));
    this.linkToLogin.addEventListener("click", () => this.toggleView(true));
    this.btnExecuteLogin.addEventListener("click", () => this.handleLogin());
    this.btnExecuteRegister.addEventListener("click", () =>
      this.handleRegister(),
    );
  }

  initNetwork() {
    this.app.network.registerHandler("auth.login", (response) => {
      if (response.status === "success") {
        localStorage.setItem("voxify_token", response.data.access_token);
        this.app.currentUser = response.data.user;
        this.app.switchToDashboard();
      } else {
        alert(response.message);
      }
    });

    this.app.network.registerHandler("auth.register", (response) => {
      if (response.status === "success") {
        alert("Registrasi sukses! Silakan login.");
        this.toggleView(true);
      } else {
        alert(response.message);
      }
    });
  }

  toggleView(showLogin) {
    if (showLogin) {
      this.loginView.classList.remove("hidden");
      this.registerView.classList.add("hidden");
    } else {
      this.loginView.classList.add("hidden");
      this.registerView.classList.remove("hidden");
    }
  }

  handleLogin() {
    const username = this.loginUsername.value.trim();
    const password = this.loginPassword.value.trim();
    if (!username || !password) {
      return;
    }

    this.app.network.sendPacket("auth.login", {
      username: username,
      password: password,
    });
  }

  handleRegister() {
    const username = this.regUsername.value.trim();
    const email = this.regEmail.value.trim();
    const display = this.regDisplay.value.trim();
    const password = this.regPassword.value.trim();
    if (!username || !email || !display || !password) {
      return;
    }

    this.app.network.sendPacket("auth.register", {
      username: username,
      email: email,
      display_name: display,
      password: password,
      avatar_url: null,
    });
  }
}
