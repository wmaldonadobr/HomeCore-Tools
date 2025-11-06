#!/bin/bash

# ==============================================================================
# HomeCore Core Update Script (core_update.sh)
# ==============================================================================

set -euo pipefail

SCRIPT_VERSION="1.0.0"
CONFIG_DIR="${HOMECORE_CONFIG_DIR:-/config/custom_components}"
LOG_DIR="${CONFIG_DIR}/homecore/logs"
LOG_FILE="${LOG_DIR}/$(date +%Y%m%dT%H%M)_core_update.log"
MAX_RETRIES=3
RETRY_DELAY=5
SYNC_ENDPOINT="${HOMECORE_SYNC_ENDPOINT:-https://homecore.com.br/api/sync/beacon.php}"
CORE_BASE_URL="https://homecore.com.br/api/update/core"

COLOR_GREEN='\033[0;32m'
COLOR_RED='\033[0;31m'
COLOR_YELLOW='\033[0;33m'
COLOR_BLUE='\033[0;34m'
COLOR_CYAN='\033[0;36m'
COLOR_NC='\033[0m'

CORE_DOWNLOAD_VERSION=""

log_message() {
    local type="$1"
    local message="$2"
    local timestamp
    timestamp=$(date +%Y-%m-%d\ %H:%M:%S)

    echo "[$timestamp] [$type] $message" >>"$LOG_FILE"

    case "$type" in
        INFO)    echo -e "${COLOR_CYAN}[INFO]${COLOR_NC} $message" ;;
        SUCCESS) echo -e "${COLOR_GREEN}[SUCCESS]${COLOR_NC} $message" ;;
        WARN)    echo -e "${COLOR_YELLOW}[WARN]${COLOR_NC} $message" ;;
        ERROR)   echo -e "${COLOR_RED}[ERROR]${COLOR_NC} $message" ;;
        *)       echo "$message" ;;
    esac
}

show_header() {
    echo -e "\n${COLOR_BLUE}=======================================================${COLOR_NC}"
    echo -e "${COLOR_BLUE}  HomeCore Core Update (v${SCRIPT_VERSION})${COLOR_NC}"
    echo -e "${COLOR_BLUE}=======================================================${COLOR_NC}"
    log_message INFO "Starting core_update (v${SCRIPT_VERSION})"
    log_message INFO "Config directory: ${CONFIG_DIR}"
    log_message INFO "Log file: ${LOG_FILE}"
}

show_footer() {
    local exit_code="$1"
    local status="${2:-}"

    echo -e "${COLOR_BLUE}=======================================================${COLOR_NC}"
    if [ "$exit_code" -eq 0 ]; then
        if [ "$status" = "no_update" ]; then
            log_message INFO "No core update available for this client."
            echo -e "${COLOR_YELLOW}  No core update available.${COLOR_NC}"
        else
            log_message SUCCESS "Core update applied successfully."
            echo -e "${COLOR_GREEN}  CORE UPDATE COMPLETED.${COLOR_NC}"
            if [ -n "$CORE_DOWNLOAD_VERSION" ]; then
                echo -e "  Version applied: ${CORE_DOWNLOAD_VERSION}"
            fi
            echo -e ""
            echo -e "${COLOR_YELLOW}  Please restart Home Assistant to apply changes.${COLOR_NC}"
        fi
    else
        log_message ERROR "Core update failed with code $exit_code"
        echo -e "${COLOR_RED}  CORE UPDATE FAILED.${COLOR_NC}"
    fi
    echo -e "${COLOR_BLUE}=======================================================${COLOR_NC}\n"
}

usage() {
    cat <<EOF
Usage: bash core_update.sh

Requires HOMECORE_TOKEN (environment variable) with the token configured in the HomeCore integration.
EOF
}

check_prerequisites() {
    log_message INFO "Checking prerequisites (curl and unzip)..."
    if ! command -v curl >/dev/null 2>&1; then
        log_message ERROR "curl not found"
        return 1
    fi
    if ! command -v unzip >/dev/null 2>&1; then
        log_message ERROR "unzip not found"
        return 1
    fi
    log_message SUCCESS "Prerequisites satisfied."
}

resolve_token() {
    if [ -n "${HOMECORE_TOKEN:-}" ]; then
        echo "${HOMECORE_TOKEN}" | tr -d '[:space:]'
        return 0
    fi

    local token_file="${CONFIG_DIR}/homecore/token"
    if [ -f "$token_file" ]; then
        tr -d '[:space:]' <"$token_file"
        return 0
    fi

    log_message ERROR "HomeCore token not found (set HOMECORE_TOKEN or file ${token_file})."
    return 1
}

