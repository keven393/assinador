const isDebugMode = Boolean(window.APP_DEBUG);

// Funções comuns para o sistema de assinatura
function signAll() {
    window.location.href = "/client/sign-all";
}

function confirmDelete(userId, username) {
    document.getElementById('deleteUsername').textContent = username;
    document.getElementById('deleteForm').action = '/admin/users/' + userId + '/delete';
    
    const deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
    deleteModal.show();
}

function copyClientInfo(clientName, clientCpf) {
    const text = `Cliente: ${clientName}\nCPF: ${clientCpf}`;
    
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(function() {
            alert('Dados copiados para a área de transferência!');
        }).catch(function(err) {
            if (isDebugMode) {
                console.error('Erro ao copiar: ', err);
            }
            fallbackCopyTextToClipboard(text);
        });
    } else {
        fallbackCopyTextToClipboard(text);
    }
}

function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.top = "0";
    textArea.style.left = "0";
    textArea.style.position = "fixed";
    
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            alert('Dados copiados para a área de transferência!');
        } else {
            alert('Erro ao copiar dados. Tente selecionar e copiar manualmente.');
        }
    } catch (err) {
        if (isDebugMode) {
            console.error('Fallback: unable to copy', err);
        }
        alert('Erro ao copiar dados. Tente selecionar e copiar manualmente.');
    }
    
    document.body.removeChild(textArea);
}

function confirmCancelSignature(signatureId, filename, clientName) {
    const message = `Deseja realmente cancelar a assinatura do documento "${filename}" para o cliente "${clientName}"?`;
    
    if (confirm(message)) {
        window.location.href = `/internal/signatures/${signatureId}/cancel`;
    }
}

// Função para mostrar instruções detalhadas
function showInstructions(filename, clientName) {
    const content = `
        <h6>Como orientar o cliente para assinar o documento:</h6>
        <ol>
            <li><strong>${filename}</strong></li>
            <li>Cliente: <strong>${clientName}</strong></li>
        </ol>
        
        <div class="alert alert-info">
            <h6><i class="fas fa-mobile-alt me-2"></i>Passos para o Cliente:</h6>
            <ol>
                <li>Acesse a <strong>Tela de Assinatura</strong> (botão laranja acima)</li>
                <li>Digite o CPF do cliente</li>
                <li>Confirme os dados e aceite os termos</li>
                <li>Desenhe a assinatura no campo indicado</li>
                <li>Clique em "Finalizar Assinatura"</li>
            </ol>
        </div>
        
        <div class="alert alert-warning">
            <h6><i class="fas fa-exclamation-triangle me-2"></i>Importante:</h6>
            <ul>
                <li>O cliente deve usar um dispositivo com tela touch (tablet/celular)</li>
                <li>A assinatura deve ser clara e legível</li>
                <li>Após a assinatura, o documento ficará disponível para download</li>
            </ul>
        </div>
    `;
    
    if (document.getElementById('instructionsContent')) {
        document.getElementById('instructionsContent').innerHTML = content;
        new bootstrap.Modal(document.getElementById('instructionsModal')).show();
    } else {
        alert('Instruções: ' + filename + ' para ' + clientName);
    }
}

// Função para confirmar cancelamento de assinatura
function confirmCancelSignature(signatureId, fileName, clientName) {
    // Preenche os dados no modal
    if (document.getElementById('cancelFileName')) {
        document.getElementById('cancelFileName').textContent = fileName;
        document.getElementById('cancelClientName').textContent = clientName;
        
        // Atualiza o action do formulário
        document.getElementById('cancelForm').action = `/internal/signature/cancel/${signatureId}`;
        
        // Mostra o modal
        new bootstrap.Modal(document.getElementById('cancelModal')).show();
    } else {
        const message = `Deseja realmente cancelar a assinatura do documento "${fileName}" para o cliente "${clientName}"?`;
        if (confirm(message)) {
            window.location.href = `/internal/signatures/${signatureId}/cancel`;
        }
    }
}

