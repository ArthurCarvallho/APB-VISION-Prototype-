# --- Imports Essenciais ---
import os
import csv
import json
import re
import logging
import requests
import sqlite3
from collections import Counter
from io import StringIO
from openpyxl import Workbook
from tempfile import NamedTemporaryFile
from datetime import datetime
import hashlib
import time

# Importações específicas do Flask (devem vir do módulo flask)
from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify, send_file

# Importações de bibliotecas de terceiros usadas nas funções (PyPDF2, docx, spacy)
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
# IMPORTANTE: Substitua pela sua chave real da API Gemini ou configure a variável de ambiente.
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyCy4sale7sldGWevMuYv9OPDRP5f8y_8iw')

# Garante que a pasta 'uploads' e 'processados' existam.
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
    """Processa texto com spaCy, retorna doc ou None se o modelo for indisponível."""
    modelo = get_nlp()
    if modelo is None:
        logger.error("Modelo spaCy não disponível. Retornando None.")
        return None
    return modelo(texto)

def analisar_com_gemini(dados_candidato):
    """Gera análise inteligente do candidato usando Gemini (Google AI)."""
    if not GEMINI_API_KEY or GEMINI_API_KEY == 'SUA_CHAVE' in GEMINI_API_KEY:
        # Se a IA não estiver disponíve':
        logger.warning("GEMINI_API_KEY não configurada. Análise Gemini será desativada.")
        return "Análise de IA desativada: Chave de API Gemini ausente ou inválida."

    # Limpa e formata os dados para o prompt
    habilidades_str = ', '.join(dados_candidato.get('habilidades', []))
    formacao_str = json.dumps(dados_candidato.get('formacao', []), ensure_ascii=False, indent=2)
    experiencia_str = json.dumps(dados_candidato.get('experiencia', []), ensure_ascii=False, indent=2)

    prompt = f"""
    Você é um especialista em RH e headhunter de uma empresa de tecnologia.
    Analise o seguinte candidato para uma vaga na área de TI/Desenvolvimento e gere um breve resumo profissional (máximo 3 frases), liste seus 3 principais pontos fortes e forneça uma recomendação final clara (Ex: "Recomendado para entrevista", "Considerar para vagas futuras", "Não recomendado no momento").
    Seja conciso, objetivo e use um tom profissional. Limite a resposta total a 500 caracteres.

    DADOS DO CANDIDATO:
    - Nome: {dados_candidato.get('nome')}
    - Cargo Desejado: {dados_candidato.get('cargo_desejado')}
    - Pontuação (calculada pelo sistema): {dados_candidato.get('pontuacao')}
    - Habilidades Principais: {habilidades_str}
    - Formação: {formacao_str}
    - Experiência: {experiencia_str}
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=45)
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and result['candidates']:
                gemini_text = result['candidates'][0]['content']['parts'][0]['text']
                return gemini_text.strip()
            else:
                logger.warning(f"Resposta Gemini sem 'candidates' ou vazia: {result}")
                return "Não foi possível gerar análise inteligente (resposta vazia da API)."
        else:
            logger.error(f"Erro na API Gemini: Status {response.status_code} - {response.text}")
            return f"Erro na comunicação com a IA (Status: {response.status_code}). Verifique a chave e as permissões."
    except requests.exceptions.Timeout:
        logger.error("Erro na requisição Gemini: Tempo limite excedido.")
        return "Erro na análise inteligente (tempo limite da requisição)."
    except Exception as e:
        logger.error(f"Erro inesperado na requisição Gemini: {e}")
        return "Erro inesperado durante a análise inteligente."


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
    MELHORIA: Adiciona colunas para hash do arquivo (evitar duplicatas) e rastreabilidade.
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
                hash_arquivo TEXT UNIQUE, -- Para evitar duplicatas de currículos
                nome_arquivo_processado TEXT, -- Nome do arquivo salvo
                data_upload TEXT -- Data do processamento
            )
        ''')
        # Garante que o índice no hash_arquivo exista para consultas rápidas
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_hash_arquivo ON candidatos (hash_arquivo)')
        db.commit()
        db.close()

# Função para banco de dados de vagas
def get_vagas_db():
    """Abre uma nova conexão com o banco de dados SQLite de vagas."""
    conn = sqlite3.connect(VAGAS_DB)
    conn.row_factory = sqlite3.Row
    return conn

# Em APP.py

def init_vagas_db():
    """Inicializa a tabela de vagas com a nova coluna para habilidades."""
    with app.app_context():
        db = get_vagas_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vagas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                requisitos TEXT NOT NULL,
                habilidades_chave TEXT, -- NOVA COLUNA ADICIONADA AQUI
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
    """Dashboard principal."""
    return render_template('dashboard.html')

@app.route('/vagas')
def vagas():
    """Renderiza a página de vagas."""
    db = get_vagas_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM vagas ORDER BY id DESC')
    vagas_db = cursor.fetchall()
    db.close()
    vagas_list = [dict(v) for v in vagas_db] # Converte para lista de dicionários
    return render_template('vagas.html', vagas=vagas_list)

# Em APP.py (substituir a função inteira)

@app.route('/candidatos_ranqueados')
def candidatos_ranqueados():
    """
    Renderiza a página de candidatos e também serve como API para calcular o "match".
    """
    vaga_id_selecionada = request.args.get('vaga_id', default=None, type=int)
    
    db_candidatos = get_db()
    candidatos = db_candidatos.execute("SELECT id, nome, pontuacao, habilidades FROM candidatos WHERE status = 'ativo'").fetchall()
    db_candidatos.close()

    # Se a requisição for para a API (feita pelo JavaScript)
    if vaga_id_selecionada:
        db_vagas = get_vagas_db()
        vaga = db_vagas.execute("SELECT habilidades_chave FROM vagas WHERE id = ?", (vaga_id_selecionada,)).fetchone()
        db_vagas.close()

        if not vaga:
            return jsonify({"error": "Vaga não encontrada"}), 404

        habilidades_vaga = set(json.loads(vaga['habilidades_chave'] or '[]'))
        total_habilidades_vaga = len(habilidades_vaga)

        candidatos_com_match = []
        for candidato in candidatos:
            candidato_dict = dict(candidato)
            habilidades_candidato = set(json.loads(candidato_dict.get('habilidades', '[]')))
            
            # Calcula as habilidades em comum
            habilidades_em_comum = habilidades_vaga.intersection(habilidades_candidato)
            
            # Calcula a pontuação de "Match"
            if total_habilidades_vaga > 0:
                match_score = round((len(habilidades_em_comum) / total_habilidades_vaga) * 100)
            else:
                match_score = 0
            
            candidato_dict['match_score'] = match_score
            candidatos_com_match.append(candidato_dict)

        # Ordena os candidatos pela maior pontuação de "Match"
        candidatos_ordenados = sorted(candidatos_com_match, key=lambda c: c['match_score'], reverse=True)
        return jsonify(candidatos_ordenados)

    # Se for a primeira vez que carrega a página (requisição normal do navegador)
    else:
        db_vagas = get_vagas_db()
        vagas = db_vagas.execute("SELECT id, nome FROM vagas ORDER BY nome").fetchall()
        db_vagas.close()
        
        # Ordena pela pontuação geral por padrão
        candidatos_ordenados = sorted([dict(c) for c in candidatos], key=lambda c: c.get('pontuacao', 0), reverse=True)

        return render_template('results.html', candidatos=candidatos_ordenados, vagas=vagas)

@app.route('/detalhes_candidato/<int:candidate_id>')
def detalhes_candidato(candidate_id):
    """Renderiza a página de detalhes de um candidato específico."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM candidatos WHERE id = ?", (candidate_id,))
    candidato = cursor.fetchone()
    db.close()

    if candidato:
        candidato_dict = dict(candidato)

        # Deserializa campos JSON com segurança
        for key in ['habilidades', 'formacao', 'experiencia', 'idiomas', 'motivos_pontuacao']:
            try:
                if candidato_dict[key] and isinstance(candidato_dict[key], str):
                    candidato_dict[key] = json.loads(candidato_dict[key])
                else:
                    candidato_dict[key] = candidato_dict[key] or []
            except (json.JSONDecodeError, TypeError):
                candidato_dict[key] = []
        
        # O campo 'analise_ia' vem direto do DB
        candidato_dict['analise_ia'] = candidato['analise_ia'] or 'Análise não gerada.'

        return render_template('candidate_details.html', candidate=candidato_dict)
    
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
    """Renderiza a página de agendamento de entrevista."""
    candidate_id = request.args.get('id')
    candidate_name = request.args.get('name')
    return render_template('agendar_entrevista.html', candidate_id=candidate_id, candidate_name=candidate_name)


