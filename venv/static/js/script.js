document.addEventListener('DOMContentLoaded', () => {
    // Estas são variáveis que podem ser usadas em múltiplas lógicas, se necessário.
    // Defina-as aqui no escopo global do DCL.
    const modal = document.getElementById('candidateOptionsModal');
    const modalCandidateName = document.getElementById('modalCandidateName');
    const btnReproveCandidate = document.getElementById('btnReproveCandidate');
    const btnDeleteCandidate = document.getElementById('btnDeleteCandidate');
    const btnCancelOption = document.getElementById('btnCancelOption');
    const closeButton = modal ? modal.getElementsByClassName('close-button')[0] : null;

    let currentCandidateId = null; // Usada para armazenar o ID do candidato clicado no modal

    // Lógica para a página de Login (presente apenas em login.html)
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', (event) => {
            event.preventDefault(); // Impede o envio padrão do formulário
            alert('Login simulado com sucesso!');
            window.location.href = '/home'; // Redireciona para a rota '/home' do Flask
        });
    }

    // Lógica para a Dashboard (presente apenas em dashboard.html)
    const btnIniciarTriagemDashboard = document.getElementById("btnIniciarTriagem");
    if (btnIniciarTriagemDashboard) {
        btnIniciarTriagemDashboard.addEventListener('click', () => {
            window.location.href = "/upload_curriculos"; // Redireciona para a página de upload
        });
    }

    // Lógica para a página de Upload de Currículos (presente apenas em upload.html)
    const btnSelecionarArquivos = document.getElementById('btnSelecionarArquivos');
    const arquivoInput = document.getElementById('arquivo');
    const dragDropArea = document.getElementById('dragDropArea');
    const btnVoltarUpload = document.getElementById('btnVoltarUpload');
    const btnIniciarTriagemUpload = document.getElementById('btnIniciarTriagemUpload');

    // Verifica se os elementos da página de upload existem antes de adicionar listeners
    if (btnSelecionarArquivos && arquivoInput && dragDropArea && btnVoltarUpload && btnIniciarTriagemUpload) {
        btnSelecionarArquivos.addEventListener('click', () => {
            arquivoInput.click();
        });

        arquivoInput.addEventListener('change', () => {
            if (arquivoInput.files.length > 0) {
                const fileNames = Array.from(arquivoInput.files).map(file => file.name).join(', ');
                alert(`Arquivo(s) selecionado(s): ${arquivoInput.files.length} - ${fileNames}`);
            }
        });

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dragDropArea.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) { e.preventDefault(); e.stopPropagation(); }
        ['dragenter', 'dragover'].forEach(eventName => { dragDropArea.addEventListener(eventName, highlight, false); });
        ['dragleave', 'drop'].forEach(eventName => { dragDropArea.addEventListener(eventName, unhighlight, false); });
        function highlight() { dragDropArea.classList.add('highlight'); }
        function unhighlight() { dragDropArea.classList.remove('highlight'); }
        dragDropArea.addEventListener('drop', handleDrop, false);
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            arquivoInput.files = files;
            const fileNames = Array.from(arquivoInput.files).map(file => file.name).join(', ');
            alert(`Arquivo(s) solto(s): ${files.length} - ${fileNames}`);
        }

        btnVoltarUpload.addEventListener('click', () => {
            window.location.href = "/home";
        });

        btnIniciarTriagemUpload.addEventListener('click', () => {
            if (arquivoInput.files.length > 0) {
                const files = arquivoInput.files;
                const formData = new FormData();
                for (let i = 0; i < files.length; i++) {
                    formData.append("arquivos[]", files[i]);
                }
                fetch("/upload_multiple_files", {
                    method: "POST",
                    body: formData
                })
                .then(response => {
                    if (!response.ok) { throw new Error('Falha no upload dos arquivos.'); }
                    return response.text();
                })
                .then(data => {
                    console.log("Upload bem-sucedido:", data);
                    window.location.href = "/processando_curriculos";
                })
                .catch(error => {
                    console.error("Erro ao fazer upload dos arquivos:", error);
                    alert("Erro ao fazer upload dos arquivos. Verifique o console para mais detalhes.");
                });
            } else {
                alert("Por favor, selecione ou arraste arquivo(s) para iniciar a triagem.");
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

    // Lógica para a página de Candidatos Ranqueados (results.html)
    const candidateList = document.getElementById('candidateList');
    const flaskDataElement = document.getElementById('flask-data'); // Elemento para pegar os dados do Flask

    if (candidateList && flaskDataElement) { // Verifica se estamos na página de resultados e se o elemento de dados existe
        let realCandidates = [];
        const rawCandidatesData = flaskDataElement.dataset.candidates; // Pega a string bruta do atributo

        // Verifica se a string não está vazia e tenta fazer o parse
        if (rawCandidatesData && rawCandidatesData.trim() !== '') {
            try {
                realCandidates = JSON.parse(rawCandidatesData);
            } catch (e) {
                console.error("Erro ao parsear dados de candidatos do Flask:", e);
                // Se houver um erro de parse, realCandidates permanece como []
            }
        } else {
            // Se a string for vazia ou só espaços em branco, realCandidates permanece como []
            console.log("Nenhum dado de candidato encontrado no atributo data-candidates. Assumindo lista vazia.");
        }

        const searchCandidate = document.getElementById('searchCandidate');
        const sortOrder = document.getElementById('sortOrder');

        function renderCandidates(candidatesToRender) {
            candidateList.innerHTML = '';
            if (candidatesToRender.length === 0) {
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
        }

        function filterAndSortCandidates() {
            let filtered = [...realCandidates];

            const searchTerm = searchCandidate.value.toLowerCase();
            if (searchTerm) {
                filtered = filtered.filter(candidate =>
                    (candidate.nome && candidate.nome.toLowerCase().includes(searchTerm))
                );
            }

            const sortValue = sortOrder.value;
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

        searchCandidate.addEventListener('input', filterAndSortCandidates);
        sortOrder.addEventListener('change', filterAndSortCandidates);
        filterAndSortCandidates(); // Renderiza na carga da página

        if (modal) { // Lógica do Modal (verificando existência)
            if (closeButton) closeButton.onclick = function() { modal.style.display = 'none'; }
            window.onclick = function(event) {
                if (event.target == modal) { modal.style.display = 'none'; }
            }
            if (btnCancelOption) btnCancelOption.onclick = function() { modal.style.display = 'none'; }

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
                }
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
                }
            }
        }
    }

    // Lógica para a página de Detalhes do Candidato (candidate_details.html)
    const dynamicCandidateNameSpan = document.getElementById('dynamicCandidateName');
    const flaskCandidateDataElement = document.getElementById('flask-candidate-data'); // Elemento para pegar os dados do candidato

    if (dynamicCandidateNameSpan && flaskCandidateDataElement) { // Verifica se estamos na página de detalhes
        let candidateData = {};
        try {
            candidateData = JSON.parse(flaskCandidateDataElement.dataset.candidate || '{}');
        } catch (e) {
            console.error("Erro ao parsear dados do candidato do Flask:", e);
        }

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

        if (candidateData) {
            dynamicCandidateNameSpan.innerText = candidateData.nome ? candidateData.nome.toUpperCase() : 'NOME INDISPONÍVEL';
            document.getElementById('candidateAge').innerText = candidateData.idade || '--';
            document.getElementById('candidateDesiredRole').innerText = candidateData.cargo_desejado || '--';
            document.getElementById('candidateLastRole').innerText = candidateData.ultimo_cargo || '--';
            document.getElementById('candidateAvailability').innerText = candidateData.disponibilidade || '--';
            document.getElementById('candidateEmail').innerText = candidateData.email || 'N/A';
            document.getElementById('candidatePhone').innerText = candidateData.telefone || 'N/A';

            const linkedinLink = document.getElementById('candidateLinkedin');
            if (linkedinLink) { // Verificação adicional
                if (candidateData.linkedin) {
                    linkedinLink.href = candidateData.linkedin.startsWith('http') ? candidateData.linkedin : `https://${candidateData.linkedin}`;
                    linkedinLink.innerText = candidateData.linkedin.replace(/^(https?:\/\/)?(www\.)?linkedin\.com\/in\//, '');
                } else {
                    linkedinLink.innerText = 'N/A';
                    linkedinLink.removeAttribute('href'); // Remove o link se não houver URL
                }
            }

            // Pontuação
            document.getElementById('overallScore').innerText = candidateData.pontuacaoGeral || 0;
            document.querySelector('#tabPontuacao .score-card:nth-child(1) .score-value span').innerText = candidateData.fitTecnico || 0;
            document.querySelector('#tabPontuacao .score-card:nth-child(2) .score-value span').innerText = candidateData.experienciaRelevante || 0;
            document.querySelector('#tabPontuacao .score-card:nth-child(3) .score-value span').innerText = candidateData.fitCultural || 0;

            const reasonsList = document.querySelector('#tabPontuacao .reasons-list');
            if (reasonsList) { // Verificação adicional
                reasonsList.innerHTML = '';
                if (candidateData.motivosPontuacao && candidateData.motivosPontuacao.length > 0) {
                    candidateData.motivosPontuacao.forEach(reason => {
                        const li = document.createElement('li');
                        li.innerText = reason;
                        reasonsList.appendChild(li);
                    });
                } else {
                    reasonsList.innerHTML = '<li>Nenhum motivo de pontuação detalhado.</li>';
                }
            }

            // Habilidades
            const skillTagsContainer = document.querySelector('#tabHabilidades .skill-tags');
            if (skillTagsContainer) { // Verificação adicional
                skillTagsContainer.innerHTML = '';
                if (candidateData.habilidades && candidateData.habilidades.length > 0) {
                    candidateData.habilidades.forEach(skill => {
                        const span = document.createElement('span');
                        span.classList.add('skill-tag');
                        span.innerText = skill;
                        skillTagsContainer.appendChild(span);
                    });
                } else {
                    skillTagsContainer.innerHTML = '<p>Nenhuma habilidade detectada.</p>';
                }
            }

            // Experiência
            const experienceContainer = document.querySelector('#tabExperiencia');
            if (experienceContainer) { // Verificação adicional
                experienceContainer.innerHTML = '<h3>Histórico Profissional</h3>';
                if (candidateData.experiencia && candidateData.experiencia.length > 0) {
                    candidateData.experiencia.forEach(exp => {
                        const div = document.createElement('div');
                        div.classList.add('experience-item');
                        const activitiesHtml = exp.atividades && exp.atividades.length > 0 ? `<ul>${exp.atividades.map(act => `<li>${act}</li>`).join('')}</ul>` : '';
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

            // Formação
            const formacaoContainer = document.querySelector('#tabFormacao');
            if (formacaoContainer) { // Verificação adicional
                formacaoContainer.innerHTML = '<h3>Formação Acadêmica</h3>';
                if (candidateData.formacao && candidateData.formacao.length > 0) {
                    candidateData.formacao.forEach(form => {
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

            // Idiomas
            const languageListContainer = document.querySelector('#tabIdioma .language-list');
            if (languageListContainer) { // Verificação adicional
                languageListContainer.innerHTML = '';
                if (candidateData.idiomas && candidateData.idiomas.length > 0) {
                    candidateData.idiomas.forEach(lang => {
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
    if (interviewForm) { // Verifica se estamos na página de agendamento
        const urlParams = new URLSearchParams(window.location.search);
        const candidateName = urlParams.get('name') || "Marcos Vinicius Mendes";
        const candidateNameInterviewSpan = document.getElementById('candidateNameInterview');
        if (candidateNameInterviewSpan) { // Verifica se o elemento existe
            candidateNameInterviewSpan.innerText = candidateName;
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
                window.location.href = "/detalhes_candidato";
            });
        }
    }

    // Lógica para a página de Vagas (vagas.html)
    const jobListContainer = document.getElementById('jobList');
    if (jobListContainer) { // Verifica se estamos na página de vagas
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