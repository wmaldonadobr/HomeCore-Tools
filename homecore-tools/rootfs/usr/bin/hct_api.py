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


# ============================================================================
# ROTAS DO DASHBOARD
# ============================================================================

@app.route('/')
def dashboard():
    """Dashboard principal com cards de versões e menu de ferramentas."""
    return render_template_string(DASHBOARD_HTML)


@app.route('/tools/sendhex')
def tool_sendhex():
    """Ferramenta de envio IR (Pronto HEX)."""
    return render_template_string(SENDHEX_HTML)


@app.route('/tools/sendir')
def tool_sendir():
    """Ferramenta de envio IR (SendIR/GC)."""
    return render_template_string(SENDIR_HTML)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/status')
def api_status():
    """Retorna status do sistema e versões dos manifests."""
    try:
        if not state.get("updater"):
            return jsonify({"error": "Updater não inicializado"}), 500
        
        # Buscar manifests para obter versões
        manifests = {}
        for manifest_type in ['core', 'hcc', 'molsmart']:
            manifest = state["updater"].fetch_manifest(manifest_type)
            if manifest:
                manifests[manifest_type] = {
                    "version": manifest.get("version", "N/A"),
                    "available": True
                }
            else:
                manifests[manifest_type] = {
                    "version": "N/A",
                    "available": False
                }
        
        return jsonify({
            "status": "ok",
            "manifests": manifests,
            "last_check": state.get("last_check"),
            "updates_available": len(state.get("updates_available", []))
        })
    
    except Exception as e:
        logger.error("hct-api", "api_status", "Erro ao obter status", exception=e)
        return jsonify({"error": str(e)}), 500


