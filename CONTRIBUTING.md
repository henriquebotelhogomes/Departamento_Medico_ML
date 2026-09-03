# Guia de Contribuição — RadioAI

Agradecemos o seu interesse em contribuir com o **RadioAI**! 🚀
Este documento fornece as diretrizes e instruções para configurar o ambiente e submeter contribuições.

---

## 🛠️ Requisitos de Desenvolvimento

- **Python 3.12** com gerenciador de pacotes [uv](https://docs.astral.sh/uv/)
- **Node.js 20+** com 
pm
- **Docker** e **Docker Compose** (para testes integrados)
- **Git LFS** (para modelos e pesos de deep learning)

---

## 🚀 Configuração do Ambiente Local

### 1. Clonar o Repositório e Modelos LFS
\\\ash
git clone https://github.com/henriquebotelhogomes/Departamento_Medico_ML.git
cd Departamento_Medico_ML
git lfs install
git lfs pull
\\\

### 2. Backend (FastAPI + uv)
\\\ash
cd backend
uv sync --extra dev
uv run ruff check app
uv run pytest
\\\

### 3. Frontend (React 18 + Vite)
\\\ash
cd frontend
npm ci
npm run lint
npm run test
npm run build
\\\

---

## 📋 Padrão de Commits

Seguimos a convenção [Conventional Commits](https://www.conventionalcommits.org/):
- \eat:\ Nova funcionalidade
- \ix:\ Correção de bug
- \docs:\ Alteração em documentações
- \style:\ Formatação e estilo sem alteração de lógica
- \efactor:\ Refatoração de código
- \	est:\ Adição ou ajuste de testes
- \ci:\ Alterações em workflows de CI/CD

---

## 🔄 Fluxo de Pull Requests

1. Crie uma branch descritiva a partir de \main\:
   \\\ash
   git checkout -b feat/minha-melhoria
   \\\
2. Escreva testes para novas funcionalidades ou correções de bugs.
3. Certifique-se de que os linters e testes locais estão passando:
   \\\ash
   # No backend:
   uv run ruff check app && uv run pytest

   # No frontend:
   npm run lint && npm run test
   \\\
4. Abra um Pull Request utilizando nosso template padrão preenchido.