perform_backup() {
    local backup_root="${CONFIG_DIR}/homecore/backups/core_$(date +%Y%m%dT%H%M)"
    local packages_dir="${CONFIG_DIR}/packages"
    local www_dir="${CONFIG_DIR}/www"
    local manifest="${CONFIG_DIR}/homecore/core_manifest.json"

    mkdir -p "$backup_root"

    if [ -d "$packages_dir" ]; then
        log_message INFO "Backing up packages to ${backup_root}/packages"
        cp -a "$packages_dir" "${backup_root}/packages"
    fi

    if [ -d "${www_dir}/homecore" ]; then
        log_message INFO "Backing up www/homecore to ${backup_root}/www/homecore"
        mkdir -p "${backup_root}/www"
        cp -a "${www_dir}/homecore" "${backup_root}/www/homecore"
    fi

    if [ -f "$manifest" ]; then
        log_message INFO "Backing up core_manifest.json"
        cp -a "$manifest" "${backup_root}/core_manifest.json"
    fi
}

get_local_core_version() {
    local manifest="${CONFIG_DIR}/homecore/core_manifest.json"
    if [ ! -f "$manifest" ]; then
        echo ""
        return 0
    fi

    python3 - <<'PY' "$manifest" 2>/dev/null || true
import json, sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    data = json.loads(path.read_text())
except Exception:
    sys.exit(0)

version = data.get("version")
if isinstance(version, (str, int, float)):
    print(str(version))
PY
}

download_and_extract() {
    local token="$1"
    local metadata
    local artifact_url
    local checksum
    local version

    metadata=$(curl -fsSL -H "Authorization: Bearer ${token}" "${SYNC_ENDPOINT}?action=client_version" 2>>"$LOG_FILE" || true)
    if [ -z "$metadata" ]; then
        log_message INFO "No response from client_version endpoint; assuming no update."
        CORE_DOWNLOAD_VERSION=""
        return 2
    fi

    artifact_url=""
    checksum=""
    version=""

    read -r artifact_url checksum version <<EOF
$(python3 - <<'PY'
import json
import sys

try:
    data = json.loads(sys.stdin.read())
except Exception:
    print("\n\n")
    sys.exit(0)

artifact = data.get("core_artifact_url") or data.get("core_artifact") or ""
checksum = data.get("core_checksum") or ""
version = data.get("core_version") or ""

releases = data.get("releases") or []
for item in releases:
    if isinstance(item, dict) and item.get("kind") == "core":
        artifact = item.get("artifact_url") or item.get("url") or artifact
        checksum = item.get("checksum") or checksum
        version = item.get("version") or version
        break

print(artifact or "")
print(checksum or "")
print(version or "")
PY
<<<"$metadata")
EOF

    if [ -z "$artifact_url" ]; then
        log_message INFO "No core release reported for this client."
        CORE_DOWNLOAD_VERSION=""
        return 2
    fi

    CORE_DOWNLOAD_VERSION="$version"

    local local_version=""
    local_version=$(get_local_core_version)
    if [ -n "$version" ] && [ -n "$local_version" ] && [ "$version" = "$local_version" ]; then
        log_message INFO "Core version ${version} already installed; skipping download."
        CORE_DOWNLOAD_VERSION="$version"
        return 2
    fi

    if [[ "$artifact_url" != http* ]]; then
        artifact_url="${CORE_BASE_URL%/}/${artifact_url#./}"
    fi

    local tmp_zip
    local tmp_dir
    tmp_zip=$(mktemp -t core_update.XXXXXX)
    tmp_dir=$(mktemp -d -t core_update.extract.XXXXXX)

    log_message INFO "Downloading core package from ${artifact_url}"

    local attempt=0
    local success=0
    local no_update=0
    while [ $attempt -lt $MAX_RETRIES ]; do
        attempt=$((attempt + 1))
        log_message INFO "Download attempt ${attempt}/${MAX_RETRIES}"
        if curl -fSL -H "Authorization: Bearer ${token}" --insecure "$artifact_url" -o "$tmp_zip" 2>>"$LOG_FILE"; then
            success=1
            break
        else
            local status=$?
            if [ "$status" -eq 22 ]; then
                log_message INFO "Core artifact returned HTTP 404; treating as no update."
                no_update=1
                break
            fi
            log_message WARN "Download failed with status $status"
            if [ $attempt -lt $MAX_RETRIES ]; then
                sleep "$RETRY_DELAY"
            fi
        fi
    done

    if [ $no_update -eq 1 ]; then
        rm -f "$tmp_zip"
        rm -rf "$tmp_dir"
        CORE_DOWNLOAD_VERSION=""
        return 2
    fi

    if [ $success -eq 0 ]; then
        log_message ERROR "Unable to download core package after ${MAX_RETRIES} attempts."
        rm -f "$tmp_zip"
        rm -rf "$tmp_dir"
        CORE_DOWNLOAD_VERSION=""
        return 1
    fi

    if [ ! -s "$tmp_zip" ]; then
        log_message ERROR "Downloaded file is empty."
        rm -f "$tmp_zip"
        rm -rf "$tmp_dir"
        CORE_DOWNLOAD_VERSION=""
        return 1
    fi

    if [ -n "$checksum" ]; then
        if ! echo "${checksum}  ${tmp_zip}" | sha256sum -c - >/dev/null 2>>"$LOG_FILE"; then
            log_message ERROR "Checksum validation failed."
            rm -f "$tmp_zip"
            rm -rf "$tmp_dir"
            CORE_DOWNLOAD_VERSION=""
            return 1
        fi
        log_message SUCCESS "Checksum validated."
    else
        log_message WARN "Checksum not provided; continuing without validation."
    fi

    log_message INFO "Extracting package..."
    if ! unzip -oq "$tmp_zip" -d "$tmp_dir" 2>>"$LOG_FILE"; then
        log_message ERROR "Failed to extract package."
        rm -f "$tmp_zip"
        rm -rf "$tmp_dir"
        CORE_DOWNLOAD_VERSION=""
        return 1
    fi
    rm -f "$tmp_zip"

    local staging_dir="$tmp_dir"
    local entries
    mapfile -t entries < <(find "$tmp_dir" -mindepth 1 -maxdepth 1)
    if [ "${#entries[@]}" -eq 1 ] && [ -d "${entries[0]}" ]; then
        staging_dir="${entries[0]}"
        log_message INFO "Detected nested directory ${staging_dir}; using it as payload root."
    fi

    echo "$staging_dir"
    return 0
}

