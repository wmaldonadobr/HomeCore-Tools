#!/usr/bin/with-contenv bashio
# ==============================================================================
# HomeCore Tools Add-on
# Script principal de inicialização
# ==============================================================================

set -e

bashio::log.info "Iniciando HomeCore Tools..."

# Carregar configurações do add-on
CONFIG_PATH=/data/options.json
LOG_LEVEL=$(bashio::config 'log_level' 'info')
CHECK_INTERVAL=$(bashio::config 'check_interval' '3600')
AUTO_UPDATE=$(bashio::config 'auto_update' 'true')
BACKUP_BEFORE_UPDATE=$(bashio::config 'backup_before_update' 'true')
NOTIFY_ON_UPDATE=$(bashio::config 'notify_on_update' 'true')

bashio::log.info "Configurações carregadas:"
bashio::log.info "  - Log Level: ${LOG_LEVEL}"
bashio::log.info "  - Check Interval: ${CHECK_INTERVAL}s"
bashio::log.info "  - Auto Update: ${AUTO_UPDATE}"
bashio::log.info "  - Backup Before Update: ${BACKUP_BEFORE_UPDATE}"
bashio::log.info "  - Notify On Update: ${NOTIFY_ON_UPDATE}"

# Verificar se o Supervisor está disponível
if ! bashio::supervisor.ping; then
    bashio::log.fatal "Supervisor não está disponível!"
    exit 1
fi

bashio::log.info "Supervisor disponível"

# Verificar se a integração HomeCore está instalada
bashio::log.info "Verificando integração HomeCore..."

# Criar diretórios necessários se não existirem
mkdir -p /data/logs
mkdir -p /data/manifests
mkdir -p /data/backups
mkdir -p /config/hc-tools/logs
mkdir -p /config/hc-tools/manifest_files

bashio::log.info "Diretórios criados/verificados"

# Exportar variáveis de ambiente para os scripts Python
export HCT_LOG_LEVEL="${LOG_LEVEL}"
export HCT_CHECK_INTERVAL="${CHECK_INTERVAL}"
export HCT_AUTO_UPDATE="${AUTO_UPDATE}"
export HCT_BACKUP_BEFORE_UPDATE="${BACKUP_BEFORE_UPDATE}"
export HCT_NOTIFY_ON_UPDATE="${NOTIFY_ON_UPDATE}"

# Daemon é iniciado automaticamente pelo S6 Overlay via services.d/hct-daemon/run
bashio::log.info "Inicialização concluída. Aguardando serviços..."

# Manter script rodando para não encerrar o add-on
while true; do
    sleep 3600
done
