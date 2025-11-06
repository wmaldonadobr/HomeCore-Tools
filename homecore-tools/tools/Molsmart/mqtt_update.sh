#!/bin/bash

# ==============================================================================
# HomeCore MQTT Server Update/Installation Script (mqtt_update.sh)
#
# Este script automatiza a instalação, configuração e inicialização do
# Mosquitto MQTT Broker no ambiente Home Assistant (HAOS) para uso com
# placas Molsmart.
#
# Funcionalidades:
# - Instalação e atualização do add-on 'core_mosquitto' via 'ha addons'.
# - Configuração automática do broker (usuário, senha, porta).
# - Verificação de status e reinício do serviço.
# - Idempotência (pode ser executado múltiplas vezes sem erro).
# - Tratamento de erros, logs detalhados e visual profissional.
# ==============================================================================

# --- Configurações e Variáveis Globais ---
SCRIPT_VERSION="1.0.0"
CONFIG_DIR="${HOMECORE_CONFIG_DIR:-/config}"
LOG_DIR="${CONFIG_DIR}/hc-tools/logs"
LOG_FILE="${LOG_DIR}/$(date +%Y%m%dT%H%M)_mqtt_update.log"
MQTT_ADDON_SLUG="core_mosquitto"
MQTT_CONFIG_DIR="${CONFIG_DIR}/mosquitto"
MQTT_USER="homeassistant"
MQTT_PASS="ha123" # Senha padrão conforme especificado no documento
MQTT_PORT="1883"

# --- Códigos de Cores ANSI (para melhor visualização no terminal) ---
COLOR_GREEN='\033[0;32m'
COLOR_RED='\033[0;31m'
COLOR_YELLOW='\033[0;33m'
COLOR_BLUE='\033[0;34m'
COLOR_CYAN='\033[0;36m'
COLOR_NC='\033[0m' # No Color

# --- Funções de Log e Saída (Reutilizadas do hcc_update.sh) ---

# Função para escrever no log e, opcionalmente, no terminal
log_message() {
    local type="$1"
    local message="$2"
    local timestamp=$(date +%Y-%m-%d\ %H:%M:%S)
    
    # Escreve no arquivo de log
    echo "[$timestamp] [$type] $message" >> "$LOG_FILE"
    
    # Escreve no terminal com cores
    case "$type" in
        INFO)
            echo -e "${COLOR_CYAN}[INFO]${COLOR_NC} $message"
            ;;
        SUCCESS)
            echo -e "${COLOR_GREEN}[SUCESSO]${COLOR_NC} $message"
            ;;
        WARN)
            echo -e "${COLOR_YELLOW}[AVISO]${COLOR_NC} $message" >&2
            ;;
        ERROR)
            echo -e "${COLOR_RED}[ERRO]${COLOR_NC} $message" >&2
            ;;
        *)
            echo "$message"
            ;;
    esac
}

# Função para exibir o cabeçalho
show_header() {
    echo -e "\n${COLOR_BLUE}=======================================================${COLOR_NC}"
    echo -e "${COLOR_BLUE}  HomeCore MQTT Server Setup (v${SCRIPT_VERSION})${COLOR_NC}"
    echo -e "${COLOR_BLUE}=======================================================${COLOR_NC}"
    log_message INFO "Iniciando script de instalação/atualização MQTT (v${SCRIPT_VERSION})"
    log_message INFO "Diretório de Configuração: $CONFIG_DIR"
    log_message INFO "Arquivo de Log: $LOG_FILE"
}

# Função para exibir o rodapé
show_footer() {
    local exit_code=$1
    echo -e "${COLOR_BLUE}=======================================================${COLOR_NC}"
    if [ "$exit_code" -eq 0 ]; then
        log_message SUCCESS "Configuração MQTT concluída com sucesso!"
        echo -e "${COLOR_GREEN}  CONFIGURAÇÃO MQTT CONCLUÍDA COM SUCESSO!${COLOR_NC}"
    else
        log_message ERROR "Configuração MQTT falhou. Código de saída: $exit_code"
        echo -e "${COLOR_RED}  CONFIGURAÇÃO MQTT FALHOU! (Verifique o log para detalhes)${COLOR_NC}"
    fi
    echo -e "${COLOR_BLUE}=======================================================${COLOR_NC}\n"
}

# Função para exibir o uso do script
usage() {
    cat <<EOF
Uso: bash mqtt_update.sh

Instala, configura e inicia o Mosquitto MQTT Broker no Home Assistant.
EOF
}

# --- Funções de Instalação e Configuração MQTT ---

# 1. Instala ou verifica o add-on Mosquitto
install_mqtt_addon() {
    log_message INFO "Verificando status do add-on Mosquitto..."
    
    # ha addons info retorna 0 se o add-on for encontrado, mesmo que não esteja instalado.
    # O grep é usado para verificar se o add-on está na lista de add-ons disponíveis/instalados.
    if ha addons list | grep -q "$MQTT_ADDON_SLUG"; then
        log_message SUCCESS "Add-on Mosquitto ($MQTT_ADDON_SLUG) já está instalado."
        return 0
    else
        log_message INFO "Add-on Mosquitto não encontrado. Iniciando instalação..."
        # O comando 'ha addons install' pode falhar se o add-on já estiver na lista, mas não instalado.
        # Vamos tentar instalar e capturar o erro, ou assumir que o add-on está disponível.
        if ha addons install "$MQTT_ADDON_SLUG" 2>> "$LOG_FILE"; then
            log_message SUCCESS "Instalação do add-on Mosquitto concluída."
            return 0
        else
            log_message ERROR "Falha ao instalar o add-on Mosquitto. Verifique a conectividade ou permissões."
            return 1
        fi
    fi
}

