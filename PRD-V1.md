# PRD-V1 — Evolução para Nível Sênior

> **Projeto:** RadioAI — Classificação de Raio-X Torácico  
> **Stack atual:** FastAPI + React/TypeScript/Vite + TailwindCSS + TensorFlow/Keras  
> **Objetivo:** Elevar o projeto de nível pleno para sênior em Data Science, ML e Engenharia de Software  
> **Estimativa total:** ~40-60h de implementação

---

## Seção de Prioridade Absoluta (Top 5)

Os 5 itens abaixo são os que mais elevam a percepção do projeto com menor esforço:

### Checklist de Prioridades

- [x] **1. Docker Compose** (backend + frontend + PostgreSQL) — ~3h
- [x] **2. GitHub Actions CI** (lint + test + build) — ~2h
- [x] **3. MLflow + Script de treino reproduzível** — ~6h
- [x] **4. Testes pytest com cobertura ≥ 80%** — ~6h
- [x] **5. Model Card com métricas** (confusion matrix, ROC, bias analysis) — ~3h

---

### 1. Docker Compose

**Objetivo:** Qualquer pessoa executa o projeto inteiro com `docker compose up`.

**Arquivos a criar:**

```
/Dockerfile.backend
/Dockerfile.frontend
/docker-compose.yml
/.dockerignore
```

**Dockerfile.backend:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Dockerfile.frontend:**
```dockerfile
FROM node:20-alpine AS build

WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

**docker-compose.yml:**
```yaml
version: "3.9"
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: radioai
      POSTGRES_PASSWORD: ${DB_PASSWORD:-radioai_dev}
      POSTGRES_DB: radioai
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U radioai"]
      interval: 5s
      timeout: 3s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    environment:
      DATABASE_URL: postgresql+asyncpg://radioai:${DB_PASSWORD:-radioai_dev}@db:5432/radioai
      SECRET_KEY: ${SECRET_KEY:-dev-secret-change-in-prod}
      OOD_REFERENCE_DIR: /app/examples
    volumes:
      - ./examples:/app/examples:ro
      - ./models:/app/models:ro
      - uploads:/app/uploads
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

volumes:
  pgdata:
  uploads:
```

**nginx.conf** (para frontend):
```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 10M;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

**.dockerignore:**
```
node_modules
__pycache__
*.pyc
.venv
dist
.git
*.egg-info
```

**Comandos de verificação:**
```bash
docker compose up --build -d
docker compose ps          # todos healthy
curl http://localhost:8000/api/health
curl http://localhost:3000  # frontend carrega
docker compose down
```

---

### 2. GitHub Actions CI

**Objetivo:** Pipeline automatizado que roda em cada push/PR: lint → test → build.

**Arquivo a criar:** `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_radioai
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U test"
          --health-interval 5s
          --health-timeout 3s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        working-directory: backend
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio httpx ruff

      - name: Lint (ruff)
        working-directory: backend
        run: |
          ruff check .
          ruff format --check .

      - name: Type check (pyright)
        working-directory: backend
        run: |
          pip install pyright
          pyright

      - name: Tests with coverage
        working-directory: backend
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test_radioai
          SECRET_KEY: test-secret
        run: |
          pytest --cov=app --cov-report=xml --cov-fail-under=80

      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: backend-coverage
          path: backend/coverage.xml

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install
        working-directory: frontend
        run: npm ci

      - name: Lint
        working-directory: frontend
        run: npm run lint

      - name: Type check
        working-directory: frontend
        run: npx tsc --noEmit

      - name: Tests
        working-directory: frontend
        run: npm run test

      - name: Build
        working-directory: frontend
        run: npm run build

  docker:
    runs-on: ubuntu-latest
    needs: [backend, frontend]
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker images
        run: docker compose build
```

---

### 3. MLflow + Script de Treino Reproduzível

**Objetivo:** Treino documentado, métricas registradas, modelo versionado.

**Dependências a instalar:**
```bash
pip install mlflow scikit-learn matplotlib seaborn
```

**Arquivos a criar:**
```
/training/
  train.py
  evaluate.py
  config.yaml
  requirements.txt
  README.md
/mlruns/              (gerado pelo MLflow, adicionar ao .gitignore)
```

**training/config.yaml:**
```yaml
data:
  dataset_dir: "../data/chest_xray"     # estrutura: train/val/test × 4 classes
  image_size: 256
  batch_size: 32
  seed: 42

model:
  backbone: "resnet50"
  weights: "imagenet"
  freeze_backbone_epochs: 5
  unfreeze_lr: 1.0e-5
  head_lr: 1.0e-3
  dropout: 0.3

training:
  epochs: 30
  early_stopping_patience: 5
  class_weights: "balanced"    # sklearn compute_class_weight

mlflow:
  experiment_name: "radioai-chest-xray"
  tracking_uri: "mlruns"       # local. Em prod: http://mlflow-server:5000
```

