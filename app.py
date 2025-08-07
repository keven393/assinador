from flask import Flask, render_template, request, jsonify, send_file, session
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.units import inch, cm
import io
import os
from datetime import datetime
import tempfile
import base64
from PIL import Image
import numpy as np
import uuid
import shutil

app = Flask(__name__)
app.secret_key = 'assinador_pdf_secret_key_2024'

# Diretório para arquivos temporários
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_files')
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Diretório para assets estáticos
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

def cleanup_temp_files():
    """Remove arquivos temporários antigos"""
    try:
        for filename in os.listdir(TEMP_DIR):
            file_path = os.path.join(TEMP_DIR, filename)
            if os.path.isfile(file_path):
                # Remove arquivos mais antigos que 1 hora
                if os.path.getmtime(file_path) < datetime.now().timestamp() - 3600:
                    os.remove(file_path)
    except Exception:
        pass

def create_logo_image():
    """Cria um logo padrão se não existir"""
    logo_path = os.path.join(STATIC_DIR, 'images', 'logo.png')
    
    if not os.path.exists(logo_path):
        # Cria um logo simples usando PIL
        from PIL import Image, ImageDraw, ImageFont
        
        # Cria uma imagem 200x100 com fundo azul
        img = Image.new('RGB', (200, 100), color='#0d6efd')
        draw = ImageDraw.Draw(img)
        
        # Adiciona texto "LOGO"
        try:
            # Tenta usar uma fonte do sistema
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        # Centraliza o texto
        text = "LOGO"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (200 - text_width) // 2
        y = (100 - text_height) // 2
        
        draw.text((x, y), text, fill='white', font=font)
        img.save(logo_path)
    
    return logo_path