apply_core_payload() {
    local source_dir="$1"
    local packages_dir="${CONFIG_DIR}/packages"
    local www_dir="${CONFIG_DIR}/www"
    local manifest="${CONFIG_DIR}/homecore/core_manifest.json"

    log_message INFO "Applying core payload from ${source_dir}"

    if [ -d "${source_dir}/packages" ]; then
        log_message INFO "Updating ${packages_dir}"
        mkdir -p "$packages_dir"
        cp -a "${source_dir}/packages/." "$packages_dir/"
    fi

    if [ -d "${source_dir}/www" ]; then
        log_message INFO "Updating ${www_dir}"
        mkdir -p "$www_dir"
        cp -a "${source_dir}/www/." "$www_dir/"
    fi

    if [ -f "${source_dir}/core_manifest.json" ]; then
        log_message INFO "Updating core_manifest.json"
        mkdir -p "$(dirname "$manifest")"
        cp -a "${source_dir}/core_manifest.json" "$manifest"
    fi
}

cleanup_temp() {
    local path="$1"
    if [ -n "$path" ] && [ -d "$path" ]; then
        rm -rf "$path"
    fi
}

main() {
    mkdir -p "$LOG_DIR"
    show_header

    if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
        usage
        exit 0
    fi

    if ! check_prerequisites; then
        show_footer 1
        exit 1
    fi

    local token=""
    if ! token=$(resolve_token); then
        show_footer 1
        exit 1
    fi
    log_message SUCCESS "Token resolved successfully."

    perform_backup

    local temp_dir=""
    CORE_DOWNLOAD_VERSION=""

    if temp_dir=$(download_and_extract "$token"); then
        apply_core_payload "$temp_dir"
        cleanup_temp "$temp_dir"
        show_footer 0
        exit 0
    else
        local status=$?
        cleanup_temp "$temp_dir"
        if [ "$status" -eq 2 ]; then
            show_footer 0 "no_update"
            exit 0
        fi
        show_footer 1
        exit 1
    fi
}

main "$@"
