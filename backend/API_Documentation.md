# API Documentation

## Overview
This document provides comprehensive documentation for the API endpoints, including request/response formats, authentication requirements, and usage examples.

## Base URL
```
http://localhost:3000/api
```

## Authentication
All protected endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

## Error Responses
All endpoints return consistent error responses in the following format:
```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": "Additional error details (optional)"
}
```

## HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

## Endpoints

### Authentication

#### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe"
}
```

**Response:**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "user_id",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

#### POST /auth/login
Authenticate user and receive JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "token": "jwt_token_here",
  "user": {
    "id": "user_id",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

#### POST /auth/logout
Logout user (requires authentication).

**Response:**
```json
{
  "message": "Logged out successfully"
}
```

### User Management

#### GET /users/profile
Get current user profile (requires authentication).

**Response:**
```json
{
  "user": {
    "id": "user_id",
    "email": "user@example.com",
    "name": "John Doe",
    "createdAt": "2023-01-01T00:00:00.000Z"
  }
}
```

#### PUT /users/profile
Update user profile (requires authentication).

**Request Body:**
```json
{
  "name": "Updated Name",
  "email": "updated@example.com"
}
```

**Response:**
```json
{
  "message": "Profile updated successfully",
  "user": {
    "id": "user_id",
    "email": "updated@example.com",
    "name": "Updated Name"
  }
}
```

### Data Operations

#### GET /data
Retrieve data items (requires authentication).

**Query Parameters:**
- `page` (optional) - Page number for pagination (default: 1)
- `limit` (optional) - Number of items per page (default: 10)
- `sort` (optional) - Sort field (default: createdAt)
- `order` (optional) - Sort order: asc/desc (default: desc)

**Response:**
```json
{
  "data": [
    {
      "id": "item_id",
      "title": "Item Title",
      "description": "Item description",
      "createdAt": "2023-01-01T00:00:00.000Z",
      "updatedAt": "2023-01-01T00:00:00.000Z"
    }
  ],
  "pagination": {
    "current": 1,
    "total": 5,
    "pages": 1,
    "limit": 10
  }
}
```

#### POST /data
Create a new data item (requires authentication).

**Request Body:**
```json
{
  "title": "New Item",
  "description": "Item description"
}
```

**Response:**
```json
{
  "message": "Item created successfully",
  "data": {
    "id": "item_id",
    "title": "New Item",
    "description": "Item description",
    "createdAt": "2023-01-01T00:00:00.000Z"
  }
}
```

#### GET /data/:id
Get a specific data item by ID (requires authentication).

**Response:**
```json
{
  "data": {
    "id": "item_id",
    "title": "Item Title",
    "description": "Item description",
    "createdAt": "2023-01-01T00:00:00.000Z",
    "updatedAt": "2023-01-01T00:00:00.000Z"
  }
}
```

#### PUT /data/:id
Update a specific data item (requires authentication).

**Request Body:**
```json
{
  "title": "Updated Title",
  "description": "Updated description"
}
```

**Response:**
```json
{
  "message": "Item updated successfully",
  "data": {
    "id": "item_id",
    "title": "Updated Title",
    "description": "Updated description",
    "updatedAt": "2023-01-01T00:00:00.000Z"
  }
}
```

#### DELETE /data/:id
Delete a specific data item (requires authentication).

**Response:**
```json
{
  "message": "Item deleted successfully"
}
```

## Rate Limiting
API endpoints are rate-limited to prevent abuse:
- Authentication endpoints: 5 requests per minute
- General endpoints: 100 requests per minute

## CORS
Cross-Origin Resource Sharing is enabled for the following origins:
- `http://localhost:3000`
- `http://localhost:3001`

## Security
- All passwords are hashed using bcrypt
- JWT tokens expire after 24 hours
- Input validation is performed on all endpoints
- SQL injection protection is implemented

## Examples

### cURL Examples

**Register a new user:**
```bash
curl -X POST http://localhost:3000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "name": "John Doe"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

**Get user profile:**
```bash
curl -X GET http://localhost:3000/api/users/profile \
  -H "Authorization: Bearer your_jwt_token_here"
```

**Create data item:**
```bash
curl -X POST http://localhost:3000/api/data \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_jwt_token_here" \
  -d '{
    "title": "New Item",
    "description": "Item description"
  }'
```

## Testing
You can test the API using tools like:
- Postman
- Insomnia
- curl
- Thunder Client (VS Code extension)

## Changelog
- v1.0.0 - Initial API release
- v1.1.0 - Added pagination support
- v1.2.0 - Implemented rate limiting
- v1.3.0 - Enhanced error handling

## Support
For API support and questions, please contact:
- Email: support@example.com
- GitHub Issues: [Repository Issues](https://github.com/username/repository/issues)