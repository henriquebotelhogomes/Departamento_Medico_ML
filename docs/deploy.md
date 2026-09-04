# Deploy

## Google Cloud Run (Recomendado — Serverless Scale-to-Zero $0/mês)

O deploy no **Google Cloud Run** permite hospedar a aplicação completa (API FastAPI + Frontend React) em arquitetura serverless com auto-scaling até 0 instâncias quando ocioso, garantindo custo fixo de **$0/mês** para demonstração de portfólio.

### Deploy Automatizado com Script

```bash
# Definir o ID do seu projeto no GCP
export GCP_PROJECT_ID="seu-projeto-gcp"
export GCP_REGION="us-central1"

# Executar o script de provisionamento automatizado
bash scripts/deploy_cloud_run.sh
```

O script habilita as APIs necessárias (Cloud Build, Cloud Run, Artifact Registry), compila o container multi-stage e publica o serviço com 2 GB de memória e 1 vCPU.

### Deploy via Google Cloud Build

Alternativamente, utilize o arquivo `cloudbuild.yaml` incluído na raiz do projeto:

```bash
gcloud builds submit --config=cloudbuild.yaml
```

## Render (always-on alternativo)

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
