#!/usr/bin/env python3
"""
HomeCore Tools - Daemon Principal
Orquestra verificações periódicas, atualizações e API web
"""

import os
import sys
import json
import time
import asyncio
import signal
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import URLError

# Importar módulos HCT
sys.path.insert(0, '/usr/bin')
from hct_logger import get_logger
from hct_updater import HCTUpdater

logger = get_logger("hct-daemon")


class HCTDaemon:
    """Daemon principal do HomeCore Tools."""
    
    def __init__(self):
        self.running = True
        self.token: Optional[str] = None
        self.updater: Optional[HCTUpdater] = None
        
        # Configurações do add-on
        self.log_level = os.environ.get('HCT_LOG_LEVEL', 'INFO')
        self.check_interval = int(os.environ.get('HCT_CHECK_INTERVAL', '3600'))
        self.auto_update = os.environ.get('HCT_AUTO_UPDATE', 'true').lower() == 'true'
        self.backup_before_update = os.environ.get('HCT_BACKUP_BEFORE_UPDATE', 'true').lower() == 'true'
        self.notify_on_update = os.environ.get('HCT_NOTIFY_ON_UPDATE', 'true').lower() == 'true'
        
        # Supervisor token
        self.supervisor_token = os.environ.get('SUPERVISOR_TOKEN')
        
        # Registrar handlers de sinal
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)
    
    def handle_shutdown(self, signum, frame):
        """Handler para sinais de shutdown."""
        logger.info("hct-daemon", "shutdown", "Recebido sinal de shutdown")
        self.running = False
    
    def get_homecore_token(self) -> Optional[str]:
        """Obtém token da integração HomeCore via Supervisor API."""
        if not self.supervisor_token:
            logger.error("hct-daemon", "get_token", "SUPERVISOR_TOKEN não disponível")
            return None
        
        logger.info("hct-daemon", "get_token", "Obtendo token da integração HomeCore")
        
        try:
            url = "http://supervisor/core/api/config_entries"
            request = Request(url)
            request.add_header('Authorization', f'Bearer {self.supervisor_token}')
            request.add_header('Content-Type', 'application/json')
            
            with urlopen(request, timeout=30) as response:
                if response.status == 200:
                    entries = json.loads(response.read().decode('utf-8'))
                    
                    # Procurar integração homecore
                    for entry in entries:
                        if entry.get('domain') == 'homecore':
                            token = entry.get('data', {}).get('token')
                            if token:
                                logger.success("hct-daemon", "get_token", "Token obtido com sucesso")
                                return token
                    
                    logger.warning("hct-daemon", "get_token", "Integração HomeCore não encontrada")
                    return None
                else:
                    logger.error("hct-daemon", "get_token", f"HTTP {response.status}")
                    return None
        
        except Exception as e:
            logger.error("hct-daemon", "get_token", "Erro ao obter token", exception=e)
            return None
    
    def send_notification(self, title: str, message: str, notification_id: str = None):
        """Envia notificação persistente para o Home Assistant."""
        if not self.notify_on_update:
            return
        
        if not self.supervisor_token:
            logger.warning("hct-daemon", "send_notification", "SUPERVISOR_TOKEN não disponível")
            return
        
        logger.info("hct-daemon", "send_notification", f"Enviando notificação: {title}")
        
        try:
            url = "http://supervisor/core/api/services/persistent_notification/create"
            request = Request(url, method='POST')
            request.add_header('Authorization', f'Bearer {self.supervisor_token}')
            request.add_header('Content-Type', 'application/json')
            
            data = {
                "title": title,
                "message": message
            }
            
            if notification_id:
                data["notification_id"] = notification_id
            
            request.data = json.dumps(data).encode('utf-8')
            
            with urlopen(request, timeout=10) as response:
                if response.status in [200, 201]:
                    logger.success("hct-daemon", "send_notification", "Notificação enviada")
                else:
                    logger.warning("hct-daemon", "send_notification", f"HTTP {response.status}")
        
        except Exception as e:
            logger.error("hct-daemon", "send_notification", "Erro ao enviar notificação", exception=e)
    
    def check_and_update(self):
        """Verifica e aplica atualizações se disponíveis."""
        if not self.updater:
            logger.warning("hct-daemon", "check_and_update", "Updater não inicializado")
            return
        
        logger.info("hct-daemon", "check_and_update", "Verificando atualizações")
        
        try:
            # Verificar atualizações disponíveis
            updates = self.updater.check_updates()
            
            if not updates:
                logger.info("hct-daemon", "check_and_update", "Nenhuma atualização disponível")
                return
            
            # Notificar sobre atualizações disponíveis
            update_list = "\n".join([
                f"- {u['type']}: {u['current']} → {u['available']}"
                for u in updates
            ])
            
            self.send_notification(
                "Atualizações HomeCore Disponíveis",
                f"Foram encontradas {len(updates)} atualização(ões):\n\n{update_list}",
                "homecore_updates_available"
            )
            
            # Aplicar atualizações se auto_update estiver habilitado
            if self.auto_update:
                logger.info("hct-daemon", "check_and_update", f"Aplicando {len(updates)} atualização(ões)")
                
                success_count = 0
                failed_updates = []
                
                for update in updates:
                    logger.info("hct-daemon", "check_and_update", f"Atualizando {update['type']}")
                    
                    if self.updater.update(update):
                        success_count += 1
                    else:
                        failed_updates.append(update['type'])
                
                # Notificar resultado
                if success_count > 0:
                    message = f"{success_count} atualização(ões) aplicada(s) com sucesso."
                    
                    if failed_updates:
                        message += f"\n\nFalhas: {', '.join(failed_updates)}"
                    
                    message += "\n\n⚠️ Reinicie o Home Assistant para aplicar as configurações."
                    
                    self.send_notification(
                        "Atualizações HomeCore Aplicadas",
                        message,
                        "homecore_updates_applied"
                    )
                
                logger.success("hct-daemon", "check_and_update", "Processo de atualização concluído", {
                    "success": success_count,
                    "failed": len(failed_updates)
                })
            else:
                logger.info("hct-daemon", "check_and_update", "Auto-update desabilitado, atualizações não aplicadas")
        
        except Exception as e:
            logger.error("hct-daemon", "check_and_update", "Erro durante verificação/atualização", exception=e)
    
    def run(self):
        """Loop principal do daemon."""
        logger.info("hct-daemon", "startup", "HomeCore Tools Daemon iniciado", {
            "log_level": self.log_level,
            "check_interval": self.check_interval,
            "auto_update": self.auto_update
        })
        
        # Obter token da integração
        self.token = self.get_homecore_token()
        
        if not self.token:
            logger.error("hct-daemon", "startup", "Não foi possível obter token da integração HomeCore")
            logger.error("hct-daemon", "startup", "Certifique-se de que a integração HomeCore está instalada e configurada")
            
            self.send_notification(
                "HomeCore Tools - Erro",
                "Não foi possível obter token da integração HomeCore. "
                "Certifique-se de que a integração está instalada e configurada.",
                "homecore_tools_error"
            )
            
            # Aguardar um tempo antes de tentar novamente
            time.sleep(300)  # 5 minutos
            
            # Tentar novamente
            self.token = self.get_homecore_token()
            
            if not self.token:
                logger.error("hct-daemon", "startup", "Falha ao obter token após retry, encerrando")
                return
        
        # Inicializar updater
        self.updater = HCTUpdater(self.token)
        logger.info("hct-daemon", "startup", "Updater inicializado")
        
        # Enviar notificação de inicialização
        self.send_notification(
            "HomeCore Tools Iniciado",
            f"O sistema de atualização automática está ativo.\n\n"
            f"Verificações a cada {self.check_interval // 60} minutos.\n"
            f"Auto-update: {'Habilitado' if self.auto_update else 'Desabilitado'}",
            "homecore_tools_started"
        )
        
        # Primeira verificação imediata
        logger.info("hct-daemon", "startup", "Executando verificação inicial")
        self.check_and_update()
        
        # Loop principal
        last_check = time.time()
        
        while self.running:
            try:
                # Verificar se é hora de checar atualizações
                current_time = time.time()
                
                if current_time - last_check >= self.check_interval:
                    self.check_and_update()
                    last_check = current_time
                
                # Aguardar um pouco antes do próximo ciclo
                time.sleep(60)  # Verificar a cada minuto se é hora de atualizar
            
            except Exception as e:
                logger.error("hct-daemon", "main_loop", "Erro no loop principal", exception=e)
                time.sleep(60)
        
        logger.info("hct-daemon", "shutdown", "Daemon encerrado")


def main():
    """Função principal."""
    daemon = HCTDaemon()
    
    try:
        daemon.run()
    except KeyboardInterrupt:
        logger.info("hct-daemon", "main", "Interrompido pelo usuário")
    except Exception as e:
        logger.error("hct-daemon", "main", "Erro fatal", exception=e)
        sys.exit(1)


if __name__ == "__main__":
    main()
