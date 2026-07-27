# Deploy

## Render (primary, always-on)

RadioAI ships with a `render.yaml` Blueprint that deploys a single Web Service using the root multi-stage Dockerfile.

### Steps

1. Push the repo to GitHub (with Git LFS tracking the `.keras` model).
2. Create a new **Blueprint** on Render pointing at the repo.
3. Render will auto-detect `render.yaml` and provision the service.
4. Set the required environment variables in the Render dashboard:

| Variable               | Description                             |
|------------------------|-----------------------------------------|
| `SECRET_KEY`           | Random 32+ char secret                  |
| `DATABASE_URL`         | Supabase Postgres connection string     |
| `STORAGE_BACKEND`      | `supabase`                              |
| `SUPABASE_URL`         | Supabase project URL                    |
| `SUPABASE_SERVICE_KEY` | Supabase service-role key               |
| `SUPABASE_BUCKET`      | Storage bucket name (e.g., `uploads`)   |

### Supabase setup

1. Create a project on [supabase.com](https://supabase.com).
2. Copy the Postgres connection string (Project Settings → Database → URI).
3. Create a Storage bucket named `uploads` (public or private).
4. Get the service-role key from Project Settings → API.

## HuggingFace Spaces (alternative)

The same Dockerfile works on HF Spaces:

1. Create a **Docker** Space.
2. Set env vars as above.
3. HF exposes port `7860` by default; set `PORT=7860` in the Space settings.

## Notes

- The Supabase free tier pauses after ~1 week of inactivity; the app itself runs on Render/HF which stay active.
- The model file (~215 MB) is tracked by Git LFS. Ensure LFS is enabled on your host/CI.