# 2. Configura o Mosquitto (usuário, senha, porta)
configure_mqtt_broker() {
    log_message INFO "Iniciando configuração do broker Mosquitto..."
    
    # 2.1 Criar diretório de configuração
    log_message INFO "Criando diretório de configuração: $MQTT_CONFIG_DIR"
    mkdir -p "$MQTT_CONFIG_DIR" 2>> "$LOG_FILE"
    
    # 2.2 Criar ou atualizar o arquivo de configuração mosquitto.conf
    log_message INFO "Criando/Atualizando arquivo de configuração: $MQTT_CONFIG_DIR/mosquitto.conf"
    cat > "$MQTT_CONFIG_DIR/mosquitto.conf" <<EOF
listener $MQTT_PORT
allow_anonymous false
password_file $MQTT_CONFIG_DIR/passwd
EOF
    
    # 2.3 Criar o arquivo de senha
    log_message INFO "Criando arquivo de senha para o usuário '$MQTT_USER'..."
    
    # Tenta usar mosquitto_passwd se disponível (mais seguro)
    if command -v mosquitto_passwd >/dev/null 2>&1; then
        log_message INFO "Usando 'mosquitto_passwd' para criar o arquivo de senha."
        if mosquitto_passwd -b "$MQTT_CONFIG_DIR/passwd" "$MQTT_USER" "$MQTT_PASS" 2>> "$LOG_FILE"; then
            log_message SUCCESS "Arquivo de senha criado com sucesso."
        else
            log_message WARN "Falha ao usar 'mosquitto_passwd'. Tentando método manual."
            echo "$MQTT_USER:$MQTT_PASS" > "$MQTT_CONFIG_DIR/passwd"
            log_message SUCCESS "Arquivo de senha criado manualmente (senha em texto simples)."
        fi
    else
        # Fallback manual (menos seguro, mas funcional)
        log_message WARN "'mosquitto_passwd' não disponível. Criando senha manualmente (texto simples)."
        echo "$MQTT_USER:$MQTT_PASS" > "$MQTT_CONFIG_DIR/passwd"
        log_message SUCCESS "Arquivo de senha criado manualmente (senha em texto simples)."
    fi
    
    return 0
}

# 3. Iniciar e Reiniciar o Serviço
start_and_restart_mqtt() {
    log_message INFO "Iniciando/Reiniciando o add-on Mosquitto para aplicar as alterações..."
    
    # ha addons restart é o comando correto, mas pode falhar se o add-on não estiver em um estado reiniciável.
    # Vamos tentar iniciar primeiro, o que é idempotente e mais seguro para o primeiro uso.
    if ha addons start "$MQTT_ADDON_SLUG" 2>> "$LOG_FILE"; then
        log_message SUCCESS "Comando de início do Mosquitto enviado com sucesso."
    else
        log_message WARN "Falha ao iniciar o add-on Mosquitto. Tentando reiniciar..."
        if ha addons restart "$MQTT_ADDON_SLUG" 2>> "$LOG_FILE"; then
            log_message SUCCESS "Comando de reinício do Mosquitto enviado com sucesso."
        else
            log_message ERROR "Falha crítica ao iniciar/reiniciar o add-on Mosquitto."
            return 1
        fi
    fi
        
    # Espera um pouco para o serviço subir
    log_message INFO "Aguardando 10 segundos para o serviço iniciar..."
    sleep 10
    
    # 4. Testar se o broker está ativo
    log_message INFO "Verificando se o broker está ativo na porta $MQTT_PORT..."
    if command -v nc >/dev/null 2>&1; then
        if nc -z 127.0.0.1 "$MQTT_PORT" 2>> "$LOG_FILE"; then
            log_message SUCCESS "Broker MQTT ativo e respondendo na porta $MQTT_PORT."
            return 0
        else
            log_message ERROR "Falha ao conectar ao Broker MQTT na porta $MQTT_PORT. Verifique o log do add-on."
            return 1
        fi
    else
        log_message WARN "Comando 'nc' (netcat) não encontrado. Não foi possível verificar a conectividade da porta."
        return 0 # Assume sucesso se o restart foi bem-sucedido
    fi
}

# --- Função Principal ---

main() {
    # Define o comportamento em caso de erro (sai imediatamente)
    set -e
    
    # Cria o diretório de logs se não existir
    mkdir -p "$LOG_DIR"
    
    # Exibe o cabeçalho
    show_header
    
    # Verifica se o usuário pediu ajuda
    if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
        usage
        exit 0
    fi
    
    # 1. Instalação
    if ! install_mqtt_addon; then
        show_footer 1
        exit 1
    fi
    
    # 2. Configuração
    if ! configure_mqtt_broker; then
        show_footer 1
        exit 1
    fi
    
    # 3. Início/Reinício e Teste
    if ! start_and_restart_mqtt; then
        show_footer 1
        exit 1
    fi
    
    # Fim da execução bem-sucedida
    show_footer 0
}

# Executa a função principal e captura o código de saída
main "$@"
exit $?