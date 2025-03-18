describe('ClientLogger', () => {
    let originalFetch;
    let mockFetch;

    beforeEach(() => {
        // Sauvegarder fetch original
        originalFetch = window.fetch;
        // Mock de fetch
        mockFetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ status: 'success' })
        }));
        window.fetch = mockFetch;

        // Reset de la console
        console.log = jest.fn();
        console.error = jest.fn();
        console.warn = jest.fn();
        console.debug = jest.fn();

        // Configuration initiale
        ClientLogger.config.enabled = true;
        ClientLogger.config.logToConsole = true;
        ClientLogger.config.logToServer = true;
    });

    afterEach(() => {
        // Restaurer fetch original
        window.fetch = originalFetch;
    });

    describe('Configuration', () => {
        test('devrait avoir une configuration par défaut', () => {
            expect(ClientLogger.config).toBeDefined();
            expect(ClientLogger.config.enabled).toBe(true);
            expect(ClientLogger.config.logToConsole).toBe(true);
            expect(ClientLogger.config.logToServer).toBe(true);
            expect(ClientLogger.config.serverEndpoint).toBe('/api/logs/');
            expect(ClientLogger.config.minLevel).toBe('info');
        });
    });

    describe('Méthodes de logging', () => {
        test('devrait logger un message info', () => {
            ClientLogger.info('test message');
            expect(console.log).toHaveBeenCalled();
            expect(mockFetch).toHaveBeenCalled();
        });

        test('devrait logger une erreur', () => {
            ClientLogger.error('test error');
            expect(console.error).toHaveBeenCalled();
            expect(mockFetch).toHaveBeenCalled();
        });

        test('devrait logger un warning', () => {
            ClientLogger.warning('test warning');
            expect(console.warn).toHaveBeenCalled();
            expect(mockFetch).toHaveBeenCalled();
        });

        test('devrait logger un message debug', () => {
            ClientLogger.debug('test debug');
            expect(console.debug).toHaveBeenCalled();
            // Ne devrait pas envoyer au serveur par défaut (minLevel: 'info')
            expect(mockFetch).not.toHaveBeenCalled();
        });
    });

    describe('Formatage des messages', () => {
        test('devrait formater correctement un message', () => {
            const message = 'test message';
            const extra = { key: 'value' };
            const formatted = ClientLogger.formatMessage('info', message, extra);

            expect(formatted).toHaveProperty('timestamp');
            expect(formatted).toHaveProperty('level', 'info');
            expect(formatted).toHaveProperty('message', message);
            expect(formatted).toHaveProperty('extra', extra);
            expect(formatted).toHaveProperty('url');
            expect(formatted).toHaveProperty('userAgent');
        });
    });

    describe('Envoi au serveur', () => {
        test('devrait envoyer au serveur avec le bon format', async () => {
            const logData = {
                level: 'info',
                message: 'test message'
            };

            await ClientLogger.sendToServer(logData);

            expect(mockFetch).toHaveBeenCalledWith(
                ClientLogger.config.serverEndpoint,
                expect.objectContaining({
                    method: 'POST',
                    headers: expect.objectContaining({
                        'Content-Type': 'application/json'
                    }),
                    body: JSON.stringify(logData)
                })
            );
        });

        test('ne devrait pas envoyer si logToServer est désactivé', async () => {
            ClientLogger.config.logToServer = false;
            await ClientLogger.info('test message');
            expect(mockFetch).not.toHaveBeenCalled();
        });
    });

    describe('Capture d\'erreurs', () => {
        test('devrait capturer les erreurs non gérées', () => {
            const errorEvent = new ErrorEvent('error', {
                error: new Error('test error'),
                message: 'test error message',
                filename: 'test.js',
                lineno: 1,
                colno: 1
            });

            window.dispatchEvent(errorEvent);

            expect(console.error).toHaveBeenCalled();
            expect(mockFetch).toHaveBeenCalled();
        });

        test('devrait capturer les rejets de promesse non gérés', () => {
            const promiseRejectionEvent = new PromiseRejectionEvent('unhandledrejection', {
                reason: new Error('test rejection'),
                promise: Promise.reject(new Error('test rejection'))
            });

            window.dispatchEvent(promiseRejectionEvent);

            expect(console.error).toHaveBeenCalled();
            expect(mockFetch).toHaveBeenCalled();
        });
    });
}); 