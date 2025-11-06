#!/bin/bash

# ==============================================================================
# HomeCore Client Update Script (hcc_update.sh)
#
# Este script baixa e aplica a última configuração do cliente HomeCore
# diretamente no diretório /config do Home Assistant.
#
# Funcionalidades:
# - Compatibilidade com o ambiente Home Assistant (HA).
# - Melhoria visual profissional na saída do terminal.
# - Tratamento robusto de erros e retries.
# - Geração de logs detalhados.
# - Sempre baixa a versão mais recente sem verificação de versão.
# ==============================================================================

# --- Configurações e Variáveis Globais ---
SCRIPT_VERSION="1.0.1"
API_URL="homecore.com.br/api/hcc_update.php"
CONFIG_DIR="${HOMECORE_CONFIG_DIR:-/config}"
LOG_DIR="${CONFIG_DIR}/hc-tools/logs"
LOG_FILE="${LOG_DIR}/$(date +%Y%m%dT%H%M)_hcc_update.log"
MAX_RETRIES=3
RETRY_DELAY=5 # segundos

# --- Códigos de Cores ANSI (para melhor visualização no terminal) ---
COLOR_GREEN='\033[0;32m'
COLOR_RED='\033[0;31m'
COLOR_YELLOW='\033[0;33m'
COLOR_BLUE='\033[0;34m'
COLOR_CYAN='\033[0;36m'
COLOR_NC='\033[0m' # No Color

# --- Funções de Log e Saída ---

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
    echo -e "${COLOR_BLUE}  HomeCore Client Update (v${SCRIPT_VERSION})${COLOR_NC}"
    echo -e "${COLOR_BLUE}=======================================================${COLOR_NC}"
    log_message INFO "Iniciando script de atualização HomeCore (v${SCRIPT_VERSION})"
    log_message INFO "Diretório de Configuração: $CONFIG_DIR"
    log_message INFO "Arquivo de Log: $LOG_FILE"
}

# Função para exibir o rodapé
show_footer() {
    local exit_code=$1
    local status="${2:-}"
    echo -e "${COLOR_BLUE}=======================================================${COLOR_NC}"
    if [ "$exit_code" -eq 0 ]; then
        if [[ "$status" == "no_update" ]]; then
            log_message INFO "Nenhuma atualização disponível; ambiente já está alinhado."
            echo -e "${COLOR_YELLOW}  Nenhuma atualização disponível no momento.${COLOR_NC}"
            echo -e ""
        else
            log_message SUCCESS "Atualização concluída com sucesso!"
            echo -e "${COLOR_GREEN}  ATUALIZAÇÃO CONCLUÍDA COM SUCESSO!${COLOR_NC}"
            echo -e ""
            echo -e "${COLOR_YELLOW}\u26A0 Reinicie o HAOS para aplicar as configurações.${COLOR_NC}"
        fi
    else
        log_message ERROR "Atualização falhou. Código de saída: $exit_code"
        echo -e "${COLOR_RED}  ATUALIZAÇÃO FALHOU! (Verifique o log para detalhes)${COLOR_NC}"
    fi
    echo -e "${COLOR_BLUE}=======================================================${COLOR_NC}\n"
}

# Função para exibir o uso do script
usage() {
    cat <<EOF
Uso: bash hcc_update.sh

Baixa e aplica a última configuração do cliente HomeCore.

Requer a variável de ambiente HOMECORE_TOKEN com o token informado ao registrar a integração.

EOF
}

# --- Funções de Pré-requisitos e Resolução de ID ---

# Função para verificar pré-requisitos
check_prerequisites() {
    log_message INFO "Verificando pré-requisitos (curl e unzip)..."
    if ! command -v curl >/dev/null 2>&1; then
        log_message ERROR "O comando 'curl' é necessário para o download, mas não foi encontrado."
        return 1
    fi
    if ! command -v unzip >/dev/null 2>&1; then
        log_message ERROR "O comando 'unzip' é necessário para a extração, mas não foi encontrado."
        return 1
    fi
    log_message SUCCESS "Pré-requisitos atendidos."
    return 0
}

# Função para resolver o ID do cliente (token fornecido pela integração)
resolve_device_key() {
    local explicit="${1:-}"

    if [[ -n "$explicit" ]]; then
        echo "$explicit" | tr -d '[:space:]'
        return 0
    fi

    if [[ -n "${HOMECORE_TOKEN:-}" ]]; then
        echo "${HOMECORE_TOKEN}" | tr -d '[:space:]'
        return 0
    fi

    if [[ -n "${HOMECORE_DEVICE_KEY:-}" ]]; then
        echo "${HOMECORE_DEVICE_KEY}" | tr -d '[:space:]'
        return 0
    fi

    log_message ERROR "Variável HOMECORE_TOKEN não definida; defina-a antes de executar."
    return 1
}

# --- Funções de Execução Principal ---

# Função para fazer backup do diretório hc-tools
perform_backup() {
    local backup_source="${CONFIG_DIR}/hc-tools"
    local backup_target="${CONFIG_DIR}/hc-tools_backup_$(date +%Y%m%dT%H%M)"
    
    if [ -d "$backup_source" ]; then
        log_message INFO "Iniciando backup de $backup_source para $backup_target..."
        if cp -r "$backup_source" "$backup_target"; then
            log_message SUCCESS "Backup concluído com sucesso."
            return 0
        else
            log_message WARN "Falha ao criar backup. Continuando sem backup."
            return 1
        fi
    else
        log_message INFO "Diretório de ferramentas ($backup_source) não encontrado. Pulando backup."
        return 0
    fi
}

