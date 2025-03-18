document.addEventListener('DOMContentLoaded', function() {
    // Fonction pour appliquer le thème sombre
    function applyDarkTheme() {
        document.body.classList.add('dark-theme');
        localStorage.setItem('theme', 'dark');
    }

    // Fonction pour appliquer le thème clair
    function applyLightTheme() {
        document.body.classList.remove('dark-theme');
        localStorage.setItem('theme', 'light');
    }

    // Initialisation du thème
    const savedTheme = localStorage.getItem('theme') || 'dark';
    if (savedTheme === 'dark') {
        applyDarkTheme();
    }

    // Ajout du bouton de changement de thème
    const userTools = document.getElementById('user-tools');
    if (userTools) {
        const themeToggle = document.createElement('button');
        themeToggle.id = 'theme-toggle';
        themeToggle.className = 'theme-toggle';
        themeToggle.innerHTML = savedTheme === 'dark' ? '☀️' : '🌙';
        
        themeToggle.addEventListener('click', function() {
            if (document.body.classList.contains('dark-theme')) {
                applyLightTheme();
                this.innerHTML = '🌙';
            } else {
                applyDarkTheme();
                this.innerHTML = '☀️';
            }
        });
        
        userTools.appendChild(themeToggle);
    }

    // Amélioration des formulaires
    const formRows = document.querySelectorAll('.form-row');
    formRows.forEach(row => {
        const label = row.querySelector('label');
        const help = row.querySelector('.help');
        if (label && help) {
            label.title = help.textContent;
        }
    });

    // Amélioration des tableaux de résultats
    const resultList = document.getElementById('result_list');
    if (resultList) {
        const tbody = resultList.querySelector('tbody');
        if (tbody) {
            tbody.querySelectorAll('tr').forEach(row => {
                row.addEventListener('click', function(e) {
                    if (!e.target.closest('a') && !e.target.closest('input')) {
                        const link = this.querySelector('th a, td a');
                        if (link) {
                            link.click();
                        }
                    }
                });
            });
        }
    }

    // Gestion des messages
    const messages = document.querySelectorAll('.messagelist li');
    messages.forEach(message => {
        message.addEventListener('click', function() {
            this.style.opacity = '0';
            setTimeout(() => this.remove(), 300);
        });
    });
}); 