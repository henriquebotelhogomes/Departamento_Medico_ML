# ==============================================================================
# RadioAI — One-Click Deploy to Google Cloud Run (Scale-to-Zero / $0 Cost)
# Execução nativa no Windows PowerShell
# ==============================================================================

[CmdletBinding()]
param(
    [string]$ProjectId = "",
    [string]$Region = "us-central1",
    [string]$ServiceName = "radioai"
)

$ErrorActionPreference = "Stop"

if (-not $ProjectId) {
    try {
        $ProjectId = (gcloud config get-value project 2>$null).Trim()
    } catch {
        $ProjectId = ""
    }
}

if (-not $ProjectId) {
    Write-Host "❌ Erro: Google Cloud Project ID não definido." -ForegroundColor Red
    Write-Host "👉 Execute: gcloud config set project SEU_PROJECT_ID" -ForegroundColor Yellow
    exit 1
}

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "🚀 Iniciando Deploy do RadioAI no Google Cloud Run..." -ForegroundColor Cyan
Write-Host "📦 Projeto GCP:  $ProjectId" -ForegroundColor Green
Write-Host "🌐 Região:       $Region" -ForegroundColor Green
Write-Host "⚙️  Serviço:      $ServiceName" -ForegroundColor Green
Write-Host "💰 Política:     Scale-to-Zero (min-instances=0 -> Custo $0/mês)" -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Cyan

# 1. Habilitar APIs necessárias no GCP
Write-Host "`n🔧 [1/3] Habilitando APIs essenciais (Cloud Run, Cloud Build)..." -ForegroundColor Yellow
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project $ProjectId

# 2. Compilar e empacotar container no Cloud Build (respeitando .gcloudignore)
Write-Host "`n🐳 [2/3] Compilando e enviando imagem de container no Cloud Build..." -ForegroundColor Yellow
gcloud builds submit --tag "gcr.io/$ProjectId/${ServiceName}:latest" . --project $ProjectId

# 3. Deploy no Cloud Run com política Scale-to-Zero
Write-Host "`n⚡ [3/3] Publicando serviço serverless no Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $ServiceName `
    --image "gcr.io/$ProjectId/${ServiceName}:latest" `
    --region $Region `
    --platform managed `
    --allow-unauthenticated `
    --memory 2Gi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 2 `
    --port 8000 `
    --project $ProjectId

$LiveUrl = (gcloud run services describe $ServiceName --platform managed --region $Region --project $ProjectId --format 'value(status.url)').Trim()

Write-Host "`n==================================================================" -ForegroundColor Green
Write-Host "🎉 DEPLOY CONCLUÍDO COM SUCESSO!" -ForegroundColor Green
Write-Host "🔗 URL Pública de Produção: $LiveUrl" -ForegroundColor Cyan
Write-Host "💰 Custo Ocioso: $0/mês (instâncias escalam a zero automaticamente)" -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Green
