# Changelog

Todas as alterações notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [1.1.0] - 2026-09-04

### Adicionado
- **Estação PACS Médica Interativa**: Visualizador clínico profissional com controles on-screen para Zoom (50%-300%), Brilho (50%-200%), Contraste (50%-250%), Inversão Monocromática, opacidade dinâmica do mapa de calor Grad-CAM e suporte a tela cheia.
- **Galeria 1-Click Demo**: Teste instantâneo de 6 amostras clínicas representativas (Normal, Covid-19, Pneumonia Bacteriana, Pneumonia Viral, Anomalia OOD e Exame DICOM hospitalar).
- **Ingestão Hospitalar DICOM (.dcm)**: Processamento nativo de radiografias hospitalares DICOM, rotina de desidentificação de dados sensíveis (padrão DICOM PS 3.15, em conformidade com HIPAA e LGPD) e extração de metadados técnicos (kVp, incidência radiológica, dimensões).
- **Consenso Diagnóstico & Laudos Multi-LLM**:
  - Integração com Google Gemini 3.8 / 2.5 Flash via Google AI Studio.
  - Roteamento dinâmico para modelos OpenCode Zen: GPT 5.6 Luna (`/responses`), DeepSeek V4 Flash (`/chat/completions`) e Qwen 3.7 Plus (`/messages`).
  - Motor Clínico Local Determinístico baseado em regras médicas para operação 100% offline e resiliente.
  - Painel de Consenso Lado a Lado (*Side-by-Side*) permitindo comparar simultaneamente as conclusões de diferentes IAs.
- **Supervisão Médica & Human-in-the-Loop (HITL)**:
  - Detecção automática de ambiguidade diagnóstica / empate técnico com margem estreita ($\Delta < 15\%$).
  - Painel de intervenção soberana do médico especialista para sobrescrever a conduta, incluir justificativa clínica com biomarcadores séricos (Procalcitonina / PCR) e orientar a redação do laudo.
- **Motor de Impressão Hospitalar A4 Timbrada**: Layout de impressão `@media print` que gera folha médica timbrada formal em 1 página A4 com dados desidentificados, seções estruturadas, campo para carimbo e assinatura do médico responsável (CRM/RQE).
- **Ajuste Fino de Contraste Light/Dark Mode**: Otimização completa da paleta visual para legibilidade perfeita em ambientes clínicos iluminados ou salas escuras de radiologia.

## [1.0.0] - 2026-09-03

### Adicionado
- **Classificador ResNet50 Fine-Tuned**: Modelo de deep learning treinado em dois datasets (COVID-19 Radiography Database e Mendeley Chest X-Ray) cobrindo 4 classes clínicas (Covid-19, Normal, Pneumonia Viral, Pneumonia Bacteriana).
- **Explainability com Grad-CAM**: Geração de mapas de calor de ativação sobrepostos à imagem original, indicando regiões que determinaram a predição.
- **Detecção Out-of-Distribution (OOD)**: Rejeição de imagens não médicas / não raio-X via similaridade de embeddings, evitando falsos positivos e alucinações.
- **Backend FastAPI assíncrono**: Endpoints para autenticação JWT, inferência de imagens, histórico de predições, métricas e estatísticas agregadas.
- **Frontend SPA em React 18**: Interface moderna com upload com drag-and-drop, visualizador de mapa de calor Grad-CAM, filtros, gráficos e histórico paginado.
- **Deploy Containerizado**: Suporte completo a Docker e Docker Compose multi-stage build.
- **CI/CD no GitHub Actions**: Workflows para linting (Ruff), testes automatizados com Pytest e Vitest, validação de LFS, publicação no GitHub Packages (GHCR) e releases automáticas.
- **Templates e Governança**: Issue templates estruturados, pull request template, dependabot para segurança de dependências e guias de contribuição.
