#!/bin/bash
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                     HomeCore Board Scanner v2.0                           ║
# ║                   Scanner de dispositivos MolSmart                        ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# Varre uma sub-rede e tenta detectar dispositivos acessíveis via HTTP.
# Para cada IP alcançável, tenta ler /relay_cgi_load.cgi e extrai quantidade/estados de relés.
#
# Uso básico:
#   bash board_scanner.sh --prefix 192.168.1. --from 190 --to 205
#   bash board_scanner.sh --prefix 192.168.1. --from 1 --to 254 --timeout 2 --delay 0
#
# Opções:
#   --prefix PFX      Prefixo da rede (ex.: 192.168.1.)
#   --from N          Início do range (ex.: 1)
#   --to M            Fim do range (ex.: 254)
#   --port PORT       Porta HTTP (ex.: 80, 8080)
#   --timeout SEC     Timeout em segundos para cada requisição (padrão: 1)
#   --delay SEC       Delay em segundos entre requisições (padrão: 0)
#   --endpoint EP     Caminho do endpoint de detalhes (padrão: /relay_cgi_load.cgi)
#   --format FMT      Saída: json|table|visual (padrão: visual)
#   --no-progress     Desabilita barra de progresso (útil para redirecionamento)
#
# Dependências: bash, curl

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES PADRÃO
# ═══════════════════════════════════════════════════════════════════════════

PREFIX=""
FROM=1
TO=254
PORT=80
TIMEOUT=0.2        # em segundos
DELAY=0          # em segundos
ENDPOINT="/relay_cgi_load.cgi"
FORMAT="visual"
SHOW_PROGRESS=true
DEBUG=false

# ═══════════════════════════════════════════════════════════════════════════
# SINCRONIZAÇÃO COM A PLATAFORMA HOMEC0RE
# ═══════════════════════════════════════════════════════════════════════════

SYNC_ENABLED=true
SYNC_URL="${HOMECORE_SYNC_URL:-https://homecore.com.br/api/sync/molsmart_sync.php}"
TOKEN=""
TOKEN_FILE=""
CONFIG_DIR="${HOMECORE_CONFIG_DIR:-/config}"
DRY_RUN=false

MQTT_SERVER="${HOMECORE_MQTT_SERVER:-}"
MQTT_PORT="${HOMECORE_MQTT_PORT:-1883}"
MQTT_USER="${HOMECORE_MQTT_USER:-homeassistant}"
MQTT_PASS="${HOMECORE_MQTT_PASS:-ha123}"

LOG_DIR="${CONFIG_DIR}/hc-tools/logs"
LOG_FILE="${LOG_DIR}/board_scanner.log"

SYNC_SERIALS_SEEN_LIST=""
JSON_VALIDATOR_WARNING_SHOWN=false

# ═══════════════════════════════════════════════════════════════════════════
# CORES E FORMATAÇÃO ANSI
# ═══════════════════════════════════════════════════════════════════════════

