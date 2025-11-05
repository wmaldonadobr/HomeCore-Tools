#!/usr/bin/env bash
set -euo pipefail

mkdir -p /data/logs \
         /data/backups/api \
         /data/backups/core \
         /data/backups/hcc

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8125}"
