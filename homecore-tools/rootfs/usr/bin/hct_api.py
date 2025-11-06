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
from flask_cors import CORS

# Importar módulos HCT
sys.path.insert(0, '/usr/bin')
from hct_logger import get_logger
from hct_updater import HCTUpdater

logger = get_logger("hct-api")

app = Flask(__name__)
CORS(app)

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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HomeCore Tools</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 32px;
            margin-bottom: 10px;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 16px;
        }
        
        .card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .card h2 {
            font-size: 20px;
            margin-bottom: 15px;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .status-item {
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        
        .status-item label {
            display: block;
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        
        .status-item value {
            display: block;
            font-size: 18px;
            font-weight: bold;
            color: #333;
        }
        
        .update-item {
            padding: 15px;
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        
        .update-item h3 {
            font-size: 16px;
            margin-bottom: 5px;
            color: #856404;
        }
        
        .update-item p {
            font-size: 14px;
            color: #856404;
        }
        
        .no-updates {
            padding: 20px;
            text-align: center;
            color: #28a745;
            background: #d4edda;
            border-radius: 5px;
            border: 1px solid #c3e6cb;
        }
        
        .btn {
            display: inline-block;
            padding: 12px 24px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            text-decoration: none;
            transition: background 0.3s;
        }
        
        .btn:hover {
            background: #5568d3;
        }
        
        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        
        .btn-success {
            background: #28a745;
        }
        
        .btn-success:hover {
            background: #218838;
        }
        
        .btn-group {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        
        .log-entry {
            padding: 10px;
            background: #f8f9fa;
            border-left: 3px solid #6c757d;
            border-radius: 3px;
            margin-bottom: 8px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }
        
        .log-entry.info {
            border-left-color: #17a2b8;
        }
        
        .log-entry.success {
            border-left-color: #28a745;
        }
        
        .log-entry.warning {
            border-left-color: #ffc107;
        }
        
        .log-entry.error {
            border-left-color: #dc3545;
        }
        
        .log-time {
            color: #6c757d;
            margin-right: 10px;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: #666;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛠️ HomeCore Tools</h1>
            <p>Sistema de Manutenção e Atualização Automática</p>
        </div>
        
        <div class="card">
            <h2>📊 Status do Sistema</h2>
            <div class="status-grid" id="status-grid">
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Carregando...</p>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>🔄 Atualizações Disponíveis</h2>
            <div id="updates-container">
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Verificando...</p>
                </div>
            </div>
            <div class="btn-group">
                <button class="btn" onclick="checkUpdates()">🔍 Verificar Atualizações</button>
                <button class="btn btn-success" onclick="applyUpdates()" id="apply-btn" disabled>✅ Aplicar Atualizações</button>
            </div>
        </div>
        
        <div class="card">
            <h2>📝 Logs Recentes</h2>
            <div id="logs-container">
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Carregando logs...</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let updatesAvailable = [];
        
        async function loadStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                const statusGrid = document.getElementById('status-grid');
                statusGrid.innerHTML = `
                    <div class="status-item">
                        <label>Token</label>
                        <value>${data.token ? '✅ Configurado' : '❌ Não encontrado'}</value>
                    </div>
                    <div class="status-item">
                        <label>Última Verificação</label>
                        <value>${data.last_check || 'Nunca'}</value>
                    </div>
                    <div class="status-item">
                        <label>Auto-Update</label>
                        <value>${data.auto_update ? '✅ Habilitado' : '❌ Desabilitado'}</value>
                    </div>
                    <div class="status-item">
                        <label>Intervalo</label>
                        <value>${data.check_interval / 60} min</value>
                    </div>
                `;
            } catch (error) {
                console.error('Erro ao carregar status:', error);
            }
        }
        
        async function loadUpdates() {
            try {
                const response = await fetch('/api/manifests');
                const data = await response.json();
                
                updatesAvailable = data.updates || [];
                const container = document.getElementById('updates-container');
                const applyBtn = document.getElementById('apply-btn');
                
                if (updatesAvailable.length === 0) {
                    container.innerHTML = '<div class="no-updates">✅ Sistema atualizado! Nenhuma atualização disponível.</div>';
                    applyBtn.disabled = true;
                } else {
                    container.innerHTML = updatesAvailable.map(update => `
                        <div class="update-item">
                            <h3>📦 ${update.type.toUpperCase()}</h3>
                            <p><strong>Atual:</strong> ${update.current} → <strong>Disponível:</strong> ${update.available}</p>
                        </div>
                    `).join('');
                    applyBtn.disabled = false;
                }
            } catch (error) {
                console.error('Erro ao carregar atualizações:', error);
            }
        }
        
        async function loadLogs() {
            try {
                const response = await fetch('/api/logs?limit=20');
                const data = await response.json();
                
                const container = document.getElementById('logs-container');
                
                if (data.logs.length === 0) {
                    container.innerHTML = '<p style="text-align: center; color: #666;">Nenhum log disponível</p>';
                } else {
                    container.innerHTML = data.logs.reverse().map(log => {
                        const time = new Date(log.timestamp).toLocaleString('pt-BR');
                        const levelClass = log.status || log.level.toLowerCase();
                        return `
                            <div class="log-entry ${levelClass}">
                                <span class="log-time">${time}</span>
                                <strong>${log.component}</strong> - ${log.action}: ${log.details.message || JSON.stringify(log.details)}
                            </div>
                        `;
                    }).join('');
                }
            } catch (error) {
                console.error('Erro ao carregar logs:', error);
            }
        }
        
        async function checkUpdates() {
            const container = document.getElementById('updates-container');
            container.innerHTML = '<div class="loading"><div class="spinner"></div><p>Verificando atualizações...</p></div>';
            
            try {
                const response = await fetch('/api/update/check', { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    await loadUpdates();
                } else {
                    container.innerHTML = `<div class="no-updates" style="background: #f8d7da; border-color: #f5c6cb; color: #721c24;">❌ Erro ao verificar atualizações</div>`;
                }
            } catch (error) {
                console.error('Erro ao verificar atualizações:', error);
                container.innerHTML = `<div class="no-updates" style="background: #f8d7da; border-color: #f5c6cb; color: #721c24;">❌ Erro: ${error.message}</div>`;
            }
        }
        
        async function applyUpdates() {
            if (updatesAvailable.length === 0) {
                alert('Nenhuma atualização disponível para aplicar');
                return;
            }
            
            if (!confirm(`Deseja aplicar ${updatesAvailable.length} atualização(ões)? O sistema criará um backup antes.`)) {
                return;
            }
            
            const container = document.getElementById('updates-container');
            container.innerHTML = '<div class="loading"><div class="spinner"></div><p>Aplicando atualizações... Isso pode levar alguns minutos.</p></div>';
            
            try {
                const response = await fetch('/api/update/apply', { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    container.innerHTML = `
                        <div class="no-updates" style="background: #d4edda; border-color: #c3e6cb; color: #155724;">
                            ✅ Atualizações aplicadas com sucesso!<br>
                            <strong>Sucesso:</strong> ${data.success_count}<br>
                            ${data.failed_count > 0 ? `<strong>Falhas:</strong> ${data.failed_count}` : ''}
                            <br><br>
                            ⚠️ Reinicie o Home Assistant para aplicar as configurações.
                        </div>
                    `;
                    await loadUpdates();
                    await loadLogs();
                } else {
                    container.innerHTML = `<div class="no-updates" style="background: #f8d7da; border-color: #f5c6cb; color: #721c24;">❌ Erro ao aplicar atualizações</div>`;
                }
            } catch (error) {
                console.error('Erro ao aplicar atualizações:', error);
                container.innerHTML = `<div class="no-updates" style="background: #f8d7da; border-color: #f5c6cb; color: #721c24;">❌ Erro: ${error.message}</div>`;
            }
        }
        
        // Carregar dados iniciais
        loadStatus();
        loadUpdates();
        loadLogs();
        
        // Atualizar a cada 30 segundos
        setInterval(() => {
            loadStatus();
            loadLogs();
        }, 30000);
    </script>
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
    """Executa servidor Flask."""
    logger.info("hct-api", "startup", f"Iniciando servidor web em {host}:{port}")
    
    # Desabilitar TODOS os logs do Flask/Werkzeug redirecionando stderr
    # Isso evita que logs contaminem respostas JSON via Ingress
    import os
    sys.stderr = open(os.devnull, 'w')
    
    # Desabilitar loggers
    logging.getLogger('werkzeug').disabled = True
    app.logger.disabled = True
    
    # Iniciar servidor silencioso
    app.run(host=host, port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    # Teste standalone
    logger.info("hct-api", "test", "Modo de teste - API sem updater")
    run_api()
