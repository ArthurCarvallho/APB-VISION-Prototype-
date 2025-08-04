// ==============================================================================
// APB VISION - SCRIPT.JS - VERSÃO DEFINITIVA E ESTÁVEL
// DATA: 29/07/2025
// ==============================================================================

document.addEventListener('DOMContentLoaded', () => {

    console.log("APB Vision script.js carregado e em execução.");

    // --- LÓGICA UNIVERSAL (Executa em todas as páginas) ---

    // Preenche o nome do usuário no cabeçalho
    const userNomeSpan = document.getElementById('user-nome');
    if (userNomeSpan) {
        const nomeUsuario = localStorage.getItem('user_nome');
        if (nomeUsuario) {
            userNomeSpan.textContent = `Olá, ${nomeUsuario}!`;
        }
    }

// --- LÓGICA DA PÁGINA DE VAGAS (vagas.html) ---
const jobListContainer = document.getElementById('jobList');
if (jobListContainer) {
    // Mapeamento de todos os elementos da página e do modal
    const modal = document.getElementById('modalNovaVaga');
    const btnOpenModal = document.getElementById('btnCriarNovaVaga');
    const btnCloseModal = document.getElementById('closeModalNovaVaga');
    const form = document.getElementById('formNovaVaga');
    const vagaNomeInput = document.getElementById('vagaNome');
    const vagaRequisitosTextarea = document.getElementById('vagaRequisitos');
    const btnSugerirHabilidades = document.getElementById('btnSugerirHabilidades');
    const tagsContainer = document.getElementById('tagsContainer');
    const manualSkillInput = document.getElementById('manualSkillInput');
    const btnCancelModal = document.getElementById('btnCancelModal');

    // Função para adicionar uma tag de habilidade na UI do modal
    function adicionarTag(habilidade) {
        if (!habilidade || habilidade.trim() === '') return;
        const tag = document.createElement('div');
        tag.className = 'skill-tag-editavel';
        tag.innerHTML = `<span>${habilidade.trim()}</span><span class="remover-tag">&times;</span>`;
        tag.querySelector('.remover-tag').onclick = () => tag.remove();
        if (tagsContainer) tagsContainer.appendChild(tag);
    }

    // Função principal para buscar e renderizar as vagas na página
    async function renderVagas() {
        jobListContainer.innerHTML = '<p>Carregando vagas...</p>';
        try {
            const res = await fetch('/api/vagas');
            if (!res.ok) throw new Error('Falha ao buscar vagas do servidor.');
            
            const data = await res.json();
            jobListContainer.innerHTML = ''; // Limpa a área

            if (data.success && data.vagas.length > 0) {
                data.vagas.forEach(vaga => {
                    const vagaCard = document.createElement('div');
                    vagaCard.className = 'vaga-card-moderno';
                    vagaCard.id = `vaga-${vaga.id}`;

                    const habilidadesHTML = vaga.habilidades_chave.map(h => `<span class="skill-tag">${h}</span>`).join('');
                    const descricaoCompleta = vaga.requisitos;
                    const ehLongo = descricaoCompleta.length > 150;
                    const descricaoVisivel = ehLongo ? descricaoCompleta.substring(0, 150) + '...' : descricaoCompleta;

                    vagaCard.innerHTML = `
                        <div class="vaga-card-header">
                            <h4>${vaga.nome}</h4>
                            <span class="vaga-data">Criada em: ${vaga.data_criacao || 'N/A'}</span>
                        </div>
                        <div class="vaga-card-body">
                            <p class="vaga-descricao">${descricaoVisivel}</p>
                            ${ehLongo ? `<a href="#" class="toggle-details-btn" data-fulltext="${encodeURIComponent(descricaoCompleta)}">Ver mais...</a>` : ''}
                        </div>
                        <div class="vaga-card-footer">
                            <div class="vaga-habilidades-tags">${habilidadesHTML || 'Nenhuma habilidade.'}</div>
                            <button class="btn btn-danger btn-sm btn-excluir-vaga" data-id="${vaga.id}">Excluir</button>
                        </div>
                    `;
                    jobListContainer.appendChild(vagaCard);
                });
            } else {
                jobListContainer.innerHTML = '<p>Nenhuma vaga criada ainda. Clique em "Criar Nova Vaga" para começar.</p>';
            }
        } catch (error) {
            console.error("Erro ao renderizar vagas:", error);
            jobListContainer.innerHTML = '<p style="color:red;">Não foi possível carregar as vagas. Verifique o console para mais detalhes.</p>';
        }
    }

    // Listener de eventos centralizado para a lista de vagas (Excluir e Ver mais)
    jobListContainer.addEventListener('click', async (e) => {
        const target = e.target;
        // Lógica para o botão "Excluir"
        if (target.classList.contains('btn-excluir-vaga')) {
            const vagaId = target.dataset.id;
            if (confirm('Tem certeza que deseja excluir esta vaga?')) {
                await fetch(`/api/vagas/${vagaId}`, { method: 'DELETE' });
                renderVagas();
            }
        }
        // Lógica para o botão "Ver mais..."
        if (target.classList.contains('toggle-details-btn')) {
            e.preventDefault();
            const link = target;
            const descricaoP = link.previousElementSibling; // O <p> da descrição
            
            if (link.textContent === 'Ver mais...') {
                descricaoP.textContent = decodeURIComponent(link.dataset.fulltext);
                link.textContent = 'Ocultar';
            } else {
                descricaoP.textContent = decodeURIComponent(link.dataset.fulltext).substring(0, 150) + '...';
                link.textContent = 'Ver mais...';
            }
        }
    });
    
    // --- Lógica Completa do Modal ---
    const openModal = () => { if (modal) modal.style.display = 'flex'; };
    const closeModal = () => { if (modal) { modal.style.display = 'none'; form.reset(); if (tagsContainer) tagsContainer.innerHTML = ''; }};
    if (btnOpenModal) btnOpenModal.onclick = openModal;
    if (btnCloseModal) btnCloseModal.onclick = closeModal;
    if (btnCancelModal) btnCancelModal.onclick = closeModal;

    // Botão de Sugerir Habilidades com IA
    if (btnSugerirHabilidades) {
        btnSugerirHabilidades.addEventListener('click', async () => {
            const descricao = vagaRequisitosTextarea.value;
            if (descricao.trim().length < 20) {
                alert("Por favor, insira uma descrição de vaga com pelo menos 20 caracteres.");
                return;
            }
            btnSugerirHabilidades.disabled = true;
            btnSugerirHabilidades.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sugerindo...';

            try {
                const res = await fetch('/api/vagas/sugerir-habilidades', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ descricao })
                });
                const data = await res.json();
                if (data.success) {
                    if (tagsContainer) tagsContainer.innerHTML = '';
                    data.habilidades.forEach(h => adicionarTag(h));
                } else { alert('Não foi possível sugerir habilidades.'); }
            } catch (error) {
                console.error("Erro ao sugerir habilidades:", error);
                alert('Erro de comunicação com o servidor.');
            } finally {
                btnSugerirHabilidades.disabled = false;
                btnSugerirHabilidades.innerHTML = '<i class="fas fa-magic"></i> Sugerir com IA';
            }
        });
    }

    // Adicionar Habilidade Manualmente com a tecla Enter
    if (manualSkillInput) {
        manualSkillInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault(); // Impede o envio do formulário
                adicionarTag(manualSkillInput.value);
                manualSkillInput.value = '';
            }
        });
    }
    
    // Salvar a Nova Vaga
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const nome = vagaNomeInput.value;
            const requisitos = vagaRequisitosTextarea.value;
            const habilidades_chave = tagsContainer ? Array.from(tagsContainer.querySelectorAll('span:first-child')).map(span => span.textContent) : [];
            const res = await fetch('/api/vagas', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nome, requisitos, habilidades_chave })
            });
            if (res.ok) {
                closeModal();
                renderVagas();
            } else {
                alert('Erro ao criar vaga. Verifique se todos os campos foram preenchidos.');
            }
        });
    }

    // Chama a renderização inicial das vagas ao carregar a página
    renderVagas();
}

    // --- LÓGICA DA PÁGINA DE LOGIN (login.html) ---
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const btnLogin = document.getElementById('btnLogin');
            btnLogin.disabled = true;
            btnLogin.textContent = 'Entrando...';

            try {
                const res = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: email, senha: password })
                });
                const data = await res.json();
                if (data.success) {
                    localStorage.setItem('user_nome', data.nome);
                    window.location.href = '/home';
                } else {
                    alert(data.message || 'Credenciais inválidas.');
                    btnLogin.disabled = false;
                    btnLogin.textContent = 'Entrar';
                }
            } catch (error) {
                alert('Erro na comunicação com o servidor.');
                btnLogin.disabled = false;
                btnLogin.textContent = 'Entrar';
            }
        });
    }
    