// Função para mostrar detalhes do documento cancelado
function showDocumentDetails(filename, clientName, createdDate) {
    const content = `
        <div class="row">
            <div class="col-md-6">
                <h6>Informações do Documento:</h6>
                <ul class="list-unstyled">
                    <li><strong>Nome:</strong> ${filename}</li>
                    <li><strong>Cliente:</strong> ${clientName}</li>
                    <li><strong>Criado em:</strong> ${createdDate}</li>
                    <li><strong>Status:</strong> <span class="badge bg-danger">Cancelada</span></li>
                </ul>
            </div>
            <div class="col-md-6">
                <h6>Motivos Comuns de Cancelamento:</h6>
                <ul>
                    <li>Cliente desistiu da assinatura</li>
                    <li>Documento com informações incorretas</li>
                    <li>Problemas técnicos durante o processo</li>
                    <li>Mudança de requisitos</li>
                    <li>Documento substituído por versão atualizada</li>
                </ul>
            </div>
        </div>
        
        <div class="alert alert-warning mt-3">
            <h6><i class="fas fa-exclamation-triangle me-2"></i>Importante:</h6>
            <p class="mb-0">
                Documentos cancelados não podem ser reativados. Para processar novamente, 
                crie uma nova assinatura com o mesmo documento.
            </p>
        </div>
    `;
    
    if (document.getElementById('documentDetailsContent')) {
        document.getElementById('documentDetailsContent').innerHTML = content;
        new bootstrap.Modal(document.getElementById('documentDetailsModal')).show();
    } else {
        alert('Detalhes: ' + filename + ' - ' + clientName + ' - ' + createdDate);
    }
}

// Auto-refresh para verificar atualizações
function startAutoRefresh() {
    setInterval(function() {
        if (document.visibilityState === 'visible' && isDebugMode) {
            console.log('Verificando atualizações...');
        }
    }, 30000);
}

// Event listeners para botões com data-attributes
document.addEventListener('DOMContentLoaded', function() {
    startAutoRefresh();
    
    // Event listener para formulários com confirmação
    document.addEventListener('submit', function(e) {
        const form = e.target;
        const submitBtn = form.querySelector('[data-confirm]');
        if (submitBtn) {
            const message = submitBtn.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        }
        if (form) {
            form.addEventListener('submit', function() {
                if (isDebugMode) {
                    console.log('Formulário de remoção submetido');
                }
            });
        }
    });
    
    const callIfExists = (fnName, ...args) => {
        const fn = window[fnName];
        if (typeof fn === 'function') {
            return fn(...args);
        }
        if (isDebugMode) {
            console.warn(`Função não encontrada: ${fnName}`);
        }
        return undefined;
    };

    document.addEventListener('click', function(e) {
        const button = e.target.closest('[data-action]');
        if (!button) return;
        
        const action = button.getAttribute('data-action');
        
        switch(action) {
            case 'copy':
                const clientName = button.getAttribute('data-client-name');
                const clientCpf = button.getAttribute('data-client-cpf');
                copyClientInfo(clientName, clientCpf);
                break;
                
            case 'instructions':
                const filename = button.getAttribute('data-filename');
                const clientName2 = button.getAttribute('data-client-name');
                showInstructions(filename, clientName2);
                break;
                
            case 'cancel':
                const signatureId = button.getAttribute('data-signature-id');
                const filename2 = button.getAttribute('data-filename');
                const clientName3 = button.getAttribute('data-client-name');
                confirmCancelSignature(signatureId, filename2, clientName3);
                break;
                
            case 'details':
                const signatureId2 = button.getAttribute('data-signature-id');
                callIfExists('showSignatureDetails', signatureId2);
                break;
                
            case 'document-details':
                const filename3 = button.getAttribute('data-filename');
                const clientName4 = button.getAttribute('data-client-name');
                const timestamp = button.getAttribute('data-timestamp');
                callIfExists('showDocumentDetails', filename3, clientName4, timestamp);
                break;
                
            case 'apply-filters':
                callIfExists('applyFilters');
                break;
                
            case 'export-csv':
                callIfExists('exportToCSV');
                break;
                
            case 'delete':
                const userId = button.getAttribute('data-user-id');
                const username = button.getAttribute('data-username');
                confirmDelete(userId, username);
                break;
                
            case 'close-window':
                window.close();
                break;
                
            case 'reload':
                location.reload();
                break;
                
            case 'reset-upload':
                callIfExists('resetUpload');
                break;
                
            case 'add-more-files':
                callIfExists('addMoreFiles');
                break;
                
            case 'clear-all-files':
                callIfExists('clearAllFiles');
                break;
                
            case 'remove-file':
                const index = button.getAttribute('data-index');
                callIfExists('removeFile', index);
                break;
                
            case 'select-file':
                const pdfInput = document.getElementById('pdfFile');
                if (pdfInput) {
                    pdfInput.click();
                }
                break;
                
            case 'clear-file':
                callIfExists('clearFile');
                break;
                
            case 'sign-all':
                signAll();
                break;
        }
    });
});
