# PRD: Framework de Avaliação Sistemática (Evals), Observabilidade & FinOps de LLMs Clínicas

> **Documento de Requisitos de Produto & Arquitetura Técnica (PRD)**  
> **Projeto:** RadioAI — Plataforma de Triagem Radiológica & Laudos com Inteligência Artificial  
> **Módulo:** GenAI Clinical Intelligence, Evaluation Framework & Observability Engine  
> **Versão:** 1.0.0  
> **Data:** 04 de Setembro de 2026  
> **Status:** Aprovado para Implementação  
> **Padrão de Qualidade:** Nível Startup Global de Tecnologia em Saúde (MedTech Series A+)  
> **Conformidade Regulatória:** HIPAA Safe Harbor / LGPD Art. 11 / Padrão DICOM PS 3.15  

---

## 1. Contexto & Diagnóstico do Problema

### 1.1. O Desafio em Produção Médica
O RadioAI integra com sucesso um modelo neural de Visão Computacional (ResNet50 fine-tuned) para classificação de radiografias torácicas em 4 classes clínicas (Covid-19, Normal, Pneumonia Viral, Pneumonia Bacteriana) com explainability via Grad-CAM e detecção Out-of-Distribution (OOD).

Para a emissão de laudos estruturados, a plataforma utiliza um ecossistema Multi-LLM (Google Gemini 3.8 Flash, GPT 5.6 Luna, DeepSeek V4 Flash, Qwen 3.7 Plus e Motor Determinístico Local).

No entanto, operar LLMs em ambientes de saúde sem ferramentas dedicadas de **avaliação sistemática contínua (*Evals*)** e **observabilidade especializada de IA** acarreta três riscos críticos:
1. **Risco Clínico de Alucinação Silenciosa:** Mudanças sutis de versão do modelo pelo provedor (ex: atualização interna de pesos ou recálculo de temperatura) podem introduzir novos termos radiológicos incorretos ou incompatíveis com a imagem sem que a equipe perceba.
2. **Opacidade Financeira (*FinOps Void*):** Falta de visibilidade em tempo real sobre quantos tokens cada laudo está consumindo, qual o custo financeiro unitário por exame e se determinado modelo está extrapolando o orçamento.
3. **Ausência de Telemetria de Resiliência:** Impossibilidade de quantificar a taxa de degradação/fallback (quantas vezes uma API externa caiu e foi substituída pelo motor local), mascarando instabilidades de provedores em produção.

### 1.2. Objetivos do Produto (OKRs)
* **Objetivo 1 (Qualidade Clínica Sistemática):** Estabelecer um pipeline automatizado de testes e benchmark de laudos (*Evals*) com Golden Dataset, garantindo 0% de alucinação estrutural e >= 98% de concordância com o código CID-10 e a decisão do médico assistente (*Human-in-the-Loop*).
* **Objetivo 2 (Observabilidade & FinOps Total):** Instrumentar 100% das chamadas a LLMs, extraindo latência líquida, contagem exata de tokens (entrada/saída) e custo estimado em USD/BRL em tempo real.
* **Objetivo 3 (Transparência Institucional para o Usuário):** Exibir na interface clínica os metadados de inferência da IA (tempo de geração, tokens consumidos e provedor ativo) e manter uma trilha de auditoria imutável no banco de dados.

---

## 2. Visão Geral da Arquitetura Proposta

