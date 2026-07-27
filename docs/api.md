# API Reference

RadioAI exposes a REST API under `/api`. Interactive documentation is available at:

- **Swagger UI**: [`/api/docs`](http://localhost:8000/api/docs)
- **ReDoc**: [`/api/redoc`](http://localhost:8000/api/redoc)

## Authentication

All endpoints except `/api/health`, `/api/version`, `/api/auth/register`, and `/api/auth/login` require a Bearer token.

### `POST /api/auth/login`

Form-encoded (`application/x-www-form-urlencoded`): `username` (accepts username or email), `password`.

Returns `{ access_token, refresh_token, token_type }`.

### `POST /api/auth/register`

JSON: `{ username, email, password }`. Returns the created user.

### `POST /api/auth/refresh`

JSON: `{ refresh_token }`. Returns a new token pair.

### `GET /api/auth/me`

Returns the authenticated user's profile.

## Predictions

### `POST /api/predictions`

Multipart upload with field `file` (JPEG, PNG, WEBP, BMP; max 10 MB).

Returns `{ id, predicted_class, label, confidence, probs, inference_ms, image_url, created_at }`.

### `GET /api/predictions`

Paginated listing. Query params: `page`, `page_size`, `predicted_class`, `date_from`, `date_to`.

### `GET /api/predictions/{id}`

Single prediction detail with signed image URL.

### `DELETE /api/predictions/{id}`

Deletes the prediction and its stored image. Returns 204.

## Statistics

### `GET /api/stats`

Returns `{ total_predictions, average_confidence, by_class, over_time }`.

## System

### `GET /api/health`

Returns `{ status: "ok", model_loaded: true/false }`.

### `GET /api/version`

Returns application version, environment, supported classes, and TTA status.