if [ -t 1 ]; then
  # Terminal suporta cores
  RESET='\033[0m'
  BOLD='\033[1m'
  DIM='\033[2m'
  
  # Cores principais
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[0;33m'
  BLUE='\033[0;34m'
  MAGENTA='\033[0;35m'
  CYAN='\033[0;36m'
  WHITE='\033[0;37m'
  GRAY='\033[0;90m'
  
  # Cores brilhantes
  BRED='\033[1;31m'
  BGREEN='\033[1;32m'
  BYELLOW='\033[1;33m'
  BBLUE='\033[1;34m'
  BMAGENTA='\033[1;35m'
  BCYAN='\033[1;36m'
  BWHITE='\033[1;37m'
  BG_RED='\033[41m'
  BG_GREEN='\033[42m'
  BG_BLUE='\033[44m'
  BG_CYAN='\033[46m'
else
  # Sem cores
  RESET='' BOLD='' DIM=''
  RED='' GREEN='' YELLOW='' BLUE='' MAGENTA='' CYAN='' WHITE=''
  BRED='' BGREEN='' BYELLOW='' BBLUE='' BMAGENTA='' BCYAN='' BWHITE=''
  BG_GREEN='' BG_RED='' BG_BLUE='' BG_CYAN=''
fi

# ═══════════════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════════════

current_utc_timestamp() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

ensure_log_ready() {
  if [ -z "$LOG_FILE" ]; then
    return
  fi
  if [ -n "$LOG_DIR" ] && [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR" 2>/dev/null || true
  fi
  if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE" 2>/dev/null || true
  fi
}

log_to_file() {
  local level="$1"
  shift
  local message="$*"
  if [ -z "$LOG_FILE" ]; then
    return
  fi
  ensure_log_ready
  if [ -w "$LOG_FILE" ] || [ ! -e "$LOG_FILE" ]; then
    printf "%s [%s] %s\n" "$(current_utc_timestamp)" "$level" "$message" >> "$LOG_FILE" 2>/dev/null || true
  fi
}

# ═══════════════════════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES
# ═══════════════════════════════════════════════════════════════════════════

log() {
  log_to_file "INFO" "$*"
  if [ "$FORMAT" = "visual" ]; then
    printf "%b %b\n" "${CYAN}[INFO]${RESET}" "$*" >&2
  fi
}

log_success() {
  log_to_file "SUCCESS" "$*"
  if [ "$FORMAT" = "visual" ]; then
    printf "%b %b\n" "${BGREEN}[✓]${RESET}" "$*" >&2
  fi
}

log_error() {
  log_to_file "ERROR" "$*"
  if [ "$FORMAT" = "visual" ]; then
    printf "%b %b\n" "${BRED}[✗]${RESET}" "$*" >&2
  fi
}

log_warning() {
  log_to_file "WARN" "$*"
  if [ "$FORMAT" = "visual" ]; then
    printf "%b %b\n" "${BYELLOW}[⚠]${RESET}" "$*" >&2
  fi
}

log_debug() {
  if [ "$DEBUG" = true ]; then
    log_to_file "DEBUG" "$*"
    printf "%b %b\n" "${DIM}[DBG]${RESET}" "$*" >&2
  fi
}

print_header() {
  if [ "$FORMAT" = "visual" ]; then
    printf "%b\n" "${GREEN}"
    printf "%s\n" "╔═══════════════════════════════════════════════════════════════════════════╗"
    printf "%s\n" "║                     HomeCore Board Scanner v2.0                           ║"
    printf "%s\n" "║                   Scanner de dispositivos MolSmart                        ║"
    printf "%s\n" "╚═══════════════════════════════════════════════════════════════════════════╝"
    printf "%b\n" "${RESET}"
  fi
}

print_config() {
  if [ "$FORMAT" = "visual" ]; then
    local mqtt_display sync_display
    if [ -n "$MQTT_SERVER" ]; then
      mqtt_display="${MQTT_SERVER}:${MQTT_PORT}"
    else
      mqtt_display="auto:${MQTT_PORT}"
    fi
    sync_display="$SYNC_URL"
    printf "%b\n" "${BCYAN}┌─ Configurações ────────────────────────────────────────────────────────────┐${RESET}"
    printf "%b\n" "${CYAN}│${RESET} ${BOLD}Rede:${RESET}     ${PREFIX}${FROM}-${TO}"
    printf "%b\n" "${CYAN}│${RESET} ${BOLD}Porta:${RESET}    ${PORT}"
    printf "%b\n" "${CYAN}│${RESET} ${BOLD}Timeout:${RESET}  ${TIMEOUT}s"
    printf "%b\n" "${CYAN}│${RESET} ${BOLD}Delay:${RESET}    ${DELAY}s"
    printf "%b\n" "${CYAN}│${RESET} ${BOLD}Endpoint:${RESET} ${ENDPOINT}"
    printf "%b\n" "${CYAN}│${RESET} ${BOLD}MQTT:${RESET}     ${mqtt_display}"
    printf "%b\n" "${CYAN}│${RESET} ${BOLD}Sync:${RESET}     ${sync_display}"
    printf "%b\n" "${BCYAN}└────────────────────────────────────────────────────────────────────────────┘${RESET}"
    printf "\n"
  fi
}

# Auto-detectar IP local primário (IPv4 não loopback)
detect_primary_ip() {
  local ip=""

  if command -v ip >/dev/null 2>&1; then
    ip=$(ip -4 addr show 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1 | grep -v '^127\.' | head -1)
  fi

  if [ -z "$ip" ] && command -v ifconfig >/dev/null 2>&1; then
    ip=$(ifconfig 2>/dev/null | grep 'inet ' | grep -v '127.0.0.1' | head -1 | awk '{print $2}' | sed 's/addr://')
  fi

  if [ -z "$ip" ] && command -v hostname >/dev/null 2>&1; then
    ip=$(hostname -I 2>/dev/null | awk '{print $1}')
  fi

  echo "$ip"
}

# Auto-detectar prefixo a partir do primeiro IP local
auto_prefix() {
  local ip=""
  ip=$(detect_primary_ip)
  
  # Extrair prefixo (primeiros 3 octetos)
  if [ -n "$ip" ]; then
    echo "$ip" | awk -F. '{print $1"."$2"."$3"."}'
  else
    echo "192.168.1."
  fi
}

normalize_state_value() {
  local raw="$1"
  local cleaned
  cleaned=$(echo "$raw" | tr -cd '0-9')
  if [ "$cleaned" = "1" ]; then
    echo "1"
  else
    echo "0"
  fi
}

build_channel_config() {
  local count="$1"
  local states_csv="$2"
  local label="$3"

  if [ -z "$count" ] || [ "$count" -le 0 ]; then
    echo "[]"
    return
  fi

  local states_array=()
  if [ -n "$states_csv" ]; then
    local old_ifs="$IFS"
    IFS=',' read -r -a states_array <<< "$states_csv"
    IFS="$old_ifs"
  fi

  local idx state entry json=""
  for ((idx=1; idx<=count; idx++)); do
    if [ ${#states_array[@]} -ge "$idx" ]; then
      state=$(normalize_state_value "${states_array[$((idx-1))]}")
    else
      state="0"
    fi
    entry=$(printf '{"channel":%d,"name":"%s %d","state":%d,"enabled":true}' \
      "$idx" "$label" "$idx" "$state")
    if [ -z "$json" ]; then
      json="$entry"
    else
      json="${json},$entry"
    fi
  done

  printf "[%s]" "$json"
}

resolve_mqtt_server() {
  if [ -n "$MQTT_SERVER" ]; then
    return 0
  fi

  MQTT_SERVER=$(detect_primary_ip)
  if [ -n "$MQTT_SERVER" ]; then
    log_debug "MQTT server detectado automaticamente: $MQTT_SERVER"
    return 0
  fi

  log_warning "Não foi possível detectar IP local para configuração MQTT"
  return 1
}

configure_board_mqtt() {
  local ip="$1"

  if ! resolve_mqtt_server; then
    return 1
  fi

  local url="http://${ip}/mqtt.cgi?server=${MQTT_SERVER}&port=${MQTT_PORT}&user=${MQTT_USER}&pass=${MQTT_PASS}"
  curl -m "$TIMEOUT" -sS "$url" >/dev/null 2>&1
  local status=$?
  if [ $status -eq 0 ]; then
    log_debug "Configuração MQTT enviada para $ip"
    return 0
  fi

  log_warning "Falha ao configurar MQTT em $ip (curl exit $status)"
  return 1
}

validate_json_string() {
  local json="$1"

  if [ -z "$json" ]; then
    return 1
  fi

  if command -v python3 >/dev/null 2>&1; then
    printf '%s' "$json" | python3 -c 'import json, sys; json.load(sys.stdin)' >/dev/null 2>&1
    return $?
  fi

  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$json" | jq empty >/dev/null 2>&1
    return $?
  fi

  if [ "$JSON_VALIDATOR_WARNING_SHOWN" = false ]; then
    JSON_VALIDATOR_WARNING_SHOWN=true
    log_warning "Ferramentas de validação JSON indisponíveis; prosseguindo sem validação automatizada"
  fi

  return 0
}

add_sync_entry() {
  local ip="$1"
  local qty="$2"
  local states_csv="$3"

  local qty_clean states_clean states_json now_utc board_json
  local output_config_json input_config_json board_model input_count dedup_key
  local mqtt_config_json mqtt_server_value mqtt_port_clean

  qty_clean=$(echo "$qty" | tr -cd '0-9')
  if [ -z "$qty_clean" ]; then
    log_debug "Ignorando dispositivo em $ip: quantidade de relés inválida ($qty)"
    return
  fi

  states_clean=$(echo "$states_csv" | tr -d '\r\n ')
  states_clean=$(echo "$states_clean" | sed 's/[^0-9,]//g')
  if [ -n "$states_clean" ]; then
    states_json="[$states_clean]"
  else
    states_json="[]"
  fi

  dedup_key="ip:${ip}"
  if printf '%s' "$SYNC_SERIALS_SEEN_LIST" | grep -Fxq "$dedup_key"; then
    log_debug "Dispositivo em $ip já registrado na sessão; ignorando duplicata"
    return
  fi
  SYNC_SERIALS_SEEN_LIST="${SYNC_SERIALS_SEEN_LIST}${dedup_key}"$'\n'

  output_config_json=$(build_channel_config "$qty_clean" "$states_clean" "Relay")
  input_config_json=$(build_channel_config "$qty_clean" "" "Input")

  input_count=$qty_clean
  board_model="molsmart_${qty_clean}"

  mqtt_server_value="$MQTT_SERVER"
  if [ -z "$mqtt_server_value" ]; then
    mqtt_server_value=$(detect_primary_ip)
  fi
  mqtt_port_clean=$(echo "$MQTT_PORT" | tr -cd '0-9')
  if [ -z "$mqtt_port_clean" ]; then
    mqtt_port_clean="1883"
  fi
  mqtt_config_json=$(printf '{"server":"%s","port":%s,"user":"%s"}' \
    "${mqtt_server_value:-""}" "$mqtt_port_clean" "$MQTT_USER")

  now_utc=$(current_utc_timestamp)
  board_json=$(printf '{"board_ip":"%s","board_model":"%s","relay_count":%s,"input_count":%s,"output_config":%s,"input_config":%s,"states":%s,"mqtt_config":%s,"last_seen":"%s"}' \
    "$ip" "$board_model" "$qty_clean" "$input_count" "$output_config_json" "$input_config_json" "$states_json" "$mqtt_config_json" "$now_utc")

  if [ -z "$SYNC_ENTRIES" ]; then
    SYNC_ENTRIES="$board_json"
  else
    SYNC_ENTRIES="${SYNC_ENTRIES},$board_json"
  fi

  SYNC_COUNT=$((SYNC_COUNT + 1))
  log_debug "Registrado para sync: $ip com $qty_clean relés"
}

resolve_homecore_token() {
  if [ -n "$TOKEN" ]; then
    TOKEN=$(echo "$TOKEN" | tr -d '[:space:]')
    if [ -n "$TOKEN" ]; then
      return 0
    fi
  fi

  if [ -n "$TOKEN_FILE" ] && [ -f "$TOKEN_FILE" ]; then
    local file_token
    file_token=$(tr -d '[:space:]' < "$TOKEN_FILE" 2>/dev/null)
    if [ -n "$file_token" ]; then
      TOKEN="$file_token"
      log_debug "Token carregado de arquivo personalizado: $TOKEN_FILE"
      return 0
    fi
  fi

  if [ -n "$HOMECORE_TOKEN" ]; then
    local env_token
    env_token=$(echo "$HOMECORE_TOKEN" | tr -d '[:space:]')
    if [ -n "$env_token" ]; then
      TOKEN="$env_token"
      log_debug "Token carregado de HOMECORE_TOKEN"
      return 0
    fi
  fi

  local candidate
  for candidate in \
    "$CONFIG_DIR/HOMECORE_TOKEN" \
    "$CONFIG_DIR/CLIENT_KEY" \
    "$CONFIG_DIR/hc-tools/HOMECORE_TOKEN" \
    "$CONFIG_DIR/hc-tools/CLIENT_KEY"
  do
    if [ -f "$candidate" ]; then
      local read_token
      read_token=$(tr -d '[:space:]' < "$candidate" 2>/dev/null)
      if [ -n "$read_token" ]; then
        TOKEN="$read_token"
        log_debug "Token carregado de $candidate"
        return 0
      fi
    fi
  done

  local config_entries="$CONFIG_DIR/.storage/core.config_entries"
  if [ -f "$config_entries" ]; then
    local py_bin=""
    if command -v python3 >/dev/null 2>&1; then
      py_bin="python3"
    elif command -v python >/dev/null 2>&1; then
      py_bin="python"
    fi

    if [ -n "$py_bin" ]; then
      local py_token
      py_token=$("$py_bin" - "$config_entries" <<'PY'
import json, sys
from pathlib import Path

if len(sys.argv) < 2:
    sys.exit(0)

path = Path(sys.argv[1])
try:
    data = json.loads(path.read_text())
except Exception:
    sys.exit(0)

entries = data.get("data", {}).get("entries") or []
for entry in entries:
    if entry.get("domain") == "homecore":
        token = entry.get("data", {}).get("token")
        if token:
            print(token.strip())
            sys.exit(0)
PY
)
      if [ -n "$py_token" ]; then
        TOKEN=$(echo "$py_token" | tr -d '[:space:]')
        if [ -n "$TOKEN" ]; then
          log_debug "Token carregado de core.config_entries"
          return 0
        fi
      fi
    fi
  fi

  return 1
}

send_sync_payload() {
  local payload="$1"

  if [ -z "$TOKEN" ]; then
    log_error "Token do HomeCore não disponível; cancelando sincronização"
    return 1
  fi

  if ! validate_json_string "$payload"; then
    log_error "Payload JSON inválido; sincronização abortada"
    return 1
  fi

  if [ "$DRY_RUN" = true ]; then
    log "Dry-run habilitado. Payload não enviado:"
    printf "%s\n" "$payload" >&2
    return 0
  fi

  local tmp_body
  tmp_body=$(mktemp) || {
    log_error "Não foi possível criar arquivo temporário para resposta"
    return 1
  }

  local curl_status http_code body
  if [ "$DEBUG" = true ]; then
    log_debug "Payload preparado: $payload"
  fi
  http_code=$(curl -sS -o "$tmp_body" -w "%{http_code}" \
    -X POST "$SYNC_URL" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    --data "$payload" 2>/dev/null)
  curl_status=$?
  body=$(cat "$tmp_body" 2>/dev/null)
  rm -f "$tmp_body"

  if [ $curl_status -ne 0 ]; then
    log_error "Falha ao enviar dados para a API HomeCore (curl exit $curl_status)"
    return 1
  fi

  if ! echo "$http_code" | grep -Eq '^[0-9]+$'; then
    log_error "Código HTTP inválido recebido da API: $http_code"
    if [ -n "$body" ]; then
      printf "%s\n" "$body" >&2
    fi
    return 1
  fi

  if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
    log_success "Registro das placas MolSmart concluído (HTTP $http_code)"
    if [ "$DEBUG" = true ] && [ -n "$body" ]; then
      printf "%s\n" "$body" >&2
    fi
    return 0
  fi

  log_error "API HomeCore retornou HTTP $http_code"
  if [ -n "$body" ]; then
    printf "%s\n" "$body" >&2
  fi
  return 1
}

# ═══════════════════════════════════════════════════════════════════════════
# BARRA DE PROGRESSO
# ═══════════════════════════════════════════════════════════════════════════

draw_progress_bar() {
  local current=$1
  local total=$2
  local width=40
  
  # Evita divisão por zero
  if [ "$total" -eq 0 ]; then
    local percentage=0
    local filled=0
  else
    local percentage=$((current * 100 / total))
    local filled=$((current * width / total))
  fi

  local empty=$((width - filled))

  # Construir barra simples
  local bar="${RESET}"
  local i
  
  # Caracteres preenchidos (preenchido)
  i=0
  while [ $i -lt $filled ]; do
    bar="${bar}${GREEN}#${RESET}"
    i=$((i + 1))
  done
  
  # Caracteres vazios (vazio)
  i=0
  while [ $i -lt $empty ]; do
    bar="${bar}${GRAY}#${RESET}"
    i=$((i + 1))
  done

  # Spinner simples baseado no índice atual
  local spinner
  case $((current % 4)) in
    0) spinner="|";;
    1) spinner="/";;
    2) spinner="-";;
    3) spinner="\\";;
  esac

  # Atualiza em uma única linha: \r para retorno de carro
  # >&2 para sair na saída de erro padrão
  echo -ne "\rProgresso [${bar}${RESET}] ${current}/${total} (${percentage}%) ${spinner}" >&2
}