`
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 ARQUITETURA ALVO                                       │
└────────────────────────────────────────────────────────────────────────────────────────┘

 [Requisição de Laudo] ──► [llm_report.py (Telemetry Wrapper)]
                                  │
      ┌───────────────────────────┼───────────────────────────┐
      │                           │                           │
      ▼                           ▼                           ▼
[Google Gemini API]     [OpenCode Zen API]      [Motor Local Determinístico]
 (usage_metadata)             (usage)                 (0 tokens / .00)
      │                           │                           │
      └───────────────────────────┼───────────────────────────┘
                                  │
                                  ▼
                   [Telemetry & FinOps Engine]
                   - Tokens (Prompt + Completion)
                   - Latência Líquida da LLM (ms)
                   - Cálculo de Custo (USD & BRL)
                   - Trilha Forense SHA-256
                                  │
         ┌────────────────────────┴────────────────────────┐
         ▼                                                 ▼
[Resposta API / Telemetria UI]               [Banco de Dados / Auditoria]
 (Exibição no Laudo Clínico)                  (Tabela: report_generations_audit)
                                                           ▲
                                                           │
                                             [Suite de Evals Sistemáticos]
                                              - Golden Dataset (30+ Casos)
                                              - Factuality & CID-10 Match
                                              - LLM-as-a-Judge (Rubrica)
`

---

## 3. Pilar 1: Avaliação Sistemática (Evals) de LLMs Clínicas

### 3.1. Golden Dataset de Benchmark Clínico (training/evals/data/clinical_benchmark.json)
Deve ser criado um arquivo JSON canônico contendo uma coleção curada de casos de teste representando a distribuição do mundo real:
- **Casos Típicos:** Exames clássicos de cada uma das 4 classes (consolidação lobar com broncograma para bacteriana; infiltrado intersticial para viral; opacidades periféricas em vidro fosco para Covid; parênquima limpo para normal).
- **Casos de Empate Técnico / Ambiguidade (Delta < 15%):** Cenários onde o modelo de CV teve dúvida (ex: 51% bacteriana vs 49% viral), avaliando se a LLM mantém o diagnóstico diferencial aberto e orienta a dosagem de **Procalcitonina sérica**.
- **Casos de Intervenção Médica (*Human-in-the-Loop*):** Casos onde o médico sobrescreve o resultado da rede neural, avaliando se a LLM adota integralmente o parecer humano soberano.
- **Casos com Metadados DICOM:** Verificação se a técnica radiológica mencionada reflete a projeção (PA/AP) e quilovoltagem (kVp) do cabeçalho DICOM.

#### Estrutura de Cada Amostra de Teste:
`json
{
  case_id: BENCH-001-COVID,
  category: typical,
  input: {
    predicted_class: 0,
    label: Covid-19,
    confidence: 0.965,
    probs: [
      {class_id: 0, label: Covid-19, probability: 0.965},
      {class_id: 1, label: Normal, probability: 0.005},
      {class_id: 2, label: Pneumonia viral, probability: 0.025},
      {class_id: 3, label: Pneumonia bacteriana, probability: 0.005}
    ],
    dicom_metadata: {
      patient_position: PA,
      kvp: 120
    },
    override_label: null,
    override_notes: null,
    is_ambiguous: false
  },
  ground_truth: {
    expected_icd_10_prefix: U07.1,
    mandatory_findings: [vidro fosco, periféric, bilateral],
    forbidden_hallucinations: [pneumotórax, derrame pleural volumoso, cavitação apical],
    expected_impression_keywords: [covid-19, sars-cov-2]
  }
}
`

### 3.2. Métricas de Avaliação Automatizada
A suite de evals executará todos os casos de benchmark contra os modelos configurados e calculará:

1. **CID-10 Accuracy Score:**
   - Concordância do código CID-10 retornado com o esperado (Meta: >= 98%).
2. **Compliance de Formato Estruturado (Section Completeness):**
   - Presença integral das 5 seções regulatórias: TECNICA, ACHADOS, IMPRESSAO, CID_10, RECOMENDACOES (Meta: 100%).
3. **Índice de Alucinação Radiológica (*Hallucination Penalty*):**
   - Mencionamento de achados graves inexistentes no ground-truth (Meta: 0%).
4. **Taxa de Fidelidade ao Human-in-the-Loop:**
   - Adoção estrita da sobrescrita médica (Meta: 100%).
