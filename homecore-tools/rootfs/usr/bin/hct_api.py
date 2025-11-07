#!/usr/bin/env python3
"""
HomeCore Tools - API REST e Dashboard Web
Interface web para monitoramento e controle via Ingress
"""

import os
import sys
import json
import logging
from pathlib import Path
from flask import Flask, jsonify, request, render_template_string

# Importar módulos HCT
sys.path.insert(0, '/usr/bin')
from hct_logger import get_logger
from hct_updater import HCTUpdater

logger = get_logger("hct-api")

app = Flask(__name__)

# Estado global
state = {
    "token": None,
    "updater": None,
    "last_check": None,
    "updates_available": []
}


# HTML do Dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>HomeCore Tools</title>
    <style>
        body {
            margin: 0;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #f5f5f5;
            color: #333;
        }
        .title {
            font-size: 32px;
            font-weight: 600;
        }
        .subtitle {
            margin-top: 10px;
            font-size: 14px;
            opacity: 0.6;
        }
    </style>
</head>
<body>
    <div class="title">HomeCore Tools</div>
    <div class="subtitle">Funcionalidades exclusivas em breve</div>
</body>
</html>
"""


@app.route('/')
def dashboard():
    """Página principal do dashboard."""
    return render_template_string(DASHBOARD_HTML)


@app.route('/api/status')
def api_status():
    """Retorna status atual do sistema."""
    return jsonify({
        "token": state["token"] is not None,
        "last_check": state.get("last_check"),
        "auto_update": os.environ.get('HCT_AUTO_UPDATE', 'true').lower() == 'true',
        "check_interval": int(os.environ.get('HCT_CHECK_INTERVAL', '3600')),
        "log_level": os.environ.get('HCT_LOG_LEVEL', 'INFO')
    })


@app.route('/api/manifests')
def api_manifests():
    """Retorna manifests e atualizações disponíveis."""
    return jsonify({
        "updates": state.get("updates_available", [])
    })


@app.route('/api/logs')
def api_logs():
    """Retorna logs recentes."""
    limit = request.args.get('limit', 100, type=int)
    
    try:
        logs = logger.get_recent_logs(limit=limit)
        return jsonify({"logs": logs})
    except Exception as e:
        logger.error("hct-api", "api_logs", "Erro ao obter logs", exception=e)
        return jsonify({"error": str(e)}), 500


@app.route('/api/update/check', methods=['POST'])
def api_update_check():
    """Verifica atualizações disponíveis."""
    if not state.get("updater"):
        return jsonify({"success": False, "error": "Updater não inicializado"}), 500
    
    try:
        logger.info("hct-api", "update_check", "Verificando atualizações via API")
        updates = state["updater"].check_updates()
        state["updates_available"] = updates
        state["last_check"] = json.dumps({"time": "now"})
        
        return jsonify({
            "success": True,
            "updates": updates
        })
    except Exception as e:
        logger.error("hct-api", "update_check", "Erro ao verificar atualizações", exception=e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/update/apply', methods=['POST'])
def api_update_apply():
    """Aplica atualizações disponíveis."""
    if not state.get("updater"):
        return jsonify({"success": False, "error": "Updater não inicializado"}), 500
    
    updates = state.get("updates_available", [])
    
    if not updates:
        return jsonify({"success": False, "error": "Nenhuma atualização disponível"}), 400
    
    try:
        logger.info("hct-api", "update_apply", f"Aplicando {len(updates)} atualização(ões) via API")
        
        success_count = 0
        failed_count = 0
        
        for update in updates:
            if state["updater"].update(update):
                success_count += 1
            else:
                failed_count += 1
        
        # Limpar lista de atualizações
        state["updates_available"] = []
        
        return jsonify({
            "success": True,
            "success_count": success_count,
            "failed_count": failed_count
        })
    except Exception as e:
        logger.error("hct-api", "update_apply", "Erro ao aplicar atualizações", exception=e)
        return jsonify({"success": False, "error": str(e)}), 500


def init_api(token: str, updater: HCTUpdater):
    """Inicializa a API com token e updater."""
    state["token"] = token
    state["updater"] = updater
    logger.info("hct-api", "init", "API inicializada")

def run_api(host: str = '0.0.0.0', port: int = 8099):
    """Executa servidor Flask com wsgiref (silencioso)."""
    logger.info("hct-api", "startup", f"Iniciando servidor web em {host}:{port}")
    
    # Usar wsgiref ao invés do servidor Flask padrão
    # wsgiref não imprime logs de inicialização
    from wsgiref.simple_server import make_server
    import os
    
    # Redirecionar stderr para evitar qualquer log
    sys.stderr = open(os.devnull, 'w')
    
    # Desabilitar loggers do Flask
    logging.getLogger('werkzeug').disabled = True
    app.logger.disabled = True
    
    # Criar e iniciar servidor wsgiref (100% silencioso)
    server = make_server(host, port, app)
    server.serve_forever()

if __name__ == "__main__":
    # Teste standalone
    logger.info("hct-api", "test", "Modo de teste - API sem updater")
    run_api()