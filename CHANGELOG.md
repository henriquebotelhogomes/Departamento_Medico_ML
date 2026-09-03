# Changelog

Todas as alterações notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

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