// --- LÓGICA DA DASHBOARD (dashboard.html) ---
const dashboardContainer = document.querySelector('.dashboard-grid');
if (dashboardContainer) {
    const btnIniciarTriagemDashboard = document.getElementById("btnIniciarTriagem");
    if (btnIniciarTriagemDashboard) {
        btnIniciarTriagemDashboard.addEventListener('click', () => {
            window.location.href = "/upload_curriculos";
        });
    }

    async function fetchDashboardData() {
        try {
            const res = await fetch('/dashboard_data');
            if (!res.ok) {
                throw new Error(`Erro na API: ${res.status}`);
            }
            const data = await res.json();
            if (!data) return;

            document.getElementById('totalCandidatos').textContent = data.total_candidatos || 0;
            document.getElementById('mediaPontuacao').textContent = data.media_pontuacao || 0;

            // Gráfico de Habilidades
            const habilidadesCtx = document.getElementById('habilidadesChart');
            if (habilidadesCtx && data.habilidades_mais_comuns) {
                new Chart(habilidadesCtx, {
                    type: 'bar',
                    data: {
                        labels: Object.keys(data.habilidades_mais_comuns),
                        datasets: [{
                            label: 'Número de Candidatos',
                            data: Object.values(data.habilidades_mais_comuns),
                            backgroundColor: 'rgba(0, 119, 255, 0.7)',
                            borderColor: 'rgba(0, 119, 255, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: { indexAxis: 'y', responsive: true, plugins: { legend: { display: false }, title: { display: true, text: 'Habilidades Mais Comuns na Base de Talentos' } } }
                });
            }

            // Gráfico de Distribuição de Pontuações
            const pontuacaoCtx = document.getElementById('pontuacaoChart');
            if (pontuacaoCtx && data.distribuicao_pontuacoes) {
                new Chart(pontuacaoCtx, {
                    type: 'bar',
                    data: {
                        labels: Object.keys(data.distribuicao_pontuacoes),
                        datasets: [{
                            label: 'Número de Candidatos',
                            data: Object.values(data.distribuicao_pontuacoes),
                            backgroundColor: 'rgba(40, 167, 69, 0.7)',
                            borderColor: 'rgba(40, 167, 69, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: { responsive: true, plugins: { legend: { display: false }, title: { display: true, text: 'Distribuição de Pontuações dos Candidatos' } }, scales: { y: { beginAtZero: true } } }
                });
            }

            // Lista de Formações Mais Comuns
            const formacoesList = document.getElementById('topFormacoes');
            if (formacoesList && data.formacoes_mais_comuns) {
                formacoesList.innerHTML = Object.entries(data.formacoes_mais_comuns)
                    .map(([formacao, count]) => `<li>${formacao}: <span class="count">${count}</span></li>`)
                    .join('');
            }

        } catch (error) {
            console.error("Erro ao buscar dados do dashboard:", error);
            dashboardContainer.innerHTML = '<p style="color:red; text-align:center;">Não foi possível carregar os dados da dashboard.</p>';
        }
    }

    fetchDashboardData();
}
    // --- LÓGICA DA PÁGINA DE UPLOAD (upload.html) ---
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        const btnIniciar = document.getElementById('btnIniciarTriagemUpload');
        const fileInput = document.getElementById('arquivo');
        
        uploadForm.addEventListener('submit', (event) => {
            if (fileInput.files.length === 0) {
                alert("Por favor, selecione um ou mais arquivos antes de iniciar a triagem.");
                event.preventDefault(); // Impede o envio do formulário se nenhum arquivo for selecionado
                return;
            }

            if (btnIniciar) {
                btnIniciar.disabled = true;
                btnIniciar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processando, por favor aguarde...';
            }
        });

        // Lógica de drag-and-drop
        const fileDisplay = document.getElementById('arquivosSelecionados');
        const dragDropArea = document.getElementById('dragDropArea');
        if(fileInput && fileDisplay && dragDropArea){
            document.getElementById('btnSelecionarArquivos').addEventListener('click', () => fileInput.click());
            fileInput.addEventListener('change', () => updateFileDisplay(fileInput.files));
    
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                dragDropArea.addEventListener(eventName, e => { e.preventDefault(); e.stopPropagation(); });
            });
            ['dragenter', 'dragover'].forEach(eventName => dragDropArea.addEventListener(eventName, () => dragDropArea.classList.add('highlight')));
            ['dragleave', 'drop'].forEach(eventName => dragDropArea.addEventListener(eventName, () => dragDropArea.classList.remove('highlight')));
            dragDropArea.addEventListener('drop', e => {
                fileInput.files = e.dataTransfer.files;
                updateFileDisplay(fileInput.files);
            });
    
            function updateFileDisplay(files) {
                fileDisplay.textContent = files.length > 0 ? `${files.length} arquivo(s) selecionado(s).` : 'Arraste e solte os arquivos aqui';
            }
        }
    }

    // --- LÓGICA DA PÁGINA DE DETALHES (candidate_details.html) ---
    const tabsContainer = document.querySelector('.tabs-navigation');
    if (tabsContainer) {
        const tabButtons = tabsContainer.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetTabId = button.dataset.tab;
                
                tabButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                
                tabContents.forEach(content => {
                    // Oculta todos os conteúdos
                    content.style.display = 'none';
                    // Mostra apenas o conteúdo da aba clicada
                    if (content.id === `tab${targetTabId.charAt(0).toUpperCase() + targetTabId.slice(1)}`) {
                        content.style.display = 'block';
                    }
                });
            });
        });
        
        // Ativa a primeira aba por padrão ao carregar a página
        if(tabButtons.length > 0) {
            tabButtons[0].click();
        }
    }
   /// --- LÓGICA DA PÁGINA DE CANDIDATOS (candidatos_ranqueados.html) ---
