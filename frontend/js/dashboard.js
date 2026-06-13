export class DashboardModule {
  constructor(appController) {
    this.app = appController;
    this.userDisplayTag = document.getElementById("user-display-tag");
    this.roomsList = document.getElementById("rooms-list");
    this.dmsList = document.getElementById("dms-list");
    this.onlineUsersList = document.getElementById("online-users-list");
    this.onlineCount = document.getElementById("online-count");
    this.chatLog = document.getElementById("chat-log");
    this.chatHeaderTitle = document.getElementById("chat-header-title");
    this.entryBox = document.getElementById("entry-box");
    this.btnSend = document.getElementById("btn-send");
    this.btnLogout = document.getElementById("btn-logout");
    this.actionCreateRoom = document.getElementById("action-create-room");
    this.actionJoinRoom = document.getElementById("action-join-room");

    // Chat header actions
    this.btnShowInvite = document.getElementById("btn-show-invite");
    this.btnShowMembers = document.getElementById("btn-show-members");
    this.btnLeaveRoom = document.getElementById("btn-leave-room");

    // Right panel
    this.rightPanel = document.getElementById("right-panel");
    this.rightPanelTitle = document.getElementById("right-panel-title");
    this.rightPanelBody = document.getElementById("right-panel-body");
    this.btnCloseRightPanel = document.getElementById("btn-close-right-panel");

    // Room modal
    this.roomModal = document.getElementById("room-modal");
    this.modalTitle = document.getElementById("modal-title");
    this.modalLabel1 = document.getElementById("modal-label-1");
    this.modalInput1 = document.getElementById("modal-input-1");
    this.modalInput2 = document.getElementById("modal-input-2");
    this.modalField2 = document.getElementById("modal-field-2");
    this.modalInviteResult = document.getElementById("modal-invite-result");
    this.modalInviteCode = document.getElementById("modal-invite-code");
    this.btnCopyInvite = document.getElementById("btn-copy-invite");
    this.btnModalCancel = document.getElementById("btn-modal-cancel");
    this.btnModalSubmit = document.getElementById("btn-modal-submit");

    // Emoji picker
    this.emojiPicker = document.getElementById("emoji-picker");
    this._emojiTargetMsgId = null;

    this.activeChatType = null;
    this.activeChatId = null;
    this.activeRoomData = null; // stores the full room object for invite code etc.
    this.currentModalMode = null;
    this._currentSocketRoom = null;
    this._roomsCache = []; // cache room.list data for invite code lookups

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
      if (this.chatLog.scrollTop === 0) this.loadMoreHistory();
    });
    this.btnCopyInvite.addEventListener("click", () =>
      this.copyInviteCode(this.modalInviteCode.textContent),
    );

    // Chat header actions
    this.btnShowInvite.addEventListener("click", () => this.showInvitePanel());
    this.btnShowMembers.addEventListener("click", () =>
      this.showMembersPanel(),
    );
    this.btnLeaveRoom.addEventListener("click", () => this.leaveCurrentRoom());
    this.btnCloseRightPanel.addEventListener("click", () =>
      this.closeRightPanel(),
    );

    // Logout
    this.btnLogout.addEventListener("click", () => {
      localStorage.removeItem("voxify_token");
      location.reload();
    });

    // Emoji picker — close on outside click
    document.addEventListener("click", (e) => {
      if (
        !this.emojiPicker.contains(e.target) &&
        !e.target.classList.contains("reaction-add-btn")
      ) {
        this.emojiPicker.classList.add("hidden");
      }
    });

    // Emoji option clicks
    this.emojiPicker.querySelectorAll(".emoji-option").forEach((el) => {
      el.addEventListener("click", () => {
        if (this._emojiTargetMsgId) {
          this.app.network.sendPacket("reaction.add", {
            message_id: this._emojiTargetMsgId,
            emoji: el.dataset.emoji,
          });
          this.emojiPicker.classList.add("hidden");
        }
      });
    });
  }

  initNetwork() {
    this.app.network.registerHandler("new_message", (packet) => {
      if (this.activeChatId === packet.room_id) {
        this.appendMessage(packet.message);
      } else {
        this.refreshSidebar();
      }
    });

    this.app.network.registerHandler("new_dm", (packet) => {
      const msg = packet.message;
      if (
        this.activeChatId === msg.sender.id ||
        this.activeChatId === msg.receiver_id
      ) {
        this.appendMessage(msg);
      } else {
        this.refreshSidebar();
      }
    });

    this.app.network.registerHandler("room.create", (packet) => {
      if (packet.status === "success") {
        // Show invite code in the modal
        this.modalInviteResult.classList.remove("hidden");
        this.modalInviteCode.textContent = packet.data.invite_code;
        this.btnModalSubmit.classList.add("hidden");
        this.modalInput1.disabled = true;
        this.modalInput2.disabled = true;
        this.refreshSidebar();
      }
    });

    this.app.network.registerHandler("room.join", (packet) => {
      if (packet.status === "success") {
        this.closeModal();
        this.refreshSidebar();
      }
    });

    this.app.network.registerHandler("room.list", (packet) => {
      this._roomsCache = packet.data || [];
      this.renderRooms(this._roomsCache);
    });

    this.app.network.registerHandler("dm.conversations", (packet) =>
      this.renderDMs(packet.data),
    );
    this.app.network.registerHandler("message.history", (packet) =>
      this.renderHistory(packet.data),
    );
    this.app.network.registerHandler("dm.history", (packet) =>
      this.renderHistory(packet.data),
    );

    // Online user list
    this.app.network.registerHandler("user.online_list", (packet) => {
      if (packet.status === "success") {
        this.renderOnlineUsers(packet.data);
      }
    });

    // User presence broadcast (real-time online/offline)
    this.app.network.registerHandler("user_presence", (packet) => {
      // Refresh the online list whenever someone comes online or goes offline
      this.app.network.sendPacket("user.online_list");
    });

    // Room members
    this.app.network.registerHandler("room.members", (packet) => {
      if (packet.status === "success") {
        this.renderMembersPanel(packet.data);
      }
    });

    // Room leave
    this.app.network.registerHandler("room.leave", (packet) => {
      if (packet.status === "success") {
        this.activeChatType = null;
        this.activeChatId = null;
        this.activeRoomData = null;
        this.chatHeaderTitle.textContent = "# select-a-channel";
        this.chatLog.innerHTML = "";
        this.updateChatHeaderActions();
        this.closeRightPanel();
        this.refreshSidebar();
      } else {
        alert(packet.message || "Cannot leave room.");
      }
    });

    // Real-time reaction broadcast from server (received by ALL room members)
    this.app.network.registerHandler("reaction_update", (packet) => {
      this.patchReactionBar(packet.message_id, packet.reactions);
    });

    // reaction.add / reaction.remove: only the sender gets these responses.
    // The broadcast via reaction_update handles everyone else, so no reload needed.
    this.app.network.registerHandler("reaction.add", (_packet) => {});
    this.app.network.registerHandler("reaction.remove", (_packet) => {});
  }

  setupUserTag() {
    this.userDisplayTag.textContent = `🟢 ${this.app.currentUser.display_name}`;
  }

  refreshSidebar() {
    this.app.network.sendPacket("room.list");
    this.app.network.sendPacket("dm.conversations");
    this.app.network.sendPacket("user.online_list");
  }

  /* ═══════ MODAL ═══════ */

  openModal(mode) {
    this.currentModalMode = mode;
    this.roomModal.classList.remove("hidden");
    this.modalInput1.value = "";
    this.modalInput2.value = "";
    this.modalInput1.disabled = false;
    this.modalInput2.disabled = false;
    this.modalInviteResult.classList.add("hidden");
    this.btnModalSubmit.classList.remove("hidden");

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
    this.modalInviteResult.classList.add("hidden");
    this.btnModalSubmit.classList.remove("hidden");
    this.modalInput1.disabled = false;
    this.modalInput2.disabled = false;
  }

  handleModalSubmit() {
    const val1 = this.modalInput1.value.trim();
    const val2 = this.modalInput2.value.trim();
    if (!val1) return;

    if (this.currentModalMode === "create") {
      this.app.network.sendPacket("room.create", { name: val1, topic: val2 });
    } else {
      this.app.network.sendPacket("room.join", { invite_code: val1 });
    }
  }

  copyInviteCode(code) {
    navigator.clipboard.writeText(code).then(() => {
      this.btnCopyInvite.textContent = "✅";
      setTimeout(() => (this.btnCopyInvite.textContent = "📋"), 1500);
    });
  }

  /* ═══════ RENDER SIDEBAR ═══════ */

  renderRooms(rooms) {
    this.roomsList.innerHTML = "";
    rooms.forEach((room) => {
      const div = document.createElement("div");
      div.className = `room-item ${this.activeChatId === room.id ? "active" : ""}`;
      div.innerHTML = `
        <span># ${room.name}</span>
        <span class="room-invite-tag" title="Click to copy invite code">${room.invite_code}</span>
      `;
      // Click on name -> switch channel
      div.addEventListener("click", (e) => {
        if (e.target.classList.contains("room-invite-tag")) {
          e.stopPropagation();
          this.copyInviteCode(room.invite_code);
          e.target.textContent = "Copied!";
          setTimeout(() => (e.target.textContent = room.invite_code), 1200);
          return;
        }
        this.activeRoomData = room;
        this.switchChannel("room", room.id, `# ${room.name}`);
      });
      this.roomsList.appendChild(div);
    });
  }

  renderDMs(conversations) {
    this.dmsList.innerHTML = "";
    conversations.forEach((dm) => {
      const div = document.createElement("div");
      div.className = `dm-item ${this.activeChatId === dm.other_user.id ? "active" : ""}`;
      let badgeHtml =
        dm.unread_count > 0
          ? `<span class="unread-badge">${dm.unread_count}</span>`
          : "";

      div.innerHTML = `
        <div>
          <span>${dm.other_user.display_name || dm.other_user.username}</span>
          <span class="dm-preview">${dm.last_message || ""}</span>
        </div>
        ${badgeHtml}
      `;
      div.addEventListener("click", () =>
        this.switchChannel(
          "dm",
          dm.other_user.id,
          dm.other_user.display_name || dm.other_user.username,
        ),
      );
      this.dmsList.appendChild(div);
    });
  }

  renderOnlineUsers(users) {
    this.onlineUsersList.innerHTML = "";
    this.onlineCount.textContent = users.length;
    users.forEach((user) => {
      // Don't show self in the list
      if (user.id === this.app.currentUser?.id) return;
      const div = document.createElement("div");
      div.className = "online-user-item";
      div.innerHTML = `
        <span class="online-dot"></span>
        <span>${user.display_name || user.username}</span>
      `;
      // Click to start DM
      div.addEventListener("click", () => {
        this.switchChannel(
          "dm",
          user.id,
          user.display_name || user.username,
        );
      });
      this.onlineUsersList.appendChild(div);
    });
  }

  /* ═══════ CHANNEL SWITCHING ═══════ */

  switchChannel(type, id, title) {
    // Leave previous room socket if any
    if (this._currentSocketRoom) {
      this.app.network.sendPacket("room.leave_socket", {
        room_id: this._currentSocketRoom,
      });
      this._currentSocketRoom = null;
    }

    this.activeChatType = type;
    this.activeChatId = id;
    this.chatHeaderTitle.textContent = title;
    this.chatLog.innerHTML = "";
    this.closeRightPanel();

    const items = document.querySelectorAll(".room-item, .dm-item");
    items.forEach((el) => el.classList.remove("active"));

    if (type === "room") {
      // Find room data from cache
      this.activeRoomData =
        this._roomsCache.find((r) => r.id === id) || this.activeRoomData;
      // Join room socket for real-time broadcasts
      this.app.network.sendPacket("room.join_socket", { room_id: id });
      this._currentSocketRoom = id;
      this.app.network.sendPacket("message.history", {
        room_id: id,
        limit: 50,
        before_id: null,
      });
    } else {
      this.activeRoomData = null;
      this.app.network.sendPacket("dm.history", {
        other_user_id: id,
        limit: 50,
        before_id: null,
      });
    }

    this.updateChatHeaderActions();
    this.refreshSidebar();
  }

  updateChatHeaderActions() {
    if (this.activeChatType === "room") {
      this.btnShowInvite.classList.remove("hidden");
      this.btnShowMembers.classList.remove("hidden");
      this.btnLeaveRoom.classList.remove("hidden");
    } else {
      this.btnShowInvite.classList.add("hidden");
      this.btnShowMembers.classList.add("hidden");
      this.btnLeaveRoom.classList.add("hidden");
    }
  }

  /* ═══════ RIGHT PANEL ═══════ */

  showInvitePanel() {
    const room = this.activeRoomData;
    if (!room) return;
    this.rightPanelTitle.textContent = "Invite Code";
    this.rightPanelBody.innerHTML = `
      <div class="invite-code-block">
        <label>SHARE THIS CODE</label>
        <code>${room.invite_code}</code>
        <button class="btn-copy" id="btn-copy-panel-invite">📋 Copy Code</button>
        <p>Others can join by entering this code</p>
      </div>
    `;
    this.rightPanel.classList.remove("hidden");
    document
      .getElementById("btn-copy-panel-invite")
      .addEventListener("click", (e) => {
        this.copyInviteCode(room.invite_code);
        e.target.textContent = "✅ Copied!";
        setTimeout(() => (e.target.textContent = "📋 Copy Code"), 1500);
      });
  }

  showMembersPanel() {
    if (!this.activeChatId || this.activeChatType !== "room") return;
    this.rightPanelTitle.textContent = "Members";
    this.rightPanelBody.innerHTML = `<div style="color:var(--text-muted);font-size:13px;">Loading...</div>`;
    this.rightPanel.classList.remove("hidden");
    this.app.network.sendPacket("room.members", {
      room_id: this.activeChatId,
    });
  }

  renderMembersPanel(members) {
    this.rightPanelBody.innerHTML = "";
    members.forEach((m) => {
      const div = document.createElement("div");
      div.className = "member-item";
      div.innerHTML = `
        <span class="online-dot"></span>
        <span>${m.user_id}</span>
        <span class="member-role">${m.role}</span>
      `;
      this.rightPanelBody.appendChild(div);
    });
    if (members.length === 0) {
      this.rightPanelBody.innerHTML = `<div style="color:var(--text-muted);font-size:13px;">No members found.</div>`;
    }
  }

  closeRightPanel() {
    this.rightPanel.classList.add("hidden");
  }

  leaveCurrentRoom() {
    if (!this.activeChatId || this.activeChatType !== "room") return;
    if (!confirm("Leave this room?")) return;
    this.app.network.sendPacket("room.leave", {
      room_id: this.activeChatId,
    });
  }

  /* ═══════ MESSAGING ═══════ */

  sendMessage() {
    const text = this.entryBox.value.trim();
    if (!text || !this.activeChatId) return;

    if (this.activeChatType === "room") {
      this.app.network.sendPacket("message.send", {
        room_id: this.activeChatId,
        message: {
          content: text,
          file_metadata: null,
        },
      });
    } else {
      this.app.network.sendPacket("dm.send", {
        receiver_id: this.activeChatId,
        content: text,
        file_metadata: null,
      });
    }
    this.entryBox.value = "";
  }

  createMessageCard(msg) {
    const isSelf = msg.sender.id === this.app.currentUser.id;
    const card = document.createElement("div");
    card.className = `message-card ${isSelf ? "self" : ""}`;
    card.setAttribute("data-msg-id", msg.id);

    // Reaction bar
    let reactionsHtml = "";
    if (msg.reactions && msg.reactions.length > 0) {
      reactionsHtml = `<div class="reaction-bar">`;
      msg.reactions.forEach((r) => {
        reactionsHtml += `<span class="reaction-pill" data-emoji="${r.emoji}" data-msg-id="${msg.id}">${r.emoji} ${r.count}</span>`;
      });
      reactionsHtml += `</div>`;
    }

    card.innerHTML = `
      <button class="reaction-add-btn" data-msg-id="${msg.id}" title="Add Reaction">😀</button>
      <div class="message-meta">
        <span class="sender">${msg.sender.display_name}</span>
        <span class="timestamp">${this.formatTimestamp(msg.created_at)}</span>
      </div>
      <div class="message-content">${this.escapeHtml(msg.content)}</div>
      ${reactionsHtml}
    `;

    // Emoji add button
    card.querySelector(".reaction-add-btn").addEventListener("click", (e) => {
      e.stopPropagation();
      this.openEmojiPicker(e.target, msg.id);
    });

    // Click on existing reaction pill to toggle (add or remove)
    card.querySelectorAll(".reaction-pill").forEach((pill) => {
      pill.addEventListener("click", () => {
        const emoji = pill.dataset.emoji;
        const msgId = pill.dataset.msgId;
        if (pill.classList.contains("active")) {
          this.app.network.sendPacket("reaction.remove", {
            message_id: msgId,
            emoji: emoji,
          });
        } else {
          this.app.network.sendPacket("reaction.add", {
            message_id: msgId,
            emoji: emoji,
          });
        }
      });
    });

    return card;
  }

  appendMessage(msg) {
    const card = this.createMessageCard(msg);
    this.chatLog.appendChild(card);
    this.chatLog.scrollTop = this.chatLog.scrollHeight;
  }

  renderHistory(messages) {
    if (!messages || messages.length === 0) {
      if (this.chatLog.innerHTML.includes("Loading history...")) {
        this.chatLog.innerHTML = "";
      }
      return;
    }

    const isInitialLoad = this.chatLog.innerHTML.includes("Loading history...");
    if (isInitialLoad) {
      this.chatLog.innerHTML = "";
      // Initial load: server returns descending (newest first).
      // We want chronological order (oldest to newest), so we reverse and append.
      const chronological = [...messages].reverse();
      chronological.forEach((msg) => this.appendMessage(msg));
    } else {
      // Pagination load: prepend descending messages one by one.
      // This will place the oldest at the very top.
      const oldScrollHeight = this.chatLog.scrollHeight;
      messages.forEach((msg) => {
        const card = this.createMessageCard(msg);
        this.chatLog.prepend(card);
      });
      // Restore scroll position so it doesn't jump to the top
      this.chatLog.scrollTop = this.chatLog.scrollHeight - oldScrollHeight;
    }
  }

  loadMoreHistory() {
    const firstMsg = this.chatLog.firstElementChild;
    if (!firstMsg) return;
    const beforeId = firstMsg.getAttribute("data-msg-id");
    if (this.activeChatType === "room") {
      this.app.network.sendPacket("message.history", {
        room_id: this.activeChatId,
        limit: 50,
        before_id: beforeId,
      });
    } else {
      this.app.network.sendPacket("dm.history", {
        other_user_id: this.activeChatId,
        limit: 50,
        before_id: beforeId,
      });
    }
  }

  /**
   * Surgically update the reaction bar of a single message card.
   * Called when a `reaction_update` broadcast is received — no full reload needed.
   */
  patchReactionBar(messageId, reactions) {
    const card = this.chatLog.querySelector(`[data-msg-id="${messageId}"]`);
    if (!card) return; // Message not currently visible

    // Remove existing reaction bar
    const existing = card.querySelector(".reaction-bar");
    if (existing) existing.remove();

    if (!reactions || reactions.length === 0) return;

    const bar = document.createElement("div");
    bar.className = "reaction-bar";

    reactions.forEach((r) => {
      const pill = document.createElement("span");
      pill.className = "reaction-pill";
      pill.dataset.emoji = r.emoji;
      pill.dataset.msgId = messageId;
      pill.textContent = `${r.emoji} ${r.count}`;
      if (r.me) pill.classList.add("active");

      pill.addEventListener("click", () => {
        if (pill.classList.contains("active")) {
          this.app.network.sendPacket("reaction.remove", {
            message_id: messageId,
            emoji: r.emoji,
          });
        } else {
          this.app.network.sendPacket("reaction.add", {
            message_id: messageId,
            emoji: r.emoji,
          });
        }
      });

      bar.appendChild(pill);
    });

    card.appendChild(bar);
  }

  /* ═══════ EMOJI PICKER ═══════ */

  openEmojiPicker(anchorEl, msgId) {
    this._emojiTargetMsgId = msgId;
    const rect = anchorEl.getBoundingClientRect();
    this.emojiPicker.style.top = `${rect.bottom + 4}px`;
    this.emojiPicker.style.left = `${rect.left - 60}px`;
    this.emojiPicker.classList.remove("hidden");
  }

  /* ═══════ UTILS ═══════ */

  escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  formatTimestamp(ts) {
    if (!ts) return "";
    try {
      const date = new Date(ts);
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
      return ts;
    }
  }
}