**training/train.py** (estrutura):
```python
"""
Treino reproduzível do modelo RadioAI.

Uso:
    python train.py --config config.yaml
    python train.py --config config.yaml --epochs 50 --lr 0.0001

Requer:
    - Dataset em data/chest_xray/ com estrutura ImageFolder
    - GPU recomendada (NVIDIA com CUDA)
"""
import argparse
import yaml
import mlflow
import mlflow.tensorflow
import numpy as np
import tensorflow as tf
from pathlib import Path
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import classification_report, confusion_matrix

def set_seeds(seed: int):
    """Reprodutibilidade."""
    np.random.seed(seed)
    tf.random.set_seed(seed)

def build_model(cfg: dict) -> tf.keras.Model:
    """Constrói modelo com ResNet50 + cabeça customizada."""
    base = tf.keras.applications.ResNet50(
        include_top=False,
        weights=cfg["model"]["weights"],
        input_shape=(cfg["data"]["image_size"], cfg["data"]["image_size"], 3),
        pooling="avg",
    )
    base.trainable = False  # freeze inicial

    inputs = tf.keras.Input(shape=(cfg["data"]["image_size"], cfg["data"]["image_size"], 3))
    x = tf.keras.applications.resnet50.preprocess_input(inputs)
    x = base(x)
    x = tf.keras.layers.Dropout(cfg["model"]["dropout"])(x)
    x = tf.keras.layers.Dense(128, activation="relu")(x)
    x = tf.keras.layers.Dropout(cfg["model"]["dropout"])(x)
    outputs = tf.keras.layers.Dense(4, activation="softmax")(x)

    return tf.keras.Model(inputs, outputs)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    set_seeds(cfg["data"]["seed"])

    # --- Data loading ---
    train_ds = tf.keras.utils.image_dataset_from_directory(
        Path(cfg["data"]["dataset_dir"]) / "train",
        image_size=(cfg["data"]["image_size"], cfg["data"]["image_size"]),
        batch_size=cfg["data"]["batch_size"],
        seed=cfg["data"]["seed"],
        label_mode="int",
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        Path(cfg["data"]["dataset_dir"]) / "val",
        image_size=(cfg["data"]["image_size"], cfg["data"]["image_size"]),
        batch_size=cfg["data"]["batch_size"],
        seed=cfg["data"]["seed"],
        label_mode="int",
    )

    # --- Class weights ---
    labels = np.concatenate([y.numpy() for _, y in train_ds])
    class_weights_arr = compute_class_weight("balanced", classes=np.unique(labels), y=labels)
    class_weight_dict = dict(enumerate(class_weights_arr))

    # --- Model ---
    model = build_model(cfg)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(cfg["model"]["head_lr"]),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    # --- MLflow tracking ---
    mlflow.set_tracking_uri(cfg["mlflow"]["tracking_uri"])
    mlflow.set_experiment(cfg["mlflow"]["experiment_name"])

    with mlflow.start_run():
        mlflow.log_params({
            "backbone": cfg["model"]["backbone"],
            "image_size": cfg["data"]["image_size"],
            "batch_size": cfg["data"]["batch_size"],
            "epochs": cfg["training"]["epochs"],
            "head_lr": cfg["model"]["head_lr"],
            "unfreeze_lr": cfg["model"]["unfreeze_lr"],
            "dropout": cfg["model"]["dropout"],
            "seed": cfg["data"]["seed"],
        })

        # Phase 1: Head only
        history = model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=cfg["model"]["freeze_backbone_epochs"],
            class_weight=class_weight_dict,
        )

        # Phase 2: Unfreeze
        model.layers[1].trainable = True  # ResNet50 layer
        model.compile(
            optimizer=tf.keras.optimizers.Adam(cfg["model"]["unfreeze_lr"]),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )

        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                patience=cfg["training"]["early_stopping_patience"],
                restore_best_weights=True,
                monitor="val_accuracy",
            ),
            tf.keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=3),
        ]

        history = model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=cfg["training"]["epochs"],
            class_weight=class_weight_dict,
            callbacks=callbacks,
        )

        # --- Evaluate ---
        test_ds = tf.keras.utils.image_dataset_from_directory(
            Path(cfg["data"]["dataset_dir"]) / "test",
            image_size=(cfg["data"]["image_size"], cfg["data"]["image_size"]),
            batch_size=cfg["data"]["batch_size"],
            label_mode="int",
        )

        y_true = np.concatenate([y.numpy() for _, y in test_ds])
        y_pred = np.argmax(model.predict(test_ds), axis=1)

        report = classification_report(y_true, y_pred, output_dict=True)
        cm = confusion_matrix(y_true, y_pred)

        mlflow.log_metrics({
            "test_accuracy": report["accuracy"],
            "test_f1_macro": report["macro avg"]["f1-score"],
            "test_f1_weighted": report["weighted avg"]["f1-score"],
        })

        # Log model
        mlflow.tensorflow.log_model(model, "model")

        # Save locally
        model.save("../models/chest_xray_model.keras")
        mlflow.log_artifact("../models/chest_xray_model.keras")

        print(f"Test Accuracy: {report['accuracy']:.4f}")
        print(f"Test F1 (macro): {report['macro avg']['f1-score']:.4f}")

if __name__ == "__main__":
    main()
```