clear_progress_bar() {
  # Limpa a linha atual, imprime uma nova linha
  # Imprime espaços para cobrir o conteúdo anterior
  echo -e "\r$(printf '%*s' 80) \r" >&2
}

# ═══════════════════════════════════════════════════════════════════════════
# FORMATAÇÃO DE SAÍDA
# ═══════════════════════════════════════════════════════════════════════════

print_json_header() { echo -n '['; }
print_json_footer() { echo ']'; }

print_json_entry() {
  local ip="$1"; local code="$2"; local qty="$3"; local states_csv="$4"
  local reachable=false
  if [ "$code" != "000" ] && [ "$code" != "0000" ]; then reachable=true; fi
  local detail="null"
  if [ -n "$qty" ] && [ -n "$states_csv" ]; then
    local states_json="["
    local first_state=true
    local old_ifs="$IFS"
    IFS=','
    for s in $states_csv; do
      if [ "$first_state" = true ]; then
        first_state=false
      else
        states_json="${states_json},"
      fi
      states_json="${states_json}$s"
    done
    IFS="$old_ifs"
    states_json="${states_json}]"
    detail="{\"qty\":$qty,\"states\":$states_json}"
  fi
  echo -n "{\"ip\":\"$ip\",\"reachable\":$reachable,\"http_status\":$code,\"detail\":$detail}"
}

