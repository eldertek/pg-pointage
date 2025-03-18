import logging
import os
import json
from typing import Optional, Dict, Any
import re
from datetime import datetime

class UserActionFileHandler(logging.FileHandler):
    def __init__(self, filename: str, mode: str = 'a', encoding: Optional[str] = None):
        # Création du dossier des logs s'il n'existe pas
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        super().__init__(filename, mode, encoding=encoding or 'utf-8')
        
        # Nombre max de tentatives de réécriture en cas d'erreur
        self.max_retries = 3
        
        # Taille maximale d'un message
        self.max_message_length = 1000
        
        # Caractères autorisés dans les messages (inclut les caractères spéciaux)
        self.valid_chars_pattern = re.compile(r'^[a-zA-Z0-9\s\-_.,;:!?@#€$%&*()\[\]{}+=<>éèêëàâäôöûüç\'\"]+$')
        
    def emit(self, record: logging.LogRecord) -> None:
        if not record.msg:
            return
            
        try:
            # Si le message est une chaîne JSON, on le parse
            if isinstance(record.msg, str):
                messages = record.msg.strip().split('\n')
                for msg in messages:
                    if msg:
                        try:
                            log_entry = json.loads(msg)
                            self._write_log_entry(log_entry)
                        except json.JSONDecodeError:
                            # Si ce n'est pas du JSON, on écrit le message tel quel
                            self._write_message(msg)
            else:
                self._write_message(str(record.msg))
                
        except Exception as e:
            self.handleError(record)
            
    def _write_log_entry(self, log_entry: Dict[str, Any]) -> None:
        # Validation et nettoyage des données
        message = log_entry.get('message', '')
        if not message:
            return
            
        # Vérification de la taille
        if len(message) > self.max_message_length:
            message = message[:self.max_message_length] + '...'
            
        # Nettoyage des caractères non autorisés tout en préservant les caractères spéciaux
        if not self.valid_chars_pattern.match(message):
            message = ''.join(c for c in message if self.valid_chars_pattern.match(c) or c.isspace())
            
        # Ajout d'un timestamp si non présent
        if 'timestamp' not in log_entry:
            log_entry['timestamp'] = datetime.now().isoformat()
            
        # Écriture avec retry
        for attempt in range(self.max_retries):
            try:
                self.stream.write(json.dumps(log_entry) + self.terminator)
                self.flush()
                break
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e
                continue
                
    def _write_message(self, message: str) -> None:
        # Validation et nettoyage du message simple
        if len(message) > self.max_message_length:
            message = message[:self.max_message_length] + '...'
            
        if not self.valid_chars_pattern.match(message):
            message = ''.join(c for c in message if self.valid_chars_pattern.match(c) or c.isspace())
            
        # Écriture avec retry
        for attempt in range(self.max_retries):
            try:
                self.stream.write(message + self.terminator)
                self.flush()
                break
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e
                continue 