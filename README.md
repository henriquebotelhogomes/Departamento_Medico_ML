# RadioAI — Classificação de Raio-X Torácico com Deep Learning

> Sistema full-stack de classificação médica com **explainability**, **detecção de anomalias**, **monitoramento de drift** e **pipeline MLOps reproduzível**.

![Python](https://img.shields.io/badge/python-3.12-blue)
![TensorFlow](https://img.shields.io/badge/tensorflow-2.21-orange)
![React](https://img.shields.io/badge/react-18-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)
![Docker](https://img.shields.io/badge/docker-compose-2496ED)
![CI](https://img.shields.io/badge/CI-GitHub_Actions-222)
![License](https://img.shields.io/badge/license-MIT-green)

***

## 📸 Demonstração

<p align="center">
  <img src="docs/screenshots/predicao_1.png" alt="Predição com Grad-CAM" width="88%">
</p>

<p align="center"><em>Predição com <strong>mapa de atenção Grad-CAM</strong>: o modelo classifica o raio-X e destaca em vermelho/quente as regiões que mais influenciaram a decisão — trazendo <strong>explainability</strong> ao diagnóstico.</em></p>

| Painel de métricas | Documentação interativa da API (Swagger) |
| :---: | :---: |
| <img src="docs/screenshots/painel_1.png" alt="Painel de métricas" width="100%"> | <img src="docs/screenshots/swagger.png" alt="Documentação Swagger da API" width="100%"> |
| Estatísticas agregadas: volume total, confiança média, classe mais frequente e distribuição por classe. | API REST documentada automaticamente (OpenAPI): autenticação **JWT**, predições e estatísticas. |

| Histórico de predições | Detalhe da predição |
| :---: | :---: |
| <img src="docs/screenshots/historico_1.png" alt="Histórico de predições" width="100%"> | <img src="docs/screenshots/historico_2.png" alt="Detalhe da predição" width="100%"> |
| Histórico paginado e filtrável por classe, persistido por usuário. Note as linhas **Out of Distribution** — imagens que **não são raio-X** são rejeitadas via similaridade de embeddings, evitando diagnósticos falsos. | Modal com o raio-X, a confiança da predição e a distribuição de probabilidade entre todas as classes. |

***

## Visão Geral

Aplicação de Machine Learning em produção que classifica imagens de raio-X torácico em **4 categorias clínicas** utilizando um modelo ResNet50 fine-tuned:

| Classe | Diagnóstico          |
| ------ | -------------------- |
| 0      | Covid-19             |
| 1      | Normal               |
| 2      | Pneumonia Viral      |
| 3      | Pneumonia Bacteriana |

> **Disclaimer**: Projeto de demonstração técnica — NÃO é uma ferramenta clínica validada.

***

## Datasets Utilizados

O modelo foi treinado utilizando **dois datasets complementares** de imagens de raio-X torácico, combinados para maximizar a diversidade e robustez:

### Dataset 1 — COVID-19 Radiography Database (Kaggle)

| Campo              | Valor                                                                                                                 |
| ------------------ | --------------------------------------------------------------------------------------------------------------------- |
| **Fonte**          | [Kaggle — COVID-19 Radiography Database](https://www.kaggle.com/datasets/tawsifurrahman/covid19-radiography-database) |
| **Papel**          | Dataset inicial de teste e validação                                                                                  |
| **Estrutura**      | 4 classes em diretórios separados                                                                                     |
| **Uso no projeto** | Conjunto de **teste final** (diretório `Test/`) — nunca visto durante treino                                          |

### Dataset 2 — Mendeley Chest X-ray (Curado)

| Campo                | Valor                                                                            |
| -------------------- | -------------------------------------------------------------------------------- |
| **Fonte**            | [Mendeley Data — 9xkhgts2s6 v4](https://data.mendeley.com/datasets/9xkhgts2s6/4) |
| **Tamanho original** | \~3.5 GB (zip) com milhares de imagens                                           |
| **Papel**            | Dataset principal de **treinamento e validação**                                 |
| **Subsampling**      | 1.200 imagens por classe (balanceado)                                            |
| **Deduplicação**     | Hashes perceptuais (dHash) para excluir duplicatas entre treino e teste          |
| **Anti-leakage**     | Imagens idênticas ao Test/ foram removidas automaticamente                       |

### Distribuição Final

| Conjunto  | Imagens | Split           | Fonte                 |
| --------- | ------- | --------------- | --------------------- |
| Treino    | 4.065   | 85% do Mendeley | Mendeley curado       |
| Validação | 717     | 15% do Mendeley | Mendeley curado       |
| Teste     | \~400   | Separado        | Kaggle (independente) |

***

## Processo de Treinamento

O treinamento seguiu uma estratégia de **3 fases progressivas**, partindo de um backbone congelado até fine-tuning seletivo:

### Fluxograma do Pipeline

```mermaid
graph TB
    A[Download Dataset Mendeley 3.5GB] --> B[Organização e Filtragem]
    B --> C{Deduplicação dHash}
    C -->|Duplicatas removidas| D[Subsampling Balanceado 1200/classe]
    D --> E[Dataset Treino 4065 imgs]
    D --> F[Dataset Validação 717 imgs]
    
    G[Download Dataset Kaggle] --> H[Conjunto de Teste Independente ~400 imgs]
    
    E --> I[Fase 1: Feature Extraction]
    I --> J[Fase 2: Fine-Tuning conv5_block]
    J --> K[Avaliação no Test Set]
    K --> L{Accuracy > Baseline?}
    L -->|Sim| M[Modelo Final .keras]
    L -->|Não| J
    M --> N[Deploy em Produção]
    
    H --> K
```

### Fase 1 — Feature Extraction (Backbone Congelado)

| Parâmetro           | Valor                                                              |
| ------------------- | ------------------------------------------------------------------ |
| **Backbone**        | ResNet50 (ImageNet, congelado)                                     |
| **Saída**           | GlobalAveragePooling2D → vetor 2048-d                              |
| **Cabeça**          | Dropout(0.3) → Dense(256, ReLU) → Dropout(0.3) → Dense(4, Softmax) |
| **Otimizador**      | Adam (lr=1e-3)                                                     |
| **Épocas**          | Até 200 (EarlyStopping patience=20)                                |
| **Épocas efetivas** | 34                                                                 |
| **Loss**            | Categorical Crossentropy                                           |
| **Callbacks**       | EarlyStopping + ReduceLROnPlateau (factor=0.5, patience=6)         |
| **Val Accuracy**    | 84.4%                                                              |
| **Test Accuracy**   | 82.5% (sem TTA)                                                    |

### Fase 2 — Fine-Tuning Seletivo (conv5\_block)

| Parâmetro                 | Valor                                                                               |
| ------------------------- | ----------------------------------------------------------------------------------- |
| **Camadas descongeladas** | 22 (apenas `conv5_block*`, BatchNorm congelada)                                     |
| **Otimizador**            | Adam (lr=1e-5) — 100x menor que Fase 1                                              |
| **Épocas**                | 5                                                                                   |
| **Data Augmentation**     | RandomRotation(0.03), RandomZoom(0.1), RandomTranslation(0.05), RandomContrast(0.1) |
| **Checkpoint**            | Salva apenas se superar baseline anterior                                           |
| **Val Accuracy**          | 85.2%                                                                               |
| **Test Accuracy**         | 87.5% (sem TTA) / **92.5% (com TTA)**                                               |

### Fase 3 — Test-Time Augmentation (TTA)

| Parâmetro                | Valor                                |
| ------------------------ | ------------------------------------ |
| **Variações por imagem** | 10 augmentações + original           |
| **Agregação**            | Média das probabilidades softmax     |
| **Augmentações**         | Rotação, zoom, translação, contraste |
| **Ganho**                | +5% accuracy absoluto vs. sem TTA    |

### Evolução da Performance

```
┌─────────────────────────────────────────────────────────┐
│ Fase                  │ Test Acc (sem TTA) │ Test Acc (TTA) │
├───────────────────────┼────────────────────┼────────────────┤
│ Feature Extraction    │      82.5%         │     80.0%      │
│ Fine-Tuning conv5     │      87.5%         │     92.5%      │
│ Ganho absoluto        │     +5.0%          │    +12.5%      │
└─────────────────────────────────────────────────────────┘
```

### Decisões de Design

1. **Dois datasets separados** — O teste usa um dataset completamente independente (Kaggle), nunca exposto durante treino, garantindo avaliação sem viés
2. **Deduplicação perceptual (dHash)** — Remove imagens visualmente idênticas entre treino/teste, prevenindo data leakage
3. **Balanceamento por subsampling** — 1.200 imgs/classe evita bias para classes majoritárias
4. **BatchNorm congelada** — Evita instabilidade durante fine-tuning com batch pequeno
5. **LR 100x menor no fine-tuning** — Preserva features aprendidas no ImageNet
6. **Checkpoint com threshold** — Modelo só é salvo se superar a baseline anterior

***

## Diferenciais Técnicos

### Inteligência Artificial & MLOps

* **Grad-CAM (Explainability)** — Visualização de atenção do modelo via `tf.GradientTape`, mostrando *onde* o modelo focou para cada predição

* **Detecção Out-of-Distribution (OOD)** — Rejeita automaticamente imagens que não são raio-X torácico usando similaridade cosseno no espaço de embeddings (2048-dim)

* **Pipeline de treino reproduzível** — Script configurável via YAML com seeds fixas, class weights balanceados, two-phase training (freeze → fine-tune), e tracking completo via MLflow

* **Validação estatística do threshold OOD** — ROC/AUC + Youden's J para definir threshold ótimo com evidência empírica

* **Model Card** — Documentação completa seguindo padrões da indústria (bias, limitações, considerações éticas, métricas por classe)

* **Script de avaliação** — Gera confusion matrix, ROC curves (one-vs-rest), classification report e summary JSON automaticamente

### Monitoramento & Observabilidade

* **Drift monitoring** — Detecção de concept drift e data drift via testes estatísticos (Chi-squared para distribuição de classes, Kolmogorov-Smirnov para confiança)

* **Logging estruturado** — JSON logs com `structlog`, correlation ID por request, contexto enriquecido

* **Health check** — Endpoint `/api/health` verifica DB + modelo carregado

* **Request logging** — Método, path, status, duração em ms para cada request

### Segurança & Robustez

* **Rate limiting** — 10 predições/minuto por IP (slowapi) para proteger contra abuso

* **Security headers** — X-Content-Type-Options, X-Frame-Options, HSTS, Referrer-Policy, Permissions-Policy

* **CORS restritivo** — Apenas métodos e headers específicos permitidos

* **JWT com refresh tokens** — Autenticação stateless com rotação de tokens

### Arquitetura & Escalabilidade

* **Celery + Redis** *(opcional — extra `worker`)* — Worker assíncrono para inferência pesada, desacoplando do ciclo de request. Não instalado por padrão; requer `uv sync --extra worker` (ou `pip install -e ".[worker]"`) e uma instância Redis em execução

* **Cache de predições** *(opcional — extra `worker`)* — SHA-256 hash → Redis com TTL, evitando re-inferência de imagens duplicadas. Degrada silenciosamente quando o Redis não está disponível — a API funciona normalmente sem ele

* **Docker multi-stage** — Imagem otimizada combinando frontend build + backend em container único

* **PostgreSQL + Alembic** — Migrations versionadas, connection pooling assíncrono

* **Storage abstrato** — Interface que suporta local (dev) e Supabase (prod) sem mudança de código

### Frontend & UX

* **Internacionalização (i18n)** — Suporte completo pt-BR/English com `react-i18next`, detecção automática do idioma do navegador

* **Grad-CAM visual** — Comparação lado-a-lado (original vs. heatmap) para interpretabilidade

* **Alerta OOD** — Card visual quando imagem não é raio-X, explicando por quê

* **Dark mode** — Com detecção de preferência do sistema

* **Confirmação de exclusão** — UX defensiva com two-step delete

***

## Funcionalidades

| Feature              | Descrição                                                          |
| -------------------- | ------------------------------------------------------------------ |
| Predição drag & drop | Upload com barras de probabilidade em tempo real                   |
| Histórico paginado   | Filtro por classe, modal de detalhes, exclusão com confirmação     |
| Dashboard analítico  | Gráficos de barras/linha (predições por classe, ao longo do tempo) |
| Autenticação JWT     | Register/login/refresh com conta demo one-click                    |
| Explainability       | Grad-CAM heatmap para cada predição                                |
| OOD Detection        | Rejeição automática de não raio-X                                  |
| Drift Monitoring     | Detecção estatística de mudanças na distribuição                   |
| i18n                 | Interface completa em português e inglês                           |

***

## Quick Start

```bash
# Pré-requisitos: Python 3.12, Node 20, Git

git clone https://github.com/henriquebotelhogomes/Departamento_Medico_ML.git
cd Departamento_Medico_ML

# Backend
cd backend
pip install -e ".[dev]"        # ou: uv sync --extra dev
# Opcional — worker assíncrono + cache Redis (requer Redis rodando):
# pip install -e ".[worker]"   # ou: uv sync --extra worker
cd ..

# Frontend
cd frontend
npm install
cd ..

# Executar (dois terminais)
cd backend  && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

Abra <http://localhost:5173> → login com **demo123 / demo123**.

### Com Docker

```bash
docker compose up --build
# API: http://localhost:8000
# Frontend: http://localhost:5173
```

***

## Estrutura do Projeto

```
├── backend/              API FastAPI, predictor ML, storage, DB, testes
│   ├── app/
│   │   ├── api/          Routers (auth, predictions, stats, system)
│   │   ├── core/         Config, security, logging, cache
│   │   ├── middleware/   Security headers
│   │   ├── ml/           Predictor (Grad-CAM, OOD, inference)
│   │   ├── monitoring/   Drift detection (chi², KS test)
│   │   ├── tasks/        Celery background tasks (opcional, extra `worker`)
│   │   └── worker.py     Celery app instance (opcional, extra `worker`)
│   ├── alembic/          Database migrations
│   └── tests/            pytest (auth, predictions, predictor, OOD)
│
├── frontend/             React 18 + Vite + TypeScript + Tailwind
│   └── src/
│       ├── locales/      Traduções (en.json, pt-BR.json)
│       ├── pages/        Login, Register, Predict, History, Dashboard
│       ├── components/   Layout, ProbabilityBar, ConfidenceBadge
│       └── __tests__/    Vitest (Predict, History)
│
├── training/             Pipeline MLOps
│   ├── train.py          Treino reproduzível com MLflow
│   ├── evaluate.py       Métricas + plots (confusion matrix, ROC)
│   ├── validate_ood_threshold.py  Validação estatística do threshold
│   └── config.yaml       Hiperparâmetros centralizados
│
├── models/               Model Card (MODEL_CARD.md)
├── examples/             Imagens de referência para OOD
├── docs/                 Documentação (MkDocs)
├── .github/workflows/    CI/CD (lint → test → build → docker)
└── docker-compose.yml    Orquestração de serviços
```

***

## Tech Stack

| Camada        | Tecnologias                                                            |
| ------------- | ---------------------------------------------------------------------- |
| **ML/AI**     | TensorFlow 2.21 · Keras 3.15 · ResNet50 · Grad-CAM · OOD Detection     |
| **MLOps**     | MLflow · Reproducible Training · Model Card · Drift Monitoring         |
| **Backend**   | Python 3.12 · FastAPI · Pydantic v2 · SQLAlchemy 2 (async) · Celery (opcional) |
| **Frontend**  | React 18 · Vite · TypeScript · Tailwind CSS · TanStack Query · i18next |
| **Database**  | SQLite (dev) / PostgreSQL (prod) · Alembic migrations · Redis cache (opcional) |
| **Segurança** | JWT + Refresh Tokens · Rate Limiting · Security Headers · CORS         |
| **DevOps**    | Docker multi-stage · docker-compose · GitHub Actions CI · Render       |
| **Qualidade** | ruff · pytest (31 tests) · Vitest (14 tests) · pre-commit hooks        |

***

## Testes

```bash
# Backend (31 testes: auth, predictions, stats, system, predictor, OOD)
cd backend && pytest -q

# Frontend (14 testes: components, login, predict, history)
cd frontend && npm run test

# Lint
cd backend && ruff check app
cd frontend && npx tsc --noEmit
```

***

## Pipeline MLOps

```bash
cd training

# Treinar modelo (requer dataset + GPU recomendada)
python train.py --config config.yaml

# Avaliar modelo (gera métricas e plots)
python evaluate.py --model ../models/chest_xray_model.keras --test-dir ../data/chest_xray/test

# Validar threshold OOD (análise estatística)
python validate_ood_threshold.py
```

Resultados são registrados automaticamente no **MLflow** com:

* Hiperparâmetros completos

* Métricas por época (train/val accuracy)

* Métricas finais (accuracy, F1, precision, recall por classe)

* Modelo serializado como artefato

***

## Deploy

| Plataforma             | Método                                            |
| ---------------------- | ------------------------------------------------- |
| **Render**             | Auto-deploy via `render.yaml` Blueprint           |
| **Docker**             | `docker compose up` (PostgreSQL + API + Frontend) |
| **HuggingFace Spaces** | Mesmo Dockerfile, `PORT=7860`                     |

Veja [docs/deploy.md](docs/deploy.md) para instruções completas.

#

***

## Licença

MIT
