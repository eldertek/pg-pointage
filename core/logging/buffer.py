import logging
import orjson  # Plus rapide que json standard
from threading import Lock
from typing import List, Dict, Optional, Any
from datetime import datetime
from queue import Queue
from io import StringIO
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import asyncio
from collections import deque

class LogBuffer:
    def __init__(self, max_size: int = 200):
        self.buffer = deque(maxlen=max_size * 2)
        self.max_size = max_size
        self._lock = threading.RLock()
        self.logger = logging.getLogger('user_actions')
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._batch_size = 200
        self._write_lock = threading.Lock()
        self._last_timestamp = None
        self._timestamp_update_interval = 5.0
        self._last_timestamp_update = 0
        self._write_buffer = StringIO()
        self._write_buffer_size = 0
        self._max_write_buffer = 4 * 1024 * 1024  # Augmenté à 4MB
        
        # Pool de dictionnaires pré-alloués
        self._message_pool = deque([
            {
                'message': None,
                'timestamp': None,
                'user_id': None,
                'username': None
            } for _ in range(max_size * 2)
        ])
        self._pool_lock = threading.Lock()
        
    def _get_message_dict(self) -> dict:
        """Récupère un dictionnaire du pool ou en crée un nouveau"""
        with self._pool_lock:
            if self._message_pool:
                return self._message_pool.popleft()
            return {
                'message': None,
                'timestamp': None,
                'user_id': None,
                'username': None
            }
            
    def _return_message_dict(self, msg_dict: dict) -> None:
        """Retourne un dictionnaire au pool après utilisation"""
        with self._pool_lock:
            if len(self._message_pool) < self.max_size * 2:
                # Réinitialise les valeurs
                for key in msg_dict:
                    msg_dict[key] = None
                self._message_pool.append(msg_dict)
        
    def _get_timestamp(self) -> str:
        """Retourne un timestamp optimisé avec mise en cache agressive"""
        current_time = time.time()
        if not self._last_timestamp or (current_time - self._last_timestamp_update) >= self._timestamp_update_interval:
            self._last_timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-4]
            self._last_timestamp_update = current_time
        return self._last_timestamp
        
    def add_message(self, message: str, user_id: int, username: str) -> None:
        """Ajoute un message au buffer avec les informations de l'utilisateur"""
        entry = self._get_message_dict()
        entry['message'] = message
        entry['timestamp'] = self._get_timestamp()
        entry['user_id'] = user_id
        entry['username'] = username
        
        with self._lock:
            self.buffer.append(entry)
            if len(self.buffer) >= self._batch_size:
                self._flush_buffer()
    
    def _flush_buffer(self) -> None:
        """Vide le buffer de manière optimisée"""
        with self._lock:
            if not self.buffer:
                return
            messages = list(self.buffer)
            self.buffer.clear()
            
        if messages:
            try:
                self._write_batch(messages)
                # Retourne les dictionnaires au pool
                for msg in messages:
                    self._return_message_dict(msg)
            except Exception as e:
                self.logger.error(f"Erreur batch: {str(e)}")
                with self._lock:
                    self.buffer.extend(messages)
    
    def _write_batch(self, batch: List[Dict]) -> None:
        """Écrit un lot de messages avec buffering optimisé"""
        try:
            # Utilise orjson pour une sérialisation plus rapide
            batch_content = StringIO()
            for msg in batch:
                batch_content.write(orjson.dumps(msg).decode('utf-8'))
                batch_content.write('\n')
            content = batch_content.getvalue()
            batch_content.close()
            
            with self._write_lock:
                self._write_buffer.write(content)
                self._write_buffer_size += len(content)
                
                # Flush si le buffer est plein ou si beaucoup de messages
                if self._write_buffer_size >= self._max_write_buffer or len(batch) >= self._batch_size:
                    content = self._write_buffer.getvalue()
                    self._write_buffer = StringIO()
                    self._write_buffer_size = 0
                    self.logger.info(content)
                    
        except Exception as e:
            self.logger.error(f"Erreur écriture: {str(e)}")
            raise
    
    def flush(self) -> None:
        """Force le vidage des buffers"""
        self._flush_buffer()
        with self._write_lock:
            if self._write_buffer_size > 0:
                content = self._write_buffer.getvalue()
                self._write_buffer = StringIO()
                self._write_buffer_size = 0
                self.logger.info(content)
    
    def clear(self) -> None:
        """Vide les buffers"""
        with self._lock:
            # Retourne tous les messages au pool
            for msg in self.buffer:
                self._return_message_dict(msg)
            self.buffer.clear()
        with self._write_lock:
            self._write_buffer = StringIO()
            self._write_buffer_size = 0
            
    def get_size(self) -> int:
        """Retourne la taille du buffer de messages"""
        with self._lock:
            return len(self.buffer)
            
    def __del__(self):
        """Nettoyage des ressources"""
        try:
            self.flush()
            self._executor.shutdown(wait=True)
        except:
            pass 