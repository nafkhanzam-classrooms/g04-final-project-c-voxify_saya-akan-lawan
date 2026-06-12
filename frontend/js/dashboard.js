export class DashboardModule {
  constructor(appController) {
    this.app = appController;

    this.userDisplayTag = document.getElementById("user-display-tag");
    this.roomsList = document.getElementById("rooms-list");
    this.dmsList = document.getElementById("dms-list");
    this.chatLog = document.getElementById("chat-log");
    this.chatHeader = document.getElementById("active-chat-header");
    this.entryBox = document.getElementById("entry-box");
    this.btnSend = document.getElementById("btn-send");

    this.actionCreateRoom = document.getElementById("action-create-room");
    this.actionJoinRoom = document.getElementById("action-join-room");

    this.roomModal = document.getElementById("room-modal");
    this.modalTitle = document.getElementById("modal-title");
    this.modalLabel1 = document.getElementById("modal-label-1");
    this.modalLabel2 = document.getElementById("modal-label-2");
    this.modalInput1 = document.getElementById("modal-input-1");
    this.modalInput2 = document.getElementById("modal-input-2");
    this.modalField2 = document.getElementById("modal-field-2");
    this.btnModalCancel = document.getElementById("btn-modal-cancel");
    this.btnModalSubmit = document.getElementById("btn-modal-submit");

    this.activeChatType = null;
    this.activeChatId = null;
    this.currentModalMode = null;

    this.initEvents();
    this.initNetwork();
  }

  initEvents() {
    this.btnSend.addEventListener("click", () => this.sendMessage());
    this.entryBox.addEventListener("keypress", (e) => {
      if (e.key === "Enter") this.sendMessage();
    });

    this.actionCreateRoom.addEventListener("click", () =>
      this.openModal("create"),
    );
    this.actionJoinRoom.addEventListener("click", () => this.openModal("join"));
    this.btnModalCancel.addEventListener("click", () => this.closeModal());
    this.btnModalSubmit.addEventListener("click", () =>
      this.handleModalSubmit(),
    );

    this.chatLog.addEventListener("scroll", () => {
      if (this.chatLog.scrollTop === 0) {
        this.loadMoreHistory();
      }
    });
  }

  initNetwork() {
    this.app.network.registerHandler("new_message", (data) => {
      if (
        this.activeChatId === data.room_id ||
        this.activeChatId === data.sender.id
      ) {
        this.appendMessage(data);
      } else {
        this.incrementUnread(data);
      }
    });

    this.app.network.registerHandler("room_created", () => {
      this.closeModal();
      this.refreshSidebar();
    });

    this.app.network.registerHandler("room_joined", () => {
      this.closeModal();
      this.refreshSidebar();
    });

    this.app.network.registerHandler("rooms_list_data", (rooms) =>
      this.renderRooms(rooms),
    );
    this.app.network.registerHandler("dms_list_data", (conversations) =>
      this.renderDMs(conversations),
    );
    this.app.network.registerHandler("chat_history_data", (messages) =>
      this.renderHistory(messages),
    );
  }

  setupUserTag() {
    this.userDisplayTag.textContent = `🟢 ${this.app.currentUser.display_name}`;
  }

  refreshSidebar() {
    this.app.network.sendPacket("get_rooms");
    this.app.network.sendPacket("get_dms");
  }

  openModal(mode) {
    this.currentModalMode = mode;
    this.roomModal.classList.remove("hidden");
    this.modalInput1.value = "";
    this.modalInput2.value = "";

    if (mode === "create") {
      this.modalTitle.textContent = "Create Room";
      this.modalLabel1.textContent = "ROOM NAME";
      this.modalField2.classList.remove("hidden");
    } else {
      this.modalTitle.textContent = "Join Room";
      this.modalLabel1.textContent = "INVITE CODE";
      this.modalField2.classList.add("hidden");
    }
  }

  closeModal() {
    this.roomModal.classList.add("hidden");
  }

  handleModalSubmit() {
    const val1 = this.modalInput1.value.trim();
    const val2 = this.modalInput2.value.trim();

    if (!val1) return;

    if (this.currentModalMode === "create") {
      this.app.network.sendPacket("create_room", { name: val1, topic: val2 });
    } else {
      this.app.network.sendPacket("join_room", { invite_code: val1 });
    }
  }

  renderRooms(rooms) {
    this.roomsList.innerHTML = "";
    rooms.forEach((room) => {
      const div = document.createElement("div");
      div.className = `room-item ${this.activeChatId === room.id ? "active" : ""}`;
      div.innerHTML = `<span># ${room.name}</span>`;
      div.addEventListener("click", () =>
        this.switchChannel("room", room.id, `# ${room.name}`),
      );
      this.roomsList.appendChild(div);
    });
  }

  renderDMs(conversations) {
    this.dmsList.innerHTML = "";
    conversations.forEach((dm) => {
      const div = document.createElement("div");
      div.className = `dm-item ${this.activeChatId === dm.user_id ? "active" : ""}`;

      let badgeHtml =
        dm.unread_count > 0
          ? `<span class="unread-badge">${dm.unread_count}</span>`
          : "";

      div.innerHTML = `
                <div>
                    <span>${dm.display_name}</span>
                    <span class="dm-preview">${dm.last_message || ""}</span>
                </div>
                ${badgeHtml}
            `;
      div.addEventListener("click", () =>
        this.switchChannel("dm", dm.user_id, dm.display_name),
      );
      this.dmsList.appendChild(div);
    });
  }

  switchChannel(type, id, title) {
    this.activeChatType = type;
    this.activeChatId = id;
    this.chatHeader.textContent = title;
    this.chatLog.innerHTML = "";

    const items = document.querySelectorAll(".room-item, .dm-item");
    items.forEach((el) => el.classList.remove("active"));

    this.app.network.sendPacket("get_chat_history", {
      chat_type: type,
      target_id: id,
      limit: 50,
    });

    this.refreshSidebar();
  }

  sendMessage() {
    const text = this.entryBox.value.trim();
    if (!text || !this.activeChatId) return;

    this.app.network.sendPacket("send_message", {
      chat_type: this.activeChatType,
      target_id: this.activeChatId,
      content: text,
    });

    this.entryBox.value = "";
  }

  appendMessage(msg) {
    const isSelf = msg.sender.id === this.app.currentUser.id;
    const card = document.createElement("div");
    card.className = `message-card ${isSelf ? "self" : ""}`;
    card.setAttribute("data-msg-id", msg.id);

    let reactionsHtml = "";
    if (msg.reactions && msg.reactions.length > 0) {
      reactionsHtml = `<div class="reaction-bar">`;
      msg.reactions.forEach((r) => {
        reactionsHtml += `<span class="reaction-pill">${r.emoji} ${r.count}</span>`;
      });
      reactionsHtml += `</div>`;
    }

    card.innerHTML = `
            <div class="message-meta">
                <span class="sender">${msg.sender.display_name}</span>
                <span class="timestamp">${msg.created_at}</span>
            </div>
            <div class="message-content">${msg.content}</div>
            ${reactionsHtml}
        `;

    this.chatLog.appendChild(card);
    this.chatLog.scrollTop = this.chatLog.scrollHeight;
  }

  renderHistory(messages) {
    this.chatLog.innerHTML = "";
    messages.forEach((msg) => this.appendMessage(msg));
  }

  loadMoreHistory() {
    const firstMsg = this.chatLog.firstElementChild;
    if (!firstMsg) return;

    const beforeId = firstMsg.getAttribute("data-msg-id");
    this.app.network.sendPacket("get_chat_history", {
      chat_type: this.activeChatType,
      target_id: this.activeChatId,
      limit: 50,
      before_id: beforeId,
    });
  }

  incrementUnread(data) {
    this.refreshSidebar();
  }
}
