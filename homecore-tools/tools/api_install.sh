#!/bin/bash

################################################################################
# HomeCore API - Script de Instalação com OAuth (Device Flow)
# 
# Este script instala a integração HomeCore no Home Assistant OS
# usando autenticação OAuth do GitHub (similar ao HACS)
# 
# Repositório: https://github.com/wmaldonadobr/homecore_api
# Consulte a documentação para realizar a instalação
################################################################################

set -e  # Parar execução em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configurações OAuth
# NOTA: Este Client ID é público e embutido no código (isso é seguro para Device Flow)
# Veja: https://github.com/cli/oauth/issues/1
GITHUB_CLIENT_ID="Ov23liO47asIVRengI5v"  # Substitua pelo seu Client ID real
REPO_OWNER="wmaldonadobr"
REPO_NAME="homecore_api"
BRANCH="main"

# Função para exibir mensagens
print_message() {
    echo -e "${BLUE}[HomeCore]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_info() {
    echo -e "${CYAN}[i]${NC} $1"
}

# Banner
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                            ║${NC}"
echo -e "${BLUE}║     HomeCore API - Instalador OAuth        ║${NC}"
echo -e "${BLUE}║                                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Verificar se está rodando no Home Assistant OS
print_message "Verificando ambiente..."
if [ ! -d "/config" ]; then
    print_error "Diretório /config não encontrado!"
    print_error "Este script deve ser executado no Home Assistant OS."
    exit 1
fi
print_success "Ambiente Home Assistant OS detectado"

# Verificar se curl está disponível
if ! command -v curl &> /dev/null; then
    print_error "curl não está instalado!"
    print_error "Por favor, instale o add-on 'Terminal & SSH' ou 'Advanced SSH & Web Terminal'"
    exit 1
fi
print_success "curl disponível"

# Verificar se jq está disponível (para parsing JSON)
if ! command -v jq &> /dev/null; then
    print_warning "jq não está disponível, usando parsing manual de JSON"
    USE_JQ=false
else
    USE_JQ=true
fi

# Função para extrair valor JSON sem jq
extract_json_value() {
    local json="$1"
    local key="$2"
    echo "$json" | grep -o "\"$key\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" | sed 's/.*"\([^"]*\)"/\1/' | head -n 1
}

# Função para extrair valor numérico JSON sem jq
extract_json_number() {
    local json="$1"
    local key="$2"
    echo "$json" | grep -o "\"$key\"[[:space:]]*:[[:space:]]*[0-9]*" | sed 's/.*:[[:space:]]*//' | head -n 1
}

echo ""
print_message "Iniciando autenticação OAuth com GitHub..."
print_info "Este processo é similar ao usado pelo HACS"
echo ""

# Passo 1: Solicitar Device Code
print_message "Solicitando código de verificação..."

DEVICE_RESPONSE=$(curl -s -X POST https://github.com/login/device/code \
    -H "Accept: application/json" \
    -d "client_id=${GITHUB_CLIENT_ID}&scope=repo")

if [ $? -ne 0 ]; then
    print_error "Falha ao solicitar código de verificação"
    exit 1
fi

# Extrair valores da resposta
if [ "$USE_JQ" = true ]; then
    DEVICE_CODE=$(echo "$DEVICE_RESPONSE" | jq -r '.device_code')
    USER_CODE=$(echo "$DEVICE_RESPONSE" | jq -r '.user_code')
    VERIFICATION_URI=$(echo "$DEVICE_RESPONSE" | jq -r '.verification_uri')
    EXPIRES_IN=$(echo "$DEVICE_RESPONSE" | jq -r '.expires_in')
    INTERVAL=$(echo "$DEVICE_RESPONSE" | jq -r '.interval')
else
    DEVICE_CODE=$(extract_json_value "$DEVICE_RESPONSE" "device_code")
    USER_CODE=$(extract_json_value "$DEVICE_RESPONSE" "user_code")
    VERIFICATION_URI=$(extract_json_value "$DEVICE_RESPONSE" "verification_uri")
    EXPIRES_IN=$(extract_json_number "$DEVICE_RESPONSE" "expires_in")
    INTERVAL=$(extract_json_number "$DEVICE_RESPONSE" "interval")
fi

# Validar resposta
if [ -z "$DEVICE_CODE" ] || [ -z "$USER_CODE" ]; then
    print_error "Falha ao obter código de verificação"
    print_error "Resposta: $DEVICE_RESPONSE"
    exit 1