print_table_header() {
  echo "┌──────────────────┬───────────┬────────┬──────────────────────────────────┐"
  echo "│ IP               │ Status    │ Relés  │ Estados                          │"
  echo "├──────────────────┼───────────┼────────┼──────────────────────────────────┤"
}

print_table_footer() {
  echo "└──────────────────┴───────────┴────────┴──────────────────────────────────┘"
}

print_table_entry() {
  local ip="$1"; local code="$2"; local qty="$3"; local states_csv="$4"
  local status_text
  
  if [ "$code" != "000" ] && [ "$code" != "0000" ]; then
    status_text="${BGREEN}ONLINE${RESET}"
  else
    status_text="${DIM}offline${RESET}"
  fi
  
  local relay_info="${DIM}N/A${RESET}"
  if [ -n "$qty" ]; then
    relay_info="${BWHITE}${qty}${RESET}"
  fi
  
  local states_display="${DIM}-${RESET}"
  if [ -n "$states_csv" ]; then
    states_display=""
    local old_ifs="$IFS"
    IFS=','
    for s in $states_csv; do
      if [ "$s" = "1" ]; then
        states_display="${states_display}${BG_GREEN}${BOLD} 1 ${RESET} "
      else
        states_display="${states_display}${BG_RED}${BOLD} 0 ${RESET} "
      fi
    done
    IFS="$old_ifs"
  fi
  
  printf "│ %-16s │ %-17b │ %-14b │ %-50b │\n" "$ip" "$status_text" "$relay_info" "$states_display"
}

