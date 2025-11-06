#!/usr/bin/env python3
"""
HomeCore Tools - Sistema de Atualização
Gerenciamento de atualizações automáticas via manifests
"""

import os
import sys
import json
import shutil
import hashlib
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# Importar logger
sys.path.insert(0, '/usr/bin')
from hct_logger import get_logger

logger = get_logger("hct-updater")


class HCTUpdater:
    """Sistema de atualização automática para HomeCore Tools."""
    
    def __init__(self, token: str):
        self.token = token
        self.api_base = "https://homecore.com.br/api"
        self.config_dir = Path(os.environ.get('HCT_CONFIG_DIR', '/config'))
        self.data_dir = Path(os.environ.get('HCT_DATA_DIR', '/data'))
        self.manifests_dir = self.data_dir / 'manifests'
        self.backups_dir = self.data_dir / 'backups'
        self.max_retries = 3
        self.retry_delay = 5
        
        # Criar diretórios
        self.manifests_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_remote_manifest(self, manifest_type: str) -> Optional[Dict[str, Any]]:
        """Busca manifest remoto da API."""
        url = f"{self.api_base}/manifests/{self.token}/{manifest_type}_manifest.json"
        
        logger.info("hct-updater", "fetch_manifest", f"Buscando manifest {manifest_type}", {
            "url": url,
            "type": manifest_type
        })
        
        try:
            request = Request(url)
            request.add_header('User-Agent', 'HomeCore-Tools/1.0')
            
            with urlopen(request, timeout=30) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    
                    # Salvar cache local
                    cache_file = self.manifests_dir / f"{manifest_type}_manifest.json"
                    with open(cache_file, 'w') as f:
                        json.dump(data, f, indent=2)
                    
                    logger.success("hct-updater", "fetch_manifest", f"Manifest {manifest_type} obtido", {
                        "version": data.get('version'),
                        "name": data.get('name')
                    })
                    
                    return data
                else:
                    logger.warning("hct-updater", "fetch_manifest", f"HTTP {response.status}", {
                        "type": manifest_type
                    })
                    return None
        
        except HTTPError as e:
            if e.code == 404:
                logger.info("hct-updater", "fetch_manifest", f"Manifest {manifest_type} não disponível")
            else:
                logger.error("hct-updater", "fetch_manifest", f"Erro HTTP {e.code}", exception=e)
            return None
        
        except (URLError, Exception) as e:
            logger.error("hct-updater", "fetch_manifest", "Erro ao buscar manifest", exception=e)
            return None
    
    def load_local_manifest(self, manifest_type: str) -> Optional[Dict[str, Any]]:
        """Carrega manifest local instalado."""
        manifest_file = self.config_dir / 'hc-tools' / 'manifest_files' / f"{manifest_type}_manifest.json"
        
        if not manifest_file.exists():
            logger.debug("hct-updater", "load_local_manifest", f"Manifest local {manifest_type} não encontrado")
            return None
        
        try:
            with open(manifest_file, 'r') as f:
                data = json.load(f)
            
            logger.debug("hct-updater", "load_local_manifest", f"Manifest local {manifest_type} carregado", {
                "version": data.get('version')
            })
            
            return data
        
        except Exception as e:
            logger.error("hct-updater", "load_local_manifest", "Erro ao ler manifest local", exception=e)
            return None
    
    def compare_versions(self, local_version: str, remote_version: str) -> bool:
        """Compara versões (retorna True se remote > local)."""
        try:
            # Versão simples: comparação de strings
            # TODO: Implementar comparação semântica (SemVer)
            return remote_version != local_version
        except Exception:
            return False
    
    def check_updates(self) -> list:
        """Verifica atualizações disponíveis para todos os manifests."""
        manifest_types = ['core', 'hcc', 'molsmart']
        updates = []
        
        logger.info("hct-updater", "check_updates", "Verificando atualizações disponíveis")
        
        for manifest_type in manifest_types:
            remote = self.fetch_remote_manifest(manifest_type)
            if not remote:
                continue
            
            local = self.load_local_manifest(manifest_type)
            local_version = local.get('version', '0.0.0') if local else '0.0.0'
            remote_version = remote.get('version', '0.0.0')
            
            if self.compare_versions(local_version, remote_version):
                update_info = {
                    'type': manifest_type,
                    'current': local_version,
                    'available': remote_version,
                    'manifest': remote
                }
                updates.append(update_info)
                
                logger.info("hct-updater", "check_updates", f"Atualização disponível: {manifest_type}", {
                    "current": local_version,
                    "available": remote_version
                })
        
        if not updates:
            logger.info("hct-updater", "check_updates", "Nenhuma atualização disponível")
        
        return updates
    
    def create_backup(self) -> Optional[Path]:
        """Cria backup antes da atualização."""
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        backup_dir = self.backups_dir / f"hc-tools_backup_{timestamp}"
        
        logger.info("hct-updater", "create_backup", "Criando backup", {
            "backup_dir": str(backup_dir)
        })
        
        try:
            # Backup do diretório hc-tools
            source_dir = self.config_dir / 'hc-tools'
            if source_dir.exists():
                shutil.copytree(source_dir, backup_dir)
            
            # Backup de arquivos sensíveis
            sensitive_files = ['configuration.yaml', 'automations.yaml', 'scripts.yaml', 'scenes.yaml']
            for filename in sensitive_files:
                source_file = self.config_dir / filename
                if source_file.exists():
                    shutil.copy2(source_file, backup_dir / filename)
            
            logger.success("hct-updater", "create_backup", "Backup criado com sucesso", {
                "backup_dir": str(backup_dir)
            })
            
            return backup_dir
        
        except Exception as e:
            logger.error("hct-updater", "create_backup", "Erro ao criar backup", exception=e)
            return None
    
    def download_package(self, manifest: Dict[str, Any]) -> Optional[Path]:
        """Baixa pacote de atualização."""
        manifest_type = manifest.get('name', 'unknown')
        download_url = manifest.get('download_url', f"{self.api_base}/hcc_update.php")
        
        # Adicionar client_id à URL
        if '?' in download_url:
            download_url += f"&client_id={self.token}"
        else:
            download_url += f"?client_id={self.token}"
        
        logger.info("hct-updater", "download_package", f"Baixando pacote {manifest_type}", {
            "url": download_url
        })
        
        # Criar arquivo temporário
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_path = Path(temp_file.name)
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug("hct-updater", "download_package", f"Tentativa {attempt}/{self.max_retries}")
                
                request = Request(download_url)
                request.add_header('User-Agent', 'HomeCore-Tools/1.0')
                
                with urlopen(request, timeout=300) as response:
                    if response.status == 200:
                        with open(temp_path, 'wb') as f:
                            f.write(response.read())
                        
                        # Verificar se arquivo não está vazio
                        if temp_path.stat().st_size == 0:
                            logger.error("hct-updater", "download_package", "Arquivo baixado está vazio")
                            continue
                        
                        logger.success("hct-updater", "download_package", "Download concluído", {
                            "size": temp_path.stat().st_size,
                            "attempt": attempt
                        })
                        
                        return temp_path
                
            except Exception as e:
                logger.warning("hct-updater", "download_package", f"Falha na tentativa {attempt}", exception=e)
                
                if attempt < self.max_retries:
                    import time
                    time.sleep(self.retry_delay)
        
        # Limpar arquivo temporário em caso de falha
        if temp_path.exists():
            temp_path.unlink()
        
        logger.error("hct-updater", "download_package", "Falha no download após todas as tentativas")
        return None
    
    def verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """Verifica checksum do arquivo."""
        if not expected_checksum:
            logger.warning("hct-updater", "verify_checksum", "Checksum não fornecido, pulando verificação")
            return True
        
        logger.info("hct-updater", "verify_checksum", "Verificando integridade do arquivo")
        
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            calculated = sha256_hash.hexdigest()
            expected = expected_checksum.replace('sha256:', '')
            
            if calculated == expected:
                logger.success("hct-updater", "verify_checksum", "Checksum válido")
                return True
            else:
                logger.error("hct-updater", "verify_checksum", "Checksum inválido", {
                    "expected": expected,
                    "calculated": calculated
                })
                return False
        
        except Exception as e:
            logger.error("hct-updater", "verify_checksum", "Erro ao verificar checksum", exception=e)
            return False
    
    def apply_update(self, package_path: Path, manifest: Dict[str, Any]) -> bool:
        """Aplica atualização extraindo e copiando arquivos."""
        logger.info("hct-updater", "apply_update", "Aplicando atualização")
        
        temp_dir = None
        try:
            # Criar diretório temporário para extração
            temp_dir = Path(tempfile.mkdtemp(prefix='hct_extract_'))
            
            # Extrair ZIP
            logger.debug("hct-updater", "apply_update", "Extraindo pacote")
            result = subprocess.run(
                ['unzip', '-oq', str(package_path), '-d', str(temp_dir)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error("hct-updater", "apply_update", "Erro ao extrair pacote", {
                    "stderr": result.stderr
                })
                return False
            
            # Detectar diretório raiz (se houver)
            extracted_items = list(temp_dir.iterdir())
            if len(extracted_items) == 1 and extracted_items[0].is_dir():
                staging_dir = extracted_items[0]
                logger.debug("hct-updater", "apply_update", "Diretório raiz detectado", {
                    "staging_dir": str(staging_dir)
                })
            else:
                staging_dir = temp_dir
            
            # Copiar arquivos para /config
            logger.info("hct-updater", "apply_update", "Copiando arquivos para /config")
            
            result = subprocess.run(
                ['cp', '-r', f"{staging_dir}/.", str(self.config_dir)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error("hct-updater", "apply_update", "Erro ao copiar arquivos", {
                    "stderr": result.stderr
                })
                return False
            
            # Atualizar manifest local
            manifest_type = manifest.get('name', 'unknown').lower().replace(' ', '_')
            local_manifest_file = self.config_dir / 'hc-tools' / 'manifest_files' / f"{manifest_type}_manifest.json"
            local_manifest_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(local_manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            logger.success("hct-updater", "apply_update", "Atualização aplicada com sucesso", {
                "version": manifest.get('version')
            })
            
            return True
        
        except Exception as e:
            logger.error("hct-updater", "apply_update", "Erro ao aplicar atualização", exception=e)
            return False
        
        finally:
            # Limpar diretório temporário
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def rollback(self, backup_dir: Path) -> bool:
        """Restaura backup em caso de falha."""
        logger.warning("hct-updater", "rollback", "Iniciando rollback", {
            "backup_dir": str(backup_dir)
        })
        
        try:
            # Restaurar hc-tools
            target_dir = self.config_dir / 'hc-tools'
            if target_dir.exists():
                shutil.rmtree(target_dir)
            
            shutil.copytree(backup_dir, target_dir)
            
            # Restaurar arquivos sensíveis
            for item in backup_dir.iterdir():
                if item.is_file() and item.suffix == '.yaml':
                    shutil.copy2(item, self.config_dir / item.name)
            
            logger.success("hct-updater", "rollback", "Rollback concluído com sucesso")
            return True
        
        except Exception as e:
            logger.error("hct-updater", "rollback", "Erro ao fazer rollback", exception=e)
            return False
    
    def update(self, update_info: Dict[str, Any]) -> bool:
        """Executa processo completo de atualização."""
        manifest = update_info['manifest']
        manifest_type = update_info['type']
        
        logger.info("hct-updater", "update", f"Iniciando atualização: {manifest_type}", {
            "current": update_info['current'],
            "target": update_info['available']
        })
        
        backup_dir = None
        package_path = None
        
        try:
            # 1. Criar backup
            if os.environ.get('HCT_BACKUP_BEFORE_UPDATE', 'true').lower() == 'true':
                backup_dir = self.create_backup()
                if not backup_dir:
                    logger.error("hct-updater", "update", "Falha ao criar backup, abortando")
                    return False
            
            # 2. Baixar pacote
            package_path = self.download_package(manifest)
            if not package_path:
                logger.error("hct-updater", "update", "Falha no download, abortando")
                return False
            
            # 3. Verificar checksum (se disponível)
            checksum = manifest.get('checksum')
            if checksum and not self.verify_checksum(package_path, checksum):
                logger.error("hct-updater", "update", "Checksum inválido, abortando")
                return False
            
            # 4. Aplicar atualização
            if not self.apply_update(package_path, manifest):
                logger.error("hct-updater", "update", "Falha ao aplicar atualização")
                
                # Rollback se backup disponível
                if backup_dir:
                    self.rollback(backup_dir)
                
                return False
            
            logger.success("hct-updater", "update", f"Atualização {manifest_type} concluída com sucesso", {
                "version": update_info['available']
            })
            
            return True
        
        except Exception as e:
            logger.error("hct-updater", "update", "Erro durante atualização", exception=e)
            
            # Rollback se backup disponível
            if backup_dir:
                self.rollback(backup_dir)
            
            return False
        
        finally:
            # Limpar arquivo temporário
            if package_path and package_path.exists():
                package_path.unlink()


if __name__ == "__main__":
    # Teste do updater
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: hct-updater.py <token>")
        sys.exit(1)
    
    token = sys.argv[1]
    updater = HCTUpdater(token)
    
    # Verificar atualizações
    updates = updater.check_updates()
    
    if updates:
        print(f"\n{len(updates)} atualização(ões) disponível(is):")
        for update in updates:
            print(f"  - {update['type']}: {update['current']} -> {update['available']}")
    else:
        print("\nNenhuma atualização disponível")