# --- Rotas de Ações (APIs para o Frontend) ---

# API para criar vaga
# Em APP.py

@app.route('/api/vagas', methods=['POST'])
def api_criar_vaga():
    """API para criar uma nova vaga, agora com habilidades-chave."""
    data = request.get_json()
    nome = data.get('nome')
    requisitos = data.get('requisitos')
    # Recebe a nova lista de habilidades do frontend
    habilidades_chave = data.get('habilidades_chave', []) 

    if not nome or not requisitos:
        return jsonify({'success': False, 'message': 'Nome e requisitos são obrigatórios.'}), 400
    
    db = get_vagas_db()
    cursor = db.cursor()
    # Insere as habilidades como uma string JSON
    cursor.execute(
        'INSERT INTO vagas (nome, requisitos, habilidades_chave) VALUES (?, ?, ?)',
        (nome, requisitos, json.dumps(habilidades_chave))
    )
    db.commit()
    vaga_id = cursor.lastrowid
    db.close()
    
    return jsonify({'success': True, 'id': vaga_id, 'nome': nome, 'requisitos': requisitos, 'habilidades_chave': habilidades_chave})
# API para listar vagas
# Em APP.py

@app.route('/api/vagas', methods=['GET'])
def api_listar_vagas():
    """API para listar todas as vagas, incluindo as habilidades-chave."""
    db = get_vagas_db()
    # MUDANÇA: Adicionado 'habilidades_chave' na consulta SELECT
    vagas_db = db.execute('SELECT id, nome, requisitos, habilidades_chave FROM vagas ORDER BY id DESC').fetchall()
    db.close()
    
    vagas_list = []
    for v in vagas_db:
        vaga_dict = dict(v)
        # Tenta carregar as habilidades_chave de JSON para lista, se não for nulo
        try:
            vaga_dict['habilidades_chave'] = json.loads(vaga_dict['habilidades_chave'] or '[]')
        except (json.JSONDecodeError, TypeError):
            vaga_dict['habilidades_chave'] = []
        vagas_list.append(vaga_dict)

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