print_visual_device() {
  local ip="$1"
  echo "Dispositivo encontrado $ip"
}

# ═══════════════════════════════════════════════════════════════════════════
# PARSE DE ARGUMENTOS
# ═══════════════════════════════════════════════════════════════════════════

while [ $# -gt 0 ]; do
  case "$1" in
    --prefix) PREFIX="$2"; shift 2;;
    --from) FROM="$2"; shift 2;;
    --to) TO="$2"; shift 2;;
    --port) PORT="$2"; shift 2;;
    --timeout) TIMEOUT="$2"; shift 2;;
    --delay) DELAY="$2"; shift 2;;
    --endpoint) ENDPOINT="$2"; shift 2;;
    --format) FORMAT="$2"; shift 2;;
    --no-progress) SHOW_PROGRESS=false; shift;;
    --debug) DEBUG=true; shift;;
    --sync-url) SYNC_URL="$2"; shift 2;;
    --sync) SYNC_ENABLED=true; shift;;
    --no-sync) SYNC_ENABLED=false; shift;;
    --token) TOKEN="$2"; shift 2;;
    --token-file) TOKEN_FILE="$2"; shift 2;;
    --config-dir) CONFIG_DIR="$2"; shift 2;;
    --dry-run) DRY_RUN=true; shift;;
    -h|--help)
      head -n 30 "$0" 2>/dev/null || sed -n '1,30p' "$0"; exit 0;;
    *) 
      echo "Opção desconhecida: $1" >&2
      exit 1
      ;;
  esac
