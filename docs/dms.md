# Direct Messages API Contract

Endpoints for one-on-one private messaging.

### 1. Send DM
- **URL:** `/api/v1/dms`
- **Method:** `POST`
- **Auth Required:** Yes
- **Request Body:**
  ```json
  {
    "receiver_id": "uuid",
    "content": "Hey, how are you?",
    "file_metadata": null
  }
  ```
- **Response (201):**
  ```json
  {
    "status": "success",
    "data": {
      "id": "uuid",
      "content": "Hey, how are you?",
      "created_at": "timestamp",
      "sender": {
        "id": "uuid",
        "username": "johndoe",
        "display_name": "John Doe",
        "avatar_url": null
      },
      "receiver_id": "uuid"
    }
  }
  ```

### 2. List DM Conversations
- **URL:** `/api/v1/dms/conversations`
- **Method:** `GET`
- **Auth Required:** Yes
- **Response (200):**
  ```json
  {
    "status": "success",
    "data": [
      {
        "user_id": "uuid",
        "username": "janedoe",
        "display_name": "Jane Doe",
        "avatar_url": "https://example.com/jane.png",
        "last_message": "Hey, how are you?",
        "unread_count": 1,
        "last_message_at": "timestamp"
      }
    ]
  }
  ```

### 3. Get DM Messages
- **URL:** `/api/v1/dms/{other_user_id}`
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
        "content": "Hey, how are you?",
        "is_read": true,
        "created_at": "timestamp",
        "sender": {
          "id": "uuid",
          "username": "janedoe",
          "display_name": "Jane Doe",
          "avatar_url": "https://example.com/jane.png"
        }
      }
    ]
  }
  ```