# Em APP.py, substitua a função antiga por esta

@app.route('/api/vagas/sugerir-habilidades', methods=['POST'])
def sugerir_habilidades_de_vaga():
    """
    Usa a IA para extrair habilidades-chave de uma descrição de vaga.
    VERSÃO MELHORADA: Mais tolerante a timeouts e a respostas inesperadas da API.
    """
    data = request.get_json()
    descricao = data.get('descricao')

    if not descricao or len(descricao.strip()) < 20:
        return jsonify({'success': False, 'message': 'Descrição da vaga muito curta ou ausente.'}), 400

    if not GEMINI_API_KEY or 'SUA_CHAVE' in GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY não configurada. Sugestão de habilidades retornará exemplos.")
        return jsonify({'success': True, 'habilidades': ['Python', 'SQL', 'Análise de Dados', 'Comunicação']})

    prompt = f"""
    Você é um especialista em recrutamento de TI. Analise a seguinte descrição de vaga de emprego.
    Extraia as 5 a 8 habilidades (técnicas e comportamentais) mais importantes mencionadas.
    Retorne APENAS uma lista de habilidades separadas por vírgula, sem nenhuma outra formatação ou texto.

    Exemplo de retorno:
    Python, Django, API REST, AWS, PostgreSQL, Trabalho em Equipe, Proatividade

    Descrição da Vaga:
    "{descricao}"
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        # MUDANÇA 1: Aumentamos o tempo de espera para 60 segundos
        response = requests.post(url, headers=headers, json=payload, timeout=60)

        if response.status_code == 200:
            result = response.json()
            
            # MUDANÇA 2: Verificação de segurança antes de tentar ler a resposta
            if 'candidates' in result and result['candidates']:
                texto_habilidades = result['candidates'][0]['content']['parts'][0]['text'].strip()
                lista_habilidades = [habilidade.strip() for habilidade in texto_habilidades.split(',') if habilidade.strip()]
                return jsonify({'success': True, 'habilidades': lista_habilidades})
            else:
                # Se a resposta veio sem a parte 'candidates', provavelmente foi um bloqueio de segurança
                logger.warning(f"Resposta da Gemini veio sem 'candidates': {result}")
                return jsonify({'success': False, 'message': 'A IA não retornou uma sugestão válida (possivelmente por filtros de segurança).'}), 500
        else:
            logger.error(f"Erro na API Gemini ao sugerir habilidades: Status {response.status_code} - {response.text}")
            return jsonify({'success': False, 'message': 'Erro ao comunicar com a IA.'}), 500
            
    except requests.exceptions.Timeout:
        logger.error("Timeout ao chamar a API Gemini para sugerir habilidades.")
        return jsonify({'success': False, 'message': 'A IA demorou muito para responder. Tente novamente.'}), 500
    except Exception as e:
        logger.error(f"Erro na requisição para sugerir habilidades: {e}")
        return jsonify({'success': False, 'message': 'Erro inesperado na análise da vaga.'}), 500
    
@app.route('/reprove_candidate/<int:candidate_id>', methods=['POST'])
def reprove_candidate(candidate_id):
    """Reprova candidato (status = 'reprovado')."""
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
    """Exclui candidato do banco de dados."""
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


# --- Rota Principal de Upload e Processamento ---
# Em APP.py, COLE ESTE BLOCO DE CÓDIGO INTEIRO
# logo acima da linha "@app.route('/upload_multiple_files', methods=['POST'])"

def extrair_dados_com_gemini(texto_curriculo: str) -> dict:
    """Usa a IA Gemini para extrair informações estruturadas de um texto de currículo."""
    
    if not GEMINI_API_KEY or 'SUA_CHAVE' in GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY não configurada. Extração de dados retornará um exemplo.")
        # Retorna um dicionário com a mesma estrutura para evitar erros
        return {
            "nome": "Nome de Exemplo (IA Desativada)", "email": "exemplo@ia.com", "telefone": "",
            "linkedin": "", "idade": "", "cargo_desejado": "", "habilidades": ["Python", "Flask"],
            "formacao": [], "experiencia": []
        }

    prompt = f"""
    Analise o texto deste currículo e extraia as informações em um formato JSON.
    O JSON deve ter EXATAMENTE a seguinte estrutura:
    {{
      "nome": "Nome completo do candidato",
      "email": "email@dominio.com",
      "telefone": "(XX) XXXXX-XXXX",
      "linkedin": "https://linkedin.com/in/perfil",
      "idade": "XX anos",
      "cargo_desejado": "O cargo ou objetivo descrito",
      "habilidades": ["Habilidade 1", "Habilidade 2", "Habilidade 3"],
      "formacao": [
        {{
          "curso": "Nome do Curso",
          "instituicao": "Nome da Instituição",
          "periodo": "Ano de início - Ano de conclusão"
        }}
      ],
      "experiencia": [
        {{
          "cargo": "Cargo Ocupado",
          "empresa": "Nome da Empresa",
          "periodo": "Mês/Ano - Mês/Ano",
          "atividades": "Descrição das atividades."
        }}
      ]
    }}
    Se uma informação não for encontrada, retorne um valor vazio ("" ou []).

    Texto do Currículo:
    ---
    {texto_curriculo}
    ---
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and result['candidates']:
                json_text = result['candidates'][0]['content']['parts'][0]['text']
                return json.loads(json_text)
            else:
                logger.warning(f"Resposta da Gemini veio sem 'candidates': {result}")
                return {}
        else:
            logger.error(f"Erro na API Gemini ao extrair dados: Status {response.status_code} - {response.text}")
            return {}
    except Exception as e:
        logger.error(f"Erro na requisição de extração: {e}", exc_info=True)
        return {}