done

if [ -z "$PREFIX" ]; then PREFIX=$(auto_prefix); fi

ensure_log_ready
log_to_file "INFO" "Iniciando HomeCore Board Scanner"
resolve_mqtt_server || true

# Fallback para HAOS: desabilitar barra de progresso se o ambiente não renderiza \r
#if command -v ha >/dev/null 2>&1; then
#  SHOW_PROGRESS=false
#fi

# ═══════════════════════════════════════════════════════════════════════════
# EXECUÇÃO PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

print_header
print_config

TOTAL=$((TO - FROM + 1))
CURRENT=0
FOUND=0
FOUND_MESSAGES=""
SYNC_ENTRIES=""
SYNC_COUNT=0

# Inicializar formato de saída
if [ "$FORMAT" = "json" ]; then
  print_json_header
elif [ "$FORMAT" = "table" ]; then
  print_table_header
elif [ "$FORMAT" = "visual" ]; then
  log "Iniciando escaneamento de ${BWHITE}${TOTAL}${RESET} endereços..."
  echo ""
fi

first=true

for i in $(seq $FROM $TO); do
  ip="${PREFIX}${i}"
  CURRENT=$((CURRENT + 1))
  
  # Opcional: barra de progresso (desativada automaticamente em HAOS)
  if [ "$SHOW_PROGRESS" = true ] && [ "$FORMAT" = "visual" ]; then
    draw_progress_bar "$CURRENT" "$TOTAL"
  fi

  # Motor simples: tentar ler diretamente o endpoint e detectar padrão &0&
  resp=$(curl -m "$TIMEOUT" -s "http://$ip:$PORT$ENDPOINT" 2>/dev/null)
  
  # Verificar se obtivemos resposta válida
  if [ $? -eq 0 ] && [ -n "$resp" ]; then
    if echo "$resp" | grep -q "&0&"; then
      relays=$(echo "$resp" | awk -F'&' '{print $3}')
      states_raw=$(echo "$resp" | awk -F'&' '{print $4}')
      states_clean=$(echo "$states_raw" | tr -d '\r\n ')
      states_clean=$(echo "$states_clean" | sed 's/[^0-9,]//g')
      if [ -n "$states_clean" ]; then
        states_json="[$states_clean]"
      else
        states_json="[]"
      fi
      configure_board_mqtt "$ip" || true
      log "MolSmart detectada em $ip com ${relays} relés"
      add_sync_entry "$ip" "$relays" "$states_raw"
      FOUND=$((FOUND + 1))
      if [ "$FORMAT" = "visual" ]; then
        FOUND_MESSAGES="${FOUND_MESSAGES}MolSmart em $ip → ${relays} relés\n"
      elif [ "$FORMAT" = "json" ]; then
        if [ "$first" = true ]; then first=false; else echo -n ","; fi
        echo -n "{\"ip\":\"$ip\",\"reachable\":true,\"http_status\":200,\"detail\":{\"qty\":$relays,\"states\":$states_json}}"
      elif [ "$FORMAT" = "table" ]; then
        printf "│ %-16s │ %-17b │ %-14b │ %-50b │\n" "$ip" "${BGREEN}ONLINE${RESET}" "${BWHITE}${relays}${RESET}" "$states_clean"
      fi
    fi
  fi
  
  # Delay entre requisições
  if [ "$DELAY" -gt 0 ]; then
    sleep "$DELAY"
  fi
