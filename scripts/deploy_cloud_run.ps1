# ==============================================================================
# RadioAI — One-Click Deploy to Google Cloud Run (Scale-to-Zero /  Cost)
# Execução nativa no Windows PowerShell
# ==============================================================================

[CmdletBinding()]
param(
    [string] = "",
    [string] = "us-central1",
    [string] = "radioai"
)

Continue = "Stop"

if (-not ) {
    try {
         = (gcloud config get-value project 2>$null).Trim()
    } catch {
         = ""
    }
}

if (-not ) {
    Write-Host "❌ Erro: Google Cloud Project ID não definido." -ForegroundColor Red
    Write-Host "👉 Execute: gcloud config set project SEU_PROJECT_ID" -ForegroundColor Yellow
    exit 1
}

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "🚀 Iniciando Deploy do RadioAI no Google Cloud Run..." -ForegroundColor Cyan
Write-Host "📦 Projeto GCP:  " -ForegroundColor Green
Write-Host "🌐 Região:       " -ForegroundColor Green
Write-Host "⚙️  Serviço:      " -ForegroundColor Green
Write-Host "💰 Política:     Scale-to-Zero (min-instances=0 -> Custo /mês)" -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Cyan

# 1. Habilitar APIs necessárias no GCP
Write-Host "
🔧 [1/3] Habilitando APIs essenciais (Cloud Run, Cloud Build)..." -ForegroundColor Yellow
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project 

# 2. Compilar e empacotar container no Cloud Build (respeitando .gcloudignore)
Write-Host "
🐳 [2/3] Compilando e enviando imagem de container no Cloud Build..." -ForegroundColor Yellow
gcloud builds submit --tag "gcr.io//:latest" . --project 

# 3. Deploy no Cloud Run com política Scale-to-Zero
Write-Host "
⚡ [3/3] Publicando serviço serverless no Cloud Run..." -ForegroundColor Yellow
gcloud run deploy  
    --image "gcr.io//:latest" 
    --region  
    --platform managed 
    --allow-unauthenticated 
    --memory 2Gi 
    --cpu 1 
    --min-instances 0 
    --max-instances 2 
    --port 8000 
    --project 

 = (gcloud run services describe  --platform managed --region  --project  --format 'value(status.url)').Trim()

Write-Host "
==================================================================" -ForegroundColor Green
Write-Host "🎉 DEPLOY CONCLUÍDO COM SUCESSO!" -ForegroundColor Green
Write-Host "🔗 URL Pública de Produção: " -ForegroundColor Cyan
Write-Host "💰 Custo Ocioso: /mês (instâncias escalam a zero automaticamente)" -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Green
