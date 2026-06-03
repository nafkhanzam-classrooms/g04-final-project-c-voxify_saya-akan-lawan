# Messages & Reactions API Contract

Endpoints for sending messages in rooms and managing reactions.

### 1. Send Message (Room)
- **URL:** `/api/v1/rooms/{room_id}/messages`
- **Method:** `POST`
- **Auth Required:** Yes
- **Request Body:**
  ```json
  {
    "content": "Hello everyone!",
    "file_metadata": null
  }
  ```
- **Response (201):**
  ```json
  {
    "status": "success",
    "data": {
      "id": "uuid",
      "room_id": "uuid",
      "content": "Hello everyone!",
      "created_at": "timestamp",
      "sender": {
        "id": "uuid",
        "username": "johndoe",
        "display_name": "John Doe",
        "avatar_url": null
      }
    }
  }
  ```

### 2. Add Reaction
- **URL:** `/api/v1/messages/{message_id}/reactions`
- **Method:** `POST`
- **Auth Required:** Yes
- **Request Body:**
  ```json
  {
    "emoji": "👍"
  }
  ```
- **Response (200):**
  ```json
  {
    "status": "success",
    "data": {
      "id": "uuid",
      "emoji": "👍",
      "user_id": "uuid"
    }
  }
  ```

### 3. Remove Reaction
- **URL:** `/api/v1/messages/{message_id}/reactions/{emoji}`
- **Method:** `DELETE`
- **Auth Required:** Yes
- **Response (200):**
  ```json
  {
    "status": "success",
    "message": "Reaction removed"
  }
  ```