# Função para baixar e extrair o pacote com retries
download_and_extract() {
    local client_id="$1"
    local zip_url="http://${API_URL}?client_id=${client_id}"
    local tmp_zip
    if ! tmp_zip=$(mktemp -t hcc_update.XXXXXX); then
        log_message ERROR "Não foi possível criar arquivo temporário para o download."
        return 1
    fi
    local attempt=0
    local success=0
    local no_update=0

    log_message INFO "URL de Download: $zip_url"
    log_message INFO "ID do Cliente: $client_id"
    
    # --- 1. Download com Retries ---
    while [ $attempt -lt $MAX_RETRIES ]; do
        attempt=$((attempt + 1))
        log_message INFO "Tentativa de download $attempt de $MAX_RETRIES..."
        
        # -f: Fail silently on server errors (404, 500, etc.)
        # -s: Silent mode
        # -L: Follow redirects
        # -o: Output file
        # --insecure: Adicionado para contornar possíveis problemas de certificado SSL/TLS no ambiente HAOS
        if curl -fSL --insecure "$zip_url" -o "$tmp_zip" 2>> "$LOG_FILE"; then
            log_message SUCCESS "Download concluído com sucesso na tentativa $attempt."
            success=1
            break
        else
            local curl_status=$?
            if [ "$curl_status" -eq 22 ]; then
                log_message INFO "Nenhuma atualização disponível no momento para este cliente (HTTP 404)."
                no_update=1
                break
            fi
            log_message WARN "Falha no download na tentativa $attempt. Código de saída do curl: $curl_status."
            if [ $attempt -lt $MAX_RETRIES ]; then
                log_message INFO "Aguardando $RETRY_DELAY segundos antes de tentar novamente..."
                sleep $RETRY_DELAY
            fi
        fi
    done

    if [ $no_update -eq 1 ]; then
        rm -f "$tmp_zip"
        return 2
    fi

    if [ $success -eq 0 ]; then
        log_message ERROR "Falha crítica: Não foi possível baixar o pacote após $MAX_RETRIES tentativas."
        rm -f "$tmp_zip"
        return 1
    fi
    
    # --- 2. Verificação de Integridade (simples) ---
    if [ ! -s "$tmp_zip" ]; then
        log_message ERROR "O arquivo baixado está vazio ou inválido."
        rm -f "$tmp_zip"
        return 1
    fi
    
    # --- 3. Extração ---
    log_message INFO "Iniciando extração do pacote para diretório temporário..."

    local tmp_dir
    if ! tmp_dir=$(mktemp -d -t hcc_update.extract.XXXXXX); then
        log_message ERROR "Não foi possível criar diretório temporário para extração."
        rm -f "$tmp_zip"
        return 1
    fi

    if ! unzip -oq "$tmp_zip" -d "$tmp_dir" 2>> "$LOG_FILE"; then
        log_message ERROR "Falha na extração do pacote. Código de saída do unzip: $?."
        rm -f "$tmp_zip"
        rm -rf "$tmp_dir"
        return 1
    fi

    log_message SUCCESS "Pacote extraído temporariamente em $tmp_dir."

    local extracted_entries=()
    while IFS= read -r entry; do
        extracted_entries+=("$entry")
    done < <(find "$tmp_dir" -mindepth 1 -maxdepth 1)

    local staging_dir="$tmp_dir"
    if [[ ${#extracted_entries[@]} -eq 1 && -d "${extracted_entries[0]}" ]]; then
        staging_dir="${extracted_entries[0]}"
        log_message INFO "Detectado diretório raíz dentro do pacote. Usando conteúdo de $staging_dir."
    fi

    log_message INFO "Mesclando arquivos de $staging_dir para $CONFIG_DIR..."
    if cp -r "$staging_dir"/. "$CONFIG_DIR"/ 2>> "$LOG_FILE"; then
        log_message SUCCESS "Arquivos aplicados com sucesso em $CONFIG_DIR."
        rm -f "$tmp_zip"
        rm -rf "$tmp_dir"
        return 0
    else
        log_message ERROR "Falha ao copiar arquivos para $CONFIG_DIR."
        rm -f "$tmp_zip"
        rm -rf "$tmp_dir"
        return 1
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
    
    # Verifica pré-requisitos
    if ! check_prerequisites; then
        show_footer 1
        exit 1
    fi
    
    # Resolve o ID do cliente
    log_message INFO "Validando token do cliente fornecido pela integração..."
    local client_id=""
    if ! client_id=$(resolve_device_key); then
        log_message ERROR "Token ausente. Configure HOMECORE_TOKEN na integração antes de prosseguir."
        show_footer 1
        exit 1
    fi
    log_message SUCCESS "ID do Cliente resolvido: $client_id"
    
    # Faz o backup
    perform_backup
    
    # Baixa e extrai o pacote
    local download_status=0
    if download_and_extract "$client_id"; then
        :
    else
        download_status=$?
        if [ "$download_status" -eq 2 ]; then
            log_message INFO "Atualização não disponível no momento; nada foi alterado."
            show_footer 0 "no_update"
            exit 0
        fi
        show_footer 1
        exit 1
    fi
    
    # Fim da execução bem-sucedida
    show_footer 0
}

# Executa a função principal e captura o código de saída
main "$@"
exit $?
