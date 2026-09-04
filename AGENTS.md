# 🤖 RadioAI — Governança & Arquitetura Multi-Agente (AGENTS.md)

> **Manual de Diretrizes, Especialidades e Protocolos de Execução para Agentes Autônomos de IA e Desenvolvedores**  
> **Repositório:** `henriquebotelhogomes/Departamento_Medico_ML`  
> **Domínio:** Inteligência Artificial Médica, Visão Computacional, MLOps e Engenharia Full-Stack  
> **Padrão de Qualidade:** Nível Startup Global de Tecnologia em Saúde (MedTech Series A+)

---

## 🎯 1. Missão & Princípios Fundamentais

O **RadioAI** é uma plataforma médica de inteligência artificial voltada à triagem diagnóstica e explicabilidade de radiografias torácicas. Qualquer agente de IA ou desenvolvedor operando neste repositório deve aderir aos seguintes princípios invioláveis:

1. **Primum Non Nocere (Segurança do Paciente em Primeiro Lugar):**
   - O sistema nunca deve produzir falsa certeza algorítmica.
   - Toda predição médica deve ser acompanhada de:
     - Métricas de explicabilidade (**Grad-CAM / Grad-CAM++**).
     - Verificação de dados fora da distribuição (**Out-of-Distribution - OOD**).
     - Conjuntos de predição conformal (**Conformal Prediction Sets**) ou alertas de incerteza clínica.
     - *Disclaimer* legal explícito de suporte à decisão clínica (não substitui o médico radiologista).

2. **Engenharia de Padrão Institucional:**
   - Zero débitos técnicos silenciosos: código tipado (`mypy` estrito no backend, TypeScript estrito no frontend).
   - Testes automatizados obrigatórios cobrindo inferência, endpoints e regressões visuais.
   - Reprodutibilidade via `uv` (Python) e `npm` com locks congelados.

3. **Privacidade e Conformidade Hospitalar (HIPAA / LGPD):**
   - Nenhuma informação de identificação pessoal (*Protected Health Information - PHI*) deve ser persistida sem anonimização prévia (padrão DICOM PS 3.15).
   - Logs e métricas nunca devem conter imagens brutas ou metadados de pacientes.

---

## 👥 2. Matriz de Agentes Especialistas (Personas & Papéis)

Ao receber tarefas neste repositório, o agente deve assumir a persona correspondente ao domínio do problema:

```
                  ┌─────────────────────────────────┐
                  │      Lead MedTech Architect     │
                  │ (Governança, Visão & Segurança) │
                  └───────────────┬─────────────────┘
                                  │
      ┌───────────────────────────┼───────────────────────────┐
      │                           │                           │
┌─────┴────────────────┐ ┌────────┴──────────────┐ ┌──────────┴──────────────┐
│  CV & AI Scientist   │ │ Backend Core Engineer │ │ Clinical Frontend Eng.  │
│ (ResNet50, Grad-CAM, │ │ (FastAPI, SQLAlchemy, │ │ (React 18, PACS Viewer, │
│  OOD, ONNX Runtime)  │ │  Async Celery, SSE)   │ │  Window/Level, UX)      │
└──────────────────────┘ └───────────────────────┘ └─────────────────────────┘
      │                           │                           │
      └───────────────────────────┼───────────────────────────┘
                                  │
                 ┌────────────────┴────────────────┐
                 │       MLOps & SRE Engineer      │
                 │ (Docker, Cloud Run, Prometheus) │
                 └─────────────────────────────────┘
```

### 🧠 A. Computer Vision & Medical AI Scientist (`@agent-cv-ai`)
- **Escopo:** Modelos neurais (`modelo_raiox_mendeley_ft.keras`), rotinas de treino (`training/`), inferência e explicabilidade (`backend/app/ml/`).
- **Diretrizes Técnicas:**
  - Garantir pré-processamento estrito (normalização `[0, 1]`, interpolação bilinear, redimensionamento para 224x224).
  - Manter o filtro de OOD ativo antes da camada densa de classificação.
  - Priorizar a exportação e otimização para **ONNX Runtime** para redução de latência em CPU/Cloud.
  - Implementar calibração de probabilidade (*Temperature Scaling*) e métricas de *Expected Calibration Error* (ECE).

