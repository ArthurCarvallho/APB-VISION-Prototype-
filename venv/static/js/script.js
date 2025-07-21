document.addEventListener('DOMContentLoaded', () => {
    // Variáveis globais para o modal de opções de candidato (usadas na página de resultados)
    const modal = document.getElementById('candidateOptionsModal');
    const modalCandidateName = document.getElementById('modalCandidateName');
    const btnReproveCandidate = document.getElementById('btnReproveCandidate');
    const btnDeleteCandidate = document.getElementById('btnDeleteCandidate');
    const btnCancelOption = document.getElementById('btnCancelOption');
    const closeButton = modal ? modal.getElementsByClassName('close-button')[0] : null; // Close button do modal

    let currentCandidateId = null; // Para armazenar o ID do candidato do modal

    // --- Lógica para a página de Login (login.html) ---
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (event) => { // Adicionado 'async'
            event.preventDefault();

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            try {
                const res = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: email, senha: password })
                });

                const data = await res.json();
                if (data.success) {
                    alert('Login bem-sucedido!');
                    // Salvar nome do usuário para exibir em outras páginas
                    localStorage.setItem('user_nome', data.nome);
                    window.location.href = '/home'; // Redireciona para a home
                } else {
                    alert(data.message || 'Erro de login.');
                }
            } catch (error) {
                console.error("Erro na requisição de login:", error);
                alert('Erro na comunicação com o servidor. Tente novamente.');
            }
        });
    }

    // Preencher nome do usuário autenticado (se existir em qualquer página)
    const userNomeSpan = document.getElementById('user-nome');
    if (userNomeSpan) {
        const nomeUsuario = localStorage.getItem('user_nome');
        if (nomeUsuario) {
            userNomeSpan.textContent = `Olá, ${nomeUsuario}!`;
        } else {
            userNomeSpan.textContent = `Olá, Usuário!`; // Fallback
        }
    }


    // --- Lógica para a Dashboard (dashboard.html) ---
    const btnIniciarTriagemDashboard = document.getElementById("btnIniciarTriagem");
    const dashboardContainer = document.querySelector('.dashboard-container');

    if (btnIniciarTriagemDashboard) {
        btnIniciarTriagemDashboard.addEventListener('click', () => {
            window.location.href = "/upload_curriculos";
        });
    }

    if (dashboardContainer) { // Se estiver na página do dashboard com gráficos
        async function fetchDashboardData() {
            try {
                const res = await fetch('/dashboard_data');
                if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
                return await res.json();
            } catch (error) {
                console.error("Erro ao buscar dados do dashboard:", error);
                return null;
            }
        }

        function renderCharts(data) {
            if (!data) return;

            document.getElementById('totalCandidatos').textContent = data.pontuacoes ? data.pontuacoes.length : 0;
            const media = (data.pontuacoes && data.pontuacoes.length) ? (data.pontuacoes.reduce((a, b) => a + b, 0) / data.pontuacoes.length).toFixed(1) : 0;
            document.getElementById('mediaPontuacao').textContent = media;
            document.getElementById('totalExperiencias').textContent = data.experiencias || 0;

            const topHabilidadesList = document.getElementById('topHabilidades');
            if (topHabilidadesList && data.habilidades) {
                const habilidadesArr = Object.entries(data.habilidades).sort((a, b) => b[1] - a[1]).slice(0, 5);
                topHabilidadesList.innerHTML = habilidadesArr.map(([h, v]) => `<li>${h} <span style='color:#0077ff;font-weight:bold;'>(${v})</span></li>`).join('');
            }

            if (document.getElementById('pontuacaoChart')) {
                new Chart(document.getElementById('pontuacaoChart'), {
                    type: 'bar',
                    data: { labels: data.pontuacoes ? data.pontuacoes.map((_, i) => `Candidato ${i + 1}`) : [], datasets: [{ label: 'Pontuação', data: data.pontuacoes || [], backgroundColor: 'rgba(0, 123, 255, 0.7)' }] },
                    options: { responsive: true, plugins: { legend: { display: false } }, animation: { duration: 1200 } }
                });
            }
            if (document.getElementById('histogramaChart')) {
                const bins = [0, 20, 40, 60, 80, 100];
                const hist = bins.map((b, i) => (data.pontuacoes || []).filter(p => p >= (bins[i - 1] || 0) && p <= b).length);
                new Chart(document.getElementById('histogramaChart'), {
                    type: 'bar',
                    data: { labels: bins.map((b, i) => i === 0 ? `0-${b}` : `${bins[i - 1] + 1}-${b}`), datasets: [{ label: 'Distribuição', data: hist, backgroundColor: 'rgba(40,167,69,0.7)' }] },
                    options: { responsive: true, plugins: { legend: { display: false } }, animation: { duration: 1200 } }
                });
            }
            if (document.getElementById('habilidadesChart')) {
                new Chart(document.getElementById('habilidadesChart'), {
                    type: 'doughnut',
                    data: { labels: data.habilidades ? Object.keys(data.habilidades) : [], datasets: [{ label: 'Habilidades', data: data.habilidades ? Object.values(data.habilidades) : [], backgroundColor: ['#007bff', '#28a745', '#ffc107', '#17a2b8', '#6610f2', '#fd7e14', '#6f42c1', '#e83e8c', '#20c997', '#343a40'] }] },
                    options: { responsive: true, animation: { animateScale: true } }
                });
            }
            if (document.getElementById('formacaoChart')) {
                new Chart(document.getElementById('formacaoChart'), {
                    type: 'pie',
                    data: { labels: data.formacoes ? Object.keys(data.formacoes) : [], datasets: [{ label: 'Formações', data: data.formacoes ? Object.values(data.formacoes) : [], backgroundColor: ['#17a2b8', '#6610f2', '#fd7e14', '#6f42c1', '#e83e8c', '#20c997', '#343a40', '#007bff', '#28a745', '#ffc107'] }] },
                    options: { responsive: true, animation: { animateScale: true } }
                });
            }
            if (document.getElementById('idiomasChart')) {
                new Chart(document.getElementById('idiomasChart'), {
                    type: 'polarArea',
                    data: { labels: data.idiomas ? Object.keys(data.idiomas) : [], datasets: [{ label: 'Idiomas', data: data.idiomas ? Object.values(data.idiomas) : [], backgroundColor: ['#ffc107', '#17a2b8', '#6610f2', '#fd7e14', '#6f42c1', '#e83e8c', '#20c997', '#343a40', '#007bff', '#28a745'] }] },
                    options: { responsive: true, animation: { animateRotate: true } }
                });
            }
        }
        fetchDashboardData().then(renderCharts);
    }


    // --- Lógica para a página de Upload de Currículos (upload.html) ---
    // Variáveis renomeadas para evitar conflitos e IDs de elementos
    const uploadBtnSelecionarArquivos = document.getElementById('btnSelecionarArquivos');
    const uploadArquivoInput = document.getElementById('arquivo');
    const uploadDragDropArea = document.getElementById('dragDropArea');
    const uploadBtnVoltarUpload = document.getElementById('btnVoltarUpload');
    const uploadBtnIniciarTriagemUpload = document.getElementById('btnIniciarTriagemUpload');
    const uploadArquivosSelecionadosDisplay = document.getElementById('arquivosSelecionados'); // O p#arquivosSelecionados

    if (uploadBtnSelecionarArquivos && uploadArquivoInput && uploadDragDropArea && uploadBtnVoltarUpload && uploadBtnIniciarTriagemUpload && uploadArquivosSelecionadosDisplay) {
        uploadBtnSelecionarArquivos.addEventListener('click', () => {
            uploadArquivoInput.click();
        });

        uploadArquivoInput.addEventListener('change', () => {
            if (uploadArquivoInput.files.length > 0) {
                const fileNames = Array.from(uploadArquivoInput.files).map(file => file.name).join(', ');
                uploadArquivosSelecionadosDisplay.textContent = `Selecionado: ${uploadArquivoInput.files.length} arquivo(s) (${fileNames})`;
            } else {
                uploadArquivosSelecionadosDisplay.textContent = 'Arraste e solte os arquivos aqui';
            }
        });

        // Funções auxiliares para Drag and Drop (declaradas dentro do if para escopo local)
        function preventDefaults(e) { e.preventDefault(); e.stopPropagation(); }
        function highlight() { uploadDragDropArea.classList.add('highlight'); }
        function unhighlight() { uploadDragDropArea.classList.remove('highlight'); }
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            uploadArquivoInput.files = files; // Atribui os arquivos soltos ao input
            if (files.length > 0) {
                const fileNames = Array.from(files).map(file => file.name).join(', ');
                uploadArquivosSelecionadosDisplay.textContent = `Solto(s): ${files.length} arquivo(s) (${fileNames})`;
            } else {
                uploadArquivosSelecionadosDisplay.textContent = 'Arraste e solte os arquivos aqui';
            }
        }

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadDragDropArea.addEventListener(eventName, preventDefaults, false);
        });
        ['dragenter', 'dragover'].forEach(eventName => { uploadDragDropArea.addEventListener(eventName, highlight, false); });
        ['dragleave', 'drop'].forEach(eventName => { uploadDragDropArea.addEventListener(eventName, unhighlight, false); });
        uploadDragDropArea.addEventListener('drop', handleDrop, false);

        uploadBtnVoltarUpload.addEventListener('click', () => {
            window.location.href = "/home";
        });

        uploadBtnIniciarTriagemUpload.addEventListener('click', async () => {
            if (uploadArquivoInput.files.length === 0) {
                alert("Por favor, selecione ou arraste arquivo(s) para iniciar a triagem.");
                return;
            }
            const files = uploadArquivoInput.files;
            const formData = new FormData();
            for (let i = 0; i < files.length; i++) {
                formData.append("arquivos[]", files[i]); // Chave CORRETA para o Flask
            }
            try {
                const res = await fetch("/upload_multiple_files", {
                    method: "POST",
                    body: formData
                });
                if (!res.ok) { // Se a resposta não for OK (status 2xx)
                    const errorText = await res.text(); // Tenta pegar o texto do erro
                    // Erro 404 (Not Found) indica rota não encontrada no backend
                    if (res.status === 404) {
                        throw new Error(`Rota de upload não encontrada: ${res.url}. Verifique seu app.py.`);
                    }
                    // Erro 400 (Bad Request) indica que o backend não gostou dos dados enviados
                    if (res.status === 400) {
                        let msg = `Dados inválidos enviados. Detalhes: ${errorText}.`;
                        if (errorText.includes("files")) { // Se a mensagem do Flask mencionar "files", pode ser nome de campo
                            msg += " Verifique se o backend espera 'arquivos[]' ou 'files'.";
                        }
                        throw new Error(msg);
                    }
                    throw new Error(`Falha no upload dos arquivos: ${res.status} ${res.statusText} - ${errorText}`);
                }
                const data = await res.text(); // Supondo que o Flask retorna texto simples
                console.log("Upload bem-sucedido:", data);
                window.location.href = "/processando_curriculos"; // Redireciona para a tela de processamento
            } catch (error) {
                console.error("Erro ao fazer upload dos arquivos:", error);
                alert(`Erro ao fazer upload dos arquivos. Detalhes: ${error.message}. Verifique o console.`);
            }
        });
    }

    // Lógica para a página de Processamento (presente apenas em processing.html)
    const progressBar = document.getElementById('progressBar');
    if (progressBar) { // Verifica se estamos na página de processamento
        let width = 0;
        const interval = setInterval(() => {
            width += 10;
            if (width <= 100) {
                progressBar.style.width = width + '%';
            } else {
                clearInterval(interval);
                window.location.href = "/candidatos_ranqueados";
            }
        }, 500);
    }

    // --- Lógica para a página de Candidatos Ranqueados (results.html) ---
    const candidateList = document.getElementById('candidateList');
    // Usa a variável global FLASK_CANDIDATES_DATA definida no <head> do results.html
    let realCandidates = Array.isArray(window.FLASK_CANDIDATES_DATA) ? window.FLASK_CANDIDATES_DATA : [];


    if (candidateList) { // Verifica se estamos na página de resultados
        const searchCandidate = document.getElementById('searchCandidate');
        const sortOrder = document.getElementById('sortOrder');

        // Funções internas para renderizar, filtrar e ordenar (declaradas DENTRO deste if)
        function renderCandidates(candidatesToRender) {
            candidateList.innerHTML = '';
            if (!Array.isArray(candidatesToRender) || candidatesToRender.length === 0) {
                candidateList.innerHTML = '<p style="text-align: center; margin-top: 30px;">Nenhum candidato encontrado.</p>';
                return;
            }
            candidatesToRender.forEach(candidate => {
                const candidateItem = document.createElement('div');
                candidateItem.classList.add('candidate-item');
                candidateItem.innerHTML = `
                    <span class="candidate-name">${candidate.nome || 'Nome Indisponível'}</span>
                    <span class="candidate-score">${candidate.pontuacao || 0}%</span>
                    <div class="candidate-actions">
                        <button class="btn btn-details btn-ver-detalhes" data-id="${candidate.id}">Ver detalhes</button>
                        <button class="btn btn-icon btn-add"><i class="fas fa-user-plus"></i></button>
                        <button class="btn btn-icon btn-remove" data-id="${candidate.id}" data-name="${candidate.nome || 'Candidato'}"><i class="fas fa-times-circle"></i></button>
                    </div>
                `;
                candidateList.appendChild(candidateItem);
            });

            document.querySelectorAll('.btn-ver-detalhes').forEach(button => {
                button.addEventListener('click', (event) => {
                    const candidateId = event.target.dataset.id;
                    window.location.href = `/detalhes_candidato/${candidateId}`;
                });
            });

            document.querySelectorAll('.btn-remove').forEach(button => {
                button.addEventListener('click', (event) => {
                    currentCandidateId = event.target.closest('button').dataset.id;
                    const candidateName = event.target.closest('button').dataset.name;
                    if (modalCandidateName) modalCandidateName.innerText = candidateName;
                    if (modal) modal.style.display = 'flex';
                });
            });

            // Adiciona event listener para o botão de adicionar contato (agendar entrevista)
            document.querySelectorAll('.btn-add').forEach(button => {
                button.addEventListener('click', (event) => {
                    const candidateItemElement = event.target.closest('.candidate-item');
                    const candidateId = candidateItemElement.querySelector('.btn-ver-detalhes').dataset.id;
                    const candidateName = candidateItemElement.querySelector('.candidate-name').innerText;
                    
                    window.location.href = `/agendar_entrevista_page?id=${candidateId}&name=${encodeURIComponent(candidateName)}`;
                });
            });
        }

        function filterAndSortCandidates() {
            let filtered = Array.isArray(realCandidates) ? [...realCandidates] : [];

            const searchTerm = searchCandidate && searchCandidate.value ? searchCandidate.value.toLowerCase() : '';
            if (searchTerm) {
                filtered = filtered.filter(candidate =>
                    (candidate.nome && candidate.nome.toLowerCase().includes(searchTerm))
                );
            }

            const sortValue = sortOrder && sortOrder.value ? sortOrder.value : 'pontuacao_desc';
            if (sortValue === "pontuacao_desc") {
                filtered.sort((a, b) => (b.pontuacao || 0) - (a.pontuacao || 0));
            } else if (sortValue === "pontuacao_asc") {
                filtered.sort((a, b) => (a.pontuacao || 0) - (b.pontuacao || 0));
            } else if (sortValue === "nome_asc") {
                filtered.sort((a, b) => (a.nome || '').localeCompare(b.nome || ''));
            } else if (sortValue === "nome_desc") {
                filtered.sort((a, b) => (b.nome || '').localeCompare(a.nome || ''));
            }

            renderCandidates(filtered);
        }

        if (searchCandidate) {
            searchCandidate.addEventListener('input', filterAndSortCandidates);
        }
        if (sortOrder) {
            sortOrder.addEventListener('change', filterAndSortCandidates);
        }
        filterAndSortCandidates(); // Renderiza na carga da página

        if (modal) { // Lógica do Modal (verificando existência)
            if (closeButton) closeButton.onclick = function() { modal.style.display = 'none'; };
            window.onclick = function(event) {
                if (event.target == modal) { modal.style.display = 'none'; }
            };
            if (btnCancelOption) btnCancelOption.onclick = function() { modal.style.display = 'none'; };

            if (btnReproveCandidate) {
                btnReproveCandidate.onclick = function() {
                    if (currentCandidateId) {
                        fetch(`/reprove_candidate/${currentCandidateId}`, { method: 'POST' })
                            .then(response => response.json())
                            .then(data => {
                                alert(data.message);
                                modal.style.display = 'none';
                                window.location.reload();
                            })
                            .catch(error => {
                                console.error('Erro ao reprovar candidato:', error);
                                alert('Erro ao reprovar candidato.');
                            });
                    }
                };
            }

            if (btnDeleteCandidate) {
                btnDeleteCandidate.onclick = function() {
                    if (currentCandidateId) {
                        if (confirm('Tem certeza que deseja EXCLUIR este candidato? Esta ação é irreversível.')) {
                            fetch(`/delete_candidate/${currentCandidateId}`, { method: 'POST' })
                                .then(response => response.json())
                                .then(data => {
                                    alert(data.message);
                                    modal.style.display = 'none';
                                    window.location.reload();
                                })
                                .catch(error => {
                                    console.error('Erro ao excluir candidato:', error);
                                    alert('Erro ao excluir candidato.');
                                });
                        }
                    }
                };
            }
        }
    }


    // Lógica para a página de Detalhes do Candidato (candidate_details.html)
    const dynamicCandidateNameSpan = document.getElementById('dynamicCandidateName');
    let candidateDataDetailsPage = {};

    if (dynamicCandidateNameSpan && window.FLASK_CANDIDATE_DETAILS_DATA) {
        candidateDataDetailsPage = window.FLASK_CANDIDATE_DETAILS_DATA;

        const tabButtons = document.querySelectorAll('.tabs-navigation .tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));
                button.classList.add('active');
                const targetTabId = button.dataset.tab;
                document.getElementById(`tab${targetTabId.charAt(0).toUpperCase() + targetTabId.slice(1)}`).classList.add('active');
            });
        });

        if (candidateDataDetailsPage) {
            document.getElementById('candidateNameTitle').innerText = `DETALHES DO CANDIDATO: ${candidateDataDetailsPage.nome ? candidateDataDetailsPage.nome.toUpperCase() : 'NOME INDISPONÍVEL'}`;
            document.getElementById('candidateAge').innerText = candidateDataDetailsPage.idade || '--';
            document.getElementById('candidateDesiredRole').innerText = candidateDataDetailsPage.cargo_desejado || '--';
            document.getElementById('candidateLastRole').innerText = candidateDataDetailsPage.ultimo_cargo || '--';
            document.getElementById('candidateAvailability').innerText = candidateDataDetailsPage.disponibilidade || '--';
            document.getElementById('candidateEmail').innerText = candidateDataDetailsPage.email || 'N/A';
            document.getElementById('candidatePhone').innerText = candidateDataDetailsPage.telefone || 'N/A';

            const linkedinLink = document.getElementById('candidateLinkedin');
            if (linkedinLink) {
                if (candidateDataDetailsPage.linkedin) {
                    linkedinLink.href = candidateDataDetailsPage.linkedin.startsWith('http') ? candidateDataDetailsPage.linkedin : `https://${candidateDataDetailsPage.linkedin}`;
                    linkedinLink.innerText = candidateDataDetailsPage.linkedin.replace(/^(https?:\/\/)?(www\.)?linkedin\.com\/in\//, '');
                } else {
                    linkedinLink.innerText = 'N/A';
                    linkedinLink.removeAttribute('href');
                }
            }

            document.getElementById('overallScore').innerText = (candidateDataDetailsPage.pontuacaoGeral || 0) + '%';
            const fitTecnicoSpan = document.querySelector('#tabPontuacao .score-card:nth-child(1) .score-value span');
            if (fitTecnicoSpan) fitTecnicoSpan.innerText = candidateDataDetailsPage.fitTecnico || 0;
            const experienciaRelevanteSpan = document.querySelector('#tabPontuacao .score-card:nth-child(2) .score-value span');
            if (experienciaRelevanteSpan) experienciaRelevanteSpan.innerText = candidateDataDetailsPage.experienciaRelevante || 0;
            const fitCulturalSpan = document.querySelector('#tabPontuacao .score-card:nth-child(3) .score-value span');
            if (fitCulturalSpan) fitCulturalSpan.innerText = candidateDataDetailsPage.fitCultural || 0;

            const reasonsList = document.querySelector('#tabPontuacao .reasons-list');
            if (reasonsList) {
                reasonsList.innerHTML = '';
                // Preferir 'motivos_pontuacao' do DB, que é a análise IA ou a lista de motivos formatada
                if (candidateDataDetailsPage.motivos_pontuacao && candidateDataDetailsPage.motivos_pontuacao.length > 0) {
                    candidateDataDetailsPage.motivos_pontuacao.forEach(reason => {
                        const li = document.createElement('li');
                        li.innerText = reason;
                        reasonsList.appendChild(li);
                    });
                } else { // Fallback se 'motivos_pontuacao' estiver vazio ou não for array
                    reasonsList.innerHTML = '<li>Nenhum motivo de pontuação detalhado.</li>';
                }
            }

            const geminiAnalysisTextElement = document.getElementById('geminiAnalysisText');
            if (geminiAnalysisTextElement) {
                geminiAnalysisTextElement.innerText = candidateDataDetailsPage.analise_ia || 'N/A';
            }


            const skillTagsContainer = document.querySelector('#tabHabilidades .skill-tags');
            if (skillTagsContainer) {
                skillTagsContainer.innerHTML = '';
                if (candidateDataDetailsPage.habilidades && candidateDataDetailsPage.habilidades.length > 0) {
                    candidateDataDetailsPage.habilidades.forEach(skill => {
                        const span = document.createElement('span');
                        span.classList.add('skill-tag');
                        span.innerText = skill;
                        skillTagsContainer.appendChild(span);
                    });
                } else {
                    skillTagsContainer.innerHTML = '<p>Nenhuma habilidade detectada.</p>';
                }
            }


            const experienceContainer = document.querySelector('#tabExperiencia');
            if (experienceContainer) {
                experienceContainer.innerHTML = '<h3>Histórico Profissional</h3>';
                if (candidateDataDetailsPage.experiencia && candidateDataDetailsPage.experiencia.length > 0) {
                    candidateDataDetailsPage.experiencia.forEach(exp => {
                        const div = document.createElement('div');
                        div.classList.add('experience-item');
                        const activitiesHtml = exp.atividades && Array.isArray(exp.atividades) && exp.atividades.length > 0 ? `<ul>${exp.atividades.map(act => `<li>${act}</li>`).join('')}</ul>` : '';
                        div.innerHTML = `
                            <h4>${exp.cargo || 'Cargo Desconhecido'}</h4>
                            <p>${exp.empresa || 'Empresa Desconhecida'} - ${exp.periodo || 'Período Indefinido'}</p>
                            ${activitiesHtml}
                        `;
                        experienceContainer.appendChild(div);
                    });
                } else {
                    experienceContainer.innerHTML += '<p>Nenhuma experiência profissional encontrada.</p>';
                }
            }


            const formacaoContainer = document.querySelector('#tabFormacao');
            if (formacaoContainer) {
                formacaoContainer.innerHTML = '<h3>Formação Acadêmica</h3>';
                if (candidateDataDetailsPage.formacao && candidateDataDetailsPage.formacao.length > 0) {
                    candidateDataDetailsPage.formacao.forEach(form => {
                        const div = document.createElement('div');
                        div.classList.add('education-item');
                        div.innerHTML = `
                            <h4>${form.curso || 'Curso Desconhecido'}</h4>
                            <p>${form.instituicao || 'Instituição Desconhecida'} - ${form.periodo || 'Período Indefinido'}</p>
                        `;
                        formacaoContainer.appendChild(div);
                    });
                } else {
                    formacaoContainer.innerHTML += '<p>Nenhuma formação acadêmica encontrada.</p>';
                }
            }


            const languageListContainer = document.querySelector('#tabIdioma .language-list');
            if (languageListContainer) {
                languageListContainer.innerHTML = '';
                if (candidateDataDetailsPage.idiomas && candidateDataDetailsPage.idiomas.length > 0) {
                    candidateDataDetailsPage.idiomas.forEach(lang => {
                        const li = document.createElement('li');
                        li.innerText = lang;
                        languageListContainer.appendChild(li);
                    });
                } else {
                    languageListContainer.innerHTML = '<li>Nenhum idioma encontrado.</li>';
                }
            }


            const btnDownloadCV = document.querySelector('.btn-download-cv');
            if (btnDownloadCV) {
                btnDownloadCV.addEventListener('click', () => {
                    alert("Funcionalidade de download de currículo será implementada!");
                });
            }

        } else {
            console.warn("Nenhum dado de candidato disponível para renderizar.");
        }
    }


    // Lógica para a página de Agendar Entrevista (agendar_entrevista.html)
    const interviewForm = document.getElementById('interviewForm');
    if (interviewForm) {
        const urlParams = new URLSearchParams(window.location.search);
        const candidateIdFromUrl = urlParams.get('id');
        const candidateNameFromUrl = urlParams.get('name') || "Candidato Desconhecido";

        const candidateNameInterviewSpan = document.getElementById('candidateNameInterview');
        if (candidateNameInterviewSpan) {
            candidateNameInterviewSpan.innerText = candidateNameFromUrl;
        }

        const btnConfirmAgendamento = document.getElementById('btnConfirmarAgendamento');
        const btnCancelAgendamento = document.getElementById('btnCancelarAgendamento');

        if (btnConfirmAgendamento) {
            btnConfirmAgendamento.addEventListener('click', (event) => {
                event.preventDefault();
                alert('Agendamento confirmado! (Simulação)');
                window.location.href = "/candidatos_ranqueados";
            });
        }
        if (btnCancelAgendamento) {
            btnCancelAgendamento.addEventListener('click', (event) => {
                event.preventDefault();
                alert('Agendamento cancelado!');
                if (candidateIdFromUrl) {
                    window.location.href = `/detalhes_candidato/${candidateIdFromUrl}`;
                } else {
                    window.location.href = "/candidatos_ranqueados";
                }
            });
        }
    }

    // Lógica para a página de Vagas (vagas.html)
    const jobListContainer = document.getElementById('jobList');
    if (jobListContainer) {
        const mockJobs = [
            { id: 1, title: "Analista de Dados", status: "Ativa", candidatesCount: "52", link: "/candidatos_ranqueados" },
            { id: 2, title: "Desenvolvedor Python Sênior", status: "Ativa", candidatesCount: "30", link: "/candidatos_ranqueados" },
            { id: 3, title: "Designer UX/UI", status: "Inativa", candidatesCount: "0", link: "/candidatos_ranqueados" }
        ];

        function renderJobs(jobsToRender) {
            jobListContainer.innerHTML = '';
            jobsToRender.forEach(job => {
                const jobItem = document.createElement('div');
                jobItem.classList.add('job-item');
                jobItem.innerHTML = `
                    <div class="job-title-status">
                        <span class="job-title">${job.title}</span>
                        <div class="job-status-dropdown">
                            <span class="status-text">${job.status}</span>
                            <i class="fas fa-chevron-down status-arrow"></i>
                        </div>
                    </div>
                    <div class="job-details">
                        <span class="candidate-count">${job.candidatesCount} Candidatos</span>
                        <a href="${job.link}" class="link-view-candidates" data-job-id="${job.id}">Ver candidatos</a>
                    </div>
                `;
                jobListContainer.appendChild(jobItem);
            });

            document.querySelectorAll('.link-view-candidates').forEach(link => {
                link.addEventListener('click', (event) => {
                    const jobId = event.target.dataset.jobId;
                    console.log(`Ver candidatos para a vaga ID: ${jobId}`);
                });
            });
        }
        renderJobs(mockJobs);

        const btnCriarNovaVaga = document.getElementById('btnCriarNovaVaga');
        if (btnCriarNovaVaga) {
            btnCriarNovaVaga.addEventListener('click', () => {
                alert('Funcionalidade "Criar Nova Vaga" será implementada. Por enquanto, não há rota.');
            });
        }
    }
});