**training/requirements.txt:**
```
tensorflow>=2.15
mlflow>=2.10
scikit-learn>=1.4
pyyaml>=6.0
matplotlib>=3.8
seaborn>=0.13
numpy>=1.26
```

---

### 4. Testes pytest com Cobertura ≥ 80%

**Objetivo:** Cobertura de testes abrangente para backend.

**Dependências a instalar:**
```bash
pip install pytest pytest-cov pytest-asyncio httpx factory-boy
```

**Estrutura de testes a criar/expandir:**
```
backend/tests/
  conftest.py           # fixtures globais (db session, client, auth headers)
  test_auth.py          # login, register, token refresh, unauthorized
  test_predictions.py   # upload, predict, history, delete, pagination, filters
  test_predictor.py     # unit tests do ML: predict, gradcam, OOD
  test_ood.py           # testes específicos de OOD detection
  test_health.py        # health check endpoint
  fixtures/
    covid_sample.jpg    # imagem real para testes
    normal_sample.jpg
    text_sample.png     # para testar OOD
```

**backend/tests/conftest.py:**
```python
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.config import settings
from app.db.session import get_db
from app.db.base import Base

TEST_DB_URL = "sqlite+aiosqlite:///./test.db"

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def auth_headers(client):
    """Registra usuário e retorna headers com token."""
    await client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@test.com",
        "password": "testpass123",
    })
    resp = await client.post("/api/auth/login", data={
        "username": "testuser",
        "password": "testpass123",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

**backend/tests/test_predictor.py:**
```python
"""Unit tests para o predictor ML."""
import numpy as np
import pytest
from pathlib import Path
from app.ml.predictor import Predictor

FIXTURES = Path(__file__).parent / "fixtures"

@pytest.fixture(scope="module")
def predictor():
    return Predictor(
        model_path="models/chest_xray_model.keras",
        ood_threshold=0.45,
        ood_reference_dir="examples",
    )

class TestPredictor:
    def test_predict_returns_valid_structure(self, predictor):
        result = predictor.predict(FIXTURES / "covid_sample.jpg")
        assert "predicted_class" in result
        assert "confidence" in result
        assert "probs" in result
        assert "gradcam_image" in result
        assert "is_ood" in result
        assert 0 <= result["confidence"] <= 1

    def test_predict_covid_sample(self, predictor):
        result = predictor.predict(FIXTURES / "covid_sample.jpg")
        assert result["is_ood"] is False
        assert result["predicted_class"] in [0, 1, 2, 3]
        assert len(result["probs"]) == 4

    def test_ood_detection_text_image(self, predictor):
        result = predictor.predict(FIXTURES / "text_sample.png")
        assert result["is_ood"] is True
        assert result["ood_similarity"] < 0.45

    def test_gradcam_generated(self, predictor):
        result = predictor.predict(FIXTURES / "covid_sample.jpg")
        assert result["gradcam_image"] is not None
        assert result["gradcam_image"].startswith("data:image/png;base64,")

    def test_ood_no_gradcam(self, predictor):
        result = predictor.predict(FIXTURES / "text_sample.png")
        assert result["gradcam_image"] is None

    def test_probs_sum_to_one(self, predictor):
        result = predictor.predict(FIXTURES / "normal_sample.jpg")
        total = sum(p["probability"] for p in result["probs"])
        assert abs(total - 1.0) < 0.01
```

**Comando para rodar:**
```bash
cd backend
pytest --cov=app --cov-report=html --cov-report=term-missing --cov-fail-under=80
```

---

### 5. Model Card com Métricas

**Objetivo:** Documentação completa do modelo seguindo padrões da indústria.

**Arquivo a criar:** `models/MODEL_CARD.md`

```markdown
# Model Card — RadioAI Chest X-ray Classifier

## Model Details
- **Model type:** CNN (ResNet50 fine-tuned)
- **Framework:** TensorFlow/Keras
- **Input:** Imagem RGB 256×256 pixels
- **Output:** 4 classes + OOD detection
- **Version:** 1.0.0
- **Training date:** [DATA]
- **License:** [LICENÇA]

