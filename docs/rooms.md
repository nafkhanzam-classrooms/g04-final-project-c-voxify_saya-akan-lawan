# Rooms API Contract

Endpoints for managing chat rooms and memberships.

### 1. Create Room
- **URL:** `/api/v1/rooms`
- **Method:** `POST`
- **Auth Required:** Yes
- **Request Body:**
  ```json
  {
    "name": "General Chat",
    "topic": "Anything and everything"
  }
  ```
- **Response (201):**
  ```json
  {
    "status": "success",
    "data": {
      "id": "uuid",
      "name": "General Chat",
      "invite_code": "ABC-123"
    }
  }
  ```

### 2. List Rooms (Joined)
- **URL:** `/api/v1/rooms`
- **Method:** `GET`
- **Auth Required:** Yes
- **Response (200):**
  ```json
  {
    "status": "success",
    "data": [
      {
        "id": "uuid",
        "name": "General Chat",
        "topic": "Anything and everything",
        "is_active": true
      }
    ]
  }
  ```

### 3. Join Room
- **URL:** `/api/v1/rooms/join`
- **Method:** `POST`
- **Auth Required:** Yes
- **Request Body:**
  ```json
  {
    "invite_code": "ABC-123"
  }
  ```
- **Response (200):**
  ```json
  {
    "status": "success",
    "message": "Joined room successfully"
  }
  ```

### 4. Get Room Messages
- **URL:** `/api/v1/rooms/{room_id}/messages`
- **Method:** `GET`
- **Auth Required:** Yes
- **Query Params:** `limit` (default 50), `before_id` (for pagination)
- **Response (200):**
  ```json
  {
    "status": "success",
    "data": [
      {
        "id": "uuid",
        "content": "Hello world!",
        "created_at": "2023-12-12T16:39:00Z",
        "sender": {
          "id": "uuid",
          "username": "ashtrath",
          "display_name": "ashtrath.",
          "avatar_url": "https://example.com/avatar.png"
        },
        "reactions": [
          {
            "emoji": "💀",
            "count": 2,
            "me": true
          }
        ]
      }
    ]
  }
  ```
