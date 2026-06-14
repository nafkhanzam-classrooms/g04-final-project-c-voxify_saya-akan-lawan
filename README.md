[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/90Mprfp5)

# Network Programming - Final Project [G04]

## Anggota Kelompok

| Nama                   | NRP        | Kelas |
| ---------------------- | ---------- | ----- |
| Hamzah Ali Abdillah    | 5025241023 | C     |
| Danish Faiq Ibad Yuadi | 5025241038 | C     |

## Link Youtube (Unlisted)

Link ditaruh di bawah ini

```
https://youtu.be/nS3RKiD3e0s
```

## Penjelasan Program

### Nama Aplikasi

Voxify merupakan aplikasi pesan real-time berbasis TCP socket yang mendukung text room grup maupun direct message (DM) privat antar pengguna.

### Deskripsi Singkat

Voxify dibangun dengan arsitektur berlapis:

```
Browser (JS)  <-- WebSocket --> Bridge (:8080) <-- Raw TCP --> Server (:8000) <-- async --> PostgreSQL
```

Backend ditulis Python (SQLAlchemy async + asyncpg + PostgreSQL), frontend HTML/CSS/JS vanilla (ES Modules), tanpa framework tambahan.

### Fitur Utama

- **Text Rooms**: Saluran obrolan grup, dibuat atau diikuti via invite code unik.
- **Direct Messages**: Percakapan privat 1-on-1 antar pengguna terdaftar.
- **Emoji Reactions**: Reaksi emoji pada pesan, disinkronkan real-time ke seluruh anggota room.
- **Presence System**: Status online/offline di-broadcast secara global saat connect/disconnect.
- **Chat History**: Scroll ke atas untuk memuat pesan lebih lama.

### Alur Aplikasi

1. **Login / Register**: Pengguna mendaftar dengan username, email, display name, dan password. Token JWT disimpan di localStorage setelah login berhasil.
2. **Dashboard**: Sidebar kiri menampilkan daftar Text Rooms dan DM aktif (dengan unread badge). Chat pane kanan menampilkan log pesan dan input box.
3. **Text Room**: Pengguna membuat room baru atau join via invite code. Riwayat 50 pesan terakhir dimuat otomatis. Pesan baru dari anggota lain muncul real-time.
4. **Direct Message**: Klik nama pengguna di sidebar DM untuk membuka percakapan privat. Badge unread muncul otomatis untuk pesan yang belum dibaca.
5. **Reactions**: Reaction bar muncul di bawah pesan. Perubahan reaksi disinkronkan ke seluruh anggota room via event `reaction_update`.

### Arsitektur dan Protokol

#### Protokol Framing

Setiap pesan antara Bridge dan TCP Server menggunakan format **length-prefixed JSON**:

```
[ 4 Bytes Header (Big-Endian uint) ][ JSON Payload (UTF-8, maks 1 MB) ]
```

Setiap paket dari client menyertakan:

```json
{
  "action": "nama.action",
  "data": { ... },
  "token": "jwt_token_atau_null"
}
```

Setiap respons dari server menyertakan:

```json
{
  "status": "success" | "error",
  "action": "nama.action",
  "data": { ... },
  "message": "pesan opsional"
}
```

#### Daftar Action Protocol

| Action             | Arah  | Deskripsi                                                                 |
| ------------------ | ----- | ------------------------------------------------------------------------- |
| `auth.register`    | C → S | Daftarkan akun baru (username, email, password, display_name)             |
| `auth.login`       | C → S | Login user, mengembalikan JWT dan data user                               |
| `room.create`      | C → S | Buat room baru (name, topic), server generate invite_code unik            |
| `room.join`        | C → S | Bergabung ke room via invite_code                                         |
| `room.list`        | C → S | Ambil daftar room yang diikuti user                                       |
| `room.leave`       | C → S | Keluar dari room (owner tidak bisa leave)                                 |
| `room.members`     | C → S | Ambil daftar member dalam suatu room                                      |
| `message.send`     | C → S | Kirim pesan ke room, server broadcast `new_message` ke semua member aktif |
| `message.history`  | C → S | Ambil riwayat pesan room (limit, before_id untuk pagination)              |
| `dm.send`          | C → S | Kirim DM ke user lain, server push `new_dm` ke receiver                   |
| `dm.conversations` | C → S | Daftar percakapan DM beserta last_message dan unread_count                |
| `dm.history`       | C → S | Ambil riwayat DM dengan user tertentu (pagination)                        |
| `reaction.add`     | C → S | Tambah reaksi emoji ke pesan, broadcast `reaction_update` ke room         |
| `reaction.remove`  | C → S | Hapus reaksi emoji, broadcast `reaction_update` ke room                   |
| `user.online_list` | C → S | Ambil daftar user yang sedang online                                      |
| `new_message`      | S → C | Push real-time: pesan baru di room aktif                                  |
| `new_dm`           | S → C | Push real-time: DM baru diterima                                          |
| `reaction_update`  | S → C | Push real-time: update reaksi pada suatu pesan                            |
| `user_presence`    | S → C | Broadcast global: status online/offline user                              |

Notes: C = Client, S = Server.

#### Komponen Server

| Komponen         | IP        | Port              |
| ---------------- | --------- | ----------------- |
| Client (Browser) | 127.0.0.1 | Random (otomatis) |
| WebSocket Bridge | 0.0.0.0   | 8080              |
| Raw TCP Server   | 0.0.0.0   | 8000              |
| PostgreSQL       | localhost | 5432 (default)    |

**Client (Browser)**
Tiga modul JS utama: `network.js` (WebSocket + routing), `auth.js` (login/register + token), `dashboard.js` (sidebar, chat log, modal, pagination, reactions).

**WebSocket Bridge (`bridge.py`)**
Menerima koneksi WebSocket dari browser pada port 8080, meneruskan ke TCP Server port 8000. Setiap koneksi WS memiliki satu koneksi TCP tersendiri. Relay dua arah berjalan concurrent via `asyncio.gather`.

**Raw TCP Server (`server.py`)**

### Cara Menjalankan

**Prasyarat:** Python 3.13+, `uv`, PostgreSQL aktif.

```bash
# 1. Clone repo dan masuk ke direktori backend
cd backend

# 2. Buat .env dari .env.example, isi DATABASE_URL
cp .env.example .env

# 3. Install dependensi
uv sync

# 4. Migrasi database
uv run alembic upgrade head

# 5. Jalankan TCP Server
uv run python server.py

# 6. Jalankan WebSocket Bridge (terminal baru)
uv run python bridge.py

# 7. Buka frontend/index.html di browser
```

Untuk pengujian langsung ke TCP server tanpa bridge:

```
uv run python test_tcp.py
```

## Screenshot Hasil
