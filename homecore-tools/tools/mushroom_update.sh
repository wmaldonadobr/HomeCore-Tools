#!/bin/bash
# ========================================
# Instalação/Atualização do Lovelace Mushroom
# ========================================
# Verifique novas versões no repositório oficial e atualize 
# a variável MUSHROOM_VERSION conforme necessário.
# Link: https://github.com/piitaya/lovelace-mushroom/tags
# ========================================

set -e

MUSHROOM_DIR="/config/www/lovelace-mushroom"
MUSHROOM_VERSION="v5.0.8"  # 🟢 Altere aqui para atualizar manualmente
MUSHROOM_REPO="piitaya/lovelace-mushroom"

echo ""
echo "========================================="
echo "Atualizando Lovelace Mushroom ($MUSHROOM_VERSION)"
echo "========================================="

mkdir -p "$MUSHROOM_DIR"
cd "$MUSHROOM_DIR"

# Baixa o arquivo principal
wget -q "https://github.com/$MUSHROOM_REPO/releases/download/$MUSHROOM_VERSION/mushroom.js" -O mushroom.js || {
  echo "❌ Falha ao baixar mushroom.js"
  exit 1
}

# Verifica se o arquivo foi baixado
if [ -f "mushroom.js" ]; then
  echo "✅ Lovelace Mushroom atualizado com sucesso para $MUSHROOM_VERSION"
  ls -lh mushroom.js
else
  echo "⚠️ Arquivo mushroom.js não encontrado após o download."
fi