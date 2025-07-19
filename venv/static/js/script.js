document.addEventListener('DOMContentLoaded', () => {
    // Estas são variáveis que podem ser usadas em múltiplas lógicas, se necessário.
    // Defina-as aqui no escopo global do DOMContentLoaded.
    const modal = document.getElementById('candidateOptionsModal');
    const modalCandidateName = document.getElementById('modalCandidateName');
    const btnReproveCandidate = document.getElementById('btnReproveCandidate');
    const btnDeleteCandidate = document.getElementById('btnDeleteCandidate');
    const btnCancelOption = document.getElementById('btnCancelOption');
    const closeButton = modal ? modal.getElementsByClassName('close-button')[0] : null;

    let currentCandidateId = null; // Usada para armazenar o ID do candidato clicado no modal


    // --- Lógica para a página de Login (presente apenas em login.html) ---
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', (event) => {
            event.preventDefault(); // Impede o envio padrão do formulário
            alert('Login simulado com sucesso!');
            window.location.href = '/home'; // Redireciona para a rota '/home' do Flask
        });
    }

    // --- Lógica para a Dashboard (presente apenas em dashboard.html) ---
    const btnIniciarTriagemDashboard = document.getElementById("btnIniciarTriagem");
    if (btnIniciarTriagemDashboard) {
        btnIniciarTriagemDashboard.addEventListener('click', () => {
            window.location.href = "/upload_curriculos"; // Redireciona para a página de upload
        });
    }

    // --- Lógica para a página de Upload de Currículos (presente apenas em upload.html) ---
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

        // Funções auxiliares para Drag and Drop (declaradas dentro do if para escopo local)
        function preventDefaults(e) { e.preventDefault(); e.stopPropagation(); }
        function highlight() { dragDropArea.classList.add('highlight'); }
        function unhighlight() { dragDropArea.classList.remove('highlight'); }
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            arquivoInput.files = files;
            const fileNames = Array.from(arquivoInput.files).map(file => file.name).join(', ');
            alert(`Arquivo(s) solto(s): ${files.length} - ${fileNames}`);
        }

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dragDropArea.addEventListener(eventName, preventDefaults, false);
        });
        ['dragenter', 'dragover'].forEach(eventName => { dragDropArea.addEventListener(eventName, highlight, false); });
        ['dragleave', 'drop'].forEach(eventName => { dragDropArea.addEventListener(eventName, unhighlight, false); });
        dragDropArea.addEventListener('drop', handleDrop, false);

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
            if (!Array.isArray(candidatesToRender) || candidatesToRender.length === 0) { // Adicionado verificação de array
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
            document.querySelectorAll('.btn-add').forEach(button => { // Usar document.querySelectorAll aqui
                button.addEventListener('click', (event) => {
                    // Pega o ID e o nome do candidato mais próximo
                    const candidateItemElement = event.target.closest('.candidate-item');
                    const candidateId = candidateItemElement.querySelector('.btn-ver-detalhes').dataset.id;
                    const candidateName = candidateItemElement.querySelector('.candidate-name').innerText;
                    
                    // Redireciona para a página de agendamento de entrevista
                    window.location.href = `/agendar_entrevista_page?id=${candidateId}&name=${encodeURIComponent(candidateName)}`; // Use agendar_entrevista_page
                    
                    // Ou, para integração futura (se for API):
                    /*
                    fetch(`/adicionar_contato/${candidateId}`, { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                    })
                    .catch(error => {
                        console.error('Erro ao adicionar contato:', error);
                        alert('Erro ao adicionar contato.');
                    });
                    */
                });
            });
        }

        function filterAndSortCandidates() {
            let filtered = Array.isArray(realCandidates) ? [...realCandidates] : []; // Garante que é um array

            const searchTerm = searchCandidate && searchCandidate.value ? searchCandidate.value.toLowerCase() : ''; // Adicionado verificação
            if (searchTerm) {
                filtered = filtered.filter(candidate =>
                    (candidate.nome && candidate.nome.toLowerCase().includes(searchTerm))
                );
            }

            const sortValue = sortOrder && sortOrder.value ? sortOrder.value : 'pontuacao_desc'; // Adicionado verificação
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

        // Event Listeners para busca e ordenação (dentro deste if)
        if (searchCandidate) { // Adicionado verificação
            searchCandidate.addEventListener('input', filterAndSortCandidates);
        }
        if (sortOrder) { // Adicionado verificação
            sortOrder.addEventListener('change', filterAndSortCandidates);
        }
        filterAndSortCandidates(); // Renderiza na carga da página (chamada inicial DENTRO deste if)

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
    let candidateDataDetailsPage = {}; // Renomeado para evitar conflito com 'candidateData' global, se houver

    // Verifica se estamos na página de detalhes E se a variável global de detalhes existe
    if (dynamicCandidateNameSpan && window.FLASK_CANDIDATE_DETAILS_DATA) {
        candidateDataDetailsPage = window.FLASK_CANDIDATE_DETAILS_DATA; // Pega os dados da global

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

        if (candidateDataDetailsPage) { // Usa a variável renomeada
            // Preenche o título da página
            document.getElementById('candidateNameTitle').innerText = `DETALHES DO CANDIDATO: ${candidateDataDetailsPage.nome ? candidateDataDetailsPage.nome.toUpperCase() : 'NOME INDISPONÍVEL'}`;
            
            // Preenche informações de perfil
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


            // Pontuação
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
                if (candidateDataDetailsPage.motivos_pontuacao && candidateDataDetailsPage.motivos_pontuacao.length > 0) {
                    candidateDataDetailsPage.motivos_pontuacao.forEach(reason => {
                        const li = document.createElement('li');
                        li.innerText = reason;
                        reasonsList.appendChild(li);
                    });
                } else if (candidateDataDetailsPage.motivosPontuacao && candidateDataDetailsPage.motivosPontuacao.length > 0) { // Fallback para nome antigo
                    candidateDataDetailsPage.motivosPontuacao.forEach(reason => {
                        const li = document.createElement('li');
                        li.innerText = reason;
                        reasonsList.appendChild(li);
                    });
                } else {
                    reasonsList.innerHTML = '<li>Nenhum motivo de pontuação detalhado.</li>';
                }
            }

            // Análise da IA
            const geminiAnalysisTextElement = document.getElementById('geminiAnalysisText');
            if (geminiAnalysisTextElement) {
                geminiAnalysisTextElement.innerText = candidateDataDetailsPage.analise_ia || 'N/A';
            }


            // Habilidades
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


            // Experiência
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


            // Formação
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


            // Idiomas
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
        // Pega o nome do candidato da URL ou usa um valor padrão
        const urlParams = new URLSearchParams(window.location.search);
        const candidateIdFromUrl = urlParams.get('id'); // Pega o ID da URL
        const candidateNameFromUrl = urlParams.get('name') || "Candidato Desconhecido"; // Pega o nome da URL

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
                // No futuro, enviaria os dados do agendamento para o backend
                window.location.href = "/candidatos_ranqueados"; // Redireciona após agendar
            });
        }
        if (btnCancelAgendamento) {
            btnCancelAgendamento.addEventListener('click', (event) => {
                event.preventDefault();
                alert('Agendamento cancelado!');
                // Redireciona de volta para os detalhes do candidato (se o ID estiver disponível)
                if (candidateIdFromUrl) {
                    window.location.href = `/detalhes_candidato/${candidateIdFromUrl}`;
                } else {
                    window.location.href = "/candidatos_ranqueados"; // Volta para a lista se o ID não estiver na URL
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