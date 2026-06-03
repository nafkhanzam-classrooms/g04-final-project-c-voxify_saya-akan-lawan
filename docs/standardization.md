# API Standardization

To maintain consistency across the application, all API responses must follow this structure.

## Base JSON Response

### Success Response
```json
{
  "status": "success",
  "data": { ... },
  "message": "Operation successful"
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Detailed error message",
  "code": "ERROR_CODE",
  "errors": null // Optional: for validation errors, e.g., {"field": ["error detail"]}
}
```

## HTTP Status Codes
- `200 OK`: Request succeeded.
- `201 Created`: Resource created successfully.
- `400 Bad Request`: Client-side error or validation failure.
- `401 Unauthorized`: Authentication required or failed.
- `403 Forbidden`: Authenticated but lack permission.
- `404 Not Found`: Resource not found.
- `500 Internal Server Error`: Server-side error.

## Authentication Header
Most endpoints require the following header:
`Authorization: Bearer <jwt_token>`
