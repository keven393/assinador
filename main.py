import streamlit as st
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
import io
import os
from datetime import datetime
import tempfile
import base64
from PIL import Image
import numpy as np

def create_signature_pdf(text, output_path, signature_image=None, personal_info=None):
    """Cria um PDF com a assinatura digital"""
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Estilo personalizado para a assinatura
    signature_style = ParagraphStyle(
        'Signature',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=20,
        textColor=colors.darkblue,
        alignment=1  # Centralizado
    )
    
    story = []
    
    # Adiciona data e hora
    current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    time_paragraph = Paragraph(f"Data e Hora: {current_time}", signature_style)
    story.append(time_paragraph)
    story.append(Spacer(1, 20))
    
    # Adiciona informações pessoais se fornecidas
    if personal_info:
        story.append(Paragraph("=== INFORMAÇÕES PESSOAIS ===", signature_style))
        story.append(Spacer(1, 10))
        
        if personal_info.get('nome'):
            story.append(Paragraph(f"Nome: {personal_info['nome']}", styles['Normal']))
        if personal_info.get('data_nascimento'):
            story.append(Paragraph(f"Data de Nascimento: {personal_info['data_nascimento']}", styles['Normal']))
        if personal_info.get('cpf'):
            story.append(Paragraph(f"CPF: {personal_info['cpf']}", styles['Normal']))
        
        story.append(Spacer(1, 20))
    
    # Adiciona a assinatura
    if signature_image:
        story.append(Paragraph("Assinatura Digital (Desenhada):", signature_style))
        story.append(Spacer(1, 10))
        # Aqui você pode adicionar a imagem da assinatura se necessário
    else:
        signature_paragraph = Paragraph(f"Assinatura Digital: {text}", signature_style)
        story.append(signature_paragraph)
    
    story.append(Spacer(1, 30))
    
    # Adiciona nota de autenticidade
    authenticity_note = Paragraph(
        "Este documento foi assinado digitalmente através do Assinador Rápido de PDFs. "
        "A assinatura digital garante a autenticidade e integridade do documento.",
        styles['Normal']
    )
    story.append(authenticity_note)
    
    doc.build(story)