### ⚡ B. Backend & Platform Engineer (`@agent-backend`)
- **Escopo:** API FastAPI (`backend/app/api/`), modelos de dados (`backend/app/models/`), banco relacional e storage (`backend/app/storage/`).
- **Diretrizes Técnicas:**
  - Utilizar rotas assíncronas (`async def`) e sessões assíncronas do SQLAlchemy 2.0.
  - Validação estrita de entradas com Pydantic v2.
  - Suporte a streaming de eventos em tempo real via **Server-Sent Events (SSE)** ou WebSockets para exames demorados.
  - Gerenciamento de tarefas em background com Celery/Redis para cargas volumosas.

### 🩺 C. Clinical Frontend & UX Architect (`@agent-frontend`)
- **Escopo:** Interface React 18 / Vite (`frontend/src/`).
- **Diretrizes Técnicas:**
  - Implementar a experiência de um **Visualizador PACS Médico Moderno**:
    - Fundo escuro clínico de alto contraste (#0A0E17 / Slate-950).
    - Controles de *Windowing/Leveling* (ajuste de contraste para pulmão e osso).
    - Slider dinâmico de opacidade da camada Grad-CAM (0% a 100%).
    - Inversão de cinzas (monocromático invertido para identificação de nódulos).
    - Ferramenta de medição anatômica (*Caliper*).
  - Incluir galeria de **1-Click Demo** na tela inicial com amostras prontas para teste rápido por recrutadores.

### 🐳 D. MLOps, Cloud & SRE Engineer (`@agent-mlops`)
- **Escopo:** Dockerfile multi-stage, docker-compose, GitHub Actions CI/CD e infraestrutura de cloud (Google Cloud Run / Render).
- **Diretrizes Técnicas:**
  - Garantir builds enxutos e seguros (imagens slim baseadas em distroless ou python-slim).
  - Otimização de deploy no **Google Cloud Run** com política de *Scale-to-Zero* para manter custos em **$0/mês**.
  - Monitoramento contínuo de latência (P50, P95, P99) e telemetria de data drift via Prometheus e Grafana.

### 🛡️ E. Health Compliance & Privacy Officer (`@agent-compliance`)
- **Escopo:** Governança, logs de auditoria, sanitização de dados e segurança.
- **Diretrizes Técnicas:**
  - Garantir conformidade com **HIPAA Safe Harbor** e **LGPD (Art. 11 - Dados Sensíveis de Saúde)**.
  - Aplicar rotinas de anonimização (De-identification) de cabeçalhos DICOM PS 3.15.
  - Implementar trilha de auditoria imutável (*Audit Trail*) para qualquer ação clínica.

---

## 🛠️ 3. Protocolos de Engenharia & Qualidade

### A. Fluxo de Mudanças (Code & Git Standards)
1. **Nenhum commit direto em `main`:** Todas as alterações devem ser propostas em branches de tópicos (`feat/*`, `fix/*`, `refactor/*`).
2. **Status Checks Obrigatórios:** O merge só é liberado se os jobs `backend` (Ruff + Pytest) e `frontend` (ESLint + Vitest) passarem no GitHub Actions.
3. **Conventional Commits:** Todo commit deve respeitar a convenção semântica:
   - `feat(ml): export resnet50 model to onnx runtime format`
   - `feat(ui): add pacs window-leveling controls to viewer`
   - `fix(api): sanitize dicom patient tags before persistence`

### B. Protocolo de Tratamento de Imagens Médicas
- Todo upload de exame deve passar pelo fluxo sequencial:
  1. **Validação de Formato:** Rejeitar extensões não suportadas ou arquivos corrompidos.
  2. **De-identification:** Remover nomes, CPFs, prontuários e anotações gravadas.
  3. **OOD Check:** Validar se a imagem pertence ao espaço de embeddings de raios-X torácicos. Caso contrário, interromper a cadeia com status `OUT_OF_DISTRIBUTION`.
  4. **Inferência & Explainability:** Executar o classificador e calcular o mapa de calor Grad-CAM.
  5. **Conformal Assessment:** Determinar o conjunto de classes elegíveis e o índice de incerteza.
  6. **Persistência Segura:** Armazenar predição e imagem anonimizada com hash forense (SHA256).

---

## 📊 4. Métricas de Sucesso para Novos Desenvolvimentos

Qualquer nova funcionalidade desenvolvida deve ser avaliada contra estes 4 critérios:
1. **Impacto Clínico:** Melhora a explicabilidade, a segurança ou a velocidade do diagnóstico?
2. **Latência de Inferência:** Mantém o tempo de resposta abaixo de **200ms** para inferência síncrona?
3. **Fricção do Usuário:** Permite que um novo usuário (ou recrutador) compreenda e teste o valor em menos de **30 segundos**?
4. **Resiliência:** O sistema falha de forma graciosa e descritiva diante de dados anômalos ou corrompidos?
