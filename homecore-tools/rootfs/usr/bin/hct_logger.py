#!/usr/bin/env python3
"""
HomeCore Tools - Sistema de Logs
Gerenciamento de logs estruturados em JSON com rotação automática
"""

import os
import json
import sys
import logging
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler


class HCTLogger:
    """Sistema de logs estruturados para HomeCore Tools."""
    
    def __init__(self, name: str = "hct", log_dir: str = "/data/logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar logger Python padrão
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self._get_log_level())
        
        # Handler para arquivo JSON
        json_log_file = self.log_dir / f"{name}.json.log"
        json_handler = RotatingFileHandler(
            json_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        json_handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(json_handler)
        
        # Handler para console (compatível com HA)
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(
            logging.Formatter('[%(levelname)s] %(message)s')
        )
        self.logger.addHandler(console_handler)
    
    def _get_log_level(self) -> int:
        """Obtém nível de log da variável de ambiente."""
        level_str = os.environ.get('HCT_LOG_LEVEL', 'INFO').upper()
        return getattr(logging, level_str, logging.INFO)
    
    def _create_log_entry(
        self,
        level: str,
        component: str,
        action: str,
        details: dict = None,
        status: str = "info"
    ) -> dict:
        """Cria entrada de log estruturada."""
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "component": component,
            "action": action,
            "details": details or {},
            "status": status
        }
    
    def log(
        self,
        level: str,
        component: str,
        action: str,
        message: str,
        details: dict = None,
        status: str = "info"
    ):
        """Registra log estruturado."""
        entry = self._create_log_entry(level, component, action, details, status)
        
        # Log JSON estruturado
        json_message = json.dumps(entry)
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(json_message)
        
        # Log legível para console
        console_message = f"{component} - {action}: {message}"
        if details:
            console_message += f" | {details}"
        log_method(console_message)
    
    def info(self, component: str, action: str, message: str, details: dict = None):
        """Log de informação."""
        self.log("INFO", component, action, message, details, "info")
    
    def debug(self, component: str, action: str, message: str, details: dict = None):
        """Log de debug."""
        self.log("DEBUG", component, action, message, details, "debug")
    
    def warning(self, component: str, action: str, message: str, details: dict = None):
        """Log de aviso."""
        self.log("WARNING", component, action, message, details, "warning")
    
    def error(self, component: str, action: str, message: str, details: dict = None, exception: Exception = None):
        """Log de erro."""
        if exception:
            if details is None:
                details = {}
            details["exception"] = str(exception)
            details["exception_type"] = type(exception).__name__
        self.log("ERROR", component, action, message, details, "error")
    
    def success(self, component: str, action: str, message: str, details: dict = None):
        """Log de sucesso."""
        self.log("INFO", component, action, message, details, "success")
    
    def get_recent_logs(self, limit: int = 100) -> list:
        """Obtém logs recentes."""
        json_log_file = self.log_dir / f"{self.name}.json.log"
        
        if not json_log_file.exists():
            return []
        
        logs = []
        try:
            with open(json_log_file, 'r') as f:
                for line in f:
                    try:
                        logs.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            self.error("hct-logger", "get_recent_logs", f"Erro ao ler logs: {e}")
        
        # Retornar os últimos N logs
        return logs[-limit:] if logs else []


# Singleton global
_logger_instance = None


def get_logger(name: str = "hct") -> HCTLogger:
    """Obtém instância singleton do logger."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = HCTLogger(name)
    return _logger_instance


if __name__ == "__main__":
    # Teste do logger
    logger = get_logger()
    
    logger.info("test", "startup", "Logger iniciado com sucesso")
    logger.debug("test", "config", "Configurações carregadas", {"log_level": "DEBUG"})
    logger.warning("test", "check", "Nenhuma atualização disponível")
    logger.success("test", "update", "Atualização aplicada", {"version": "1.0.0"})
    logger.error("test", "download", "Falha no download", exception=Exception("Connection timeout"))
    
    print("\n--- Logs recentes ---")
    for log in logger.get_recent_logs(limit=10):
        print(json.dumps(log, indent=2))
