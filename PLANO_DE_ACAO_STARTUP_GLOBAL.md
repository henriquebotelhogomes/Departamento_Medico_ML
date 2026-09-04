# 🏥 RadioAI — Master Plan de Engenharia & Roadmap Startup Global

> **Documento Oficial de Especificação Técnica, Arquitetura e Checklist de Execução**  
> **Repositório:** `henriquebotelhogomes/Departamento_Medico_ML`  
> **Status:** Especificação Aprovada & Aguardando Início da Implementação  
> **Padrão de Qualidade:** Nível MedTech Series A+ / Padrão Institucional Hospitalar

---

## 📑 Índice
1. [Visão Geral & Objetivos Estratégicos](#-1-visão-geral--objetivos-estratégicos)
2. [Módulo 1: Layout & Estação de Trabalho PACS Hospitalar (Frontend)](#-2-módulo-1-layout--estação-de-trabalho-pacs-hospitalar-frontend)
3. [Módulo 2: Motor Multi-LLM de Laudos Radiológicos com Seletor Interativo](#-3-módulo-2-motor-multi-llm-de-laudos-radiológicos-com-seletor-interativo)
4. [Módulo 3: Suporte a Arquivos DICOM (.dcm) & Gerador de Amostras](#-4-módulo-3-suporte-a-arquivos-dicom-dcm--gerador-de-amostras)
5. [Módulo 4: Infraestrutura & Hospedagem Serverless no Google Cloud Run ($0/mês)](#-5-módulo-4-infraestrutura--hospedagem-serverless-no-google-cloud-run-0mês)
6. [Módulo 5: Governança, Multi-Agentes & Skills Globais](#-6-módulo-5-governança-multi-agentes--skills-globais)
7. [Checklist Geral de Status & Execução (Task Board)](#-7-checklist-geral-de-status--execução-task-board)

---

## 🎯 1. Visão Geral & Objetivos Estratégicos

O objetivo deste plano é elevar o **RadioAI** de uma aplicação de portfólio intermediária para uma **vitrine de nível internacional em Inteligência Artificial Médica e Engenharia Full-Stack**, atraindo recrutadores, líderes técnicos e parcerias no LinkedIn e GitHub.

### Metas Técnicas e de Produto:
1. **Fricção Zero para Recrutadores**: Permitir que qualquer visitante teste imagens médicas reais (incluindo DICOM) com **1 clique**, sem login obrigatório e sem necessidade de baixar arquivos.
2. **Experiência Hospitalar Autêntica**: Substituir o layout genérico de dashboard por uma **Workstation Radiológica (PACS)** moderna, com controles de imagem (Windowing/Leveling, Invert, Grad-CAM slider).
3. **Inteligência Híbrida Vision + LLM**: Integrar a inferência do modelo ResNet50 a um motor gerador de laudos radiológicos descritivos estruturados (Achados, Impressão e CID-10), com um seletor visual entre as 5 melhores LLMs da atualidade.
4. **Custo de Operação $0,00/mês**: Hospedagem serverless no Google Cloud Run com política de *Scale-to-Zero*, aproveitando cotas gratuitas mensais e do ecossistema Google.

---

## 🖥️ 2. Módulo 1: Layout & Estação de Trabalho PACS Hospitalar (Frontend)

### Conceito Visual & Design System
- **Tema:** *Dark Clinical Radiology* (`#0A0E17` / `slate-950`), com contraste médico preto-e-branco de alta precisão.
- **Tipografia:** Monospace técnica para métricas e HUD (`font-mono`), Sans moderna para laudos e controles (`Inter` ou `Plus Jakarta Sans`).
- **Arquitetura Visual:**
  - **Barra Superior (Header Clínico):** Identificação do exame (`#XR-2026-XXXX`), modalidade (`CR/DX`), tempo de inferência (`ms`) e status de triagem com código de cores (Normal = Verde, Covid/Pneumonias = Vermelho/Laranja, OOD = Amarelo Alerta).
  - **Visualizador Radiológico Central (Viewport):**
    - HUD sobre a imagem com marcadores anatômicos laterais (`L` / `R`), projeção (`PA Upright`) e dados técnicos do tubo de raio-X.
    - Barra de ferramentas radiológicas superior:
      - 🎚️ **Window/Level Presets:** Pulmão (alta penetração para infiltrados), Osso (contraste ósseo/arcos costais) e Mediastino (silhueta cardíaca).
      - 🔄 **Invert Grayscale:** Inversão preto-e-branco (recurso clínico para identificação de pneumotórax e nódulos discretos).
      - 🔴 **Slider de Opacidade Grad-CAM:** Controle fluido de 0% (apenas raio-X limpo) a 100% (mapa térmico total), permitindo comparar a anatomia subjacente com a ativação neural.
      - 🔍 **Zoom & Pan:** Manipulação vetorial sem degradação visual.
  - **Painel Lateral Clínico (Right Drawer / Sidebar):**
    - Badge de Triagem de Urgência & Confiança Calibrada.
    - Gráfico de probabilidade das 4 classes clínicas + métrica de incerteza.
    - Seletor de LLMs e Card de Laudo Radiológico Estruturado.
    - Botões de Ação: `[📄 Exportar Laudo PDF]` e `[💾 Baixar Imagem com Heatmap]`.
  - **Rodapé de Acesso Rápido ("1-Click Demo"):**
    - Amostras pré-carregadas: `Normal`, `Covid-19`, `Pneumonia Bacteriana`, `Pneumonia Viral`, `Anomalia OOD (Rejeição)` e `Amostra DICOM (.dcm)`.

---

## 🤖 3. Módulo 2: Motor Multi-LLM de Laudos Radiológicos com Seletor Interativo

### O Seletor na Interface (Dropdown Customizado)
Na seção de laudos da interface, o usuário terá um `<select>` estilizado com ícones e badges destacando os 5 modelos suportados:

| # | Modelo | Provedor / Cota | Selo na UI | Papel Clínico no Laudo |
| :-: | :--- | :--- | :--- | :--- |
| **1** | **Gemini 3.8 Flash** | Google AI Studio (Free Tier) | `[⚡ Padrão / Custo Zero]` | Modelo padrão: Rápido, multimodal nativo, sem custo adicional. |
| **2** | **GPT 5.6 Luna** | OpenCode Go (2.050 reqs) | `[🔬 Alta Precisão Clínica]` | Diagnósticos complexos e correlações anatômicas aprofundadas. |
| **3** | **DeepSeek V4 Flash** | OpenCode Go (7.600 reqs) | `[🧠 Raciocínio & CID-10]` | Raciocínio lógico, estruturação JSON e mapeamento nosológico. |
| **4** | **Qwen 3.8 Flash** | OpenCode Go (5.400 reqs) | `[🌐 Estruturação Médica]` | Excelente robustez multilíngue e clareza terminológica. |
| **5** | **Motor Determinístico Local** | Local Backend (Regras) | `[🔒 Offline / Seguro]` | Resiliência total: funciona offline sem depender de APIs ou chaves. |

### Estrutura Padronizada do Laudo Radiológico Gerado
Qualquer uma das LLMs receberá um prompt médico rígido (*Few-Shot Grounding*) para retornar um laudo no formato padrão internacional:
1. **Técnica do Exame:** Incidência posteroanterior (PA), paciente em ortostase.
2. **Achados Radiológicos:** Descrição detalhada dos campos pleuropulmonares (opacidades, consolidações, infiltrados, seios costofrênicos, área cardíaca).
3. **Impressão Diagnóstica:** Conclusão alinhada à predição neural do ResNet50 e às regiões destacadas pelo Grad-CAM.
4. **Classificação CID-10:** Código internacional sugerido (ex: `U07.1` para Covid-19, `J15.9` para Pneumonia Bacteriana, `J12.9` para Pneumonia Viral).
5. **Recomendações Clínicas:** Sugestões de correlação clínico-laboratorial.
6. **Disclaimer Obrigatório:** Alerta de que a predição é um suporte à decisão clínica e não substitui o médico radiologista.

---

## 🩻 4. Módulo 3: Suporte a Arquivos DICOM (.dcm) & Gerador de Amostras

### Desafio Resolvido
O usuário e os recrutadores não possuem arquivos DICOM em suas máquinas pessoais para testar o sistema.

### Soluções Integradas:
1. **Gerador Interno de Amostras DICOM (`scripts/generate_sample_dicoms.py`)**:
   - Script em Python utilizando `pydicom` para converter radiografias de teste do repositório em arquivos `.dcm` válidos e clinicamente compatíveis com o padrão DICOM PS 3.15.
   - Metadados injetados:
     - `StudyDate`, `SeriesDate`, `Modality = "CR"`
     - `BodyPartExamined = "CHEST"`, `PatientPosition = "PA"`
     - `WindowCenter = 2048`, `WindowWidth = 4096`
     - `PhotometricInterpretation = "MONOCHROME2"`
   - Armazenamento em `examples/dicom/`:
     - `amostra_normal.dcm`
     - `amostra_covid.dcm`
     - `amostra_pneumonia_bacteriana.dcm`
2. **Parser & Sanitizador DICOM no Backend (`backend/app/ml/dicom_handler.py`)**:
   - Extração do array de pixels e aplicação de curva de Hounsfield/Rescale Slope.
   - **Anonimização Automática (De-identification):** Remoção de nomes, prontuários e CPFs antes da inferência e da persistência.
3. **Botão no Frontend:** *"Testar com Amostra DICOM (.dcm)"* e link para download das amostras de teste.

---

## ☁️ 5. Módulo 4: Infraestrutura & Hospedagem Serverless no Google Cloud Run ($0/mês)

### Arquitetura de Custo Zero
- **Serviço:** Google Cloud Run (Fully Managed Serverless Container).
- **Scale-to-Zero:** `min-instances = 0`, `max-instances = 2`.
- **Cota Gratuita Permanente (Free Tier Mensal do GCP):**
  - 2 milhões de requisições por mês grátis.
  - 360.000 GB-segundos de memória grátis.
  - 180.000 vCPU-segundos grátis.
  - 1 GB de transferência de rede de saída grátis.
- **Cold Start:** 2 a 4 segundos (em contraste com 60 segundos do Render gratuito).
- **Custo Mensal Estimado:** **R$ 0,00** para tráfego normal de portfólio.
- **Scripts & Configuração:**
  - Criação de `cloudbuild.yaml` e script automatizado `scripts/deploy_gcp.sh`.

---

## 🛡️ 6. Módulo 5: Governança, Multi-Agentes & Skills Globais

### Personas Definidas no `AGENTS.md`
- 🧠 `CV & Medical AI Scientist`: Gestão de ResNet50, Grad-CAM, OOD e ONNX.
- ⚡ `Backend Core Engineer`: FastAPI assíncrono, SQLAlchemy, factory multi-LLM.
- 🩺 `Clinical Frontend Architect`: React 18, PACS workstation, W/L, acessibilidade.
- 🐳 `MLOps & SRE Engineer`: Docker, Cloud Run, GitHub Actions, métricas.
- 🛡️ `Health Compliance Officer`: Anonimização DICOM PS 3.15, LGPD e HIPAA.

### Criação das Duas Novas Skills Globais:
1. **`healthtech-medical-imaging`**: Guia para manipulação de dados DICOM, normas de radiologia, calibração de modelos clínicos e conformidade HIPAA/LGPD.
2. **`gcp-cloud-run-deployment`**: Guia para deploy conteinerizado serverless no Google Cloud Run com política de scale-to-zero e custo $0.

---

## 📋 7. Checklist Geral de Status & Execução (Task Board)

### Legenda de Status:
- `[ ]` Não iniciado
- `[⏳]` Planejado / Especificado
- `[🔬]` Em desenvolvimento
- `[✅]` Concluído
- `[🧪]` Testado e validado

---

#### Fase 1: DICOM & Geração de Amostras de Teste
| Status | Tarefa | Responsável | Detalhes |
| :---: | :--- | :--- | :--- |
| `[✅]` | Criar `scripts/generate_sample_dicoms.py` | `CV & AI Scientist` | Converte radiografias em arquivos `.dcm` válidos com headers clínicos reais. |
| `[✅]` | Gerar e salvar amostras em `examples/dicom/` | `CV & AI Scientist` | Amostras geradas de Normal, Covid e Pneumonias prontas para uso. |
| `[✅]` | Criar `backend/app/ml/dicom_handler.py` | `Backend Engineer` | Extração de pixels, normalização Hounsfield e de-identification (PS 3.15). |
| `[✅]` | Atualizar endpoint `/predict` para aceitar `.dcm` | `Backend Engineer` | Suporte híbrido transparente para JPEG, PNG e DICOM nativo (.dcm). |
| `[✅]` | Testes unitários para o módulo DICOM | `Backend Engineer` | Validação completa em `test_dicom_and_report.py`. |

---

### Fase 2: Motor Multi-LLM de Laudos Radiológicos
| Status | Tarefa | Responsável | Detalhes |
| :---: | :--- | :--- | :--- |
| `[✅]` | Criar `backend/app/services/llm_report.py` | `Backend Engineer` | Factory multi-provedor (Google AI Studio + OpenCode Go + Motor Local). |
| `[✅]` | Suporte ao Gemini 3.8 Flash | `Backend Engineer` | Integração direta via Google AI Studio API. |
| `[✅]` | Suporte a GPT 5.6, DeepSeek V4 e Qwen 3.8 | `Backend Engineer` | Integração via cliente OpenCode Go (OpenAI-compatible). |
| `[✅]` | Implementar Motor Local Determinístico | `Backend Engineer` | Geração de laudos estruturados offline com base em templates clínicos. |
| `[✅]` | Criar endpoint `POST /api/predictions/report` | `Backend Engineer` | Endpoint para solicitar laudo com base na predição, Grad-CAM e modelo. |
| `[✅]` | Atualizar configurações de LLM | `Backend Engineer` | Adicionados em `config.py` e schemas Pydantic. |

---

### Fase 3: Layout & Estação de Trabalho PACS (Frontend)
| Status | Tarefa | Responsável | Detalhes |
| :---: | :--- | :--- | :--- |
| `[✅]` | Redesenhar Layout Geral para Tema Dark Clínico | `Frontend Architect` | Fundo escuro de alto contraste hospitalar `#0A0E17`. |
| `[✅]` | Criar Viewport Radiológico Interativo (`PacsViewer`) | `Frontend Architect` | HUD com marcadores `L`/`R`, dados técnicos e canvas de alta fidelidade. |
| `[✅]` | Implementar Presets de Windowing / Leveling | `Frontend Architect` | Presets Pulmão, Osso, Mediastino e Padrão em tempo real. |
| `[✅]` | Adicionar Slider de Opacidade do Grad-CAM | `Frontend Architect` | Controle de blend de 0% a 100% entre raio-X puro e mapa térmico. |
| `[✅]` | Implementar Botão de Inversão de Cores | `Frontend Architect` | Alternância instantânea entre visão positiva e negativa (Invert). |
| `[✅]` | Adicionar Seletor Visual das 5 LLMs (`MedicalReportCard`) | `Frontend Architect` | Dropdown estilizado para Gemini 3.8, GPT 5.6, DeepSeek V4, Qwen 3.8 e Local. |
| `[✅]` | Integrar Card do Laudo Médico Estruturado | `Frontend Architect` | Visual de prontuário com Achados, Impressão, CID-10 e Recomendações. |
| `[✅]` | Adicionar Galeria "1-Click Demo" | `Frontend Architect` | 6 amostras instantâneas (Normal, Covid, Pneumonias, OOD e DICOM). |
| `[✅]` | Implementar Exportação e Impressão | `Frontend Architect` | Botões de cópia de laudo e impressão/PDF médico. |

---

### Fase 4: Deploy no Google Cloud Run ($0/mês) & Novas Skills
| Status | Tarefa | Responsável | Detalhes |
| :---: | :--- | :--- | :--- |
| `[✅]` | Criar `cloudbuild.yaml` e `scripts/deploy_cloud_run.sh` | `MLOps Engineer` | Automação de build e deploy no Cloud Run com scale-to-zero. |
| `[✅]` | Criar skill global `healthtech-medical-imaging` | `Lead Architect` | Salva e ativa em `C:\Users\henri\.gemini\config\skills\healthtech-medical-imaging\`. |
| `[✅]` | Criar skill global `gcp-cloud-run-deployment` | `MLOps Engineer` | Salva e ativa em `C:\Users\henri\.gemini\config\skills\gcp-cloud-run-deployment\`. |

---

### Fase 5: Validação, Testes Integrados & Documentação
| Status | Tarefa | Responsável | Detalhes |
| :---: | :--- | :--- | :--- |
| `[✅]` | Executar testes completos do Backend (`pytest`) | `Backend Engineer` | **35/35 testes passaram** (inferência, OOD, Grad-CAM, DICOM e LLM). |
| `[✅]` | Executar testes e build do Frontend (`vitest` / `vite build`) | `Frontend Architect` | **14/14 testes passaram** e build de produção concluído com sucesso. |
| `[✅]` | Atualizar documentação e checklist de status | `Lead Architect` | Todos os módulos documentados e validados. |

