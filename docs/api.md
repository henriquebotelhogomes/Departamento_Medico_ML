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

Upload multipart com o campo `file`.
- **Formatos suportados**: Arquivos hospitalares DICOM (`.dcm`), JPEG, PNG, WEBP, BMP (máx. 15 MB).
- **Tratamento DICOM**: Desidentificação automática de dados do paciente (conforme DICOM PS 3.15, HIPAA e LGPD), conversão de escala Hounsfield/Windowing e extração de metadados técnicos.
- **Filtro OOD**: Verificação de embeddings (2048-d) com rejeição de imagens fora do domínio torácico.

**Resposta**:
```json
{
  "id": 105,
  "predicted_class": 3,
  "label": "Pneumonia bacteriana",
  "confidence": 0.942,
  "probs": [
    { "class_id": 0, "label": "Covid-19", "probability": 0.012 },
    { "class_id": 1, "label": "Normal", "probability": 0.015 },
    { "class_id": 2, "label": "Pneumonia viral", "probability": 0.031 },
    { "class_id": 3, "label": "Pneumonia bacteriana", "probability": 0.942 }
  ],
  "inference_ms": 142.5,
  "image_url": "http://localhost:8000/api/predictions/image/105",
  "gradcam_image": "data:image/jpeg;base64,...",
  "pure_heatmap": "data:image/png;base64,...",
  "raw_image_data": "data:image/jpeg;base64,...",
  "dicom_metadata": {
    "is_dicom": true,
    "modality": "CR",
    "body_part": "CHEST",
    "patient_position": "PA",
    "kvp": "120"
  },
  "is_ood": false,
  "ood_similarity": 0.88,
  "created_at": "2026-09-04T12:00:00Z"
}
```

### `POST /api/predictions/report`

Emissão de laudo radiológico estruturado via IA Generativa ou regras médicas locais determinísticas.

**Payload JSON**:
- `predicted_class` (int): ID da classe predita (0 a 3).
- `label` (string): Rótulo diagnóstico.
- `confidence` (float): Nível de confiança calibrado.
- `probs` (array, opcional): Distribuição completa de probabilidades por classe.
- `model` (string): Identificador do modelo de IA:
  - `gemini-3.8-flash`: Google Gemini 3.8 / 2.5 Flash via Google AI Studio.
  - `gpt-5.6-luna`: GPT 5.6 Luna via OpenCode Zen API.
  - `deepseek-v4-flash`: DeepSeek V4 Flash via OpenCode Zen API.
  - `qwen3.7-plus`: Qwen 3.7 Plus via OpenCode Zen API.
  - `deterministic-local`: Motor local baseado em regras médicas (100% offline, sem consumo de API).
- `dicom_metadata` (object, opcional): Metadados técnicos do exame.
- `override_label` (string, opcional): Diagnóstico soberano definido pelo médico assistente (*Human-in-the-Loop*).
- `override_notes` (string, opcional): Justificativa clínica ou correlação com biomarcadores (ex: Procalcitonina, PCR).
- `is_ambiguous` (bool, opcional): Sinaliza se houve empate técnico / margem estreita na triagem.

**Resposta**:
```json
{
  "model_used": "Gemini 3.8 Flash",
  "provider": "Google AI",
  "technique": "Radiografia de tórax digital em incidência póstero-anterior (PA)...",
  "findings": "Campos pleuropulmonares com consolidação alveolar densa no lobo inferior direito...",
  "impression": "Consolidação alveolar lobar com broncograma aéreo, compatível com pneumonia bacteriana comunitária.",
  "icd_10": "J15.9 (Pneumonia bacteriana não especificada)",
  "recommendations": "Avaliação médica para instituição de antibioticoterapia empírica...",
  "disclaimer": "AVISO LEGAL / DECISION SUPPORT: Este laudo foi gerado por Inteligência Artificial Médica...",
  "generated_at": "2026-09-04T12:00:05Z"
}
```

### `GET /api/predictions`

Listagem paginada de predições. Query params: `page`, `page_size`, `predicted_class`, `date_from`, `date_to`.

### `GET /api/predictions/{id}`

Detalhes completos de uma predição única por ID, incluindo imagens e metadados.

### `DELETE /api/predictions/{id}`

Exclui a predição e os arquivos associados. Retorna status 204.

## Statistics

### `GET /api/stats`

Returns `{ total_predictions, average_confidence, by_class, over_time }`.

## System

### `GET /api/health`

Returns `{ status: "ok", model_loaded: true/false }`.

### `GET /api/version`

Returns application version, environment, supported classes, and TTA status.
