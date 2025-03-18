// Configuration du logging côté client
const ClientLogger = {
    // Niveaux de log
    LEVELS: {
        DEBUG: 'debug',
        INFO: 'info',
        WARNING: 'warning',
        ERROR: 'error'
    },

    // Configuration
    config: {
        enabled: true,
        logToConsole: true,
        logToServer: true,
        serverEndpoint: '/api/logs/',
        minLevel: 'info'
    },

    // Formater un message de log
    formatMessage: function(level, message, extra = null) {
        const logData = {
            timestamp: new Date().toISOString(),
            level: level,
            message: message,
            url: window.location.href,
            userAgent: navigator.userAgent
        };

        if (extra) {
            logData.extra = extra;
        }

        return logData;
    },

    // Envoyer un log au serveur
    sendToServer: async function(logData) {
        if (!this.config.logToServer) return;

        try {
            const response = await fetch(this.config.serverEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(logData)
            });

            if (!response.ok) {
                console.error('Erreur lors de l\'envoi du log au serveur:', response.statusText);
            }
        } catch (error) {
            console.error('Erreur lors de l\'envoi du log:', error);
        }
    },

    // Récupérer le token CSRF
    getCSRFToken: function() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    },

    // Méthodes de logging
    debug: function(message, extra = null) {
        this.log(this.LEVELS.DEBUG, message, extra);
    },

    info: function(message, extra = null) {
        this.log(this.LEVELS.INFO, message, extra);
    },

    warning: function(message, extra = null) {
        this.log(this.LEVELS.WARNING, message, extra);
    },

    error: function(message, extra = null) {
        this.log(this.LEVELS.ERROR, message, extra);
    },

    // Méthode principale de logging
    log: function(level, message, extra = null) {
        if (!this.config.enabled) return;

        const logData = this.formatMessage(level, message, extra);

        // Log dans la console si activé
        if (this.config.logToConsole) {
            const consoleMethod = level === 'error' ? 'error' : 
                                level === 'warning' ? 'warn' : 
                                level === 'debug' ? 'debug' : 'log';
            console[consoleMethod](`[${level.toUpperCase()}]`, message, extra || '');
        }

        // Envoi au serveur si niveau suffisant
        if (this.shouldLogToServer(level)) {
            this.sendToServer(logData);
        }
    },

    // Vérifier si le niveau de log justifie l'envoi au serveur
    shouldLogToServer: function(level) {
        const levels = ['debug', 'info', 'warning', 'error'];
        const minLevelIndex = levels.indexOf(this.config.minLevel);
        const currentLevelIndex = levels.indexOf(level);
        return currentLevelIndex >= minLevelIndex;
    },

    // Capture automatique des erreurs non gérées
    setupErrorCapture: function() {
        window.addEventListener('error', (event) => {
            this.error('Erreur JavaScript non gérée', {
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                stack: event.error?.stack
            });
        });

        window.addEventListener('unhandledrejection', (event) => {
            this.error('Promesse rejetée non gérée', {
                reason: event.reason?.toString(),
                stack: event.reason?.stack
            });
        });
    }
};

// Initialisation de la capture d'erreurs
ClientLogger.setupErrorCapture();

// Export pour utilisation dans d'autres fichiers
window.ClientLogger = ClientLogger; 