# --- Imports Essenciais ---
import os
import csv
import json
import re
import logging
import requests
import sqlite3
from io import StringIO
from openpyxl import Workbook
from tempfile import NamedTemporaryFile
from datetime import datetime
import hashlib

from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify, send_file

import PyPDF2
import docx
import spacy

# --- Configuração de Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# --- Configuração do Aplicativo Flask ---
# ESTAS LINHAS DEVEM VIR ANTES DE QUALQUER @app.route OU USO DE 'app'
app = Flask(__name__)
app.static_folder = 'static'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'troque_esta_chave_em_producao_forte_e_aleatoria')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'SUA_CHAVE_GEMINI_AQUI_OU_COLOQUE_A_SUA_REAL') # Sua chave real aqui

# Garante que a pasta 'uploads' exista. Se não existir, ela é criada.
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
if not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], 'processados')):
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'processados'))


# --- Funções Utilitárias de Processamento de Currículos ---

def extrair_texto(caminho):
    """Extrai texto de arquivos PDF ou DOCX."""
    if caminho.endswith('.pdf'):
        try:
            with open(caminho, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                return " ".join([p.extract_text() for p in reader.pages if p.extract_text()])
        except Exception as e:
            logger.error(f"Erro ao extrair PDF: {e}")
            return ""
    elif caminho.endswith('.docx'):
        try:
            doc = docx.Document(caminho)
            return " ".join([p.text for p in doc.paragraphs if p.text])
        except Exception as e:
            logger.error(f"Erro ao extrair DOCX: {e}")
            return ""
    return ""

nlp = None # Variável global para o modelo spaCy
def get_nlp():
    """Carrega o modelo spaCy para PLN (singleton para evitar recarregar)."""
    global nlp
    if nlp is None:
        try:
            nlp = spacy.load('pt_core_news_sm')
            logger.info("Modelo spaCy 'pt_core_news_sm' carregado.")
        except OSError:
            logger.warning("Modelo 'pt_core_news_sm' não encontrado. Tentando baixar...")
            try:
                spacy.cli.download('pt_core_news_sm')
                nlp = spacy.load('pt_core_news_sm')
                logger.info("Download e carregamento do modelo spaCy realizado com sucesso.")
            except Exception as e:
                logger.error(f"Falha ao baixar/carregar modelo spaCy: {e}")
                nlp = None
    return nlp

def processar_texto_com_spacy(texto):
    """Processa texto com spaCy, retorna doc ou texto bruto se modelo indisponível."""
    modelo = get_nlp()
    if modelo is None:
        logger.error("Modelo spaCy não disponível. Retornando Doc vazio.")
        # Retorna um Doc vazio a partir do vocabulário, se o vocabulário estiver disponível.
        # Adicionei uma verificação para get_nlp() para evitar erro se ele falhar na primeira vez
        return spacy.tokens.Doc(get_nlp().vocab, words=[]) if get_nlp() and get_nlp().vocab else None
    return modelo(texto)

def analisar_com_gemini(dados_candidato):
    """Gera análise inteligente do candidato usando Gemini (Google AI)."""
    if not GEMINI_API_KEY or GEMINI_API_KEY == 'SUA_CHAVE_GEMINI_AQUI_OU_COLOQUE_A_SUA_REAL':
        logger.warning("GEMINI_API_KEY não configurada. Análise Gemini será desativada.")
        return "Análise de IA desativada: Chave de API Gemini ausente ou inválida."

    prompt = f"""
    Você é um especialista em RH. Analise o seguinte candidato e gere um breve resumo profissional, com seus pontos fortes, e uma recomendação final sobre a adequação do candidato para vagas de TI/Programação.
    Use um tom objetivo e motivacional para o RH.
    Limita a resposta a 500 caracteres, seja conciso.

    Dados extraídos do currículo:
    Nome: {dados_candidato.get('nome')}
    Email: {dados_candidato.get('email')}
    Telefone: {dados_candidato.get('telefone')}
    LinkedIn: {dados_candidato.get('linkedin')}
    Idade: {dados_candidato.get('idade')}
    Cargo Desejado: {dados_candidato.get('cargo_desejado')}
    Último Cargo: {dados_candidato.get('ultimo_cargo')}
    Disponibilidade: {dados_candidato.get('disponibilidade')}
    Habilidades: {', '.join(dados_candidato.get('habilidades', []))}
    Formação: {json.dumps(dados_candidato.get('formacao', []))}
    Experiência: {json.dumps(dados_candidato.get('experiencia', []))}
    Idiomas: {', '.join(dados_candidato.get('idiomas', []))}
    Pontuação (calculada pelo sistema): {dados_candidato.get('pontuacao')}
    Motivos da pontuação (lista de pontos fortes que contribuíram para a pontuação): {', '.join(dados_candidato.get('motivos_pontuacao', []))}

    Gere o resumo e recomendação.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and result['candidates']:
                gemini_text = result['candidates'][0]['content']['parts'][0]['text']
                return gemini_text[:1000]
            else:
                logger.warning(f"Resposta Gemini sem 'candidates' ou vazia: {result}")
                return "Não foi possível gerar análise inteligente (resposta vazia)."
        else:
            logger.error(f"Erro Gemini: Status {response.status_code} - {response.text}")
            return f"Erro Gemini: {response.status_code}. Tente novamente."
    except requests.exceptions.Timeout:
        logger.error("Erro na requisição Gemini: Tempo limite excedido.")
        return "Erro na análise inteligente (tempo limite)."
    except Exception as e:
        logger.error(f"Erro na requisição Gemini: {e}")
        return "Erro na análise inteligente."


# --- Banco de Dados SQLite ---
DATABASE = 'candidatos.db' # Nome do arquivo do banco de dados
VAGAS_DB = 'vagas.db' # Nome do banco de dados para vagas

def get_db():
    """Abre uma nova conexão com o banco de dados SQLite de candidatos."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Inicializa a tabela 'candidatos' no banco de dados se ela não existir.
    Define a estrutura das colunas, incluindo 'analise_ia' e 'status'.
    """
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
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
                analise_ia TEXT,
                status TEXT DEFAULT 'ativo',
                data_processamento TEXT
            )
        ''')
        db.commit()
        db.close()

# Função para banco de dados de vagas
def get_vagas_db():
    """Abre uma nova conexão com o banco de dados SQLite de vagas."""
    conn = sqlite3.connect(VAGAS_DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_vagas_db():
    """Inicializa a tabela de vagas se não existir."""
    with app.app_context():
        db = get_vagas_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vagas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                requisitos TEXT NOT NULL,
                data_criacao TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()
        db.close()

# Inicializa AMBOS os bancos de dados ao iniciar o app.
with app.app_context():
    init_db()
    init_vagas_db()


# --- Rotas de Interface (Exibição de Páginas HTML) ---

@app.route('/')
def login():
    """Renderiza a página de login."""
    return render_template('login.html')

# --- Rotas de Autenticação (APIs) ---
USERS = [ # Usuários hardcoded para demonstração
    {'email': 'arthur@gmail.com', 'senha': 'arthur123', 'nome': 'Arthur Carvalho'}
]

@app.route('/api/login', methods=['POST'])
def api_login():
    """API para autenticação de usuário."""
    data = request.get_json()
    email = data.get('email')
    senha = data.get('senha')
    for user in USERS:
        if user['email'] == email and user['senha'] == senha:
            session['user'] = user # Armazena informações do usuário na sessão
            return jsonify({'success': True, 'nome': user['nome'], 'email': user['email']})
    return jsonify({'success': False, 'message': 'Credenciais inválidas.'}), 401

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """API para deslogar usuário."""
    session.pop('user', None) # Remove 'user' da sessão
    return jsonify({'success': True})

@app.route('/api/register', methods=['POST'])
def api_register():
    """API para registro de novo usuário (simples)."""
    data = request.get_json()
    email = data.get('email')
    senha = data.get('senha')
    nome = data.get('nome')
    if not email or not senha or not nome:
        return jsonify({'success': False, 'message': 'Todos os campos são obrigatórios.'}), 400
    for user in USERS:
        if user['email'] == email:
            return jsonify({'success': False, 'message': 'Email já cadastrado.'}), 400
    USERS.append({'email': email, 'senha': senha, 'nome': nome}) # Adiciona novo usuário (apenas em memória)
    return jsonify({'success': True, 'nome': nome, 'email': email})

@app.route('/home')
def home():
    """Renderiza a dashboard principal."""
    return render_template('dashboard.html')

@app.route('/vagas')
def vagas():
    """Renderiza a página de vagas."""
    # Busca vagas do banco de dados e as passa para o template
    db = get_vagas_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM vagas ORDER BY id DESC')
    vagas_db = cursor.fetchall()
    db.close()
    vagas_list = [dict(v) for v in vagas_db] # Converte para lista de dicionários
    return render_template('vagas.html', vagas=vagas_list)

@app.route('/candidatos_ranqueados')
def candidatos_ranqueados():
    """
    Renderiza a lista ranqueada de candidatos ativos.
    Pode filtrar por pontuação mínima se o parâmetro for passado na URL.
    """
    pontuacao_min = request.args.get('pontuacao_min', default=None, type=int)
    db = get_db()
    cursor = db.cursor()
    query = "SELECT * FROM candidatos WHERE status = 'ativo'" # Consulta SQL para candidatos ativos
    params = []
    if pontuacao_min is not None: # Adiciona filtro de pontuação se especificado
        query += " AND pontuacao >= ?"
        params.append(pontuacao_min)
    query += " ORDER BY pontuacao DESC" # Ordena por pontuação decrescente
    cursor.execute(query, params) # Executa a consulta
    candidatos_db = cursor.fetchall() # Busca todos os resultados
    db.close()
    
    candidatos_para_template = [] # Lista de dicionários para passar ao template
    for cand in candidatos_db:
        candidatos_para_template.append(dict(cand)) # Converte cada linha do DB para um dicionário
    
    # Renderiza o template results.html, passando a lista de candidatos
    return render_template('results.html', candidatos=candidatos_para_template)

@app.route('/detalhes_candidato/<int:candidate_id>')
def detalhes_candidato(candidate_id):
    """
    Renderiza a página de detalhes de um candidato específico.
    Busca o candidato pelo ID no banco de dados.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM candidatos WHERE id = ?", (candidate_id,)) # Busca candidato por ID
    candidato = cursor.fetchone() # Pega apenas um resultado
    db.close()

    if candidato: # Se o candidato for encontrado
        candidato_dict = dict(candidato) # Converte para dicionário Python

        # Deserializa campos JSON que foram salvos como strings (com verificação de tipo para segurança)
        candidato_dict['habilidades'] = json.loads(candidato_dict['habilidades']) if candidato_dict['habilidades'] and isinstance(candidato_dict['habilidades'], str) else []
        candidato_dict['formacao'] = json.loads(candidato_dict['formacao']) if candidato_dict['formacao'] and isinstance(candidato_dict['formacao'], str) else []
        candidato_dict['experiencia'] = json.loads(candidato_dict['experiencia']) if candidato_dict['experiencia'] and isinstance(candidato_dict['experiencia'], str) else []
        candidato_dict['idiomas'] = json.loads(candidato_dict['idiomas']) if candidato_dict['idiomas'] and isinstance(candidato_dict['idiomas'], str) else []
        candidato_dict['motivos_pontuacao'] = json.loads(candidato_dict['motivos_pontuacao']) if candidato_dict['motivos_pontuacao'] and isinstance(candidato_dict['motivos_pontuacao'], str) else []

        # Campos calculados para o frontend (compatibilidade com lógica JS)
        candidato_dict['pontuacaoGeral'] = candidato_dict['pontuacao']
        if candidato_dict['pontuacaoGeral'] > 0:
            candidato_dict['fitTecnico'] = max(1, min(10, round(candidato_dict['pontuacaoGeral'] * 0.9 / 10)))
            candidato_dict['experienciaRelevante'] = max(1, min(10, round(candidato_dict['pontuacaoGeral'] * 0.8 / 10)))
            candidato_dict['fitCultural'] = max(1, min(10, round(candidato_dict['pontuacaoGeral'] * 0.7 / 10)))
        else: # Se a pontuação for 0, os fits também são 0
            candidato_dict['fitTecnico'] = 0
            candidato_dict['experienciaRelevante'] = 0
            candidato_dict['fitCultural'] = 0
        
        # O campo 'analise_ia' vem direto do DB
        candidato_dict['analise_ia'] = candidato['analise_ia'] if 'analise_ia' in candidato.keys() and candidato['analise_ia'] else 'N/A'

        # Renderiza o template candidate_details.html, passando o dicionário do candidato
        return render_template('candidate_details.html', candidate=candidato_dict)
    
    # Se o candidato não for encontrado, exibe mensagem flash e redireciona
    flash('Candidato não encontrado.', 'error')
    return redirect(url_for('candidatos_ranqueados'))

@app.route('/upload_curriculos')
def upload_curriculos_page():
    """Renderiza a página de upload de currículos."""
    return render_template('upload.html')

@app.route('/processando_curriculos')
def processando_curriculos_page():
    """Renderiza a página de processamento de currículos."""
    return render_template('processing.html')

@app.route('/agendar_entrevista_page')
def agendar_entrevista_page():
    """
    Renderiza a página de agendamento de entrevista.
    Recebe 'id' e 'name' do candidato via parâmetros de URL.
    """
    candidate_id = request.args.get('id')
    candidate_name = request.args.get('name')
    return render_template('agendar_entrevista.html', candidate_id=candidate_id, candidate_name=candidate_name)


# --- Rotas de Ações (APIs para o Frontend) ---

# API para criar vaga
@app.route('/api/vagas', methods=['POST'])
def api_criar_vaga():
    """API para criar uma nova vaga."""
    data = request.get_json()
    nome = data.get('nome')
    requisitos = data.get('requisitos')
    if not nome or not requisitos:
        return jsonify({'success': False, 'message': 'Nome e requisitos obrigatórios.'}), 400
    db = get_vagas_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO vagas (nome, requisitos) VALUES (?, ?)', (nome, requisitos))
    db.commit()
    vaga_id = cursor.lastrowid
    db.close()
    return jsonify({'success': True, 'id': vaga_id, 'nome': nome, 'requisitos': requisitos})

# API para listar vagas
@app.route('/api/vagas', methods=['GET'])
def api_listar_vagas():
    """API para listar todas as vagas."""
    db = get_vagas_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM vagas ORDER BY id DESC')
    vagas_db = cursor.fetchall()
    db.close()
    vagas_list = [dict(v) for v in vagas_db]
    return jsonify({'success': True, 'vagas': vagas_list})

# API para excluir vaga
@app.route('/api/vagas/<int:vaga_id>', methods=['DELETE'])
def api_excluir_vaga(vaga_id):
    """API para excluir uma vaga."""
    db = get_vagas_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM vagas WHERE id = ?', (vaga_id,))
    db.commit()
    db.close()
    return jsonify({'success': True, 'message': 'Vaga excluída.'})


@app.route('/reprove_candidate/<int:candidate_id>', methods=['POST'])
def reprove_candidate(candidate_id):
    """
    API para reprovar um candidato (atualiza o status para 'reprovado' no DB).
    Retorna JSON com status de sucesso/erro.
    """
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("UPDATE candidatos SET status = 'reprovado' WHERE id = ?", (candidate_id,))
        db.commit()
        return jsonify({'success': True, 'message': 'Candidato reprovado com sucesso!'})
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao reprovar candidato {candidate_id}: {e}")
        return jsonify({'success': False, 'message': 'Erro ao reprovar candidato.'}), 500
    finally:
        db.close()

@app.route('/delete_candidate/<int:candidate_id>', methods=['POST'])
def delete_candidate(candidate_id):
    """
    API para excluir um candidato do banco de dados permanentemente.
    Retorna JSON com status de sucesso/erro.
    """
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM candidatos WHERE id = ?", (candidate_id,))
        db.commit()
        return jsonify({'success': True, 'message': 'Candidato excluído com sucesso!'})
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao excluir candidato {candidate_id}: {e}")
        return jsonify({'success': False, 'message': 'Erro ao excluir candidato.'}), 500
    finally:
        db.close()


# --- Rotas de Exportação ---
@app.route('/export_candidatos_completo_csv')
def export_candidatos_completo_csv():
    """
    Exporta todos os dados dos candidatos ativos em CSV, incluindo campos detalhados para integração, auditoria e relatórios.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM candidatos WHERE status = 'ativo' ORDER BY pontuacao DESC")
    candidatos = cursor.fetchall()
    db.close()

    # Inicialize a variável StringIO aqui
    from io import StringIO  # Certifique-se de importar StringIO
    si = StringIO()  # Inicializando a variável StringIO corretamente
    writer = csv.writer(si)
    
    # Cabeçalhos do CSV
    headers = [
        'ID', 'Nome', 'Email', 'Telefone', 'LinkedIn', 'Idade', 'Cargo Desejado', 
        'Último Cargo', 'Disponibilidade', 'Pontuação', 'Habilidades', 'Formação', 
        'Experiência', 'Idiomas', 'Motivos Pontuação (Detalhado)', 'Análise IA (Resumo)', 'Status', 
        'Arquivo Original (Hash)', 'Arquivo Processado'
    ]
    writer.writerow(headers)

    for cand in candidatos:
        # Tenta carregar JSON ou fallback para string/lista vazia
        habilidades = json.loads(cand['habilidades']) if cand['habilidades'] and isinstance(cand['habilidades'], str) else (cand['habilidades'] if isinstance(cand['habilidades'], list) else [])
        formacao = json.loads(cand['formacao']) if cand['formacao'] and isinstance(cand['formacao'], str) else []
        experiencia = json.loads(cand['experiencia']) if cand['experiencia'] and isinstance(cand['experiencia'], str) else []
        idiomas = json.loads(cand['idiomas']) if cand['idiomas'] and isinstance(cand['idiomas'], str) else []
        motivos_pontuacao = json.loads(cand['motivos_pontuacao']) if cand['motivos_pontuacao'] and isinstance(cand['motivos_pontuacao'], str) else []
        analise_ia_text = cand['analise_ia'] if 'analise_ia' in cand.keys() and cand['analise_ia'] else 'N/A'

        # Processar rastreabilidade de arquivos
        arquivo_original_hash = ''
        arquivo_processado = ''
        if 'data_processamento' in cand.keys() and cand['data_processamento']:
            partes = cand['data_processamento'].split(';')
            for parte in partes:
                if parte.startswith('original_hash:'):
                    arquivo_original_hash = parte.replace('original_hash:', '')
                elif parte.startswith('processado:'):
                    arquivo_processado = parte.replace('processado:', '')

        # Escreve a linha no CSV
        writer.writerow([
            cand['id'],
            cand['nome'],
            cand['email'],
            cand['telefone'],
            cand['linkedin'],
            cand['idade'],
            cand['cargo_desejado'],
            cand['ultimo_cargo'],
            cand['disponibilidade'],
            cand['pontuacao'],
            '|'.join(habilidades), # Habilidades separadas por | para fácil leitura
            json.dumps(formacao), # Mantém formação como string JSON para evitar quebra de CSV
            json.dumps(experiencia), # Mantém experiência como string JSON
            '|'.join(idiomas), # Idiomas separados por |
            '|'.join(motivos_pontuacao), # Motivos separados por |
            analise_ia_text, # Análise IA
            cand['status'],
            arquivo_original_hash,
            arquivo_processado
        ])
    output = si.getvalue()
    return app.response_class(
        output,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=candidatos_completo.csv"}
    )


@app.route('/export_candidatos_completo_excel')
def export_candidatos_completo_excel():
    """
    Exporta todos os dados dos candidatos ativos em Excel (.xlsx), incluindo campos detalhados.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM candidatos WHERE status = 'ativo' ORDER BY pontuacao DESC")
    candidatos = cursor.fetchall()
    db.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Candidatos Completo"
    
    # Cabeçalhos do Excel
    headers = [
        'ID', 'Nome', 'Email', 'Telefone', 'LinkedIn', 'Idade', 'Cargo Desejado', 
        'Último Cargo', 'Disponibilidade', 'Pontuação', 'Habilidades', 'Formação', 
        'Experiência', 'Idiomas', 'Motivos Pontuação (Detalhado)', 'Análise IA (Resumo)', 'Status', 
        'Arquivo Original (Hash)', 'Arquivo Processado'
    ]
    ws.append(headers)

    for cand in candidatos:
        habilidades = json.loads(cand['habilidades']) if cand['habilidades'] and isinstance(cand['habilidades'], str) else (cand['habilidades'] if isinstance(cand['habilidades'], list) else [])
        formacao = json.loads(cand['formacao']) if cand['formacao'] and isinstance(cand['formacao'], str) else []
        experiencia = json.loads(cand['experiencia']) if cand['experiencia'] and isinstance(cand['experiencia'], str) else []
        idiomas = json.loads(cand['idiomas']) if cand['idiomas'] and isinstance(cand['idiomas'], str) else []
        motivos_pontuacao = json.loads(cand['motivos_pontuacao']) if cand['motivos_pontuacao'] and isinstance(cand['motivos_pontuacao'], str) else []
        analise_ia_text = cand['analise_ia'] if 'analise_ia' in cand.keys() and cand['analise_ia'] else 'N/A'

        arquivo_original_hash = ''
        arquivo_processado = ''
        if 'data_processamento' in cand.keys() and cand['data_processamento']:
            partes = cand['data_processamento'].split(';')
            for parte in partes:
                if parte.startswith('original_hash:'):
                    arquivo_original_hash = parte.replace('original_hash:', '')
                elif parte.startswith('processado:'):
                    arquivo_processado = parte.replace('processado:', '')

        ws.append([
            cand['id'],
            cand['nome'],
            cand['email'],
            cand['telefone'],
            cand['linkedin'],
            cand['idade'],
            cand['cargo_desejado'],
            cand['ultimo_cargo'],
            cand['disponibilidade'],
            cand['pontuacao'],
            ', '.join(habilidades), # Excel pode lidar melhor com CSV simples aqui
            json.dumps(formacao),
            json.dumps(experiencia),
            ', '.join(idiomas),
            ', '.join(motivos_pontuacao),
            analise_ia_text,
            cand['status'],
            arquivo_original_hash,
            arquivo_processado
        ])
    from tempfile import NamedTemporaryFile
    tmp = NamedTemporaryFile(delete=False, suffix='.xlsx')
    wb.save(tmp.name)
    tmp.close()
    return send_file(tmp.name, as_attachment=True, download_name='candidatos_completo.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/export_aprovados_excel')
def export_aprovados_excel():
    """
    Exporta apenas os candidatos aprovados (pontuação >= 60) em Excel (.xlsx).
    """
    db = get_db()
    cursor = db.cursor()
    # Selecionar mais campos para serem úteis
    cursor.execute("SELECT id, nome, email, telefone, linkedin, idade, pontuacao, habilidades, formacao, experiencia, idiomas, analise_ia, data_processamento FROM candidatos WHERE status = 'ativo' AND pontuacao >= 60 ORDER BY pontuacao DESC")
    candidatos = cursor.fetchall()
    db.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Candidatos Aprovados"
    ws.append(['ID', 'Nome', 'Email', 'Telefone', 'LinkedIn', 'Idade', 'Pontuação', 'Habilidades', 'Formação', 'Experiência', 'Idiomas', 'Análise IA', 'Arquivo Original (Hash)', 'Arquivo Processado'])
    for cand in candidatos:
        habilidades = json.loads(cand['habilidades']) if cand['habilidades'] and isinstance(cand['habilidades'], str) else (cand['habilidades'] if isinstance(cand['habilidades'], list) else [])
        formacao = json.loads(cand['formacao']) if cand['formacao'] and isinstance(cand['formacao'], str) else []
        experiencia = json.loads(cand['experiencia']) if cand['experiencia'] and isinstance(cand['experiencia'], str) else []
        idiomas = json.loads(cand['idiomas']) if cand['idiomas'] and isinstance(cand['idiomas'], str) else []
        analise_ia_text = cand['analise_ia'] if 'analise_ia' in cand.keys() and cand['analise_ia'] else 'N/A'
        
        arquivo_original_hash = ''
        arquivo_processado = ''
        if 'data_processamento' in cand.keys() and cand['data_processamento']:
            partes = cand['data_processamento'].split(';')
            for parte in partes:
                if parte.startswith('original_hash:'):
                    arquivo_original_hash = parte.replace('original_hash:', '')
                elif parte.startswith('processado:'):
                    arquivo_processado = parte.replace('processado:', '')
        ws.append([
            cand['id'],
            cand['nome'],
            cand['email'],
            cand['telefone'],
            cand['linkedin'],
            cand['idade'],
            cand['pontuacao'],
            ', '.join(habilidades),
            json.dumps(formacao),
            json.dumps(experiencia),
            ', '.join(idiomas),
            analise_ia_text,
            arquivo_original_hash,
            arquivo_processado
        ])
    output = si.getvalue()
    return app.response_class(
        output,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=candidatos_aprovados.csv"}
    )

# --- Inicialização do Servidor Flask ---
if __name__ == '__main__':
    app.run(debug=True)