def add_signature_to_all_pages(pdf_file, signature_text, output_path, signature_image=None, personal_info=None, logo_path=None):
    """Adiciona assinatura digital a todas as páginas do PDF no canto inferior direito"""
    try:
        # Lê o PDF original
        with open(pdf_file, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            pdf_writer = PyPDF2.PdfWriter()
            
            # Cria logo se não existir
            if not logo_path:
                logo_path = create_logo_image()
            
            # Para cada página do PDF
            for page_num, page in enumerate(pdf_reader.pages):
                # Cria um PDF temporário para a página atual
                temp_page_path = tempfile.mktemp(suffix='.pdf')
                
                # Cria um canvas para adicionar a assinatura no canto inferior direito
                c = canvas.Canvas(temp_page_path, pagesize=A4)
                width, height = A4
                
                # Define a posição da assinatura no canto inferior direito
                signature_x = width - 10*cm  # 10cm da borda direita para acomodar logo + info + assinatura
                signature_y = 2*cm  # 2cm da borda inferior
                
                # Calcula altura da assinatura para redimensionar o logo proporcionalmente
                signature_height = 1.2*cm  # Reduzida para caber melhor
                logo_height = signature_height  # Logo na mesma altura da assinatura
                logo_width = logo_height * 1.5  # Reduzida proporção para 1.5:1
                
                # Adiciona o logo (redimensionado proporcionalmente à assinatura)
                if os.path.exists(logo_path):
                    try:
                        logo_img = RLImage(logo_path)
                        logo_img.drawHeight = logo_height
                        logo_img.drawWidth = logo_width
                        logo_img.drawOn(c, signature_x, signature_y)  # Logo alinhado com a assinatura
                    except:
                        pass
                
                # Adiciona informações pessoais no meio (alinhadas com a assinatura)
                if personal_info:
                    info_x = signature_x + logo_width + 0.5*cm  # Posição após o logo
                    info_y = signature_y + 0.8*cm  # Alinhado com a assinatura (mesma altura)
                    c.setFont("Helvetica-Bold", 8)
                    c.setFillColor(colors.darkblue)
                    
                    if personal_info.get('nome'):
                        c.drawString(info_x, info_y, f"Nome: {personal_info['nome']}")
                        info_y -= 0.3*cm
                    if personal_info.get('cpf'):
                        c.drawString(info_x, info_y, f"CPF: {personal_info['cpf']}")
                        info_y -= 0.3*cm
                    if personal_info.get('data_nascimento'):
                        c.drawString(info_x, info_y, f"Data: {personal_info['data_nascimento']}")
                
                # Adiciona a assinatura desenhada (alinhada com o logo e info)
                if signature_image:
                    try:
                        # Salva a imagem da assinatura temporariamente
                        signature_temp = tempfile.mktemp(suffix='.png')
                        with open(signature_temp, 'wb') as f:
                            f.write(base64.b64decode(signature_image.split(',')[1]))
                        
                        # Adiciona a assinatura desenhada
                        signature_img = RLImage(signature_temp)
                        signature_img.drawHeight = signature_height
                        signature_img.drawWidth = 2.5*cm  # Largura fixa para a assinatura
                        
                        # Posiciona a assinatura após as informações pessoais
                        signature_img_x = signature_x + logo_width + 3*cm  # Posição após logo + info
                        signature_img_y = signature_y  # Mesma altura do logo
                        signature_img.drawOn(c, signature_img_x, signature_img_y)
                        
                        # Limpa arquivo temporário
                        os.remove(signature_temp)
                    except Exception as e:
                        print(f"Erro ao adicionar assinatura desenhada: {e}")
                
                # Adiciona timestamp
                timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                c.setFont("Helvetica", 6)
                c.setFillColor(colors.grey)
                c.drawString(signature_x, signature_y - 0.5*cm, f"Assinado em: {timestamp}")
                
                c.save()
                
                # Lê a página com assinatura
                with open(temp_page_path, 'rb') as temp_file:
                    temp_reader = PyPDF2.PdfReader(temp_file)
                    temp_page = temp_reader.pages[0]
                    
                    # Mescla a página original com a assinatura
                    page.merge_page(temp_page)
                    pdf_writer.add_page(page)
                
                # Remove arquivo temporário
                os.remove(temp_page_path)
            
            # Salva o PDF final
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            return True
    except Exception as e:
        print(f"Erro ao processar PDF: {e}")
        return False

def create_signature_pdf(text, output_path, signature_image=None, personal_info=None):
    """Cria um PDF com a assinatura digital (mantido para compatibilidade)"""
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
    """Adiciona assinatura digital a um PDF existente (mantido para compatibilidade)"""
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
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_signature', methods=['POST'])
def process_signature():
    try:
        # Limpa arquivos temporários antigos
        cleanup_temp_files()
        
        # Recebe dados do formulário
        signature_text = request.form.get('signature_text', '')
        signature_image = request.form.get('signature_image', '')
        nome = request.form.get('nome', '')
        data_nascimento = request.form.get('data_nascimento', '')
        cpf = request.form.get('cpf', '')
        signature_type = request.form.get('signature_type', 'all_pages')  # Novo campo
        
        # Verifica se há arquivo PDF
        if 'pdf_file' not in request.files:
            return jsonify({'success': False, 'message': 'Nenhum arquivo PDF foi enviado'})
        
        pdf_file = request.files['pdf_file']
        if pdf_file.filename == '':
            return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'})
        
        # Cria arquivo temporário para o PDF original
        temp_input = tempfile.mktemp(suffix='.pdf')
        pdf_file.save(temp_input)
        
        # Cria arquivo temporário para o PDF assinado
        temp_output = tempfile.mktemp(suffix='.pdf')
        
        # Informações pessoais
        personal_info = None
        if nome or data_nascimento or cpf:
            personal_info = {
                'nome': nome,
                'data_nascimento': data_nascimento,
                'cpf': cpf
            }
        
        # Cria logo se não existir
        logo_path = create_logo_image()
        
        # Processa assinatura baseado no tipo
        success = False
        if signature_type == 'all_pages':
            # Nova funcionalidade: assinatura em todas as páginas
            success = add_signature_to_all_pages(temp_input, signature_text, temp_output, signature_image, personal_info, logo_path)
        else:
            # Funcionalidade original: assinatura no final
            success = add_signature_to_pdf(temp_input, signature_text, temp_output, signature_image, personal_info)
        
        if success:
            # Gera um ID único para o arquivo
            file_id = str(uuid.uuid4())
            final_filename = f"{file_id}_{pdf_file.filename.replace('.pdf', '_assinado.pdf')}"
            final_path = os.path.join(TEMP_DIR, final_filename)
            
            # Move o arquivo assinado para o diretório temporário
            shutil.move(temp_output, final_path)
            
            # Remove arquivo temporário de entrada
            os.remove(temp_input)
            
            # Salva apenas o ID do arquivo na sessão
            session['signed_pdf_id'] = file_id
            session['filename'] = pdf_file.filename.replace('.pdf', '_assinado.pdf')
            
            return jsonify({
                'success': True, 
                'message': 'PDF assinado com sucesso!',
                'filename': session['filename']
            })
        else:
            return jsonify({'success': False, 'message': 'Erro ao processar o PDF'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

@app.route('/download_pdf')
def download_pdf():
    if 'signed_pdf_id' in session:
        file_id = session['signed_pdf_id']
        filename = session.get('filename', 'documento_assinado.pdf')
        
        # Procura o arquivo no diretório temporário
        for temp_file in os.listdir(TEMP_DIR):
            if temp_file.startswith(file_id):
                file_path = os.path.join(TEMP_DIR, temp_file)
                
                # Limpa a sessão
                session.pop('signed_pdf_id', None)
                session.pop('filename', None)
                
                # Envia o arquivo e depois o remove
                try:
                    return send_file(
                        file_path,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/pdf'
                    )
                finally:
                    # Remove o arquivo após o download
                    try:
                        os.remove(file_path)
                    except:
                        pass
                break
        else:
            return jsonify({'success': False, 'message': 'Arquivo não encontrado'})
    else:
        return jsonify({'success': False, 'message': 'Nenhum PDF para download'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 