5. **LLM-as-a-Judge com Rubrica Radiológica (Opcional em CI):**
   - Avaliação com rubrica formal Likert (1 a 5) em Precisão Médica, Clareza, Segurança do Paciente e Respeito ao Parecer Médico.

### 3.3. Script de Execução de Evals (training/evals/run_evals.py)
- Comando CLI para execução local e em pipeline de CI:
  `ash
  uv run python training/evals/run_evals.py --model gemini-3.8-flash --output evaluation_report.md
  `
- Gera um relatório estruturado em Markdown com tabela de resultados, taxas de aprovação e métricas consolidadas.

---

## 4. Pilar 2: Instrumentação, Telemetria & FinOps de IA

### 4.1. Extração de Tokens & Latência por Provedor
O serviço llm_report.py deve envolver a requisição HTTP em um bloco de medição de tempo de alta precisão (	ime.perf_counter()) e extrair os contadores nativos de tokens:

#### A. Provedor Google Gemini (generativelanguage.googleapis.com):
- O JSON de resposta inclui usageMetadata:
  - prompt_tokens = data[usageMetadata][promptTokenCount]
  - completion_tokens = data[usageMetadata][candidatesTokenCount]
  - 	otal_tokens = data[usageMetadata][totalTokenCount]

#### B. Provedor OpenCode Zen / OpenAI-Compatible:
- O JSON de resposta inclui usage:
  - prompt_tokens = data[usage][prompt_tokens]
  - completion_tokens = data[usage][completion_tokens]
  - 	otal_tokens = data[usage][total_tokens]

#### C. Motor Local Determinístico:
- prompt_tokens = 0
- completion_tokens = 0
- 	otal_tokens = 0
- cost_usd = 0.0
- latency_ms < 5.0

### 4.2. Tabela de Preços & Motor FinOps (PRICING_TABLE)
Tabela de tarifação por 1 Milhão de tokens:

| Modelo | Identificador | Entrada (USD / 1M) | Saída (USD / 1M) |
| :--- | :--- | :--- | :--- |
| **Gemini 3.8 Flash** | gemini-3.8-flash | .075 | .30 |
| **DeepSeek V4 Flash** | deepseek-v4-flash | .14 | .28 |
| **Qwen 3.7 Plus** | qwen3.7-plus | .40 | .20 |
| **GPT 5.6 Luna** | gpt-5.6-luna | .50 | .50 |
| **Motor Local** | deterministic-local | .00 | .00 |

### 4.3. Monitoramento de Resiliência & Degradação (*Fallback Telemetry*)
Se uma chamada a um provedor externo falhar (timeout, erro 429 de quota, 500 interno ou resposta ininteligível):
1. O sistema aciona o fallback para o Motor Determinístico Local.
2. O objeto de telemetria marca:
   - allback_triggered = True
   - allback_reason = Google API HTTP 429: Quota exceeded
   - original_model_requested = gemini-3.8-flash
3. O log estruturado (structlog) emite o evento com severidade WARNING.

---

## 5. Especificação de Schemas e Banco de Dados

### 5.1. Novo Schema de Telemetria (LLMTelemetry) em ackend/app/schemas/prediction.py

`python
class LLMTelemetry(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    estimated_cost_usd: float = 0.0
    fallback_triggered: bool = False
    fallback_reason: str | None = None
`

O ReportResponse é estendido com:
`python
class ReportResponse(BaseModel):
    # ... campos existentes (model_used, technique, findings, impression, icd_10, recommendations, disclaimer) ...
    telemetry: LLMTelemetry | None = None
`

### 5.2. Tabela de Auditoria Imutável (
eport_generations_audit)
Para rastreabilidade hospitalar (HIPAA/LGPD):
- id: PK
- prediction_id: FK opcional
- model_requested: String
- model_effective: String
- provider: String
- prompt_tokens, completion_tokens, 	otal_tokens: Integer
- latency_ms, cost_usd: Float
- allback_triggered: Boolean
- allback_reason: Text
- icd_10: String
- has_human_override: Boolean
- created_at: DateTime (UTC)

