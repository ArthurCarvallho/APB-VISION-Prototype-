# ==============================================================================
# APB VISION - APP.PY - VERSÃO COMPLETA, FINAL E ESTÁVEL
# DATA: 29/07/2025
# ==============================================================================

# --- Imports Essenciais ---
import os
import json
import re
import logging
import requests
import sqlite3
from collections import Counter
from datetime import datetime
import hashlib

# Importações específicas do Flask
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify

# Importações de bibliotecas de terceiros
import PyPDF2
import docx

# --- Configuração ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.static_folder = 'static'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = 'chave-secreta-final-e-segura-para-o-projeto'
# IMPORTANTE: Cole sua chave real da API Gemini aqui
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyCy4sale7sldGWevMuYv9OPDRP5f8y_8iw')

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# --- Funções de Utilidade e IA ---

def extrair_texto(caminho):
    """Extrai texto de arquivos PDF ou DOCX."""
    ext = os.path.splitext(caminho)[1].lower()
    if ext == '.pdf':
        try:
            with open(caminho, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                return " ".join([p.extract_text() for p in reader.pages if p.extract_text()])
        except Exception as e:
            logger.error(f"Erro ao extrair PDF '{caminho}': {e}")
    elif ext == '.docx':
        try:
            doc = docx.Document(caminho)
            return " ".join([p.text for p in doc.paragraphs if p.text])
        except Exception as e:
            logger.error(f"Erro ao extrair DOCX '{caminho}': {e}")
    return ""

def extrair_dados_com_gemini(texto_curriculo: str, filename: str) -> dict:
    """Usa a IA Gemini para extrair informações estruturadas de um currículo."""
    if not GEMINI_API_KEY or 'COLE_SUA_CHAVE' in GEMINI_API_KEY:
        logger.warning(f"GEMINI_API_KEY não configurada para '{filename}'.")
        return {}
    
    prompt = f"""
    Analise o texto deste currículo e extraia as informações em um formato JSON.
    É crucial que você retorne TODOS os campos da estrutura, mesmo que o valor seja vazio ("" ou []). Não omita chaves.
    Para o campo "habilidades", extraia APENAS os nomes das tecnologias ou competências, como "Python" ou "Trabalho em equipe", e não frases descritivas.

    Estrutura JSON esperada:
    {{
      "nome": "Nome completo", "email": "email@dominio.com", "telefone": "(XX) XXXXX-XXXX", "linkedin": "https://linkedin.com/in/perfil",
      "idade": "XX anos", "cargo_desejado": "O cargo ou objetivo", "habilidades": ["Python", "MySQL"],
      "formacao": [{{"curso": "Nome do Curso", "instituicao": "Nome da Instituição", "periodo": "Início - Fim"}}],
      "experiencia": [{{"cargo": "Cargo Ocupado", "empresa": "Nome da Empresa", "periodo": "Início - Fim", "atividades": ["Descrição."]}}],
      "idiomas": ["Idioma - Nível"]
    }}

    Texto do Currículo: --- {texto_curriculo} ---
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    try:
        response = requests.post(url, json=payload, timeout=90)
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and result['candidates']:
                return json.loads(result['candidates'][0]['content']['parts'][0]['text'])
        logger.error(f"Erro na API Gemini para '{filename}': Status {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Exceção na requisição para '{filename}': {e}")
    return {}

def analisar_com_gemini(dados_candidato: dict) -> str:
    """Gera uma análise textual resumida do candidato."""
    # Esta função pode ser aprimorada no futuro.
    return "Análise de IA gerada pelo sistema com base nos dados extraídos."

# --- Gestão da Base de Dados ---
DATABASE, VAGAS_DB = 'candidatos.db', 'vagas.db'
def get_db(db_name=DATABASE):
    conn = sqlite3.connect(db_name); conn.row_factory = sqlite3.Row; return conn

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS candidatos (
                id INTEGER PRIMARY KEY, nome TEXT, email TEXT, telefone TEXT, 
                linkedin TEXT, idade TEXT, cargo_desejado TEXT, pontuacao INTEGER, 
                habilidades TEXT, formacao TEXT, experiencia TEXT, analise_ia TEXT, 
                motivos_pontuacao TEXT, idiomas TEXT, status TEXT DEFAULT "ativo", 
                hash_arquivo TEXT UNIQUE, nome_arquivo_processado TEXT, data_upload TEXT
            )''')
        db.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_hash_arquivo ON candidatos (hash_arquivo)')
        db.commit(); db.close()

def init_vagas_db():
    with app.app_context():
        db = get_db(VAGAS_DB)
        # Adicionamos localizacao, tipo_contratacao e status
        db.execute('''
            CREATE TABLE IF NOT EXISTS vagas (
                id INTEGER PRIMARY KEY,
                nome TEXT NOT NULL,
                requisitos TEXT NOT NULL,
                habilidades_chave TEXT,
                localizacao TEXT,
                tipo_contratacao TEXT,
                status TEXT DEFAULT 'Aberta',
                data_criacao TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()
        db.close()

with app.app_context():
    init_db()
    init_vagas_db()

# --- Rotas da Interface ---
@app.route('/')
def login_page(): return render_template('login.html')

@app.route('/home')
def home(): return render_template('dashboard.html')

@app.route('/vagas')
def vagas(): return render_template('vagas.html')

@app.route('/upload_curriculos')
def upload_curriculos_page(): return render_template('upload.html')

@app.route('/processing')
def processing_page(): return render_template('processing.html')

@app.route('/candidatos_ranqueados')
def candidatos_ranqueados():
    """
    Renderiza a página de candidatos e também serve como API para calcular o "match"
    de forma robusta (ignorando maiúsculas/minúsculas e espaços).
    """
    vaga_id_selecionada = request.args.get('vaga_id', default=None, type=int)
    
    db_candidatos = get_db()
    candidatos = db_candidatos.execute("SELECT * FROM candidatos WHERE status = 'ativo'").fetchall()
    db_candidatos.close()

  # Se a requisição for para a API (feita pelo JavaScript para calcular o match)
    if vaga_id_selecionada:
        db_vagas = get_db(VAGAS_DB)
        vaga = db_vagas.execute("SELECT habilidades_chave FROM vagas WHERE id = ?", (vaga_id_selecionada,)).fetchone()
        db_vagas.close()

        if not vaga:
            return jsonify({"error": "Vaga não encontrada"}), 404

        habilidades_vaga_raw = json.loads(vaga['habilidades_chave'] or '[]')
        
        # Normaliza as habilidades da vaga: minúsculas e sem espaços extras
        habilidades_vaga = {skill.strip().lower() for skill in habilidades_vaga_raw if skill.strip()}

        if not habilidades_vaga:
            # Retorna a lista com match 0 se a vaga não tiver habilidades
            return jsonify([dict(c, match_score=0) for c in candidatos])

        candidatos_com_match = []
        for candidato in candidatos:
            candidato_dict = dict(candidato)
            habilidades_candidato_raw = json.loads(candidato_dict.get('habilidades', '[]'))
            
            # Normaliza as habilidades do candidato
            habilidades_candidato = {skill.strip().lower() for skill in habilidades_candidato_raw if skill.strip()}
            
            habilidades_em_comum_count = 0
            
            # --- INÍCIO DA NOVA LÓGICA DE COMPARAÇÃO FLEXÍVEL ---
            for hv in habilidades_vaga:
                # Verifica se a habilidade da vaga (hv) tem correspondência em alguma das habilidades do candidato (hc)
                # O 'in' permite correspondência parcial. Ex: "windows" em "windows server"
                if any(hv in hc for hc in habilidades_candidato):
                    habilidades_em_comum_count += 1
            # --- FIM DA NOVA LÓGICA ---
            
            match_score = 0
            if habilidades_vaga: # Evita divisão por zero
                match_score = round((habilidades_em_comum_count / len(habilidades_vaga)) * 100)
            
            candidato_dict['match_score'] = match_score
            candidatos_com_match.append(candidato_dict)

        candidatos_ordenados = sorted(candidatos_com_match, key=lambda c: c['match_score'], reverse=True)
        return jsonify(candidatos_ordenados)
    
    # Se for a primeira vez que carrega a página
    else:
        db_vagas = get_db(VAGAS_DB)
        vagas_db = db_vagas.execute("SELECT id, nome FROM vagas ORDER BY nome").fetchall()
        db_vagas.close()
        
        # --- LINHA DA CORREÇÃO ---
        # Converte a lista de objetos 'Row' de vagas para uma lista de dicionários
        vagas_serializaveis = [dict(v) for v in vagas_db]
        
        candidatos_ordenados = sorted([dict(c) for c in candidatos], key=lambda c: c.get('pontuacao', 0), reverse=True)

        return render_template('candidatos_ranqueados.html', candidatos=candidatos_ordenados, vagas=vagas_serializaveis)


@app.route('/detalhes_candidato/<int:candidate_id>')
def detalhes_candidato(candidate_id):
    db = get_db()
    candidato = db.execute("SELECT * FROM candidatos WHERE id = ?", (candidate_id,)).fetchone()
    db.close()
    if not candidato: return redirect(url_for('candidatos_ranqueados'))
    
    candidato_dict = dict(candidato)
    for key in ['habilidades', 'formacao', 'experiencia', 'motivos_pontuacao', 'idiomas']:
        candidato_dict[key] = json.loads(candidato_dict.get(key) or '[]')
    return render_template('candidate_details.html', candidate=candidato_dict)

# --- Rota de Upload (Síncrona e Funcional) ---
@app.route('/upload_multiple_files', methods=['POST'])
def upload_multiple_files():
    if 'arquivos[]' not in request.files:
        flash('Nenhum arquivo enviado.', 'error'); return redirect(url_for('upload_curriculos_page'))
    
    arquivos = request.files.getlist('arquivos[]')
    
    for arquivo in arquivos:
        if arquivo.filename == '': continue
        filename = arquivo.filename
        
        file_content = arquivo.read()
        file_hash = hashlib.sha256(file_content).hexdigest()
        caminho_temp = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            with open(caminho_temp, 'wb') as f: f.write(file_content)

            db = get_db()
            if db.execute("SELECT id FROM candidatos WHERE hash_arquivo = ?", (file_hash,)).fetchone():
                db.close(); logger.warning(f"Ignorando duplicado: {filename}"); continue
            db.close()

            texto = extrair_texto(caminho_temp)
            if not texto: raise ValueError("Texto do currículo vazio.")

            dados_extraidos = extrair_dados_com_gemini(texto, filename)
            if not dados_extraidos.get("nome"): raise ValueError("IA não conseguiu extrair dados.")
            
            pontuacao, motivos = 0, []
            habilidades = dados_extraidos.get("habilidades", [])
            if any(h in habilidades for h in ['Python', 'SQL', 'Power BI']):
                pontuacao += 50; motivos.append("Habilidades em dados")
            if dados_extraidos.get("experiencia"):
                pontuacao += 30; motivos.append("Possui experiência")
            if dados_extraidos.get("formacao"):
                pontuacao += 20; motivos.append("Possui formação")
            pontuacao = min(pontuacao, 100)
            
            analise_ia = analisar_com_gemini(dados_extraidos)

            db = get_db()
            db.execute('''
                INSERT INTO candidatos (nome, email, telefone, linkedin, idade, cargo_desejado, pontuacao, 
                                      habilidades, formacao, experiencia, motivos_pontuacao, idiomas, analise_ia, 
                                      hash_arquivo, nome_arquivo_processado, data_upload) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                dados_extraidos.get("nome"), dados_extraidos.get("email"), dados_extraidos.get("telefone"),
                dados_extraidos.get("linkedin"), dados_extraidos.get("idade"), dados_extraidos.get("cargo_desejado"),
                pontuacao, json.dumps(habilidades), json.dumps(dados_extraidos.get("formacao", [])),
                json.dumps(dados_extraidos.get("experiencia", [])), json.dumps(motivos),
                json.dumps(dados_extraidos.get("idiomas", [])), analise_ia,
                file_hash, filename, datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            db.commit(); db.close()
            logger.info(f"Sucesso ao processar e salvar '{filename}'.")

        except Exception as e:
            logger.error(f"Falha ao processar '{filename}': {e}")
            flash(f"Erro ao processar o arquivo {filename}.", 'error')
        finally:
            if os.path.exists(caminho_temp): os.remove(caminho_temp)
    
    flash('Processamento concluído.', 'success')
    return redirect(url_for('candidatos_ranqueados'))

# --- ROTAS DE API (LOGIN, DASHBOARD, ETC.) ---
@app.route('/api/login', methods=['POST'])
def api_login():
    USERS = [{'email': 'arthur@gmail.com', 'senha': 'arthur123', 'nome': 'Arthur Carvalho'}]
    data = request.get_json()
    for user in USERS:
        if user['email'] == data.get('email') and user['senha'] == data.get('senha'):
            return jsonify({'success': True, 'nome': user['nome']})
    return jsonify({'success': False, 'message': 'Credenciais inválidas.'}), 401
    
# Adicionar outras APIs como a de Vagas e Dashboard aqui no futuro
@app.route('/dashboard_data')
def dashboard_data():
    """
    API para fornecer dados agregados para a dashboard.
    """
    try:
        db = get_db()
        candidatos = db.execute("SELECT pontuacao, habilidades, formacao FROM candidatos WHERE status = 'ativo'").fetchall()
        db.close()

        if not candidatos:
            return jsonify({
                'total_candidatos': 0, 'media_pontuacao': 0, 'habilidades_mais_comuns': {}, 'distribuicao_pontuacoes': {}, 'formacoes_mais_comuns': {}
            })

        total_candidatos = len(candidatos)
        pontuacoes = [c['pontuacao'] for c in candidatos if c['pontuacao'] is not None]
        media_pontuacao = sum(pontuacoes) / len(pontuacoes) if pontuacoes else 0

        contador_habilidades = Counter()
        contador_formacoes = Counter()

        for candidato in candidatos:
            try:
                contador_habilidades.update(json.loads(candidato['habilidades'] or '[]'))
                formacoes = [f.get('curso', 'N/A') for f in json.loads(candidato['formacao'] or '[]')]
                contador_formacoes.update(formacoes)
            except (json.JSONDecodeError, TypeError):
                continue

        # Distribuição de Pontuações (agrupando em faixas)
        faixas_pontuacao = [0] * 10  # 10 faixas de 10 pontos (0-9, 10-19, ..., 90-99)
        for pontuacao in pontuacoes:
            if 0 <= pontuacao <= 99:
                indice = pontuacao // 10
                faixas_pontuacao [indice] += 1

        labels_pontuacao = [f'{i*10}-{i*10 + 9}' for i in range(10)]
        distribuicao_pontuacoes = dict(zip(labels_pontuacao, faixas_pontuacao))

        dados_dashboard = {
            'total_candidatos': total_candidatos,
            'media_pontuacao': round(media_pontuacao, 1),
            'habilidades_mais_comuns': dict(contador_habilidades.most_common(7)),
            'distribuicao_pontuacoes': distribuicao_pontuacoes,
            'formacoes_mais_comuns': dict(contador_formacoes.most_common(5)),
        }
        return jsonify(dados_dashboard)

    except Exception as e:
        logger.error(f"Erro ao gerar dados da dashboard: {e}")
        return jsonify({"error": "Falha ao carregar dados da dashboard"}), 500
    
    # --- ROTAS DE API PARA AÇÕES DE CANDIDATOS ---

@app.route('/api/candidatos/<int:candidate_id>/reprovar', methods=['POST'])
def reprovar_candidato(candidate_id):
    """
    Altera o status de um candidato para 'reprovado'.
    O candidato não será mais exibido nas listas ativas.
    """
    try:
        db = get_db()
        db.execute("UPDATE candidatos SET status = 'reprovado' WHERE id = ?", (candidate_id,))
        db.commit()
        db.close()
        logger.info(f"Candidato ID {candidate_id} reprovado com sucesso.")
        return jsonify({'success': True, 'message': 'Candidato reprovado com sucesso!'})
    except Exception as e:
        logger.error(f"Erro ao reprovar candidato ID {candidate_id}: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor.'}), 500

@app.route('/api/candidatos/<int:candidate_id>', methods=['DELETE'])
def excluir_candidato(candidate_id):
    """
    Exclui permanentemente um candidato da base de dados.
    """
    try:
        db = get_db()
        db.execute("DELETE FROM candidatos WHERE id = ?", (candidate_id,))
        db.commit()
        db.close()
        logger.info(f"Candidato ID {candidate_id} excluído permanentemente.")
        return jsonify({'success': True, 'message': 'Candidato excluído com sucesso!'})
    except Exception as e:
        logger.error(f"Erro ao excluir candidato ID {candidate_id}: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor.'}), 500

# --- ROTAS DE API PARA VAGAS ---

@app.route('/api/vagas', methods=['GET', 'POST'])
def api_vagas():
    """API para listar e criar vagas."""
    db = get_db(VAGAS_DB)
    cursor = db.cursor()

    try:
        # Se a requisição for POST, cria uma nova vaga
        if request.method == 'POST':
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'message': 'Corpo da requisição (JSON) ausente ou inválido.'}), 400

            # Extrai os dados do JSON
            nome = data.get('nome')
            requisitos = data.get('requisitos')
            habilidades_chave = data.get('habilidades_chave', [])
            localizacao = data.get('localizacao')
            tipo_contratacao = data.get('tipo_contratacao')

            # Valida os campos obrigatórios
            if not nome or not requisitos:
                return jsonify({'success': False, 'message': 'Os campos "nome" e "requisitos" são obrigatórios.'}), 400
            
            # Insere os dados no banco de dados
            cursor.execute(
                'INSERT INTO vagas (nome, requisitos, habilidades_chave, localizacao, tipo_contratacao) VALUES (?, ?, ?, ?, ?)',
                (nome, requisitos, json.dumps(habilidades_chave), localizacao, tipo_contratacao)
            )
            vaga_id = cursor.lastrowid
            db.commit()
            
            # Retorna sucesso com o ID da nova vaga (Status 201 Created é o mais apropriado aqui)
            return jsonify({'success': True, 'id': vaga_id}), 201

        # Se a requisição for GET, lista todas as vagas
        else: # request.method == 'GET'
            cursor.execute('SELECT * FROM vagas ORDER BY id DESC')
            # fetchall() retorna uma lista de tuplas, dict() não funcionará diretamente.
            # É preciso mapear as colunas para os valores.
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            vagas_list = []
            for row in rows:
                vaga_dict = dict(zip(columns, row))
                
                # Desserializa o campo 'habilidades_chave' de string JSON para lista Python
                habilidades_str = vaga_dict.get('habilidades_chave')
                try:
                    vaga_dict['habilidades_chave'] = json.loads(habilidades_str) if habilidades_str else []
                except json.JSONDecodeError:
                    vaga_dict['habilidades_chave'] = [] # Proteção contra JSON malformado
                
                vagas_list.append(vaga_dict)
                
            return jsonify({'success': True, 'vagas': vagas_list})

    finally:
        # O bloco 'finally' garante que a conexão com o banco de dados
        # seja sempre fechada, mesmo se ocorrer um erro no 'try'.
        db.close()

@app.route('/api/vagas/<int:vaga_id>', methods=['DELETE'])
def api_excluir_vaga(vaga_id):
    """API para excluir uma vaga."""
    db = get_db(VAGAS_DB)
    db.execute('DELETE FROM vagas WHERE id = ?', (vaga_id,))
    db.commit()
    db.close()
    return jsonify({'success': True, 'message': 'Vaga excluída com sucesso!'})

@app.route('/api/vagas/sugerir-habilidades', methods=['POST'])
def sugerir_habilidades_de_vaga():
    """Usa a IA para extrair habilidades-chave de uma descrição de vaga."""
    data = request.get_json()
    descricao = data.get('descricao')
    if not descricao: return jsonify({'success': False, 'message': 'Descrição ausente.'}), 400
    if not GEMINI_API_KEY or 'COLE_SUA_CHAVE' in GEMINI_API_KEY:
        return jsonify({'success': True, 'habilidades': ['Python', 'SQL', 'Exemplo (IA Desativada)']})
    
    prompt = f"""Analise a descrição de vaga e extraia as 5 a 8 habilidades mais importantes. Retorne APENAS uma lista de habilidades separadas por vírgula. Descrição: "{descricao}" """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"
    try:
        response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and result['candidates']:
                texto = result['candidates'][0]['content']['parts'][0]['text'].strip()
                return jsonify({'success': True, 'habilidades': [h.strip() for h in texto.split(',')]})
        return jsonify({'success': False, 'message': 'Erro ao comunicar com a IA.'}), 500
    except Exception as e:
        logger.error(f"Erro ao sugerir habilidades: {e}")
        return jsonify({'success': False, 'message': 'Erro inesperado.'}), 500
    

    # --- ROTA DE EXPORTAÇÃO ---
import io
import csv
from flask import Response

@app.route('/export/candidatos.csv')
def exportar_candidatos_csv():
    """
    Gera um arquivo CSV com os dados de todos os candidatos ativos e o oferece para download.
    """
    try:
        db = get_db()
        candidatos = db.execute("SELECT * FROM candidatos WHERE status = 'ativo'").fetchall()
        db.close()

        # Usa um buffer de memória para criar o CSV sem salvar em disco
        output = io.StringIO()
        writer = csv.writer(output)

        # Escreve o cabeçalho do CSV
        headers = [
            'ID', 'Nome', 'Email', 'Telefone', 'LinkedIn', 'Idade', 
            'Cargo Desejado', 'Pontuacao', 'Habilidades', 'Formacao', 
            'Experiencia', 'Idiomas', 'Data do Upload'
        ]
        writer.writerow(headers)

        # Escreve os dados de cada candidato
        for candidato in candidatos:
            row = [
                candidato['id'],
                candidato['nome'],
                candidato['email'],
                candidato['telefone'],
                candidato['linkedin'],
                candidato['idade'],
                candidato['cargo_desejado'],
                candidato['pontuacao'],
                candidato['habilidades'], # Estes campos já são strings JSON
                candidato['formacao'],
                candidato['experiencia'],
                candidato['idiomas'],
                candidato['data_upload']
            ]
            writer.writerow(row)
        
        output.seek(0) # Volta para o início do buffer

        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=candidatos_exportados.csv"}
        )

    except Exception as e:
        logger.error(f"Erro ao exportar CSV: {e}")
        return redirect(url_for('candidatos_ranqueados'))
    
    # --- ROTAS PARA AGENDAMENTO DE ENTREVISTA ---

@app.route('/agendar_entrevista/<int:candidate_id>')
def agendar_entrevista_page(candidate_id):
    """
    Renderiza a página para agendar uma entrevista para um candidato específico.
    """
    db = get_db()
    candidato = db.execute("SELECT id, nome FROM candidatos WHERE id = ?", (candidate_id,)).fetchone()
    db.close()
    if not candidato:
        return redirect(url_for('candidatos_ranqueados'))
    
    return render_template('agendar_entrevista.html', candidato=dict(candidato))

@app.route('/api/agendar_entrevista', methods=['POST'])
def api_agendar_entrevista():
    """
    API para receber os dados do agendamento de entrevista.
    Para o protótipo, apenas registra a informação no log.
    """
    data = request.get_json()
    logger.info(f"--- NOVA ENTREVISTA AGENDADA ---")
    logger.info(f"Candidato ID: {data.get('candidato_id')}")
    logger.info(f"Nome do Candidato: {data.get('candidato_nome')}")
    logger.info(f"Tipo: {data.get('tipo')}")
    logger.info(f"Data: {data.get('data')}")
    logger.info(f"Hora: {data.get('hora')}")
    logger.info(f"Recrutador: {data.get('recrutador')}")
    logger.info(f"---------------------------------")
    
    # Em um projeto real, aqui você salvaria os dados em um 'entrevistas.db'
    
    return jsonify({'success': True, 'message': 'Entrevista agendada com sucesso!'})
    
# --- INICIALIZAÇÃO DO SERVIDOR ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)
