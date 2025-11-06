## Messaging API Integration Guide (FE-16OPS)

This guide provides frontend developers with the necessary information to run, integrate, and test the messaging API.

-----

## 1\. Running Locally (Environment Variables)

To run the backend service locally, create a `.env` file in the project's root directory with the following variables.

```sh
# Django Core
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (example for local Postgres)
DATABASE_URL=postgres://user:password@localhost:5432/messaging_db

# Frontend URL (for CORS)
CORS_ALLOWED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080

# WebSocket Channel Layer (for real-time updates)
REDIS_URL=redis://localhost:6379/1



## 2\. API Endpoints & `curl` Examples

All requests require an `Authorization: Token YOUR_AUTH_TOKEN` header, replacing `YOUR_AUTH_TOKEN` with the user's valid API token.

### A. List User's Conversations

Lists all conversations the user is a participant in, ordered by the most recent message.

  * **Endpoint:** `GET /api/messaging/conversations/`
  * **`curl` Example:**
    ```bash
    curl -X GET http://localhost:8000/api/messaging/conversations/ \
         -H "Authorization: Token YOUR_AUTH_TOKEN"
    ```
  * **Sample Response:**
    ```json
    {
      "success": true,
      "conversations": [
        {
          "id": 1,
          "title": "Chat with User B",
          "participants": [/* user objects */],
          "last_message": {
            "content": "Hello again",
            "sender_id": 1,
            "created_at": "2025-10-22T14:30:00Z"
          },
          "unread_count": 0
        }
      ]
    }
    ```

### B. Start a New Conversation

Creates a new conversation with a specific user, optionally about a product and with an initial message. If a 1-on-1 chat with this user already exists, it returns the existing conversation.

  * **Endpoint:** `POST /api/messaging/start-conversation/`
  * **`curl` Example:**
    ```bash
    curl -X POST http://localhost:8000/api/messaging/start-conversation/ \
         -H "Authorization: Token YOUR_AUTH_TOKEN" \
         -H "Content-Type: application/json" \
         -d '{"receiver_id": 2, "message": "Hi, is this product still available?", "product_id": 123}'
    ```
  * **Sample Response (Success):**
    ```json
    {
      "success": true,
      "message": "Conversation started successfully",
      "conversation": {
        "id": 2,
        "title": "Chat with User B",
        "participants": [/* user objects */],
        "related_product": 123
        /* ...etc */
      }
    }
    ```

### C. Get Conversation Details & Messages

Retrieves details for a single conversation and its messages, with pagination.

  * **Endpoint:** `GET /api/messaging/conversations/<int:conversation_id>/`
  * **`curl` Example (getting page 1):**
    ```bash
    curl -X GET "http://localhost:8000/api/messaging/conversations/1/?page=1" \
         -H "Authorization: Token YOUR_AUTH_TOKEN"
    ```
  * **Sample Response:**
    ```json
    {
      "count": 55,
      "next": "http://localhost:8000/api/messaging/conversations/1/?page=2",
      "previous": null,
      "success": true,
      "conversation": {
        "id": 1,
        "title": "Chat with User B"
        /* ...etc */
      },
      "messages": [
        {
          "id": 101,
          "sender": { "id": 1, "username": "User A" },
          "content": "Hello again",
          "created_at": "2025-10-22T14:30:00Z",
          "is_edited": false,
          "reactions": []
        }
        /* ...other messages */
      ]
    }
    ```

### D. Send a Message

Sends a new text message to an existing conversation.

  * **Endpoint:** `POST /api/messaging/conversations/<int:conversation_id>/messages/`
  * **`curl` Example:**
    ```bash
    curl -X POST http://localhost:8000/api/messaging/conversations/1/messages/ \
         -H "Authorization: Token YOUR_AUTH_TOKEN" \
         -H "Content-Type: application/json" \
         -d '{"content": "This is a new message"}'
    ```
  * **Sample Response (Success):**
    ```json
    {
      "success": true,
      "message": {
        "id": 102,
        "sender": { "id": 1, "username": "User A" },
        "content": "This is a new message",
        "message_type": "text",
        "created_at": "2025-10-22T14:35:00Z"
        /* ...etc */
      }
    }
    ```

### E. Mark Messages as Read

Marks all unread messages *from other users* in a conversation as read by the current user.

  * **Endpoint:** `POST /api/messaging/conversations/<int:conversation_id>/read/`
  * **`curl` Example:**
    ```bash
    curl -X POST http://localhost:8000/api/messaging/conversations/1/read/ \
         -H "Authorization: Token YOUR_AUTH_TOKEN" \
         -H "Content-Type: application/json" \
         -d ''
    ```
  * **Sample Response:**
    ```json
    {
      "success": true,
      "message": "Marked 3 messages as read"
    }
    ```

### F. React to a Message

Adds, updates, or removes a reaction to a specific message.

  * **Endpoint:** `POST /api/messaging/messages/<int:message_id>/react/`
  * **`curl` Example (Adding a 'like' reaction):**
    ```bash
    curl -X POST http://localhost:8000/api/messaging/messages/102/react/ \
         -H "Authorization: Token YOUR_AUTH_TOKEN" \
         -H "Content-Type: application/json" \
         -d '{"reaction_type": "👍"}'
    ```
  * **Sample Response (Added):**
    ```json
    {
      "success": true,
      "message": "Reaction added",
      "reacted": true,
      "reaction_type": "👍"
    }
    ```
  * **Note:** Sending the same `reaction_type` again will remove the reaction (`"message": "Reaction removed"`).

-----

## 3\. WebSocket Authentication

Real-time updates are pushed to clients via WebSockets. Authentication is handled by passing the user's API token as a query parameter upon connection.

  * **WebSocket URL:** `ws://localhost:8000/ws/messaging/`
  * **Connection URL (with auth):** `ws://localhost:8000/ws/messaging/?token=YOUR_AUTH_TOKEN`

