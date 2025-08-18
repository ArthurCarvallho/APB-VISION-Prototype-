# APB Vision - Triagem Inteligente de Currículos com IA

**Autor:** Arthur Paulo de Carvalho
**Projeto:** Trabalho de Conclusão de Curso (TCC)
**Status:** Protótipo Funcional Concluído

![Demonstração do Ranking de Candidatos](static/img/image.png)

---

## 1. Sobre o Projeto

O APB Vision é uma plataforma de recrutamento inteligente (ATS - Applicant Tracking System) desenvolvida como um protótipo funcional. O projeto nasceu para solucionar um desafio central no setor de Recursos Humanos: a ineficiência, o alto custo e a subjetividade do processo de triagem manual de currículos.

A solução utiliza um Modelo de Linguagem Amplo (LLM), especificamente a API do Google Gemini, para automatizar a extração de dados de currículos, calcular um "Índice de Adequação" ponderado para cada candidato em relação a uma vaga específica, e apresentar os talentos mais promissores de forma visual e intuitiva para o recrutador. O objetivo não é substituir o profissional de RH, mas sim empoderá-lo com uma ferramenta estratégica, transformando horas de trabalho operacional em minutos de análise focada nos melhores candidatos.

---

## 2. Funcionalidades Principais

O protótipo atual é 100% funcional e inclui as seguintes funcionalidades:

* **Gestão de Vagas:**
    * Criação, listagem e exclusão de vagas.
    * **Sugestão de Habilidades com IA:** O sistema analisa a descrição da vaga e sugere as competências técnicas e comportamentais mais relevantes.
    * Adição manual de habilidades.

* **Processamento de Candidatos:**
    * **Upload em Massa:** Permite o envio de múltiplos currículos nos formatos `.pdf` e `.docx`.
    * **Extração de Dados com IA:** Extrai e estrutura automaticamente informações como dados de contato, experiência profissional, formação acadêmica, habilidades e idiomas.
    * **Prevenção de Duplicatas:** Utiliza um hash do conteúdo do arquivo para evitar o processamento de currículos duplicados.

* **Ranking Inteligente:**
    * **Índice de Adequação:** Calcula uma pontuação ponderada (habilidades, experiência, formação) para ranquear os candidatos mais compatíveis com uma vaga selecionada.
    * **Níveis de Compatibilidade:** Classifica os candidatos em níveis visuais ("Excelente", "Promissor", "Requer Análise") para facilitar a tomada de decisão.
    * **Visualização em Pódio:** Destaca o "Top 3" candidatos com um design inspirado em um pódio de corrida, tornando a identificação dos melhores talentos imediata.

* **Dashboard e Análises:**
    * Exibe KPIs como o número total de candidatos e a pontuação média da base.
    * Apresenta gráficos sobre as habilidades mais comuns e a distribuição das pontuações dos candidatos.

* **Ações de RH:**
    * Permite **reprovar** ou **excluir** candidatos diretamente da lista.
    * Oferece um atalho para **agendar entrevistas**, direcionando para uma página de agendamento.
    * **Exportação para CSV:** Gera um arquivo `.csv` com os dados dos candidatos para análise externa.

---

## 3. Arquitetura e Tecnologias Utilizadas

A aplicação foi construída utilizando uma arquitetura web moderna e flexível, composta pelas seguintes tecnologias:

* **Backend:** **Python 3** com o microframework **Flask**.
* **Inteligência Artificial:** **API do Google Gemini (LLM)** para processamento de linguagem natural.
* **Banco de Dados:** **SQLite 3** para armazenamento de dados de vagas e candidatos.
* **Frontend:** **HTML5**, **CSS3** e **JavaScript** (Vanilla JS) para a interface do usuário.
* **Bibliotecas Python Notáveis:**
    * `PyPDF2` e `python-docx` para extração de texto dos arquivos.
    * `Requests` para comunicação com a API do Gemini.
* **Bibliotecas JavaScript Notáveis:**
    * `Chart.js` para a renderização dos gráficos na dashboard.

---

## 4. Como Executar o Projeto Localmente

Siga os passos abaixo para configurar e executar o projeto no seu ambiente local.

### Pré-requisitos
* Python 3.8 ou superior
* Pip (gerenciador de pacotes do Python)

### Instalação
1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/ArthurCarvallho/APB-VISION-Prototype-.git
    cd [APB-VISION-Prototype-]
    ```

2.  **Crie e ative um ambiente virtual (recomendado):**
    ```bash
    python -m venv venv
    # No Windows
    venv\Scripts\activate
    # No macOS/Linux
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Nota: Você precisará criar um arquivo `requirements.txt`. Para isso, no seu terminal com o ambiente virtual ativado, execute: `pip freeze > requirements.txt`)*

4.  **Configure a Chave da API:**
    * No arquivo `APP.py`, localize a linha:
        `GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'SUA_CHAVE_API_AQUI')`
    * Substitua `'SUA_CHAVE_API_AQUI'` pela sua chave real da API do Google Gemini.

### Execução
1.  **Inicie o servidor Flask:**
    ```bash
    python APP.py
    ```

2.  **Acesse a aplicação:**
    * Abra o seu navegador e acesse `http://127.0.0.1:5000`

---

## 5. Próximos Passos (Visão Futura)

Este protótipo serve como uma base sólida. As futuras evoluções para transformar a APB Vision em um produto completo incluem:

* **Fase 1 - Consolidação como ATS:** Implementação de um pipeline Kanban para gestão do funil, automação de e-mails e integração com agendas.
* **Fase 2 - Automação Inteligente:** Integração de um chatbot para pré-triagem e agendamento automático.
* **Fase 3 - Análise Preditiva:** Incorporação de entrevistas em vídeo assíncronas com análise de soft skills pela IA.