done

# Finalizar
if [ "$SHOW_PROGRESS" = true ] && [ "$FORMAT" = "visual" ]; then
  printf "\n" >&2  # finalizar a linha da barra
fi

if [ "$FORMAT" = "json" ]; then
  print_json_footer
elif [ "$FORMAT" = "table" ]; then
  print_table_footer
elif [ "$FORMAT" = "visual" ]; then
  echo ""
  # Imprimir mensagens de dispositivos encontrados de forma simples
  if [ -n "$FOUND_MESSAGES" ]; then
    printf "%b" "$FOUND_MESSAGES"
  fi
  log_success "Escaneamento concluído!"
  printf "%b\n" "${BCYAN}┌─ Resumo ───────────────────────────────────────────────────────────────────┐${RESET}"
  printf "%b\n" "${CYAN}│${RESET} ${BOLD}Total escaneado:${RESET}      ${BWHITE}${TOTAL}${RESET} endereços"
  printf "%b\n" "${CYAN}│${RESET} ${BOLD}Dispositivos encontrados:${RESET} ${BGREEN}${FOUND}${RESET} dispositivos"
  printf "%b\n" "${BCYAN}└────────────────────────────────────────────────────────────────────────────┘${RESET}"
fi

if [ "$SYNC_ENABLED" = true ] && [ "$SYNC_COUNT" -gt 0 ]; then
  if resolve_homecore_token; then
    payload=$(printf '{"generated_at":"%s","relay_board":[%s]}' "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "$SYNC_ENTRIES")
    if [ "$DEBUG" = true ]; then
      log_debug "Payload de sincronização preparado (${SYNC_COUNT} placas)"
    fi
    send_sync_payload "$payload"
  else
    log_warning "Token do HomeCore não encontrado; use --token ou --token-file"
    printf "[WARN] Token do HomeCore não encontrado; sincronização ignorada.\n" >&2
  fi
elif [ "$SYNC_ENABLED" = true ]; then
  log_debug "Sincronização habilitada, mas nenhuma placa encontrada"
fi