const candidateListContainer = document.getElementById('candidateList');
if (candidateListContainer) {
    const vagaSelector = document.getElementById('vagaSelector');
    const optionsModal = document.getElementById('candidateOptionsModal');
    const modalCandidateName = document.getElementById('modalCandidateName');
    const btnCloseModal = optionsModal ? optionsModal.querySelector('.close-button') : null;
    const btnReprove = document.getElementById('btnReproveCandidate');
    const btnDelete = document.getElementById('btnDeleteCandidate');
    const btnCancel = document.getElementById('btnCancelOption');
    let currentCandidateId = null;

    // Função para renderizar a lista de candidatos na tela
    function renderCandidates(candidates) {
        candidateListContainer.innerHTML = '';
        if (!candidates || candidates.length === 0) {
            candidateListContainer.innerHTML = '<p style="text-align:center; padding: 20px;">Nenhum candidato encontrado.</p>';
            return;
        }

        candidates.forEach(c => {
            const score = c.match_score !== undefined ? c.match_score : c.pontuacao;
            const scoreLabel = c.match_score !== undefined ? '% Match' : '% Geral';

            const item = document.createElement('div');
            item.className = 'candidate-item';
            item.id = `candidato-item-${c.id}`; // Adiciona um ID para fácil remoção
            item.innerHTML = `
                <span class="candidate-name">${c.nome}</span>
                <span class="candidate-score">${score}${scoreLabel}</span>
                <div class="candidate-actions">
                    <a href="/detalhes_candidato/${c.id}" class="btn btn-details">Ver detalhes</a>
                    <button class="btn-icon btn-options" data-id="${c.id}" data-name="${c.nome}" title="Mais opções">
                        <i class="fas fa-ellipsis-v"></i>
                    </button>
                </div>
            `;
            candidateListContainer.appendChild(item);
        });
    }

    // Função para abrir o modal de opções
    function openOptionsModal(id, name) {
        currentCandidateId = id;
        modalCandidateName.textContent = name;
        if(optionsModal) optionsModal.style.display = 'flex';
    }

    // Função para fechar o modal
    function closeOptionsModal() {
        if(optionsModal) optionsModal.style.display = 'none';
        currentCandidateId = null;
    }

    // Adiciona o listener principal na lista de candidatos para delegar eventos
    candidateListContainer.addEventListener('click', (e) => {
        const optionsButton = e.target.closest('.btn-options');
        if (optionsButton) {
            const id = optionsButton.dataset.id;
            const name = optionsButton.dataset.name;
            openOptionsModal(id, name);
        }
    });

    // Listeners para os botões do modal
    if (btnCloseModal) btnCloseModal.onclick = closeOptionsModal;
    if (btnCancel) btnCancel.onclick = closeOptionsModal;

    if (btnReprove) {
        btnReprove.addEventListener('click', async () => {
            if (!currentCandidateId) return;
            const res = await fetch(`/api/candidatos/${currentCandidateId}/reprovar`, { method: 'POST' });
            if (res.ok) {
                document.getElementById(`candidato-item-${currentCandidateId}`).remove();
                closeOptionsModal();
                alert('Candidato reprovado e movido da lista de ativos.');
            } else {
                alert('Erro ao reprovar candidato.');
            }
        });
    }

    if (btnDelete) {
        btnDelete.addEventListener('click', async () => {
            if (!currentCandidateId) return;
            if (confirm('ATENÇÃO: Esta ação é permanente e não pode ser desfeita. Deseja realmente excluir este candidato?')) {
                const res = await fetch(`/api/candidatos/${currentCandidateId}`, { method: 'DELETE' });
                if (res.ok) {
                    document.getElementById(`candidato-item-${currentCandidateId}`).remove();
                    closeOptionsModal();
                    alert('Candidato excluído permanentemente.');
                } else {
                    alert('Erro ao excluir candidato.');
                }
            }
        });
    }
    
    // Função para atualizar a lista com base na vaga selecionada
    async function atualizarListaPorVaga() {
        const vagaId = vagaSelector.value;
        if (vagaId === 'geral') {
            // Usa os dados que o Flask já enviou para a página na primeira carga
            renderCandidates(window.FLASK_CANDIDATES_DATA || []);
            return;
        }
        candidateListContainer.innerHTML = '<p style="text-align:center; padding: 20px;">Calculando "Match"...</p>';
        try {
            const res = await fetch(`/candidatos_ranqueados?vaga_id=${vagaId}`);
            const data = await res.json();
            renderCandidates(data);
        } catch (error) {
            candidateListContainer.innerHTML = '<p style="text-align:center; padding: 20px;">Erro ao carregar candidatos.</p>';
        }
    }

    if(vagaSelector) vagaSelector.addEventListener('change', atualizarListaPorVaga);
    
    // Renderiza a lista inicial que veio do Flask
    renderCandidates(window.FLASK_CANDIDATES_DATA || []);
}
// --- LÓGICA DA PÁGINA DE AGENDAMENTO (agendar_entrevista.html) ---
const interviewForm = document.getElementById('interviewForm');
if (interviewForm) {
    interviewForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const btnConfirmar = document.getElementById('btnConfirmarAgendamento');
        btnConfirmar.disabled = true;
        btnConfirmar.textContent = 'Agendando...';

        const interviewData = {
            candidato_id: interviewForm.dataset.candidateId,
            candidato_nome: interviewForm.dataset.candidateName,
            tipo: document.getElementById('tipoEntrevista').value,
            recrutador: document.getElementById('recrutador').value,
            data: document.getElementById('dataEntrevista').value,
            hora: document.getElementById('horaEntrevista').value
        };

        try {
            const res = await fetch('/api/agendar_entrevista', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(interviewData)
            });
            const data = await res.json();
            if (data.success) {
                alert('Entrevista agendada com sucesso! Verifique o console do servidor para ver os detalhes.');
                window.location.href = `/detalhes_candidato/${interviewData.candidato_id}`;
            } else {
                alert('Ocorreu um erro ao agendar a entrevista.');
                btnConfirmar.disabled = false;
                btnConfirmar.textContent = 'Confirmar agendamento';
            }
        } catch (error) {
            alert('Erro de comunicação com o servidor.');
            btnConfirmar.disabled = false;
            btnConfirmar.textContent = 'Confirmar agendamento';
        }
    });
}
});
