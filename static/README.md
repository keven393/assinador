# Arquivos Estáticos - Assinador de PDFs

Este diretório contém todos os arquivos estáticos (CSS, JavaScript, imagens) utilizados pela aplicação.

## Estrutura

```
static/
├── css/
│   ├── bootstrap.min.css      # Bootstrap 5.3.0 (local)
│   └── custom.css             # Estilos customizados da aplicação
├── js/
│   └── bootstrap.bundle.min.js # Bootstrap JS + Popper (local)
└── images/
    └── logo.png               # Logo da aplicação
```

## Por que arquivos locais?

Os arquivos Bootstrap foram baixados localmente (em vez de usar CDN) por questões de:

1. **Performance**: Reduz latência e dependência de servidores externos
2. **Confiabilidade**: Funciona mesmo se o CDN estiver indisponível
3. **Segurança**: Evita possíveis problemas de CSP (Content Security Policy)
4. **Privacidade**: Não compartilha dados com terceiros (CDN)

## Versões

- **Bootstrap**: 5.3.0
- **Font Awesome**: 6.0.0 (ainda via CDN - pode ser baixado se necessário)

## Baixando arquivos Bootstrap

**IMPORTANTE**: Os arquivos Bootstrap **NÃO** estão no repositório Git. Você precisa baixá-los antes de rodar a aplicação.

### Opção 1: Script automatizado (Recomendado)

```powershell
# Windows (PowerShell)
.\scripts\download_static.ps1

# Para forçar re-download
.\scripts\download_static.ps1 -Force

# Para versão específica
.\scripts\download_static.ps1 -Version "5.3.2"
```

```bash
# Linux/Mac
bash scripts/download_static.sh

# Para forçar re-download
bash scripts/download_static.sh --force

# Para versão específica
bash scripts/download_static.sh --version "5.3.2"
```

### Opção 2: Docker (automático no build)

Os arquivos são baixados automaticamente durante o `docker-compose build`:

```bash
docker-compose build
```

## Customizações (custom.css)

O arquivo `custom.css` contém:

- Variáveis CSS personalizadas
- Estilos para cards e botões
- Animações
- Estilos responsivos
- Melhorias de UX

Não modifique os arquivos Bootstrap diretamente. Sempre use `custom.css` para sobrescrever estilos.

## Deploy

Após modificar arquivos estáticos:

1. **Local (desenvolvimento)**:
   ```bash
   # Restart do Flask
   python app.py
   ```

2. **Produção (Docker)**:
   ```powershell
   # Windows
   .\deploy_static.ps1
   ```
   
   ```bash
   # Linux/Mac
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

## Cache

Os arquivos estáticos são cacheados no navegador. Se você modificar algum arquivo e não ver as mudanças:

1. Limpe o cache do navegador (Ctrl+Shift+Del)
2. Ou use Ctrl+F5 para forçar reload
3. Ou incremente a versão no URL: `?v=2`

## Otimização

Os arquivos CSS e JS já estão minificados (.min.css, .min.js). Não é necessário minificação adicional.