---

## 6. Especificação de Interface do Usuário (UI/UX)

### 6.1. Badge de Métricas no MedicalReportCard.tsx
No cabeçalho ou rodapé técnico do laudo clínico:
- **Latência:** ⚡ 1.4s (tempo de geração líquida).
- **Consumo de Tokens:** 📊 620 tokens (240 in / 380 out).
- **Custo Estimado:** 💰 .00013 USD (visibilidade e transparência para o gestor clínico).
- **Selo de Fallback:** Se houve fallback, exibir badge âmbar com explicação clara.

### 6.2. Isolamento na Impressão
A telemetria técnica de tokens e custos é marcada com .no-print, permanecendo visível em tela, mas **oculta na folha impressa A4 oficial entregue ao paciente**.

---

## 7. Plano de Implementação Detalhado

### Etapa 1: Backend — Telemetria, Extração de Tokens & FinOps
1. Criar o schema LLMTelemetry e atualizar ReportResponse em ackend/app/schemas/prediction.py.
2. Criar o módulo de cálculo de custo e telemetria em ackend/app/services/llm_report.py.
3. Atualizar as chamadas do Google Gemini e OpenCode Zen para cronometrar a requisição e capturar os contadores nativos de tokens.
4. Adicionar testes unitários em ackend/tests/test_dicom_and_report.py validando o preenchimento correto dos tokens, latência e custo.

### Etapa 2: Frontend — Exibição de Métricas Clínicas & FinOps
1. Atualizar o tipo ReportResponse em rontend/src/lib/types.ts para incluir 	elemetry.
2. Adicionar badge de telemetria no componente rontend/src/components/MedicalReportCard.tsx com ícones sutis de relógio, tokens e custo.
3. Garantir compatibilidade com modo escuro e modo claro com contraste adequado.

### Etapa 3: Banco de Dados & Auditoria Forense
1. Criar o modelo SQLAlchemy ReportAuditLog em ackend/app/models/report_audit.py.
2. Adicionar migration do Alembic para criar a tabela 
eport_generations_audit.
3. Salvar o log de auditoria de forma assíncrona ao final da geração de cada laudo.

### Etapa 4: Framework de Evals Clínicos Automatizados
1. Criar o diretório training/evals/.
2. Escrever o Golden Dataset training/evals/data/clinical_benchmark.json com os 30+ casos curados.
3. Desenvolver o script de execução training/evals/run_evals.py avaliando CID-10 accuracy, completude estrutural, ausência de alucinações e respeito à sobrescrita humana.
4. Documentar o comando de execução no README.md.

---

## 8. Critérios de Aceite & Validação (Definition of Done)

- [ ] **Extração de Tokens:** Chamadas ao Gemini e OpenCode Zen retornam contadores reais de prompt_tokens e completion_tokens maiores que zero.
- [ ] **Precisão FinOps:** O custo em USD é calculado matematicamente correto conforme a tabela de preços.
- [ ] **Latência Isolada:** O campo latency_ms mede com precisão o tempo de resposta da LLM, segregado do tempo da rede neural ResNet50.
- [ ] **Fallback Auditado:** Quando a API externa falhar ou não possuir chave, o sistema preenche allback_triggered = True com a justificativa descritiva.
- [ ] **Suite de Evals Executável:** O script 
un_evals.py executa o benchmark contra o Golden Dataset e gera relatório com taxa de aprovação quantitativa.
- [ ] **Cobertura de Testes:** Todos os testes novos e existentes passam com 100% de sucesso no pytest e no itest.
- [ ] **Zero Regressão Visual:** A folha de impressão A4 continua limpa, ocultando métricas técnicas e exibindo apenas os dados clínicos do paciente.