# A sua função @app.route('/upload_multiple_files'...) deve vir logo abaixo daqui.

@app.route('/upload_multiple_files', methods=['POST'])
def upload_multiple_files():
    """
    Processa o upload de múltiplos currículos, usando a IA para extração de dados.
    Esta é a versão completa e funcional.
    """
    if 'arquivos[]' not in request.files:
        flash('Nenhum campo de arquivo enviado.', 'error')
        return redirect(url_for('upload_curriculos_page'))

    arquivos = request.files.getlist('arquivos[]')
    
    if not arquivos or all(a.filename == '' for a in arquivos):
        flash('Nenhum arquivo selecionado.', 'warning')
        return redirect(url_for('upload_curriculos_page'))

    processados_count = 0
    ignorados_count = 0
    erros_count = 0
    ignorados_nomes = []
    erros_nomes = []

    for arquivo in arquivos:
        if arquivo.filename == '':
            continue
        
        filename = arquivo.filename
        # Define a variável caminho_arquivo_temp corretamente
        caminho_arquivo_temp = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{filename}")
        
        try:
            arquivo.save(caminho_arquivo_temp)

            with open(caminho_arquivo_temp, 'rb') as f_temp:
                file_content = f_temp.read()
                if not file_content:
                    raise ValueError("Arquivo vazio ou ilegível.")
                # Define a variável file_hash corretamente
                file_hash = hashlib.sha256(file_content).hexdigest()
            
            db = get_db()
            if db.execute("SELECT id FROM candidatos WHERE hash_arquivo = ?", (file_hash,)).fetchone():
                db.close()
                ignorados_count += 1
                ignorados_nomes.append(f"{filename} (duplicado)")
                os.remove(caminho_arquivo_temp)
                continue
            db.close()

            texto_curriculo = extrair_texto(caminho_arquivo_temp)
            if not texto_curriculo.strip():
                raise ValueError("Não foi possível extrair texto do arquivo.")

            dados_extraidos = extrair_dados_com_gemini(texto_curriculo)
            if not dados_extraidos or not dados_extraidos.get("nome"):
                raise ValueError("A IA não conseguiu extrair dados válidos do currículo.")

            pontuacao = 0
            motivos_pontuacao_lista = []
            habilidades_candidato = dados_extraidos.get("habilidades", [])
            
            if any(h in habilidades_candidato for h in ['Python', 'SQL', 'Power BI', 'Análise de Dados']):
                pontuacao += 50
                motivos_pontuacao_lista.append("Possui habilidades chave em dados")
            if dados_extraidos.get("experiencia"):
                pontuacao += 30
                motivos_pontuacao_lista.append("Possui experiência profissional")
            if dados_extraidos.get("formacao"):
                 if any("Ciências da Computação" in f.get("curso", "") or "Informática" in f.get("curso", "") for f in dados_extraidos["formacao"]):
                    pontuacao += 20
                    motivos_pontuacao_lista.append("Formação superior em área de TI")
            pontuacao = min(pontuacao, 100)

            analise_ia_final = analisar_com_gemini(dados_extraidos)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            # Define a variável nome_final_arquivo corretamente
            nome_final_arquivo = f"{timestamp}_{filename}"
            caminho_arquivo_final = os.path.join(app.config['UPLOAD_FOLDER'], 'processados', nome_final_arquivo)
            os.rename(caminho_arquivo_temp, caminho_arquivo_final)

            db = get_db()
            db.execute('''
                INSERT INTO candidatos (
                    nome, email, telefone, linkedin, idade, cargo_desejado, 
                    pontuacao, habilidades, experiencia, formacao, 
                    motivos_pontuacao, analise_ia, hash_arquivo, 
                    nome_arquivo_processado, data_upload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                dados_extraidos.get("nome"), dados_extraidos.get("email"), dados_extraidos.get("telefone"),
                dados_extraidos.get("linkedin"), dados_extraidos.get("idade"), dados_extraidos.get("cargo_desejado"),
                pontuacao, json.dumps(habilidades_candidato), json.dumps(dados_extraidos.get("experiencia", [])),
                json.dumps(dados_extraidos.get("formacao", [])), json.dumps(motivos_pontuacao_lista),
                analise_ia_final, file_hash, nome_final_arquivo, datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            db.commit()
            db.close()
            
            processados_count += 1
            time.sleep(2) 

        except Exception as e:
            logger.error(f"Erro no processamento do arquivo {filename}: {e}", exc_info=True)
            erros_count += 1
            erros_nomes.append(f"{filename} ({type(e).__name__})")
            if os.path.exists(caminho_arquivo_temp):
                os.remove(caminho_arquivo_temp)
            continue
    
    msg_parts = []
    if processados_count > 0: msg_parts.append(f'{processados_count} currículo(s) processado(s) com sucesso.')
    if ignorados_count > 0: msg_parts.append(f'{ignorados_count} ignorado(s): {", ".join(ignorados_nomes)}.')
    if erros_count > 0: msg_parts.append(f'{erros_count} falharam: {", ".join(erros_nomes)}.')
    
    flash(' '.join(msg_parts), 'info' if erros_count == 0 else 'warning')
    return redirect(url_for('candidatos_ranqueados'))
@app.route('/dashboard_data')
def dashboard_data():
    """
    API para fornecer dados agregados para a dashboard (VERSÃO DE DEPURAÇÃO).
    """
    try:
        db = get_db()
        # Pedi o 'id' do candidato para facilitar a depuração
        candidatos = db.execute("SELECT id, pontuacao, habilidades, experiencia, formacao, idiomas FROM candidatos WHERE status = 'ativo'").fetchall()
        db.close()

        if not candidatos:
            return jsonify({'total_candidatos': 0, 'media_pontuacao': 0, 'total_experiencias': 0, 'pontuacoes': [], 'habilidades': {}, 'formacoes': {}, 'idiomas': {}})

        total_experiencias = 0
        contador_habilidades = Counter()
        # ... (outros contadores)

        print("\n--- INICIANDO DEPURAÇÃO DA DASHBOARD ---")
        for candidato in candidatos:
            # Depurando a contagem de experiências
            try:
                # Tentamos carregar o JSON da coluna 'experiencia'
                experiencias_str = candidato['experiencia']
                if experiencias_str:
                    lista_de_experiencias = json.loads(experiencias_str)
                    total_experiencias += len(lista_de_experiencias)
                else:
                    # Se o campo for vazio ou None, não fazemos nada
                    pass
            except Exception as e:
                # Se houver QUALQUER erro, ele será impresso no terminal
                print(f"[ERRO] Falha ao processar 'experiencia' do candidato ID {candidato['id']}.")
                print(f"   |-- Causa: {e}")
                print(f"   |-- Valor problemático: {candidato['experiencia']}")
        
        print(f"--- FIM DA DEPURAÇÃO ---")
        print(f"Total de experiências calculado: {total_experiencias}\n")


        # O resto da lógica para calcular os outros KPIs continua aqui...
        # (copiei o resto da função anterior para garantir que tudo continue funcionando)
        pontuacoes = [c['pontuacao'] for c in candidatos if c['pontuacao'] is not None]
        total_candidatos = len(candidatos)
        media_pontuacao = sum(pontuacoes) / len(pontuacoes) if pontuacoes else 0
        contador_formacoes = Counter()
        contador_idiomas = Counter()

        for candidato in candidatos:
            try:
                contador_habilidades.update(json.loads(candidato['habilidades'] or '[]'))
                formacoes = [f.get('curso', 'N/A') for f in json.loads(candidato['formacao'] or '[]')]
                contador_formacoes.update(formacoes)
                idiomas = [i.split(':')[0].strip() for i in json.loads(candidato['idiomas'] or '[]')]
                contador_idiomas.update(idiomas)
            except:
                continue

        dados_dashboard = {
            'pontuacoes': pontuacoes,
            'habilidades': dict(contador_habilidades.most_common(10)),
            'formacoes': dict(contador_formacoes.most_common(10)),
            'idiomas': dict(contador_idiomas),
            'total_candidatos': total_candidatos,
            'media_pontuacao': round(media_pontuacao, 1),
            'total_experiencias': total_experiencias # Usando nosso valor depurado
        }

        return jsonify(dados_dashboard)

    except Exception as e:
        logger.error(f"Erro GERAL ao gerar dados da dashboard: {e}")
        return jsonify({"error": "Falha ao carregar dados da dashboard"}), 500
       
# --- Rotas de Exportação ---
@app.route('/export_candidatos_completo_csv')
def export_candidatos_completo_csv():
    """Exporta todos os dados dos candidatos ativos em CSV."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM candidatos WHERE status = 'ativo' ORDER BY pontuacao DESC")
    candidatos = cursor.fetchall()
    db.close()

    si = StringIO()
    writer = csv.writer(si)
    
    headers = [
        'ID', 'Nome', 'Email', 'Telefone', 'LinkedIn', 'Idade', 'Cargo Desejado', 
        'Pontuação', 'Habilidades', 'Formação', 'Experiência', 'Idiomas', 
        'Análise IA', 'Status', 'Data Upload', 'Arquivo Processado'
    ]
    writer.writerow(headers)

    for cand in candidatos:
        cand_dict = dict(cand)
        # Função auxiliar para formatar campos JSON
        def format_json_field(field_name):
            try:
                data = json.loads(cand_dict.get(field_name, '[]'))
                if isinstance(data, list) and data and isinstance(data[0], dict):
                    return json.dumps(data, ensure_ascii=False) # Mantém JSON para estruturas complexas
                elif isinstance(data, list):
                    return '|'.join(map(str, data)) # Junta listas simples com pipe
                return cand_dict.get(field_name, '')
            except (json.JSONDecodeError, TypeError):
                return cand_dict.get(field_name, '')
                
        writer.writerow([
            cand_dict['id'], cand_dict['nome'], cand_dict['email'], cand_dict['telefone'], cand_dict['linkedin'],
            cand_dict['idade'], cand_dict['cargo_desejado'], cand_dict['pontuacao'],
            format_json_field('habilidades'), format_json_field('formacao'),
            format_json_field('experiencia'), format_json_field('idiomas'),
            cand_dict['analise_ia'], cand_dict['status'], cand_dict['data_upload'], cand_dict['nome_arquivo_processado']
        ])

    output = si.getvalue()
    return app.response_class(
        output.encode('utf-8'), # Garante a codificação correta
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=candidatos_completo.csv"}
    )


@app.route('/export_candidatos_completo_excel')
def export_candidatos_completo_excel():
    """Exporta todos os dados dos candidatos ativos em Excel (.xlsx)."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM candidatos WHERE status = 'ativo' ORDER BY pontuacao DESC")
    candidatos = cursor.fetchall()
    db.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Candidatos Completo"
    
    headers = [
        'ID', 'Nome', 'Email', 'Telefone', 'LinkedIn', 'Idade', 'Cargo Desejado', 'Pontuação',
        'Habilidades', 'Formação', 'Experiência', 'Idiomas', 'Análise IA', 'Status', 'Data Upload', 'Arquivo Processado'
    ]
    ws.append(headers)

    for cand in candidatos:
        cand_dict = dict(cand)
        def format_field(field_name):
            try:
                data = json.loads(cand_dict.get(field_name, '[]'))
                return ', '.join(map(str, data)) if isinstance(data, list) else json.dumps(data, ensure_ascii=False)
            except (json.JSONDecodeError, TypeError):
                return cand_dict.get(field_name, '')
                
        ws.append([
            cand_dict['id'], cand_dict['nome'], cand_dict['email'], cand_dict['telefone'], cand_dict['linkedin'],
            cand_dict['idade'], cand_dict['cargo_desejado'], cand_dict['pontuacao'],
            format_field('habilidades'), format_field('formacao'), format_field('experiencia'), format_field('idiomas'),
            cand_dict['analise_ia'], cand_dict['status'], cand_dict['data_upload'], cand_dict['nome_arquivo_processado']
        ])
    
    with NamedTemporaryFile(delete=True, suffix='.xlsx') as tmp:
        wb.save(tmp.name)
        return send_file(tmp.name, as_attachment=True, download_name='candidatos_completo.xlsx')

# --- CORREÇÃO E MELHORIA DA FUNÇÃO DE EXPORTAR APROVADOS ---
@app.route('/export_aprovados_excel')
def export_aprovados_excel():
    """Exporta apenas os candidatos aprovados (pontuação >= 60) em Excel (.xlsx)."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM candidatos WHERE status = 'ativo' AND pontuacao >= 60 ORDER BY pontuacao DESC")
    candidatos = cursor.fetchall()
    db.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Candidatos Aprovados"
    
    headers = [
        'ID', 'Nome', 'Email', 'Telefone', 'LinkedIn', 'Pontuação',
        'Habilidades', 'Análise IA', 'Data Upload'
    ]
    ws.append(headers)

    for cand in candidatos:
        cand_dict = dict(cand)
        habilidades = ', '.join(json.loads(cand_dict.get('habilidades', '[]')))
        
        ws.append([
            cand_dict['id'], cand_dict['nome'], cand_dict['email'],
            cand_dict['telefone'], cand_dict['linkedin'], cand_dict['pontuacao'],
            habilidades, cand_dict['analise_ia'], cand_dict['data_upload']
        ])

    with NamedTemporaryFile(delete=True, suffix='.xlsx') as tmp:
        wb.save(tmp.name)
        return send_file(tmp.name, as_attachment=True, download_name='candidatos_aprovados.xlsx')


# --- Inicialização do Servidor Flask ---
if __name__ == '__main__':
    app.run(debug=True)