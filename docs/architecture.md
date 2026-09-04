# Architecture

RadioAI segue uma arquitetura modular de padrão hospitalar (*Enterprise MedTech*):

```mermaid
graph TB
    subgraph Frontend ["Frontend (React 18 + Vite + TypeScript)"]
        A[PACS Viewport & Sliders]
        A1[1-Click Clinical Demo Gallery]
        A2[Human-in-the-Loop Override]
        A3[A4 Medical Print Engine]
    end

    subgraph Backend ["Backend (FastAPI + Async SQLAlchemy)"]
        B[API Routers & Auth JWT]
        DH[DICOM Handler & PS 3.15 De-identifier]
        D[ML Predictor: ResNet50 + Grad-CAM + OOD]
        LLM[Multi-LLM Clinical Engine: Gemini / GPT / DeepSeek / Qwen / Local]
        C[Database Layer: PostgreSQL / SQLite]
        E[Storage Backend: Local / Supabase]
    end

    A -->|Upload DICOM/Img & Infer| B
    A2 -->|Intervenção / Override| B
    B --> DH
    DH --> D
    B --> LLM
    B --> C
    B --> E
    E -->|dev| F[Local Disk]
    E -->|prod| G[Supabase Storage]
    C -->|dev| H[SQLite]
    C -->|prod| I[PostgreSQL / Supabase]
```

## Production deployment

O sistema suporta implantação conteinerizada multi-stage:

1. **Stage 1** — Node 20 compila o SPA React otimizado com Tailwind CSS e tipos estritos.
2. **Stage 2** — Python 3.12 + `uv` instala o backend FastAPI e embute os assets em `app/static`.
3. **Scale-to-Zero ($0/mês)** — Deploy otimizado no **Google Cloud Run** permitindo redução automática a 0 instâncias quando ocioso.
4. **Always-on** — Deploy em **Render** ou instâncias dedicadas via `render.yaml` ou `docker-compose.yml`.

## Key design choices

- **De-identification HIPAA/LGPD**: Processamento seguro de arquivos DICOM com anonimização automática de tags PS 3.15 antes da persistência.
- **Human-in-the-Loop (HITL)**: Detecção estatística de margem estreita ($\Delta < 15\%$) e poder de sobrescrita soberana para o médico assistente.
- **Consenso Multi-LLM**: Roteamento dinâmico para Google AI Studio e OpenCode Zen, com fallback resiliente para motor médico determinístico local.
- **Config-driven DB**: `DATABASE_URL` alterna entre SQLite (local dev) e PostgreSQL (Supabase prod) sem alteração de código.
- **Config-driven Storage**: `STORAGE_BACKEND` alterna entre disco local e Supabase Storage (signed URLs).
- **Lazy model singleton**: O modelo Keras é carregado no startup; se o arquivo não estiver presente, a aplicação degrada graciosamente mantendo a documentação e histórico acessíveis.
- **uv para dependências Python**: Lockfile determinístico congelado (`uv.lock`), garantindo builds rápidos e reproduzíveis.
