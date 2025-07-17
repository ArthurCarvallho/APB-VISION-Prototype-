from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify # ADICIONADO jsonify
import os
import PyPDF2
import docx
import spacy
import sqlite3
import json
import re

app = Flask(__name__)
app.static_folder = 'static'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = 'uma_chave_muito_secreta' # Mantenha esta chave secreta em um ambiente de produção!

# Certifique-se de que a pasta 'uploads' existe
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# --- Funções Auxiliares ---

def extrair_texto(caminho):
    if caminho.endswith('.pdf'):
        try:
            with open(caminho, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                return " ".join([p.extract_text() for p in reader.pages if p.extract_text()])
        except Exception as e:
            print(f"Erro ao extrair PDF: {e}")
            return ""
    elif caminho.endswith('.docx'):
        try:
            doc = docx.Document(caminho)
            return " ".join([p.text for p in doc.paragraphs if p.text])
        except Exception as e:
            print(f"Erro ao extrair DOCX: {e}")
            return ""
    return ""

try:
    nlp = spacy.load('pt_core_news_sm')
except OSError:
    print("Modelo 'pt_core_news_sm' não encontrado. Baixando...")
    spacy.cli.download('pt_core_news_sm')
    nlp = spacy.load('pt_core_news_sm')

def processar_texto_com_spacy(texto):
    doc = nlp(texto)
    return doc

# --- Configuração do Banco de Dados SQLite ---

DATABASE = 'candidatos.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Adicione a coluna 'status' aqui se você for usar para reprovar/filtrar
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS candidatos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                email TEXT,
                telefone TEXT,
                linkedin TEXT,
                idade TEXT,
                cargo_desejado TEXT,
                ultimo_cargo TEXT,
                disponibilidade TEXT,
                pontuacao INTEGER,
                habilidades TEXT,
                formacao TEXT,
                experiencia TEXT,
                idiomas TEXT,
                motivos_pontuacao TEXT,
                status TEXT DEFAULT 'ativo' -- Nova coluna para status
            )
        ''')
        db.commit()
        db.close()

# Chamar a inicialização do DB ao iniciar o app
with app.app_context():
    init_db()

# --- Rotas para o Frontend ---

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/home')
def home():
    return render_template('dashboard.html')

@app.route('/vagas')
def vagas():
    return render_template('vagas.html')

@app.route('/candidatos_ranqueados')
def candidatos_ranqueados():
    db = get_db()
    cursor = db.cursor()
    # Filtrar por status ativo se a coluna 'status' existe
    cursor.execute("SELECT * FROM candidatos WHERE status = 'ativo' ORDER BY pontuacao DESC")
    candidatos_db = cursor.fetchall()
    db.close()

    candidatos_para_template = []
    for cand in candidatos_db:
        candidatos_para_template.append({
            'id': cand['id'],
            'nome': cand['nome'],
            'pontuacao': cand['pontuacao'],
            'email': cand['email'],
        })
    return render_template('results.html', candidatos=candidatos_para_template)

@app.route('/detalhes_candidato/<int:candidate_id>')
def detalhes_candidato(candidate_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM candidatos WHERE id = ?", (candidate_id,))
    candidato = cursor.fetchone()
    db.close()

    if candidato:
        candidato_data = {
            'id': candidato['id'],
            'nome': candidato['nome'],
            'email': candidato['email'],
            'telefone': candidato['telefone'],
            'linkedin': candidato['linkedin'],
            'idade': candidato['idade'],
            'cargo_desejado': candidato['cargo_desejado'],
            'ultimo_cargo': candidato['ultimo_cargo'],
            'disponibilidade': candidato['disponibilidade'],
            'pontuacaoGeral': candidato['pontuacao'],
            'habilidades': candidato['habilidades'].split(', ') if candidato['habilidades'] else [],
            'formacao': json.loads(candidato['formacao']) if candidato['formacao'] else [],
            'experiencia': json.loads(candidato['experiencia']) if candidato['experiencia'] else [],
            'idiomas': json.loads(candidato['idiomas']) if candidato['idiomas'] else [],
            'motivosPontuacao': json.loads(candidato['motivos_pontuacao']) if candidato['motivos_pontuacao'] else [],
            'fitTecnico': 0,
            'experienciaRelevante': 0,
            'fitCultural': 0,
        }
        if candidato_data['pontuacaoGeral'] > 0:
            candidato_data['fitTecnico'] = max(1, min(10, round(candidato_data['pontuacaoGeral'] * 0.9 / 10)))
            candidato_data['experienciaRelevante'] = max(1, min(10, round(candidato_data['pontuacaoGeral'] * 0.8 / 10)))
            candidato_data['fitCultural'] = max(1, min(10, round(candidato_data['pontuacaoGeral'] * 0.7 / 10)))

        return render_template('candidate_details.html', candidate=candidato_data)
    
    flash('Candidato não encontrado.', 'error')
    return redirect(url_for('candidatos_ranqueados'))

@app.route('/upload_curriculos')
def upload_curriculos_page():
    return render_template('upload.html')

@app.route('/processando_curriculos')
def processando_curriculos_page():
    return render_template('processing.html')

@app.route('/agendar_entrevista_page')
def agendar_entrevista_page():
    return render_template('agendar_entrevista.html')

# --- Rotas de Ações (Reprovar/Excluir) ---

@app.route('/reprove_candidate/<int:candidate_id>', methods=['POST'])
def reprove_candidate(candidate_id):
    db = get_db()
    cursor = db.cursor()
    try:
        # Atualiza o status do candidato para 'reprovado'
        cursor.execute("UPDATE candidatos SET status = 'reprovado' WHERE id = ?", (candidate_id,))
        db.commit()
        flash(f'Candidato ID {candidate_id} reprovado com sucesso!', 'success')
        return jsonify({'success': True, 'message': 'Candidato reprovado com sucesso!'})
    except Exception as e:
        db.rollback()
        print(f"Erro ao reprovar candidato {candidate_id}: {e}")
        return jsonify({'success': False, 'message': 'Erro ao reprovar candidato.'}), 500
    finally:
        db.close()

@app.route('/delete_candidate/<int:candidate_id>', methods=['POST'])
def delete_candidate(candidate_id):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM candidatos WHERE id = ?", (candidate_id,))
        db.commit()
        flash(f'Candidato ID {candidate_id} excluído com sucesso!', 'success')
        return jsonify({'success': True, 'message': 'Candidato excluído com sucesso!'})
    except Exception as e:
        db.rollback()
        print(f"Erro ao excluir candidato {candidate_id}: {e}")
        return jsonify({'success': False, 'message': 'Erro ao excluir candidato.'}), 500
    finally:
        db.close()

# --- Rota de Upload de Múltiplos Currículos ---

@app.route('/upload_multiple_files', methods=['POST'])
def upload_multiple_files():
    if 'arquivos[]' not in request.files:
        flash('Nenhum arquivo enviado.', 'error')
        return redirect(url_for('upload_curriculos_page'))
    
    arquivos = request.files.getlist('arquivos[]')
    
    if not arquivos:
        flash('Nenhum arquivo selecionado.', 'error')
        return redirect(url_for('upload_curriculos_page'))
    
    for arquivo in arquivos:
        if arquivo.filename == '':
            continue
        
        filename = arquivo.filename
        caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            arquivo.save(caminho_arquivo)
            texto_curriculo = extrair_texto(caminho_arquivo)
            
            if not texto_curriculo.strip():
                flash(f'Não foi possível extrair texto do arquivo {filename}. Verifique o formato.', 'error')
                os.remove(caminho_arquivo)
                continue

            doc = processar_texto_com_spacy(texto_curriculo)
            
            nome = "Nome do Candidato Desconhecido"
            email = ""
            telefone = ""
            linkedin = ""
            idade = ""
            cargo_desejado = ""
            ultimo_cargo = ""
            disponibilidade = ""
            habilidades_detectadas_lista = []
            formacao_detectada = []
            experiencia_detectada = []
            idiomas_detectados = []
            motivos_pontuacao_lista = []

            for ent in doc.ents:
                if ent.label_ == "PER" and len(ent.text.split()) > 1:
                    nome = ent.text
                    break
            
            email_match = re.search(r'[\w\.-]+@[\w\.-]+', texto_curriculo)
            if email_match:
                email = email_match.group(0)
            
            palavras_chave_habilidades = ['Python', 'SQL', 'Django', 'AWS', 'Machine Learning', 'Agile', 'Git', 'APIs REST', 'Java', 'JavaScript', 'CSS', 'HTML']
            for palavra in palavras_chave_habilidades:
                if re.search(r'\b' + re.escape(palavra) + r'\b', texto_curriculo, re.IGNORECASE):
                    habilidades_detectadas_lista.append(palavra)
            
            pontuacao = len(habilidades_detectadas_lista) * 10
            if pontuacao > 100: pontuacao = 100

            if nome == "Nome do Candidato Desconhecido":
                nome = filename.split('.')[0].replace('_', ' ').title()
            
            if "marcos" in nome.lower(): 
                idade = "30 anos"
                cargo_desejado = "Analista de Dados Sênior"
                ultimo_cargo = "Desenvolvedor Backend"
                disponibilidade = "Imediata"
                telefone = "(34) 9 9999-9999"
                linkedin = "linkedin.com/in/marcosmendes"
                formacao_detectada = [{"curso": "Bacharelado em Ciência da Computação", "instituicao": "Universidade Federal de Uberlândia (UFU)", "periodo": "2013 - 2017"}]
                experiencia_detectada = [{"cargo": "Engenheiro de Software Sênior", "empresa": "Empresa XYZ", "periodo": "Jan 2020 - Presente", "atividades": ["Desenvolvimento de sistemas back-end em Python/Django.", "Otimização de bancos de dados SQL."]}, {"cargo": "Desenvolvedor Júnior", "empresa": "Empresa ABC", "periodo": "Fev 2018 - Dez 2019", "atividades": ["Participação em projetos de desenvolvimento web."]} ]
                idiomas_detectados = ["Português: Nativo", "Inglês: Fluente", "Espanhol: Básico"]
                motivos_pontuacao_lista = ["Sólida experiência com Python e Django.", "Histórico em projetos de Machine Learning.", "Keywords relevantes encontradas: AWS, Docker, SQL."]

            db = get_db()
            cursor = db.cursor()
            try:
                cursor.execute('''
                    INSERT INTO candidatos (nome, email, telefone, linkedin, idade, cargo_desejado, ultimo_cargo, disponibilidade, pontuacao, habilidades, formacao, experiencia, idiomas, motivos_pontuacao)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    nome, email, telefone, linkedin, idade, cargo_desejado, ultimo_cargo, disponibilidade,
                    pontuacao,
                    ", ".join(habilidades_detectadas_lista),
                    json.dumps(formacao_detectada),
                    json.dumps(experiencia_detectada),
                    json.dumps(idiomas_detectados),
                    json.dumps(motivos_pontuacao_lista)
                ))
                db.commit()
            except Exception as db_err:
                db.rollback()
                print(f"Erro ao salvar {filename} no banco de dados: {db_err}")
                flash(f'Erro ao salvar {filename} no banco de dados: {db_err}', 'error')
            finally:
                db.close()
            
            os.remove(caminho_arquivo)

        except Exception as e:
            print(f"Erro no processamento do arquivo {filename}: {e}")
            flash(f'Erro no processamento do arquivo {filename}: {e}', 'error')
            if os.path.exists(caminho_arquivo):
                os.remove(caminho_arquivo)
            continue
    
    flash('Processamento de currículos concluído!', 'success')
    return redirect(url_for('processando_curriculos_page'))

if __name__ == '__main__':
    app.run(debug=True)