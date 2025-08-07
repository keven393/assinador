# 📄 Assinador Rápido de PDFs

Uma aplicação web moderna e intuitiva para assinar documentos PDF de forma rápida e segura, desenvolvida com Flask e Bootstrap.

## ✨ Funcionalidades

- **Upload de PDFs**: Suporte a qualquer arquivo PDF
- **Assinatura Digital Obrigatória**: Desenhe sua assinatura usando o mouse (obrigatório)
- **Assinatura em Todas as Páginas**: Adiciona logo, informações pessoais e assinatura desenhada lado a lado no canto inferior direito de cada página
- **Logo Padrão**: Logo da empresa incluído automaticamente nas assinaturas
- **Informações Pessoais**: Inclua nome, data de nascimento e CPF
- **Interface Moderna**: Design responsivo e intuitivo com Bootstrap
- **Download Direto**: Baixe o PDF assinado instantaneamente
- **Configurações Flexíveis**: Personalize tipo, cor e posição da assinatura
- **Segurança**: Garantia de autenticidade e integridade do documento

## 🚀 Instalação

### Pré-requisitos

- Python 3.9 ou superior
- uv (gerenciador de pacotes Python) - **Recomendado**
- ou pip (gerenciador de pacotes Python)

### Passos de Instalação

#### Usando UV (Recomendado)

1. **Clone o repositório**:
   ```bash
   git clone <url-do-repositorio>
   cd Assinaturas
   ```

2. **Instale as dependências com UV**:
   ```bash
   uv add flask PyPDF2 reportlab pillow
   ```

   Ou use o script de instalação:
   ```bash
   # Windows
   install_uv.bat
   
   # Linux/Mac
   ./install_uv.sh
   ```

#### Usando pip

1. **Clone o repositório**:
   ```bash
   git clone <url-do-repositorio>
   cd Assinaturas
   ```

2. **Instale as dependências**:
   ```bash
   pip install -e .
   ```

   Ou instale manualmente:
   ```bash
   pip install flask PyPDF2 reportlab pillow
   ```

## 🎯 Como Usar

### Executar a Aplicação

#### Usando UV (Recomendado)

1. **Inicie o servidor Flask**:
   ```bash
   uv run python app.py
   ```

2. **Acesse no navegador**:
   - A aplicação será aberta automaticamente em `http://localhost:5000`
   - Ou acesse manualmente o endereço mostrado no terminal

#### Usando pip

1. **Inicie o servidor Flask**:
   ```bash
   python app.py
   ```

2. **Acesse no navegador**:
   - A aplicação será aberta automaticamente em `http://localhost:5000`
   - Ou acesse manualmente o endereço mostrado no terminal

### Processo de Assinatura

1. **Upload do PDF**:
   - Clique em "Escolha um arquivo PDF" na seção de upload
   - Selecione o arquivo PDF que deseja assinar

2. **Desenhe a Assinatura**:
   - Use o mouse para desenhar sua assinatura no canvas (obrigatório)
   - Clique em "Salvar Assinatura" após desenhar
   - A assinatura é obrigatória para prosseguir

3. **Informações Pessoais**:
   - Preencha os campos: Nome Completo, Data de Nascimento e CPF
   - Estas informações serão incluídas no PDF assinado

4. **Configure o Tipo de Assinatura**:
   - **Todas as Páginas (Logo + Info + Assinatura)**: Adiciona logo, informações pessoais e assinatura lado a lado no canto inferior direito de cada página
   - **Página Final**: Adiciona uma página separada com a assinatura

5. **Assine o Documento**:
   - Clique no botão "🔐 ASSINAR PDF"
   - Aguarde o processamento

6. **Download**:
   - Clique em "📥 BAIXAR PDF ASSINADO" para baixar o documento assinado

## 🆕 Novas Funcionalidades

### Assinatura em Todas as Páginas

A aplicação agora suporta adicionar assinaturas em todas as páginas do PDF:

- **Logo + Info + Assinatura**: Cada página terá o logo da empresa, informações pessoais e a assinatura desenhada lado a lado no canto inferior direito
- **Informações Pessoais**: Nome, CPF e data de nascimento são posicionados entre o logo e a assinatura
- **Timestamp**: Data e hora da assinatura são automaticamente adicionadas abaixo
- **Posicionamento**: Logo, informações pessoais e assinatura posicionados horizontalmente
- **Assinatura Obrigatória**: Apenas assinaturas desenhadas são aceitas