## Intended Use
- **Primary use:** Classificação de raios-X torácicos em 4 categorias
- **Classes:** Covid-19, Normal, Pneumonia Viral, Pneumonia Bacteriana
- **Usuários alvo:** Profissionais de saúde (como ferramenta auxiliar)
- **Limitações:** NÃO deve ser usado como diagnóstico definitivo

## Training Data
- **Dataset:** [Nome do dataset, ex: COVID-19 Radiography Database]
- **Tamanho:** [N] imagens total
- **Split:** Train [N] / Val [N] / Test [N]
- **Distribuição de classes:**
  | Classe | Train | Val | Test |
  |--------|-------|-----|------|
  | Covid-19 | X | X | X |
  | Normal | X | X | X |
  | Viral Pneumonia | X | X | X |
  | Bacterial Pneumonia | X | X | X |

## Metrics (Test Set)
- **Accuracy:** X.XX%
- **F1 Score (macro):** X.XX
- **F1 Score (weighted):** X.XX

### Per-Class Metrics
| Classe | Precision | Recall | F1 | Support |
|--------|-----------|--------|-------|---------|
| Covid-19 | | | | |
| Normal | | | | |
| Viral Pneumonia | | | | |
| Bacterial Pneumonia | | | | |

### Confusion Matrix
[Incluir imagem ou tabela]

## OOD Detection
- **Método:** Cosine similarity no espaço de embeddings (GAP layer, 2048-dim)
- **Threshold:** 0.45
- **Referência:** [N] imagens de raio-X reais
- **Performance:**
  - True Positive Rate (imagens não-X-ray detectadas): X%
  - False Positive Rate (X-rays rejeitados incorretamente): X%

## Explainability
- **Método:** Grad-CAM (Gradient-weighted Class Activation Mapping)
- **Layer alvo:** Última camada convolucional do ResNet50
- **Visualização:** Heatmap sobreposto à imagem original

## Ethical Considerations
- Modelo treinado em dataset específico — pode ter bias demográfico
- Não validado clinicamente
- Não substitui diagnóstico médico profissional
- Performance pode degradar com imagens de equipamentos diferentes do treino

## Limitations
- Apenas 4 classes — não detecta outras patologias
- Sensível à qualidade da imagem (rotação, recorte, contraste)
- OOD detection pode falhar com imagens médicas de outras regiões anatômicas
```

**Script para gerar métricas automaticamente:** `training/evaluate.py`
```python
"""
Gera métricas e artefatos para o Model Card.

Uso:
    python evaluate.py --model ../models/chest_xray_model.keras --test-dir ../data/chest_xray/test
"""
import argparse
import json
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_curve,
    auc,
)

CLASS_NAMES = ["Covid-19", "Normal", "Viral Pneumonia", "Bacterial Pneumonia"]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--test-dir", required=True)
    parser.add_argument("--output-dir", default="./evaluation_results")
    args = parser.parse_args()

    output = Path(args.output_dir)
    output.mkdir(exist_ok=True)

    model = tf.keras.models.load_model(args.model)
    test_ds = tf.keras.utils.image_dataset_from_directory(
        args.test_dir,
        image_size=(256, 256),
        batch_size=32,
        label_mode="int",
        shuffle=False,
    )

    y_true = np.concatenate([y.numpy() for _, y in test_ds])
    y_probs = model.predict(test_ds)
    y_pred = np.argmax(y_probs, axis=1)

    # Classification report
    report = classification_report(y_true, y_pred, target_names=CLASS_NAMES, output_dict=True)
    with open(output / "classification_report.json", "w") as f:
        json.dump(report, f, indent=2)

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES)
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.title("Confusion Matrix")
    plt.tight_layout()
    plt.savefig(output / "confusion_matrix.png", dpi=150)

    # ROC curves (one-vs-rest)
    plt.figure(figsize=(8, 6))
    for i, name in enumerate(CLASS_NAMES):
        y_bin = (y_true == i).astype(int)
        fpr, tpr, _ = roc_curve(y_bin, y_probs[:, i])
        roc_auc = auc(fpr, tpr)
        plt.plot(fpr, tpr, label=f"{name} (AUC={roc_auc:.3f})")
    plt.plot([0, 1], [0, 1], "k--")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curves (One-vs-Rest)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output / "roc_curves.png", dpi=150)

    print(f"Accuracy: {report['accuracy']:.4f}")
    print(f"F1 macro: {report['macro avg']['f1-score']:.4f}")
    print(f"Results saved to {output}")

if __name__ == "__main__":
    main()
