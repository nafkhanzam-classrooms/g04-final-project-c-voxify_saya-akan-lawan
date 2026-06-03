# Auth API Contract

Endpoints for user authentication and account management.

### 1. Register
- **URL:** `/api/v1/auth/register`
- **Method:** `POST`
- **Auth Required:** No
- **Request Body:**
  ```json
  {
    "username": "johndoe",
    "email": "john@example.com",
    "password": "strongpassword123",
    "display_name": "John Doe"
  }
  ```
- **Response (201):**
  ```json
  {
    "status": "success",
    "data": {
      "user_id": "uuid",
      "username": "johndoe",
      "email": "john@example.com"
    }
  }
  ```

### 2. Login
- **URL:** `/api/v1/auth/login`
- **Method:** `POST`
- **Auth Required:** No
- **Request Body:**
  ```json
  {
    "username": "johndoe",
    "password": "strongpassword123"
  }
  ```
- **Response (200):**
  ```json
  {
    "status": "success",
    "data": {
      "access_token": "jwt_token_here",
      "token_type": "bearer",
      "user": {
        "id": "uuid",
        "username": "johndoe",
        "display_name": "John Doe"
      }
    }
  }
  ```

### 3. Get Current User
- **URL:** `/api/v1/auth/me`
- **Method:** `GET`
- **Auth Required:** Yes
- **Response (200):**
  ```json
  {
    "status": "success",
    "data": {
      "id": "uuid",
      "username": "johndoe",
      "email": "john@example.com",
      "display_name": "John Doe",
      "avatar_url": null,
      "is_online": true
    }
  }
  ```