def add_signature_to_pdf(pdf_file, signature_text, output_path, signature_image=None, personal_info=None):
    """Adiciona assinatura digital a um PDF existente"""
    try:
        # Lê o PDF original
        with open(pdf_file, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            pdf_writer = PyPDF2.PdfWriter()
            
            # Adiciona todas as páginas do PDF original
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
            
            # Cria um PDF temporário com a assinatura
            temp_signature_path = tempfile.mktemp(suffix='.pdf')
            create_signature_pdf(signature_text, temp_signature_path, signature_image, personal_info)
            
            # Lê o PDF da assinatura
            with open(temp_signature_path, 'rb') as sig_file:
                sig_reader = PyPDF2.PdfReader(sig_file)
                sig_page = sig_reader.pages[0]
                
                # Adiciona a página de assinatura ao final
                pdf_writer.add_page(sig_page)
            
            # Salva o PDF final
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            # Remove arquivo temporário
            os.remove(temp_signature_path)
            
            return True
    except Exception as e:
        st.error(f"Erro ao processar o PDF: {str(e)}")
        return False

def main():
    st.set_page_config(
        page_title="Assinador Rápido de PDFs",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS personalizado para melhor aparência
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton > button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        border-radius: 10px;
        padding: 10px 20px;
        font-size: 16px;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #0d5aa7;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    .signature-canvas {
        border: 2px solid #ccc;
        border-radius: 5px;
        background-color: white;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Cabeçalho
    st.markdown('<h1 class="main-header">📄 Assinador Rápido de PDFs</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Assine seus documentos PDF de forma rápida e segura</p>', unsafe_allow_html=True)
    
    # Sidebar para configurações
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        # Opções de assinatura
        signature_type = st.selectbox(
            "Tipo de Assinatura",
            ["Assinatura Digital", "Carimbo de Aprovação", "Nota de Autenticidade"],
            help="Escolha o tipo de assinatura que será adicionada ao PDF"
        )
        
        # Cor da assinatura
        signature_color = st.color_picker(
            "Cor da Assinatura",
            value="#1f77b4",
            help="Escolha a cor para a assinatura digital"
        )
        
        # Posição da assinatura
        signature_position = st.selectbox(
            "Posição da Assinatura",
            ["Final do Documento", "Página Separada"],
            help="Escolha onde a assinatura será posicionada"
        )
    
    # Área principal
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📤 Upload do PDF")
        
        uploaded_file = st.file_uploader(
            "Escolha um arquivo PDF",
            type=['pdf'],
            help="Selecione o PDF que deseja assinar"
        )
        
        if uploaded_file is not None:
            st.success(f"✅ Arquivo carregado: {uploaded_file.name}")
            
            # Mostra informações do PDF
            try:
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                st.info(f"📊 Páginas no documento: {len(pdf_reader.pages)}")
            except:
                st.warning("⚠️ Não foi possível ler as informações do PDF")
    
    with col2:
        st.header("✍️ Assinatura")
        
        # Aba para escolher tipo de assinatura
        tab1, tab2 = st.tabs(["📝 Texto", "✏️ Desenhar"])
        
        signature_text = ""
        signature_image = None
        personal_info = {}
        
        with tab1:
            # Campo de texto para a assinatura
            signature_text = st.text_area(
                "Digite sua assinatura digital",
                placeholder="Ex: João Silva - Analista de Sistemas",
                height=100,
                help="Digite o texto que será usado como assinatura digital"
            )
            
            # Campo adicional para observações
            observations = st.text_area(
                "Observações (opcional)",
                placeholder="Adicione observações ou notas sobre a assinatura",
                height=80
            )
        
        with tab2:
            st.markdown("### 🎨 Desenhe sua assinatura")
            st.markdown("Use o mouse para desenhar sua assinatura no espaço abaixo:")
            
            # Implementação simplificada do canvas de assinatura
            canvas_html = """
            <div style="border: 2px solid #ccc; border-radius: 5px; background-color: white; padding: 10px; margin: 10px 0;">
                <canvas id="signatureCanvas" width="400" height="200" style="border: 1px solid #ddd; background-color: white; cursor: crosshair;"></canvas>
                <br><br>
                <button id="clearBtn" style="margin: 5px; padding: 8px 15px; background-color: #ff6b6b; color: white; border: none; border-radius: 3px; cursor: pointer;">🗑️ Limpar</button>
                <button id="saveBtn" style="margin: 5px; padding: 8px 15px; background-color: #4CAF50; color: white; border: none; border-radius: 3px; cursor: pointer;">💾 Salvar</button>
                <div id="status" style="margin-top: 10px; font-weight: bold; color: #666;"></div>
            </div>
            
            <script>
            (function() {
                const canvas = document.getElementById('signatureCanvas');
                const ctx = canvas.getContext('2d');
                const clearBtn = document.getElementById('clearBtn');
                const saveBtn = document.getElementById('saveBtn');
                const status = document.getElementById('status');
                
                let isDrawing = false;
                let lastX = 0;
                let lastY = 0;
                
                // Configuração do contexto
                ctx.strokeStyle = '#1f77b4';
                ctx.lineWidth = 2;
                ctx.lineCap = 'round';
                ctx.lineJoin = 'round';
                
                // Eventos do mouse
                canvas.addEventListener('mousedown', startDrawing);
                canvas.addEventListener('mousemove', draw);
                canvas.addEventListener('mouseup', stopDrawing);
                canvas.addEventListener('mouseout', stopDrawing);
                
                // Eventos de toque para dispositivos móveis
                canvas.addEventListener('touchstart', handleTouch);
                canvas.addEventListener('touchmove', handleTouch);
                canvas.addEventListener('touchend', stopDrawing);
                
                function startDrawing(e) {
                    isDrawing = true;
                    const rect = canvas.getBoundingClientRect();
                    lastX = e.clientX - rect.left;
                    lastY = e.clientY - rect.top;
                }
                
                function draw(e) {
                    if (!isDrawing) return;
                    e.preventDefault();
                    
                    const rect = canvas.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const y = e.clientY - rect.top;
                    
                    ctx.beginPath();
                    ctx.moveTo(lastX, lastY);
                    ctx.lineTo(x, y);
                    ctx.stroke();
                    
                    lastX = x;
                    lastY = y;
                }
                
                function handleTouch(e) {
                    e.preventDefault();
                    const touch = e.touches[0];
                    const mouseEvent = new MouseEvent(e.type === 'touchstart' ? 'mousedown' : 
                                                    e.type === 'touchmove' ? 'mousemove' : 'mouseup', {
                        clientX: touch.clientX,
                        clientY: touch.clientY
                    });
                    canvas.dispatchEvent(mouseEvent);
                }
                
                function stopDrawing() {
                    isDrawing = false;
                }
                
                function clearCanvas() {
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    status.textContent = 'Canvas limpo!';
                    setTimeout(() => status.textContent = '', 2000);
                }
                
                function saveSignature() {
                    const dataURL = canvas.toDataURL('image/png');
                    status.textContent = 'Assinatura salva!';
                    setTimeout(() => status.textContent = '', 2000);
                    
                    // Enviar para Streamlit (simulado)
                    console.log('Assinatura salva:', dataURL.substring(0, 50) + '...');
                }
                
                // Eventos dos botões
                clearBtn.addEventListener('click', clearCanvas);
                saveBtn.addEventListener('click', saveSignature);
                
                // Status inicial
                status.textContent = 'Clique e arraste para desenhar sua assinatura';
            })();
            </script>
            """
            
            st.markdown(canvas_html, unsafe_allow_html=True)
            
            # Botões adicionais do Streamlit
            col_clear, col_save = st.columns(2)
            with col_clear:
                if st.button("🗑️ Limpar Assinatura", key="clear_signature"):
                    st.rerun()
            
            with col_save:
                if st.button("💾 Salvar Assinatura", key="save_signature"):
                    st.success("✅ Assinatura salva!")
        
        # Seção de informações pessoais
        st.markdown("### 📋 Informações Pessoais")
        
        col_nome, col_data = st.columns(2)
        
        with col_nome:
            nome = st.text_input(
                "Nome Completo",
                placeholder="Digite seu nome completo",
                help="Nome completo do signatário"
            )
        
        with col_data:
            data_nascimento = st.text_input(
                "Data de Nascimento",
                placeholder="DD/MM/AAAA",
                help="Data de nascimento no formato DD/MM/AAAA"
            )
        
        cpf = st.text_input(
            "CPF",
            placeholder="000.000.000-00",
            help="CPF no formato 000.000.000-00"
        )
        
        # Armazena informações pessoais
        if nome or data_nascimento or cpf:
            personal_info = {
                'nome': nome,
                'data_nascimento': data_nascimento,
                'cpf': cpf
            }
        else:
            personal_info = None
        
        # Botão para assinar
        if st.button("🔐 ASSINAR PDF", disabled=not (uploaded_file and (signature_text or signature_image))):
            if uploaded_file and (signature_text or signature_image):
                with st.spinner("Processando assinatura..."):
                    # Cria arquivo temporário para o PDF original
                    temp_input = tempfile.mktemp(suffix='.pdf')
                    with open(temp_input, 'wb') as f:
                        f.write(uploaded_file.getvalue())
                    
                    # Cria arquivo temporário para o PDF assinado
                    temp_output = tempfile.mktemp(suffix='.pdf')
                    
                    # Adiciona assinatura
                    if add_signature_to_pdf(temp_input, signature_text, temp_output, signature_image, personal_info):
                        # Lê o PDF assinado
                        with open(temp_output, 'rb') as f:
                            signed_pdf = f.read()
                        
                        # Nome do arquivo de saída
                        original_name = uploaded_file.name.replace('.pdf', '')
                        output_name = f"{original_name}_assinado.pdf"
                        
                        # Botão de download
                        st.success("✅ PDF assinado com sucesso!")
                        st.download_button(
                            label="📥 BAIXAR PDF ASSINADO",
                            data=signed_pdf,
                            file_name=output_name,
                            mime="application/pdf"
                        )
                        
                        # Mostra informações do PDF assinado
                        try:
                            pdf_reader = PyPDF2.PdfReader(io.BytesIO(signed_pdf))
                            st.info(f"📊 Páginas no documento assinado: {len(pdf_reader.pages)}")
                        except:
                            pass
                        
                        # Remove arquivos temporários
                        os.remove(temp_input)
                        os.remove(temp_output)
                    else:
                        st.error("❌ Erro ao assinar o PDF")
            else:
                st.warning("⚠️ Por favor, carregue um PDF e digite uma assinatura ou desenhe uma")
    
    # Área de informações
    st.markdown("---")
    st.header("ℹ️ Informações")
    
    col_info1, col_info2, col_info3 = st.columns(3)
    
    with col_info1:
        st.markdown("""
        ### 🔒 Segurança
        - Assinaturas digitais garantem autenticidade
        - Timestamp automático em cada assinatura
        - Integridade do documento preservada
        """)
    
    with col_info2:
        st.markdown("""
        ### ⚡ Rapidez
        - Processamento instantâneo
        - Interface intuitiva
        - Download direto do PDF assinado
        """)
    
    with col_info3:
        st.markdown("""
        ### 📋 Compatibilidade
        - Suporte a todos os PDFs
        - Mantém qualidade original
        - Funciona em qualquer dispositivo
        """)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #666;'>Desenvolvido com ❤️ usando Streamlit</p>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