# ============================================================================
# TEMPLATES HTML
# ============================================================================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HomeCore Tools</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;
            background: #f6f7fb;
            padding: 24px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
            color: white;
            padding: 32px;
            border-radius: 12px;
            margin-bottom: 24px;
            box-shadow: 0 8px 20px rgba(37, 99, 235, 0.15);
        }
        
        .header h1 {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
        }
        
        .header p {
            opacity: 0.95;
            font-size: 15px;
        }
        
        .section-title {
            font-size: 18px;
            font-weight: 600;
            color: #0f172a;
            margin: 32px 0 16px 0;
            padding-bottom: 8px;
            border-bottom: 2px solid #e2e8f0;
        }
        
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            margin-bottom: 32px;
        }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            border: 1px solid #e2e8f0;
        }
        
        .card-header {
            font-size: 13px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
        }
        
        .card-value {
            font-size: 32px;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 8px;
        }
        
        .card-label {
            font-size: 14px;
            color: #475569;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            margin-top: 8px;
        }
        
        .badge.success { background: #dcfce7; color: #166534; }
        .badge.warning { background: #fef3c7; color: #92400e; }
        .badge.error { background: #fee2e2; color: #991b1b; }
        
        .tools-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 16px;
        }
        
        .tool-card {
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            border: 1px solid #e2e8f0;
            transition: all 0.2s;
            cursor: pointer;
            text-decoration: none;
            color: inherit;
            display: block;
        }
        
        .tool-card:hover {
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
        }
        
        .tool-icon {
            font-size: 32px;
            margin-bottom: 12px;
        }
        
        .tool-title {
            font-size: 18px;
            font-weight: 600;
            color: #0f172a;
            margin-bottom: 8px;
        }
        
        .tool-desc {
            font-size: 14px;
            color: #64748b;
            line-height: 1.5;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: #64748b;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛠️ HomeCore Tools</h1>
            <p>Sistema de Manutenção e Atualização Automática</p>
        </div>
        
        <div class="section-title">📊 Versões dos Sistemas</div>
        <div class="cards-grid" id="versions-grid">
            <div class="loading">Carregando informações...</div>
        </div>
        
        <div class="section-title">🔧 Ferramentas</div>
        <div class="tools-grid">
            <a href="/tools/sendhex" class="tool-card">
                <div class="tool-icon">📡</div>
                <div class="tool-title">Enviar IR (Pronto HEX)</div>
                <div class="tool-desc">Envie comandos infravermelhos usando códigos Pronto HEX para dispositivos GW3 na rede local.</div>
            </a>
            
            <a href="/tools/sendir" class="tool-card">
                <div class="tool-icon">📻</div>
                <div class="tool-title">Enviar IR (SendIR/GC)</div>
                <div class="tool-desc">Envie comandos infravermelhos usando formato SendIR/GC para dispositivos compatíveis.</div>
            </a>
        </div>
    </div>
    
    <script>
        async function loadVersions() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                const grid = document.getElementById('versions-grid');
                grid.innerHTML = '';
                
                const manifests = data.manifests || {};
                const types = {
                    'core': 'Home Assistant Core',
                    'hcc': 'HomeCore Custom',
                    'molsmart': 'Molsmart'
                };
                
                for (const [key, label] of Object.entries(types)) {
                    const manifest = manifests[key] || {};
                    const version = manifest.version || 'N/A';
                    const available = manifest.available;
                    
                    const card = document.createElement('div');
                    card.className = 'card';
                    card.innerHTML = `
                        <div class="card-header">${label}</div>
                        <div class="card-value">${version}</div>
                        <div class="card-label">Versão atual</div>
                        <span class="badge ${available ? 'success' : 'warning'}">
                            ${available ? '✓ Disponível' : '⚠ Não disponível'}
                        </span>
                    `;
                    grid.appendChild(card);
                }
                
            } catch (error) {
                document.getElementById('versions-grid').innerHTML = 
                    '<div class="loading">❌ Erro ao carregar informações</div>';
            }
        }
        
        // Carregar ao iniciar
        loadVersions();
        
        // Atualizar a cada 30 segundos
        setInterval(loadVersions, 30000);
    </script>
</body>
</html>
"""

SENDHEX_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <title>GW3 • Envio IR (Pronto HEX)</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; background:#f6f7fb; margin:0; padding:24px; }
    .wrap { max-width: 960px; margin: 0 auto; background:#fff; border-radius:12px; padding:24px; box-shadow: 0 8px 20px rgba(0,0,0,.06); }
    .back-link { display: inline-block; margin-bottom: 20px; color: #2563eb; text-decoration: none; font-weight: 600; }
    .back-link:hover { text-decoration: underline; }
    h1 { font-size: 22px; margin: 0 0 18px; color:#0f172a; }
    .grid { display:grid; grid-template-columns: repeat(3, 1fr); gap:14px; }
    .full { grid-column: 1 / -1; }
    label { font-size: 13px; color:#334155; margin-bottom:6px; display:block; }
    input[type="text"], textarea {
      width:100%; box-sizing:border-box; border:1px solid #cbd5e1; border-radius:8px; padding:10px 12px; font-size:14px; outline:none;
      transition: box-shadow .2s, border-color .2s;
    }
    input:focus, textarea:focus { border-color:#2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,.15); }
    textarea { min-height: 160px; resize: vertical; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }
    .row { display:flex; gap:10px; align-items:center; }
    .btn {
      background:#2563eb; color:#fff; border:0; border-radius:10px; padding:12px 18px; font-weight:600; cursor:pointer; font-size:14px;
    }
    .btn.secondary { background:#475569; }
    .btn.warn { background:#dc2626; }
    .btn:disabled { opacity:.6; cursor:not-allowed; }
    .status { margin-top:14px; padding:12px; border-radius:8px; display:none; white-space:pre-wrap; }
    .ok { background:#dcfce7; color:#166534; display:block; }
    .err { background:#fee2e2; color:#991b1b; display:block; }
    .hint { color:#475569; font-size:12px; margin-top:6px; }
    .checkbox { display:flex; align-items:center; gap:8px; }
  </style>
</head>
<body>
  <div class="wrap">
    <a href="/" class="back-link">← Voltar ao Dashboard</a>
    <h1>GW3 • Envio de Códigos IR (POST • x-www-form-urlencoded)</h1>

    <div class="grid">
      <div>
        <label for="ip">IP do GW3</label>
        <input id="ip" type="text" placeholder="192.168.1.112" autocomplete="off">
      </div>
      <div>
        <label for="serial">Serial (serialNum)</label>
        <input id="serial" type="text" placeholder="P130-C101-A0794" autocomplete="off">
      </div>
      <div>
        <label for="pwd">Senha (verifyCode)</label>
        <input id="pwd" type="text" placeholder="72856898" autocomplete="off">
      </div>

      <div>
        <label for="c">Parâmetro c</label>
        <input id="c" type="text" placeholder="1" autocomplete="off">
      </div>
      <div>
        <label for="r">Parâmetro r</label>
        <input id="r" type="text" placeholder="2" autocomplete="off">
      </div>
      <div class="checkbox">
        <input id="upper" type="checkbox">
        <label for="upper">HEX em maiúsculas</label>
      </div>

      <div class="full">
        <label for="pronto">Código Pronto HEX (com espaços)</label>
        <textarea id="pronto" placeholder="Ex.: 0000 006D 0022 0002 0157 00AC 0015 0016 0015 0041 ..."></textarea>
        <div class="hint">Cole exatamente com espaços; o formulário codifica automaticamente. Todos os campos são salvos no seu navegador (localStorage).</div>
      </div>

      <div class="full row">
        <button class="btn" id="send">📡 Enviar (POST)</button>
        <button class="btn secondary" id="preview">🧪 Pré-visualizar corpo</button>
        <button class="btn warn" id="clear">🧹 Limpar dados salvos</button>
      </div>
    </div>

    <div id="status" class="status"></div>
  </div>

  <script>
    const F = {
      ip: document.getElementById('ip'),
      serial: document.getElementById('serial'),
      pwd: document.getElementById('pwd'),
      c: document.getElementById('c'),
      r: document.getElementById('r'),
      upper: document.getElementById('upper'),
      pronto: document.getElementById('pronto'),
      status: document.getElementById('status'),
      send: document.getElementById('send'),
      preview: document.getElementById('preview'),
      clear: document.getElementById('clear')
    };

    const KEYS = {
      ip: 'gw3_ip',
      serial: 'gw3_serial',
      pwd: 'gw3_pwd',
      c: 'gw3_c',
      r: 'gw3_r',
      pronto: 'gw3_pronto',
      upper: 'gw3_upper'
    };

    function load() {
      F.ip.value     = localStorage.getItem(KEYS.ip)     || '192.168.1.112';
      F.serial.value = localStorage.getItem(KEYS.serial) || 'P130-C101-A0794';
      F.pwd.value    = localStorage.getItem(KEYS.pwd)    || '72856898';
      F.c.value      = localStorage.getItem(KEYS.c)      || '1';
      F.r.value      = localStorage.getItem(KEYS.r)      || '2';
      F.pronto.value = localStorage.getItem(KEYS.pronto) || '';
      F.upper.checked = (localStorage.getItem(KEYS.upper) || '0') === '1';
    }

    function bindAutosave() {
      const saveText = (el, key) => el.addEventListener('input', () => localStorage.setItem(key, el.value));
      const saveCheck = (el, key) => el.addEventListener('change', () => localStorage.setItem(key, el.checked ? '1' : '0'));

      saveText(F.ip, KEYS.ip);
      saveText(F.serial, KEYS.serial);
      saveText(F.pwd, KEYS.pwd);
      saveText(F.c, KEYS.c);
      saveText(F.r, KEYS.r);
      saveText(F.pronto, KEYS.pronto);
      saveCheck(F.upper, KEYS.upper);
    }

    function normalizeHex(s) {
      let v = s.replace(/\\s+/g, ' ').trim();
      if (F.upper.checked) v = v.toUpperCase();
      return v;
    }

    function build() {
      const ip = F.ip.value.trim();
      const serial = F.serial.value.trim();
      const pwd = F.pwd.value.trim();
      const c = F.c.value.trim();
      const r = F.r.value.trim();
      let pronto = normalizeHex(F.pronto.value);

      if (!ip || !serial || !pwd || !c || !r || !pronto) {
        throw new Error('Preencha IP, serial, senha, c, r e o código Pronto HEX.');
      }

      const url = `http://${ip}/api/device/deviceDetails/smartHomeAutoHttpControl`;
      const body = new URLSearchParams();
      body.append('serialNum', serial);
      body.append('verifyCode', pwd);
      body.append('pronto', pronto);
      body.append('c', c);
      body.append('r', r);
      return { url, body };
    }

    function showOK(msg) {
      F.status.className = 'status ok';
      F.status.textContent = msg;
    }
    function showERR(msg) {
      F.status.className = 'status err';
      F.status.textContent = msg;
    }

    async function send() {
      try {
        const { url, body } = build();
        await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body,
          mode: 'no-cors'
        });
        showOK('✅ Enviado! (POST x-www-form-urlencoded com pronto=...)');
      } catch (e) {
        showERR('❌ ' + e.message);
      }
    }

    function preview() {
      try {
        const { url, body } = build();
        showOK(`URL:\\n${url}\\n\\nBody:\\n${body.toString()}`);
      } catch (e) {
        showERR('❌ ' + e.message);
      }
    }

    function clearAll() {
      Object.values(KEYS).forEach(k => localStorage.removeItem(k));
      load();
      showOK('🧹 Dados salvos apagados.');
    }

    document.addEventListener('DOMContentLoaded', () => {
      load();
      bindAutosave();
      F.send.addEventListener('click', send);
      F.preview.addEventListener('click', preview);
      F.clear.addEventListener('click', clearAll);
    });
  </script>
</body>
</html>
"""

SENDIR_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Ferramenta de Envio de Comandos IR - SendIR / GC</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap' );
        body {
            font-family: 'Roboto', sans-serif;
            background-color: #f6f7fb;
            color: #333;
            margin: 0;
            padding: 24px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .container {
            width: 100%;
            max-width: 900px;
            background: #fff;
            padding: 2em;
            border-radius: 12px;
            box-shadow: 0 8px 20px rgba(0,0,0,.06);
        }
        .back-link {
            display: inline-block;
            margin-bottom: 20px;
            color: #2563eb;
            text-decoration: none;
            font-weight: 600;
        }
        .back-link:hover {
            text-decoration: underline;
        }
        h1 {
            font-size: 1.8em;
            color: #1e3a8a;
            margin-top: 0;
            margin-bottom: 1em;
            text-align: center;
        }
        .form-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 1.5em;
        }
        .form-group {
            display: flex;
            flex-direction: column;
        }
        .full-width {
            grid-column: 1 / -1;
        }
        label {
            font-weight: 500;
            margin-bottom: 0.5em;
            color: #374151;
        }
        input, textarea {
            padding: 10px;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            font-family: 'Roboto', sans-serif;
            font-size: 1em;
            transition: border-color 0.3s, box-shadow 0.3s;
        }
        input:focus, textarea:focus {
            border-color: #2563eb;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2);
            outline: none;
        }
        textarea {
            height: 120px;
            resize: vertical;
            font-family: 'Courier New', Courier, monospace;
        }
        .button-container {
            grid-column: 1 / -1;
            display: flex;
            justify-content: center;
            margin-top: 1em;
        }
        button {
            background-color: #2563eb;
            color: white;
            padding: 12px 25px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 1.1em;
            font-weight: 600;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #1d4ed8;
        }
        #status-message {
            margin-top: 1.5em;
            padding: 1em;
            border-radius: 8px;
            text-align: center;
            font-weight: 500;
            display: none;
        }
        .status-success {
            background-color: #dcfce7;
            color: #166534;
            display: block;
        }
        .status-error {
            background-color: #fee2e2;
            color: #991b1b;
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← Voltar ao Dashboard</a>
        <h1>Ferramenta de Envio de Comandos IR (SendIR / GC)</h1>
        <div class="form-grid">
            <div class="form-group">
                <label for="ip">IP do Dispositivo:</label>
                <input type="text" id="ip">
            </div>
            <div class="form-group">
                <label for="serial">Serial Number:</label>
                <input type="text" id="serial">
            </div>
            <div class="form-group">
                <label for="pwd">Password (verifyCode):</label>
                <input type="text" id="pwd">
            </div>
            <div class="form-group full-width">
                <label for="c-value">Parâmetro 'c':</label>
                <input type="text" id="c-value">
            </div>
            <div class="form-group full-width">
                <label for="gc-code">Código SendIR / GC:</label>
                <textarea id="gc-code" placeholder="Cole o código SendIR aqui (ex: 38000,1,1,...)"></textarea>
            </div>
            <div class="button-container">
                <button id="send-button">📡 Enviar Comando</button>
            </div>
        </div>

        <div id="status-message"></div>
    </div>

    <script>
        const ipEl = document.getElementById('ip');
        const serialEl = document.getElementById('serial');
        const pwdEl = document.getElementById('pwd');
        const cEl = document.getElementById('c-value');
        const gcCodeEl = document.getElementById('gc-code');
        const sendButton = document.getElementById('send-button');
        const statusMessageEl = document.getElementById('status-message');

        function loadData() {
            ipEl.value = localStorage.getItem('sendir_ip') || '192.168.1.112';
            serialEl.value = localStorage.getItem('sendir_serial') || 'P130-C101-A0794';
            pwdEl.value = localStorage.getItem('sendir_pwd') || '72856898';
            cEl.value = localStorage.getItem('sendir_c') || '1';
            gcCodeEl.value = localStorage.getItem('sendir_gc_code') || '';
        }

        function saveData() {
            localStorage.setItem('sendir_ip', ipEl.value);
            localStorage.setItem('sendir_serial', serialEl.value);
            localStorage.setItem('sendir_pwd', pwdEl.value);
            localStorage.setItem('sendir_c', cEl.value);
            localStorage.setItem('sendir_gc_code', gcCodeEl.value);
        }

        async function sendRequest() {
            saveData();

            const ip = ipEl.value.trim();
            const serial = serialEl.value.trim();
            const pwd = pwdEl.value.trim();
            const c = cEl.value.trim();
            const gcCode = gcCodeEl.value.trim().replace(/\\s/g, '');

            if (!ip || !serial || !pwd || !c || !gcCode) {
                statusMessageEl.textContent = '❌ Erro: Todos os campos devem ser preenchidos.';
                statusMessageEl.className = 'status-error';
                return;
            }

            const url = `http://${ip}/api/device/deviceDetails/smartHomeAutoHttpControl`;
            const body = new URLSearchParams( );
            body.append('serialNum', serial);
            body.append('verifyCode', pwd);
            body.append('c', c);
            body.append('gc', gcCode);

            statusMessageEl.style.display = 'none';
            statusMessageEl.className = '';

            try {
                await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: body,
                    mode: 'no-cors'
                });

                statusMessageEl.textContent = '✅ Comando enviado com sucesso para o dispositivo!';
                statusMessageEl.className = 'status-success';

            } catch (error) {
                statusMessageEl.textContent = `❌ Erro ao enviar o comando. Verifique o IP e a conexão de rede. Detalhe: ${error.message}`;
                statusMessageEl.className = 'status-error';
            }
        }

        sendButton.addEventListener('click', sendRequest);
        document.addEventListener('DOMContentLoaded', loadData);
    </script>
</body>
</html>
"""


# ============================================================================
# INICIALIZAÇÃO
# ============================================================================

def init_api(token: str, updater: HCTUpdater):
    """Inicializa a API com token e updater."""
    state["token"] = token
    state["updater"] = updater
    logger.info("hct-api", "init", "API inicializada")


def run_api(host: str = '0.0.0.0', port: int = 8099):
    """Executa servidor Flask."""
    logger.info("hct-api", "startup", f"Iniciando servidor web em {host}:{port}")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    # Teste standalone
    logger.info("hct-api", "test", "Modo de teste - API sem updater")
    run_api()