### Frontend JavaScript Example

```javascript
const authToken = "YOUR_AUTH_TOKEN"; // Get this from user's session/storage
const chatSocket = new WebSocket(
  `ws://localhost:8000/ws/messaging/?token=${authToken}`
);

chatSocket.onopen = function (e) {
  console.log("Chat socket connected successfully!");
};

chatSocket.onmessage = function (e) {
  const data = JSON.parse(e.data);
  console.log("Received data:", data);

  // Handle different event types from the backend
  switch (data.type) {
    case 'new_message':
      // data.message will contain the new message object
      console.log("New message received:", data.message);
      // Add message to the UI
      break;
    case 'message_edited':
      // data.message will contain the updated message object
      console.log("Message edited:", data.message);
      // Find and update the message in the UI
      break;
    case 'message_deleted':
      // data.message_id will contain the ID of the deleted message
      console.log("Message deleted:", data.message_id);
      // Remove the message from the UI
      break;
    case 'reaction_updated':
      // data.reaction will contain the reaction object
      console.log("Reaction updated:", data.reaction);
      // Update reactions on the corresponding message
      break;
    case 'read_receipt':
      // data.read_receipt contains info on user and message
      console.log("Message read:", data.read_receipt);
      // Update read status in the UI
      break;
  }
};

chatSocket.onclose = function (e) {
  console.error("Chat socket closed unexpectedly");
};

// To send a message (though POST API is standard)
// chatSocket.send(JSON.stringify({
//   'message': 'Hello from client!',
//   'conversation_id': 1
// }));
```

-----

## 4\. Pre-signed URL File Flow

To upload files (images, documents), a 3-step process is required to avoid proxying large files through the server.

### Step 1: Request an Upload URL from the Backend

The frontend asks the backend for a secure, one-time URL to upload the file to S3.

  * **Endpoint:** `POST /api/messaging/generate-upload-url/` (Note: This endpoint is not in the provided code but is the standard pattern required for this flow.)
  * **`curl` Example:**
    ```bash
    curl -X POST http://localhost:8000/api/messaging/generate-upload-url/ \
         -H "Authorization: Token YOUR_AUTH_TOKEN" \
         -H "Content-Type: application/json" \
         -d '{"filename": "my-cool-photo.jpg", "filetype": "image/jpeg"}'
    ```
  * **Sample Response:**
    ```json
    {
      "success": true,
      "upload_url": "https://your-s3-bucket.s3.amazonaws.com/uploads/my-cool-photo.jpg?AWSAccessKeyId=...",
      "file_key": "uploads/my-cool-photo-uuid.jpg" 
    }
    ```

### Step 2: Upload File Directly to S3 (Frontend)

The frontend uses the `upload_url` to send the file *directly* to S3 using an HTTP `PUT` request.

```javascript
// 'file' is the File object from an <input type="file">
// 'upload_url' is from the API response in Step 1
// 'filetype' is the 'image/jpeg' from Step 1

