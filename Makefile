.PHONY: install run test format lint clean help

# Comandos principais
install: ## Instalar dependências
	uv add flask PyPDF2 reportlab pillow cryptography pycryptodome

install-dev: ## Instalar dependências de desenvolvimento
	uv add --dev pytest black flake8

run: ## Executar a aplicação
	uv run python app.py

test: ## Executar testes
	uv run pytest

test-crypto: ## Testar funcionalidades criptográficas
	uv run python test_crypto.py

format: ## Formatar código
	uv run black .

lint: ## Verificar estilo de código
	uv run flake8

clean: ## Limpar arquivos temporários
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

help: ## Mostrar esta ajuda
	@echo "Comandos disponíveis:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Comandos específicos para Windows
install-win: ## Instalar dependências (Windows)
	install_uv.bat

run-win: ## Executar aplicação (Windows)
	uv run python app.py

# Comandos específicos para Linux/Mac
install-unix: ## Instalar dependências (Linux/Mac)
	./install_uv.sh

run-unix: ## Executar aplicação (Linux/Mac)
	uv run python app.py 