```

---

## Fase 1 — Fundação de Produção

### Checklist

- [x] Docker + Docker Compose (detalhado acima na Seção Prioritária #1)
- [x] Migração para PostgreSQL
- [x] Alembic migrations
- [x] Variáveis de ambiente (.env)

---

### Migração para PostgreSQL

**Dependências backend:**
```bash
pip install asyncpg sqlalchemy[asyncio] alembic
```

**Modificar `backend/app/core/config.py`:**
```python
class Settings(BaseModel):
    database_url: str = "postgresql+asyncpg://radioai:radioai_dev@localhost:5432/radioai"
    # ... demais settings
```

**Modificar `backend/app/db/session.py`:**
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_async_engine(settings.database_url, echo=False, pool_size=20, max_overflow=10)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

---

### Alembic Migrations

**Inicializar:**
```bash
cd backend
alembic init alembic
```

**Configurar `backend/alembic.ini`:**
```ini
sqlalchemy.url = postgresql+asyncpg://radioai:radioai_dev@localhost:5432/radioai
```

**Configurar `backend/alembic/env.py`:**
```python
from app.db.base import Base
from app.core.config import settings

config.set_main_option("sqlalchemy.url", settings.database_url)
target_metadata = Base.metadata
```

**Criar primeira migration:**
```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

---

### Variáveis de Ambiente

**Criar `/.env.example`:**
```env
# Database
DATABASE_URL=postgresql+asyncpg://radioai:radioai_dev@localhost:5432/radioai

# Auth
SECRET_KEY=change-this-to-a-random-64-char-string
ACCESS_TOKEN_EXPIRE_MINUTES=60

# ML
MODEL_PATH=models/chest_xray_model.keras
OOD_THRESHOLD=0.45
OOD_REFERENCE_DIR=examples

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

**Modificar `backend/app/core/config.py` para usar pydantic-settings:**
```bash
pip install pydantic-settings
```

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://radioai:radioai_dev@localhost:5432/radioai"
    secret_key: str = "dev-secret"
    access_token_expire_minutes: int = 60
    model_path: str = "models/chest_xray_model.keras"
    ood_threshold: float = 0.45
    ood_reference_dir: str = "examples"
    cors_origins: list[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

---

## Fase 2 — Qualidade e Confiança

### Checklist

- [x] Testes backend pytest (detalhado na Seção Prioritária #4)
- [x] Testes frontend (Vitest + Testing Library)
- [x] CI/CD GitHub Actions (detalhado na Seção Prioritária #2)
- [x] Pre-commit hooks

---

### Testes Frontend

**Arquivo `frontend/src/__tests__/Predict.test.tsx`:**
```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { Predict } from "@/pages/Predict";
import "../i18n"; // inicializar i18n

const wrapper = ({ children }: { children: React.ReactNode }) => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
};

describe("Predict page", () => {
  it("renders upload zone", () => {
    render(<Predict />, { wrapper });
    expect(screen.getByText(/arraste e solte/i)).toBeInTheDocument();
  });

  it("button is disabled without file", () => {
    render(<Predict />, { wrapper });
    const btn = screen.getByRole("button", { name: /executar/i });
    expect(btn).toBeDisabled();
  });

  it("shows error for invalid file type", async () => {
    render(<Predict />, { wrapper });
    const input = document.querySelector('input[type="file"]')!;
    const file = new File(["test"], "test.txt", { type: "text/plain" });
    await userEvent.upload(input, file);
    expect(screen.getByText(/tipo de arquivo não suportado/i)).toBeInTheDocument();
  });
});
```

---

### Pre-commit Hooks

**Dependências:**
```bash
pip install pre-commit
```

**Criar `/.pre-commit-config.yaml`:**
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1.0
    hooks:
      - id: prettier
        files: \.(ts|tsx|json|css|md)$

  - repo: local
    hooks:
      - id: tsc
        name: TypeScript check
        entry: bash -c 'cd frontend && npx tsc --noEmit'
        language: system
        pass_filenames: false
        files: \.(ts|tsx)$
```

**Instalar:**
```bash
pre-commit install
pre-commit run --all-files  # verificar
```

---

## Fase 3 — MLOps (ML Reproduzível)

### Checklist