fi

# Definir intervalo padrão se não obtido
INTERVAL=${INTERVAL:-5}
EXPIRES_IN=${EXPIRES_IN:-900}

print_success "Código de verificação obtido!"
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║                                              ║${NC}"
echo -e "${BOLD}║  ${CYAN}Por favor, faça login no GitHub:${NC}${BOLD}            ║${NC}"
echo -e "${BOLD}║                                              ║${NC}"
echo -e "${BOLD}║  ${GREEN}1.${NC} Acesse: ${YELLOW}${VERIFICATION_URI}  ║${NC}"
echo -e "${BOLD}║                                              ║${NC}"
echo -e "${BOLD}║  ${GREEN}2.${NC} Digite o código: ${CYAN}${BOLD}${USER_CODE}${NC}${BOLD}               ║${NC}"
echo -e "${BOLD}║                                              ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════╝${NC}"
echo ""
print_info "Aguardando autorização... (expira em $((EXPIRES_IN/60)) minutos)"
echo ""

# Passo 2: Fazer polling para verificar autorização
MAX_ATTEMPTS=$((EXPIRES_IN / INTERVAL))
ATTEMPT=0
ACCESS_TOKEN=""

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    sleep $INTERVAL
    ATTEMPT=$((ATTEMPT + 1))
    
    TOKEN_RESPONSE=$(curl -s -X POST https://github.com/login/oauth/access_token \
        -H "Accept: application/json" \
        -d "client_id=${GITHUB_CLIENT_ID}&device_code=${DEVICE_CODE}&grant_type=urn:ietf:params:oauth:grant-type:device_code")
    
    if [ "$USE_JQ" = true ]; then
        ERROR=$(echo "$TOKEN_RESPONSE" | jq -r '.error // empty')
        ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token // empty')
    else
        ERROR=$(extract_json_value "$TOKEN_RESPONSE" "error")
        ACCESS_TOKEN=$(extract_json_value "$TOKEN_RESPONSE" "access_token")
    fi
    
    if [ -n "$ACCESS_TOKEN" ] && [ "$ACCESS_TOKEN" != "null" ]; then
        print_success "Autenticação bem-sucedida!"
        break
    elif [ "$ERROR" = "authorization_pending" ]; then
        # Ainda aguardando autorização
        printf "\r${CYAN}[i]${NC} Aguardando autorização... (tentativa %d/%d)" $ATTEMPT $MAX_ATTEMPTS
        continue
    elif [ "$ERROR" = "slow_down" ]; then
        # Reduzir velocidade de polling
        INTERVAL=$((INTERVAL + 5))
        print_warning "Reduzindo velocidade de verificação..."
        continue
    elif [ "$ERROR" = "expired_token" ]; then
        print_error "Código expirou. Execute o script novamente."
        exit 1
    elif [ "$ERROR" = "access_denied" ]; then
        print_error "Acesso negado pelo usuário."
        exit 1
    else
        print_error "Erro desconhecido: $ERROR"
        exit 1
    fi
done

echo ""

if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" = "null" ]; then
    print_error "Tempo limite excedido. Execute o script novamente."
    exit 1
fi

# Definir variáveis
CUSTOM_COMPONENTS_DIR="/config/custom_components"
HOMECORE_DIR="${CUSTOM_COMPONENTS_DIR}/homecore"
TEMP_DIR="/tmp/homecore_install_$$"

# Criar diretório temporário
print_message "Criando diretório temporário..."
mkdir -p "$TEMP_DIR"
print_success "Diretório temporário criado: $TEMP_DIR"

# Fazer download do repositório como ZIP
print_message "Fazendo download do repositório HomeCore..."
DOWNLOAD_URL="https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/zipball/${BRANCH}"

if curl -L -H "Authorization: token ${ACCESS_TOKEN}" \
        -H "Accept: application/vnd.github.v3+json" \
        -o "${TEMP_DIR}/homecore.zip" \
        "${DOWNLOAD_URL}" 2>/dev/null; then
    print_success "Download concluído"
else
    print_error "Falha ao fazer download do repositório"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Verificar se o arquivo foi baixado
if [ ! -f "${TEMP_DIR}/homecore.zip" ] || [ ! -s "${TEMP_DIR}/homecore.zip" ]; then
    print_error "Arquivo de download está vazio ou não foi criado"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Extrair o arquivo ZIP
