#!/bin/bash
# ========================================
# Neurollar - Instalação do HACS no HAOS
# ========================================
# Este script instala o HACS (Home Assistant Community Store)
# em um dispositivo Home Assistant OS (HAOS), utilizando o
# script oficial do HACS e um fallback manual caso necessário.
# ========================================
set -e

# ========================================
# CONFIGURAÇÕES
# ========================================
CONFIG_DIR="/config"
LOG_DIR="$CONFIG_DIR/haos-tools/logs"
LOG_FILE="$LOG_DIR/hacs_install.log"
TMP_DIR="/tmp/hacs_install"
CUSTOM_DIR="$CONFIG_DIR/custom_components"
HACS_DIR="$CUSTOM_DIR/hacs"

# ========================================
# FUNÇÕES
# ========================================
mkdir -p "$LOG_DIR"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"; }
error() { log "ERRO: $1"; exit 1; }

# ========================================
# INÍCIO
# ========================================
log "========================================="
log "Iniciando instalação do HACS"
log "========================================="

# Verifica se já existe uma instalação
if [ -d "$HACS_DIR" ] && [ -f "$HACS_DIR/__init__.py" ]; then
  log "HACS já parece instalado em: $HACS_DIR"
  log "Nenhuma ação necessária."
  exit 0
fi

mkdir -p "$CUSTOM_DIR"
rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"

# ========================================
# TENTATIVA 1: Script oficial HACS
# ========================================
log "Executando script oficial de instalação do HACS (hacs.xyz) ..."
if command -v curl >/dev/null 2>&1; then
  if bash -c "curl -sSL https://hacs.xyz/install | bash -" >> "$LOG_FILE" 2>&1; then
    log "✓ Script oficial executado"
  else
    log "⚠️ Falha ao executar via curl, tentando fallback manual"
  fi
elif command -v wget >/dev/null 2>&1; then
  if bash -c "wget -q -O - https://hacs.xyz/install | bash -" >> "$LOG_FILE" 2>&1; then
    log "✓ Script oficial executado"
  else
    log "⚠️ Falha ao executar via wget, tentando fallback manual"
  fi
else
  log "⚠️ Nem curl nem wget disponíveis, seguindo para fallback manual"
fi

# Se HACS foi instalado pelo script oficial, finalize
if [ -d "$HACS_DIR" ] && [ -f "$HACS_DIR/__init__.py" ]; then
  log "✓ HACS instalado com sucesso (script oficial)."
else
  # ========================================
  # TENTATIVA 2: Fallback manual
  # ========================================
  log "Iniciando fallback manual para instalação do HACS ..."
  command -v wget >/dev/null 2>&1 || error "O comando 'wget' não está disponível para fallback manual."

  HACS_ZIP_URL="https://github.com/hacs/integration/releases/latest/download/hacs.zip"
  HACS_ZIP_FILE="$TMP_DIR/hacs.zip"
  log "Baixando pacote do HACS em $HACS_ZIP_URL ..."
  wget -q -O "$HACS_ZIP_FILE" "$HACS_ZIP_URL" || error "Falha ao baixar o pacote do HACS."

  log "Extraindo pacote do HACS para $CUSTOM_DIR ..."
  mkdir -p "$HACS_DIR"

  if command -v unzip >/dev/null 2>&1; then
    # Extrai primeiro para um diretório temporário para verificar a estrutura
    EXTRACT_TMP="$TMP_DIR/extract"
    mkdir -p "$EXTRACT_TMP"
    unzip -o -q "$HACS_ZIP_FILE" -d "$EXTRACT_TMP" || error "Falha ao extrair com unzip."
    
    # Verifica se existe uma pasta 'hacs' dentro do ZIP ou se os arquivos estão na raiz
    if [ -d "$EXTRACT_TMP/hacs" ]; then
      log "Movendo conteúdo de hacs/ para $HACS_DIR ..."
      cp -r "$EXTRACT_TMP/hacs/"* "$HACS_DIR/" || error "Falha ao mover arquivos do HACS."
    elif [ -f "$EXTRACT_TMP/__init__.py" ]; then
      log "Movendo arquivos da raiz para $HACS_DIR ..."
      cp -r "$EXTRACT_TMP/"* "$HACS_DIR/" || error "Falha ao mover arquivos do HACS."
    else
      log "Estrutura do ZIP:"
      ls -la "$EXTRACT_TMP/" | tee -a "$LOG_FILE"
      error "Estrutura do ZIP não reconhecida."
    fi
  elif command -v python3 >/dev/null 2>&1; then
    python3 - "$HACS_ZIP_FILE" "$CUSTOM_DIR" "$HACS_DIR" <<'PYCODE'
import sys, zipfile, os, shutil
from pathlib import Path

zip_path = sys.argv[1]
custom_dir = sys.argv[2]
hacs_dir = sys.argv[3]

# Extrai para um diretório temporário primeiro
extract_tmp = "/tmp/hacs_extract"
Path(extract_tmp).mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(zip_path, 'r') as zf:
    zf.extractall(extract_tmp)

# Verifica a estrutura
if os.path.exists(os.path.join(extract_tmp, "hacs")):
    # Se existe pasta hacs/, move seu conteúdo
    shutil.copytree(os.path.join(extract_tmp, "hacs"), hacs_dir, dirs_exist_ok=True)
elif os.path.exists(os.path.join(extract_tmp, "__init__.py")):
    # Se __init__.py está na raiz, move tudo
    Path(hacs_dir).mkdir(parents=True, exist_ok=True)
    for item in os.listdir(extract_tmp):
        src = os.path.join(extract_tmp, item)
        dst = os.path.join(hacs_dir, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
else:
    print("Estrutura do ZIP não reconhecida:")
    for item in os.listdir(extract_tmp):
        print(f"  {item}")
    sys.exit(1)

# Limpa temporário
shutil.rmtree(extract_tmp, ignore_errors=True)
PYCODE
    if [ $? -ne 0 ]; then
      error "Falha ao extrair com Python (zipfile)."
    fi
  else
    error "Nem 'unzip' nem 'python3' disponíveis para extrair o pacote do HACS."
  fi

  # Validação final mais robusta
  if [ -d "$HACS_DIR" ] && [ -f "$HACS_DIR/__init__.py" ]; then
    log "✓ HACS instalado com sucesso (fallback manual)."
    log "Arquivos principais encontrados:"
    ls -la "$HACS_DIR/" | head -10 | tee -a "$LOG_FILE"
  else
    log "Conteúdo de $CUSTOM_DIR:"
    ls -la "$CUSTOM_DIR/" | tee -a "$LOG_FILE"
    if [ -d "$HACS_DIR" ]; then
      log "Conteúdo de $HACS_DIR:"
      ls -la "$HACS_DIR/" | tee -a "$LOG_FILE"
    fi
    error "A instalação do HACS não foi concluída corretamente."
  fi
fi

# ========================================
# LIMPEZA
# ========================================
rm -rf "$TMP_DIR"

# ========================================
# FINALIZAÇÃO
# ========================================
log "========================================="
log "Instalação do HACS finalizada."
log "Local: $HACS_DIR"
log "Reinicie o Home Assistant e adicione a integração HACS pela interface."
log "Log: $LOG_FILE"
log "========================================="
exit 0