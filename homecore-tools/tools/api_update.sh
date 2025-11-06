#!/usr/bin/env bash
set -euo pipefail

LOG_TAG="homecore-api-update"

log() {
  logger -t "$LOG_TAG" "$*"
  echo "$LOG_TAG: $*"
}

CONFIG_DIR="${CONFIG_DIR:-/config}"
TARGET_DIR="${TARGET_DIR:-${CONFIG_DIR}/custom_components/homecore}"
BACKUP_DIR="${BACKUP_DIR:-${CONFIG_DIR}/homecore/backups/api}"
DOWNLOAD_DIR="${DOWNLOAD_DIR:-/tmp/homecore-api-update}"
SYNC_ENDPOINT="${HOMECORE_SYNC_ENDPOINT:-https://homecore.com.br/api/sync/beacon.php}"
TOKEN_FILE_DEFAULT="${CONFIG_DIR}/homecore/token"
TOKEN="${HOMECORE_TOKEN:-}"

if [[ -z "$TOKEN" && -f "${HOMECORE_TOKEN_FILE:-$TOKEN_FILE_DEFAULT}" ]]; then
  TOKEN="$(tr -d '\r\n' < "${HOMECORE_TOKEN_FILE:-$TOKEN_FILE_DEFAULT}")"
fi

if [[ -z "$TOKEN" ]]; then
  log "Token HomeCore não encontrado (defina HOMECORE_TOKEN ou arquivo ${HOMECORE_TOKEN_FILE:-$TOKEN_FILE_DEFAULT})"
  exit 1
fi

mkdir -p "$DOWNLOAD_DIR" "$BACKUP_DIR"

log "Consultando versão mais recente da API"
metadata_json="$(curl -fsSL -H "Authorization: Bearer ${TOKEN}" "${SYNC_ENDPOINT}?action=api_version")"
if [[ -z "$metadata_json" ]]; then
  log "Resposta vazia do endpoint api_version"
  exit 1
fi

python_output="$(python3 - "$metadata_json" <<'PY'
import json
import sys

data = json.loads(sys.argv[1])
artifact = data.get("artifact_url") or ""
checksum = data.get("checksum") or ""
version = data.get("api_version") or ""
if not artifact:
    print("", "", "", sep="\n")
else:
    print(artifact, checksum, version, sep="\n")
PY
)"

read -r ARTIFACT_URL CHECKSUM API_VERSION <<<"$python_output"

if [[ -z "$ARTIFACT_URL" ]]; then
  log "Endpoint não retornou artifact_url"
  exit 1
fi

log "Baixando pacote da API (${API_VERSION:-desconhecida})"
PACKAGE_PATH="${DOWNLOAD_DIR}/homecore-api.zip"
curl -fsSL -H "Authorization: Bearer ${TOKEN}" "$ARTIFACT_URL" -o "$PACKAGE_PATH"

if [[ -n "$CHECKSUM" ]]; then
  echo "${CHECKSUM}  ${PACKAGE_PATH}" | sha256sum -c -
  log "Checksum validado com sucesso"
else
  log "Checksum não informado; prosseguindo sem validação"
fi

EXTRACT_DIR="${DOWNLOAD_DIR}/extracted"
rm -rf "$EXTRACT_DIR"
mkdir -p "$EXTRACT_DIR"
unzip -oq "$PACKAGE_PATH" -d "$EXTRACT_DIR"

SOURCE_DIR="$EXTRACT_DIR"
if [[ -d "${EXTRACT_DIR}/custom_components/homecore" ]]; then
  SOURCE_DIR="${EXTRACT_DIR}/custom_components/homecore"
fi

if [[ ! -d "$SOURCE_DIR" ]]; then
  log "Pacote não contém diretório custom_components/homecore"
  exit 1
fi

timestamp="$(date +%Y%m%d%H%M%S)"
if [[ -d "$TARGET_DIR" ]]; then
  BACKUP_FILE="${BACKUP_DIR}/homecore-api-${timestamp}.tar.gz"
  log "Criando backup em ${BACKUP_FILE}"
  mkdir -p "$BACKUP_DIR"
  tar -czf "$BACKUP_FILE" -C "$(dirname "$TARGET_DIR")" "$(basename "$TARGET_DIR")"
fi

log "Atualizando componente em ${TARGET_DIR}"
rm -rf "$TARGET_DIR"
mkdir -p "$(dirname "$TARGET_DIR")"
cp -a "$SOURCE_DIR" "$TARGET_DIR"

log "Limpeza de arquivos temporários"
rm -rf "$PACKAGE_PATH" "$EXTRACT_DIR"

log "Atualização da API concluída"
exit 0