print_message "Extraindo arquivos..."
if command -v unzip &> /dev/null; then
    unzip -q "${TEMP_DIR}/homecore.zip" -d "$TEMP_DIR" 2>/dev/null
    print_success "Arquivos extraídos com sucesso"
else
    print_warning "unzip não está disponível, tentando busybox unzip..."
    if busybox unzip -q "${TEMP_DIR}/homecore.zip" -d "$TEMP_DIR" 2>/dev/null; then
        print_success "Arquivos extraídos com sucesso usando busybox"
    else
        print_error "Falha ao extrair arquivos"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
fi

# Encontrar o diretório extraído
EXTRACTED_DIR=$(find "$TEMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)

if [ -z "$EXTRACTED_DIR" ]; then
    print_error "Não foi possível encontrar o diretório extraído"
    rm -rf "$TEMP_DIR"
    exit 1
fi

print_message "Diretório extraído: $(basename $EXTRACTED_DIR)"

# Verificar se a pasta homecore existe
if [ ! -d "${EXTRACTED_DIR}/homecore" ]; then
    print_error "Pasta 'homecore' não encontrada no repositório"
    rm -rf "$TEMP_DIR"
    exit 1
fi
print_success "Pasta 'homecore' encontrada no repositório"

# Criar diretório custom_components se não existir
print_message "Verificando diretório custom_components..."
if [ ! -d "$CUSTOM_COMPONENTS_DIR" ]; then
    mkdir -p "$CUSTOM_COMPONENTS_DIR"
    print_success "Diretório custom_components criado"
else
    print_success "Diretório custom_components já existe"
fi

# Fazer backup se já existir instalação anterior
if [ -d "$HOMECORE_DIR" ]; then
    BACKUP_DIR="${HOMECORE_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
    print_warning "Instalação anterior detectada"
    print_message "Criando backup em: $(basename $BACKUP_DIR)"
    mv "$HOMECORE_DIR" "$BACKUP_DIR"
    print_success "Backup criado com sucesso"
fi

# Copiar a pasta homecore
print_message "Instalando HomeCore..."
cp -r "${EXTRACTED_DIR}/homecore" "$HOMECORE_DIR"

if [ $? -eq 0 ]; then
    print_success "HomeCore instalado com sucesso!"
else
    print_error "Falha ao copiar arquivos"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Verificar arquivos essenciais
print_message "Verificando instalação..."
REQUIRED_FILES=("__init__.py" "manifest.json")
ALL_FILES_OK=true

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "${HOMECORE_DIR}/${file}" ]; then
        print_error "Arquivo obrigatório não encontrado: ${file}"
        ALL_FILES_OK=false
    fi
done

if [ "$ALL_FILES_OK" = true ]; then
    print_success "Todos os arquivos obrigatórios estão presentes"
else
    print_error "Instalação incompleta"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Exibir versão instalada
if [ -f "${HOMECORE_DIR}/manifest.json" ]; then
    if command -v grep &> /dev/null; then
        VERSION=$(grep -o '"version"[[:space:]]*:[[:space:]]*"[^"]*"' "${HOMECORE_DIR}/manifest.json" | cut -d'"' -f4)
        if [ -n "$VERSION" ]; then
            print_success "Versão instalada: $VERSION"
        fi
    fi
fi

# Limpar arquivos temporários
print_message "Limpando arquivos temporários..."
rm -rf "$TEMP_DIR"
print_success "Limpeza concluída"

# Mensagem final
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                            ║${NC}"
echo -e "${GREEN}║     Instalação concluída com sucesso!      ║${NC}"
echo -e "${GREEN}║                                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
print_message "Próximos passos:"
echo "  1. Reinicie o Home Assistant"
echo "  2. Entre na plataforma e copie o `token` do cliente
echo "  3. Volte ao HA, vá em Configurações > Dispositivos e Serviços"
echo "  4. Clique em 'Adicionar Integração'"
echo "  5. Procure por 'HomeCore' e adicione "
echo ""
print_warning "IMPORTANTE: É necessário reiniciar o Home Assistant!"
echo ""
print_message "Para reiniciar:"
echo "  - Interface: Configurações > Sistema > Reiniciar"
echo "  - Terminal: ha core restart"
echo ""
print_success "Obrigado por usar HomeCore!"
echo ""

exit 0