- [x] MLflow experiment tracking (detalhado na Seção Prioritária #3)
- [x] Script de treino reproduzível (detalhado na Seção Prioritária #3)
- [x] DVC para versionamento de dados
- [x] Model Card (detalhado na Seção Prioritária #5)
- [x] Validação estatística do threshold OOD

---

### DVC (Data Version Control)

**Instalar:**
```bash
pip install dvc dvc-gdrive   # ou dvc-s3 para AWS
```

**Inicializar:**
```bash
dvc init
dvc remote add -d storage gdrive://FOLDER_ID
```

**Versionar dataset:**
```bash
dvc add data/chest_xray
git add data/chest_xray.dvc data/.gitignore
git commit -m "Track dataset with DVC"
dvc push
```

**Reproduzir:**
```bash
dvc pull                       # baixa dataset
python training/train.py       # treina
```

---

### Validação Estatística do Threshold OOD

**Criar `training/validate_ood_threshold.py`:**
```python
"""
Valida o threshold OOD com análise estatística.

Usa dois conjuntos:
  - in_distribution/: imagens de raio-X (devem ter alta similaridade)
  - out_distribution/: imagens aleatórias (devem ter baixa similaridade)

Saída: ROC curve, precision/recall, threshold ótimo.
"""
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc, precision_recall_curve
from app.ml.predictor import Predictor
from pathlib import Path

def collect_similarities(predictor, image_dir: Path) -> list[float]:
    sims = []
    for img_path in image_dir.glob("*.*"):
        if img_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
            embedding = predictor._get_embedding(img_path)
            sim = predictor._cosine_similarity(embedding, predictor._ood_reference_mean)
            sims.append(float(sim))
    return sims

def main():
    predictor = Predictor(
        model_path="models/chest_xray_model.keras",
        ood_threshold=0.45,
        ood_reference_dir="examples",
    )

    in_dist = collect_similarities(predictor, Path("data/ood_validation/in_distribution"))
    out_dist = collect_similarities(predictor, Path("data/ood_validation/out_distribution"))

    # Labels: 0 = in-distribution, 1 = out-of-distribution
    y_true = np.array([0] * len(in_dist) + [1] * len(out_dist))
    # Scores: 1 - similarity (higher = more OOD)
    scores = np.array([1 - s for s in in_dist] + [1 - s for s in out_dist])

    # ROC
    fpr, tpr, thresholds = roc_curve(y_true, scores)
    roc_auc = auc(fpr, tpr)

    # Optimal threshold (Youden's J)
    j_scores = tpr - fpr
    optimal_idx = np.argmax(j_scores)
    optimal_threshold = 1 - thresholds[optimal_idx]  # converter de volta para similaridade

    print(f"AUC: {roc_auc:.4f}")
    print(f"Threshold ótimo (similaridade): {optimal_threshold:.4f}")
    print(f"In-dist mean: {np.mean(in_dist):.4f} ± {np.std(in_dist):.4f}")
    print(f"Out-dist mean: {np.mean(out_dist):.4f} ± {np.std(out_dist):.4f}")

    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].plot(fpr, tpr, label=f"ROC (AUC={roc_auc:.3f})")
    axes[0].plot([0, 1], [0, 1], "k--")
    axes[0].set_xlabel("FPR")
    axes[0].set_ylabel("TPR")
    axes[0].set_title("ROC Curve - OOD Detection")
    axes[0].legend()

    axes[1].hist(in_dist, bins=30, alpha=0.7, label="In-distribution", color="green")
    axes[1].hist(out_dist, bins=30, alpha=0.7, label="Out-of-distribution", color="red")
    axes[1].axvline(optimal_threshold, color="black", linestyle="--", label=f"Threshold={optimal_threshold:.3f}")
    axes[1].set_xlabel("Cosine Similarity")
    axes[1].set_ylabel("Count")
    axes[1].set_title("Similarity Distribution")
    axes[1].legend()

    plt.tight_layout()
    plt.savefig("evaluation_results/ood_validation.png", dpi=150)
    print("Plot saved to evaluation_results/ood_validation.png")

if __name__ == "__main__":
    main()
```

---

## Fase 4 — Observabilidade e Segurança

### Checklist

- [x] Health check endpoint
- [x] Logging estruturado (structlog)
- [x] Rate limiting
- [x] CORS restritivo
- [x] Security headers
- [ ] Prometheus metrics (opcional)

---

### Health Check Endpoint

**Criar `backend/app/api/routers/health.py`:**
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check — verifica DB e modelo."""
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    from app.ml.predictor import get_predictor
    model_ok = get_predictor() is not None

    status = "healthy" if (db_ok and model_ok) else "unhealthy"
    return {
        "status": status,
        "checks": {
            "database": "ok" if db_ok else "error",
            "model": "ok" if model_ok else "error",
        },
    }
```

**Registrar no `backend/app/main.py`:**
```python
from app.api.routers.health import router as health_router
app.include_router(health_router, prefix="/api")
```

---

### Logging Estruturado

**Instalar:**
```bash
pip install structlog
```

**Criar `backend/app/core/logging.py`:**
```python
import structlog
import logging

def setup_logging():
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    logging.basicConfig(level=logging.INFO, format="%(message)s")
```

**Middleware de request logging (`backend/app/middleware/logging.py`):**
```python
import time
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = structlog.get_logger()

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(elapsed_ms, 1),
            user_agent=request.headers.get("user-agent", ""),
        )
        return response
```

---

### Rate Limiting

**Instalar:**
```bash
pip install slowapi
```

**Configurar no `backend/app/main.py`:**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

**Aplicar no endpoint de predição:**
```python
from slowapi import limiter

@router.post("/predict")
@limiter.limit("10/minute")  # máximo 10 predições por minuto por IP
async def predict_endpoint(request: Request, ...):
    ...
```

---

### CORS Restritivo

**Modificar `backend/app/main.py`:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # lista específica, não "*"
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,
)
```

---

### Security Headers

**Criar `backend/app/middleware/security.py`:**
```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response
```

---

## Fase 5 — Escala e Sofisticação

### Checklist

- [x] Background worker (Celery + Redis)
- [x] Cache de predições (Redis)
- [x] Monitoramento de drift
- [ ] A/B testing de modelos (champion-challenger)

---

### Background Worker (Celery + Redis)

**Dependências:**
```bash
pip install celery[redis] redis
```

**Adicionar ao `docker-compose.yml`:**
```yaml
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

  worker:
    build:
      context: .
      dockerfile: Dockerfile.backend
    command: celery -A app.worker worker -l info -c 2
    environment:
      CELERY_BROKER_URL: redis://redis:6379/0
      DATABASE_URL: postgresql+asyncpg://radioai:${DB_PASSWORD:-radioai_dev}@db:5432/radioai
    depends_on:
      - redis
      - db
```

**Criar `backend/app/worker.py`:**
```python
from celery import Celery

celery_app = Celery(
    "radioai",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)

celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.task_track_started = True
```

**Criar `backend/app/tasks/prediction.py`:**
```python
from app.worker import celery_app
from app.ml.predictor import get_predictor

@celery_app.task(bind=True, max_retries=2, time_limit=60)
def run_prediction(self, image_path: str, user_id: int):
    """Executa predição em background."""
    predictor = get_predictor()
    result = predictor.predict(image_path)
    # Salvar resultado no banco...
    return result
```

---

### Cache de Predições (Redis)

**Criar `backend/app/core/cache.py`:**
```python
import hashlib
import json
import redis.asyncio as redis
from app.core.config import settings

_pool: redis.Redis | None = None

async def get_redis() -> redis.Redis:
    global _pool
    if _pool is None:
        _pool = redis.from_url(settings.redis_url, decode_responses=True)
    return _pool

def image_hash(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()

async def get_cached_prediction(hash_key: str) -> dict | None:
    r = await get_redis()
    data = await r.get(f"pred:{hash_key}")
    return json.loads(data) if data else None

async def cache_prediction(hash_key: str, result: dict, ttl: int = 3600):
    r = await get_redis()
    await r.setex(f"pred:{hash_key}", ttl, json.dumps(result))
```

---

### Monitoramento de Drift

**Conceito:** Comparar distribuição de predições recentes vs. baseline.

**Criar `backend/app/monitoring/drift.py`:**
```python
"""
Monitora drift na distribuição de classes e confidence.

Executa periodicamente (via cron ou Celery beat) e emite alertas
quando a distribuição difere significativamente do baseline.
"""
import numpy as np
from scipy.stats import ks_2samp, chi2_contingency
from datetime import datetime, timedelta
from sqlalchemy import select, func
from app.db.models import Prediction

async def check_class_drift(session, window_days: int = 7) -> dict:
    """Chi-squared test na distribuição de classes."""
    cutoff = datetime.utcnow() - timedelta(days=window_days)

    # Distribuição recente
    recent = await session.execute(
        select(Prediction.predicted_class, func.count())
        .where(Prediction.created_at >= cutoff)
        .group_by(Prediction.predicted_class)
    )
    recent_counts = dict(recent.all())

    # Baseline (todo o histórico antes do window)
    baseline = await session.execute(
        select(Prediction.predicted_class, func.count())
        .where(Prediction.created_at < cutoff)
        .group_by(Prediction.predicted_class)
    )
    baseline_counts = dict(baseline.all())

    if not baseline_counts or not recent_counts:
        return {"drift_detected": False, "reason": "insufficient_data"}

    # Alinhar classes
    classes = sorted(set(list(recent_counts.keys()) + list(baseline_counts.keys())))
    observed = [recent_counts.get(c, 0) for c in classes]
    expected_raw = [baseline_counts.get(c, 0) for c in classes]

    # Normalizar expected para o mesmo total
    total_obs = sum(observed)
    total_exp = sum(expected_raw)
    expected = [e * total_obs / total_exp for e in expected_raw]

    from scipy.stats import chisquare
    stat, p_value = chisquare(observed, expected)

    return {
        "drift_detected": p_value < 0.05,
        "p_value": float(p_value),
        "chi2_statistic": float(stat),
        "window_days": window_days,
        "recent_total": total_obs,
    }

async def check_confidence_drift(session, window_days: int = 7) -> dict:
    """KS test na distribuição de confidence."""
    cutoff = datetime.utcnow() - timedelta(days=window_days)

    recent = await session.execute(
        select(Prediction.confidence).where(Prediction.created_at >= cutoff)
    )
    recent_vals = [r[0] for r in recent.all()]

    baseline = await session.execute(
        select(Prediction.confidence).where(Prediction.created_at < cutoff)
    )
    baseline_vals = [r[0] for r in baseline.all()]

    if len(recent_vals) < 10 or len(baseline_vals) < 10:
        return {"drift_detected": False, "reason": "insufficient_data"}

    stat, p_value = ks_2samp(recent_vals, baseline_vals)

    return {
        "drift_detected": p_value < 0.05,
        "p_value": float(p_value),
        "ks_statistic": float(stat),
        "recent_mean_confidence": float(np.mean(recent_vals)),
        "baseline_mean_confidence": float(np.mean(baseline_vals)),
    }
```

---

## Estrutura Final de Diretórios (Alvo)

```
Departamento_Medico_ML/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .pre-commit-config.yaml
├── .env.example
├── .dockerignore
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── nginx.conf
├── PRD-V1.md
│
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── alembic.ini
│   ├── app/
│   │   ├── api/routers/
│   │   │   ├── health.py          ← NOVO
│   │   │   ├── predictions.py
│   │   │   └── auth.py
│   │   ├── core/
│   │   │   ├── config.py          ← MODIFICAR (pydantic-settings)
│   │   │   ├── cache.py           ← NOVO
│   │   │   └── logging.py         ← NOVO
│   │   ├── middleware/
│   │   │   ├── logging.py         ← NOVO
│   │   │   └── security.py        ← NOVO
│   │   ├── ml/
│   │   │   ├── predictor.py
│   │   │   └── labels.py
│   │   ├── monitoring/
│   │   │   └── drift.py           ← NOVO
│   │   ├── tasks/
│   │   │   └── prediction.py      ← NOVO
│   │   ├── worker.py              ← NOVO
│   │   └── main.py                ← MODIFICAR
│   ├── tests/
│   │   ├── conftest.py            ← NOVO/EXPANDIR
│   │   ├── test_auth.py
│   │   ├── test_predictions.py
│   │   ├── test_predictor.py      ← NOVO
│   │   ├── test_ood.py            ← NOVO
│   │   ├── test_health.py         ← NOVO
│   │   └── fixtures/
│   │       ├── covid_sample.jpg
│   │       ├── normal_sample.jpg
│   │       └── text_sample.png
│   └── requirements.txt           ← MODIFICAR
│
├── frontend/
│   ├── src/
│   │   ├── __tests__/
│   │   │   ├── Predict.test.tsx   ← NOVO
│   │   │   └── History.test.tsx   ← NOVO
│   │   └── ...
│   └── ...
│
├── training/
│   ├── train.py                   ← NOVO
│   ├── evaluate.py                ← NOVO
│   ├── validate_ood_threshold.py  ← NOVO
│   ├── config.yaml                ← NOVO
│   ├── requirements.txt           ← NOVO
│   └── README.md                  ← NOVO
│
├── models/
│   ├── chest_xray_model.keras
│   └── MODEL_CARD.md              ← NOVO
│
├── data/
│   ├── chest_xray.dvc             ← NOVO (DVC tracking)
│   └── ood_validation/
│       ├── in_distribution/       ← NOVO
│       └── out_distribution/      ← NOVO
│
└── evaluation_results/            ← NOVO (gerado por scripts)
    ├── classification_report.json
    ├── confusion_matrix.png
    ├── roc_curves.png
    └── ood_validation.png
```

---

## Notas para Implementação por LLM

1. **Ordem de implementação recomendada:** Fase 1 → 2 → 3 → 4 → 5
2. **Cada item é independente** — pode ser implementado em qualquer ordem dentro da fase
3. **Sempre verificar build** após cada mudança: `npx tsc --noEmit` (frontend) e `ruff check .` (backend)
4. **Não quebrar funcionalidade existente** — o sistema já funciona, apenas adicionar
5. **Manter i18n** — novos textos devem ser adicionados aos arquivos `src/locales/*.json`
6. **Backend atual usa SQLite** — a migração para PostgreSQL deve manter backward-compatibility temporária via env var
7. **O modelo `.keras` já existe** em `models/` — os scripts de treino são para reproduzir, não para re-treinar agora