### Logo Padrão

- **Logo Automático**: Um logo padrão é automaticamente incluído em cada página
- **Redimensionamento Responsivo**: O logo é redimensionado proporcionalmente à altura da assinatura
- **Posicionamento**: Logo posicionado à esquerda, seguido pelas informações pessoais e assinatura

## 🛠️ Tecnologias Utilizadas

- **Flask**: Framework web para aplicações Python
- **Bootstrap**: Framework CSS para interface responsiva
- **PyPDF2**: Manipulação de arquivos PDF
- **ReportLab**: Geração de PDFs com assinaturas
- **Pillow**: Processamento de imagens para assinaturas desenhadas
- **Python**: Linguagem de programação principal
- **UV**: Gerenciador de pacotes Python (recomendado)

## 📋 Estrutura do Projeto

```
Assinaturas/
├── app.py                 # Aplicação principal Flask
├── templates/
│   └── index.html        # Template HTML principal
├── static/
│   └── images/           # Diretório para logos
├── temp_files/           # Arquivos temporários (não versionado)
├── pyproject.toml        # Configurações e dependências
├── Makefile              # Comandos de desenvolvimento
├── install_uv.bat        # Script de instalação UV (Windows)
├── install_uv.sh         # Script de instalação UV (Linux/Mac)
├── install.bat           # Script de instalação pip (Windows)
├── install.sh            # Script de instalação pip (Linux/Mac)
└── README.md            # Este arquivo
```

## 🔧 Configurações Avançadas

### Usando UV para Desenvolvimento

O projeto está configurado para usar `uv` como gerenciador de pacotes principal. Alguns comandos úteis:

```bash
# Adicionar uma nova dependência
uv add nome-do-pacote

# Adicionar dependência de desenvolvimento
uv add --dev nome-do-pacote

# Executar comando no ambiente virtual
uv run python script.py

# Executar testes
uv run pytest

# Formatar código
uv run black .

# Verificar estilo de código
uv run flake8
```

### Usando Makefile (Linux/Mac)

Para facilitar o desenvolvimento, você pode usar o Makefile incluído:

```bash
# Instalar dependências
make install

# Executar aplicação
make run

# Executar testes
make test

# Formatar código
make format

# Verificar estilo
make lint

# Ver todos os comandos disponíveis
make help
```

### Personalização de Estilos

Você pode modificar os estilos CSS no arquivo `templates/index.html` para personalizar a aparência:

```css
:root {
    --primary-color: #0d6efd;
    --secondary-color: #6c757d;
    /* ... outras variáveis */
}
```

### Adicionando Novos Tipos de Assinatura

Para adicionar novos tipos de assinatura, modifique a função `add_signature_to_all_pages()`:

```python
def add_signature_to_all_pages(pdf_file, signature_text, output_path, signature_image=None, personal_info=None, logo_path=None):
    # Lógica personalizada para diferentes tipos de assinatura
    pass
```

## 🔒 Segurança

- **Assinaturas Digitais**: Cada assinatura inclui timestamp automático
- **Integridade**: O documento original é preservado
- **Autenticidade**: Nota de autenticidade incluída no PDF final
- **Processamento Local**: Todos os arquivos são processados localmente
- **Limpeza Automática**: Arquivos temporários são removidos automaticamente

## 🐛 Solução de Problemas

### Erro ao Carregar PDF
- Verifique se o arquivo é um PDF válido
- Certifique-se de que o arquivo não está corrompido

### Erro ao Processar Assinatura
- Verifique se há espaço suficiente no disco
- Certifique-se de que todas as dependências estão instaladas

### Problemas com Logo
- O logo padrão é criado automaticamente
- Se houver problemas, o sistema continuará funcionando sem o logo

### Problemas de Performance
- Para PDFs muito grandes, o processamento pode demorar
- Considere dividir documentos muito extensos

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

Se você encontrar algum problema ou tiver sugestões, por favor:

1. Abra uma issue no GitHub
2. Descreva o problema detalhadamente
3. Inclua informações sobre seu sistema operacional e versão do Python

## 🎉 Agradecimentos

- Flask pela excelente framework web
- Bootstrap pela interface responsiva
- Comunidade Python pelo suporte contínuo
- Todos os contribuidores que ajudaram a melhorar este projeto

---

**Desenvolvido com ❤️ usando Flask e Bootstrap**