const response = await fetch(upload_url, {
  method: 'PUT',
  headers: {
    'Content-Type': filetype
  },
  body: file
});

if (!response.ok) {
  console.error("File upload to S3 failed.");
}
```

### Step 3: Send the Message with the File Key

Once the upload is successful, the frontend sends a message to the conversation, using the `file_key` as the content and specifying the `message_type`.

  * **Endpoint:** `POST /api/messaging/conversations/<int:conversation_id>/messages/`
  * **`curl` Example:**
    ```bash
    curl -X POST http://localhost:8000/api/messaging/conversations/1/messages/ \
         -H "Authorization: Token YOUR_AUTH_TOKEN" \
         -H "Content-Type: application/json" \
         -d '{"content": "uploads/my-cool-photo-uuid.jpg", "message_type": "image"}'
    ```
  * **Sample Response:**
    ```json
    {
      "success": true,
      "message": {
        "id": 103,
        "sender": { "id": 1, "username": "User A" },
        "content": "uploads/my-cool-photo-uuid.jpg", // This is now an S3 key
        "message_type": "image",
        "created_at": "2025-10-22T14:40:00Z"
      }
    }
    ```

-----

## 5\. QA Acceptance Checks

### Authentication & Authorization

  * [ ] User **cannot** access any messaging endpoint without a valid `Authorization` header (expect 401 Unauthorized).
  * [ ] User **cannot** get messages for a conversation they are not a participant in (expect 404 Not Found).
  * [ ] User **cannot** send messages to a conversation they are not a participant in (expect 404 Not Found).
  * [ ] User **cannot** edit or delete a message sent by *another* user (expect 404 Not Found).

### Conversation Management

  * [ ] `GET /conversations/` correctly lists all conversations for the logged-in user.
  * [ ] `POST /start-conversation/` (with a new `receiver_id`) successfully creates a new conversation and adds both users as participants.
  * [ ] `POST /start-conversation/` (with an *existing* `receiver_id`) does *not* create a new conversation, but returns the existing one.
  * [ ] `GET /conversations/<id>/` successfully returns paginated messages.

### Message Operations

  * [ ] `POST /conversations/<id>/messages/` (text) successfully creates a message.
  * [ ] The other participant(s) receive the new message via the WebSocket connection in real-time.
  * [ ] `PUT /messages/<id>/` (with `content`) updates the message text. The message object should now have `is_edited: true`.
  * [ ] Other participants receive the `message_edited` WebSocket event.
  * [ ] `DELETE /messages/<id>/` soft-deletes the message (`is_deleted: true`). It should no longer appear in the main message list.
  * [ ] Other participants receive the `message_deleted` WebSocket event.

### Features

  * [ ] `POST /messages/<id>/react/` (with `reaction_type`) adds a reaction.
  * [S] `POST /messages/<id>/react/` (with *same* `reaction_type`) removes the reaction.
  * [ ] `POST /messages/<id>/react/` (with *different* `reaction_type`) updates the existing reaction.
  * [ ] All participants receive the `reaction_updated` WebSocket event.
  * [ ] `POST /conversations/<id>/read/` successfully creates `MessageRead` objects in the database for unread messages.

### File Flow

  * [ ] `POST /generate-upload-url/` successfully returns a valid S3 `upload_url` and a `file_key`.
  * [ ] (Manual Test) A file can be successfully `PUT` to the `upload_url`.
  * [ ] `POST /conversations/<id>/messages/` (with `message_type: 'image'` and `content: file_key`) successfully creates the file message.
  * [ ] Other participants receive the new file message via the WebSocket.