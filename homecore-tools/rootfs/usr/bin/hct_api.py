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


# HTML das Ferramentas IR
SENDHEX_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <title>GW3 • Envio IR (Pronto HEX)</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; background:#f6f7fb; margin:0; padding:24px; }
    .wrap { max-width: 960px; margin: 0 auto; background:#fff; border-radius:12px; padding:24px; box-shadow: 0 8px 20px rgba(0,0,0,.06); }
    .back-link { display: inline-block; margin-bottom: 20px; color: #667eea; text-decoration: none; font-weight: 600; }
    .back-link:hover { text-decoration: underline; }
    h1 { font-size: 22px; margin: 0 0 18px; color:#0f172a; }
    .grid { display:grid; grid-template-columns: repeat(3, 1fr); gap:14px; }
    .full { grid-column: 1 / -1; }
    label { font-size: 13px; color:#334155; margin-bottom:6px; display:block; }
    input[type="text"], textarea { width:100%; box-sizing:border-box; border:1px solid #cbd5e1; border-radius:8px; padding:10px 12px; font-size:14px; outline:none; transition: box-shadow .2s, border-color .2s; }
    input:focus, textarea:focus { border-color:#667eea; box-shadow: 0 0 0 3px rgba(102,126,234,.15); }
    textarea { min-height: 160px; resize: vertical; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
    .row { display:flex; gap:10px; align-items:center; }
    .btn { background:#667eea; color:#fff; border:0; border-radius:10px; padding:12px 18px; font-weight:600; cursor:pointer; font-size:14px; }
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
      <div><label for="ip">IP do GW3</label><input id="ip" type="text" placeholder="192.168.1.112" autocomplete="off"></div>
      <div><label for="serial">Serial (serialNum)</label><input id="serial" type="text" placeholder="P130-C101-A0794" autocomplete="off"></div>
      <div><label for="pwd">Senha (verifyCode)</label><input id="pwd" type="text" placeholder="72856898" autocomplete="off"></div>
      <div><label for="c">Parâmetro c</label><input id="c" type="text" placeholder="1" autocomplete="off"></div>
      <div><label for="r">Parâmetro r</label><input id="r" type="text" placeholder="2" autocomplete="off"></div>
      <div class="checkbox"><input id="upper" type="checkbox"><label for="upper">HEX em maiúsculas</label></div>
      <div class="full"><label for="pronto">Código Pronto HEX (com espaços)</label><textarea id="pronto" placeholder="Ex.: 0000 006D 0022 0002 0157 00AC 0015 0016 0015 0041 ..."></textarea><div class="hint">Cole exatamente com espaços; o formulário codifica automaticamente. Todos os campos são salvos no seu navegador (localStorage).</div></div>
      <div class="full row"><button class="btn" id="send">📡 Enviar (POST)</button><button class="btn secondary" id="preview">🧪 Pré-visualizar corpo</button><button class="btn warn" id="clear">🧹 Limpar dados salvos</button></div>
    </div>
    <div id="status" class="status"></div>
  </div>
  <script>
    const F={ip:document.getElementById('ip'),serial:document.getElementById('serial'),pwd:document.getElementById('pwd'),c:document.getElementById('c'),r:document.getElementById('r'),upper:document.getElementById('upper'),pronto:document.getElementById('pronto'),status:document.getElementById('status'),send:document.getElementById('send'),preview:document.getElementById('preview'),clear:document.getElementById('clear')};
    const KEYS={ip:'gw3_ip',serial:'gw3_serial',pwd:'gw3_pwd',c:'gw3_c',r:'gw3_r',pronto:'gw3_pronto',upper:'gw3_upper'};
    function load(){F.ip.value=localStorage.getItem(KEYS.ip)||'192.168.1.112';F.serial.value=localStorage.getItem(KEYS.serial)||'P130-C101-A0794';F.pwd.value=localStorage.getItem(KEYS.pwd)||'72856898';F.c.value=localStorage.getItem(KEYS.c)||'1';F.r.value=localStorage.getItem(KEYS.r)||'2';F.pronto.value=localStorage.getItem(KEYS.pronto)||'';F.upper.checked=(localStorage.getItem(KEYS.upper)||'0')==='1';}
    function bindAutosave(){const saveText=(el,key)=>el.addEventListener('input',()=>localStorage.setItem(key,el.value));const saveCheck=(el,key)=>el.addEventListener('change',()=>localStorage.setItem(key,el.checked?'1':'0'));saveText(F.ip,KEYS.ip);saveText(F.serial,KEYS.serial);saveText(F.pwd,KEYS.pwd);saveText(F.c,KEYS.c);saveText(F.r,KEYS.r);saveText(F.pronto,KEYS.pronto);saveCheck(F.upper,KEYS.upper);}
    function normalizeHex(s){let v=s.replace(/\\s+/g,' ').trim();if(F.upper.checked)v=v.toUpperCase();return v;}
    function build(){const ip=F.ip.value.trim();const serial=F.serial.value.trim();const pwd=F.pwd.value.trim();const c=F.c.value.trim();const r=F.r.value.trim();let pronto=normalizeHex(F.pronto.value);if(!ip||!serial||!pwd||!c||!r||!pronto){throw new Error('Preencha IP, serial, senha, c, r e o código Pronto HEX.');}const url=`http://${ip}/api/device/deviceDetails/smartHomeAutoHttpControl`;const body=new URLSearchParams();body.append('serialNum',serial);body.append('verifyCode',pwd);body.append('pronto',pronto);body.append('c',c);body.append('r',r);return{url,body};}
    function showOK(msg){F.status.className='status ok';F.status.textContent=msg;}function showERR(msg){F.status.className='status err';F.status.textContent=msg;}
    async function send(){try{const{url,body}=build();await fetch(url,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body,mode:'no-cors'});showOK('✅ Enviado! (POST x-www-form-urlencoded com pronto=...)');}catch(e){showERR('❌ '+e.message);}}
    function preview(){try{const{url,body}=build();showOK(`URL:\\n${url}\\n\\nBody:\\n${body.toString()}`);}catch(e){showERR('❌ '+e.message);}}
    function clearAll(){Object.values(KEYS).forEach(k=>localStorage.removeItem(k));load();showOK('🧹 Dados salvos apagados.');}
    document.addEventListener('DOMContentLoaded',()=>{load();bindAutosave();F.send.addEventListener('click',send);F.preview.addEventListener('click',preview);F.clear.addEventListener('click',clearAll);});
  </script>
</body>
</html>
"""

SENDIR_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8"><title>Ferramenta de Envio de Comandos IR - SendIR / GC</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body{font-family:'Roboto',sans-serif;background-color:#f6f7fb;color:#333;margin:0;padding:24px;display:flex;justify-content:center;align-items:center;min-height:100vh;}
        .container{width:100%;max-width:900px;background:#fff;padding:2em;border-radius:12px;box-shadow:0 8px 20px rgba(0,0,0,.06);}
        .back-link{display:inline-block;margin-bottom:20px;color:#667eea;text-decoration:none;font-weight:600;}.back-link:hover{text-decoration:underline;}
        h1{font-size:1.8em;color:#1e3a8a;margin-top:0;margin-bottom:1em;text-align:center;}
        .form-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:1.5em;}
        .form-group{display:flex;flex-direction:column;}.full-width{grid-column:1/-1;}
        label{font-weight:500;margin-bottom:0.5em;color:#374151;}
        input,textarea{padding:10px;border:1px solid #cbd5e1;border-radius:8px;font-family:'Roboto',sans-serif;font-size:1em;transition:border-color 0.3s,box-shadow 0.3s;}
        input:focus,textarea:focus{border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,0.2);outline:none;}
        textarea{height:120px;resize:vertical;font-family:'Courier New',Courier,monospace;}
        .button-container{grid-column:1/-1;display:flex;justify-content:center;margin-top:1em;}
        button{background-color:#667eea;color:white;padding:12px 25px;border:none;border-radius:10px;cursor:pointer;font-size:1.1em;font-weight:600;transition:background-color 0.3s;}button:hover{background-color:#5568d3;}
        #status-message{margin-top:1.5em;padding:1em;border-radius:8px;text-align:center;font-weight:500;display:none;}
        .status-success{background-color:#dcfce7;color:#166534;display:block;}.status-error{background-color:#fee2e2;color:#991b1b;display:block;}
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← Voltar ao Dashboard</a>
        <h1>Ferramenta de Envio de Comandos IR (SendIR / GC)</h1>
        <div class="form-grid">
            <div class="form-group"><label for="ip">IP do Dispositivo:</label><input type="text" id="ip"></div>
            <div class="form-group"><label for="serial">Serial Number:</label><input type="text" id="serial"></div>
            <div class="form-group"><label for="pwd">Password (verifyCode):</label><input type="text" id="pwd"></div>
            <div class="form-group full-width"><label for="c-value">Parâmetro 'c':</label><input type="text" id="c-value"></div>
            <div class="form-group full-width"><label for="gc-code">Código SendIR / GC:</label><textarea id="gc-code" placeholder="Cole o código SendIR aqui (ex: 38000,1,1,...)"></textarea></div>
            <div class="button-container"><button id="send-button">📡 Enviar Comando</button></div>
        </div>
        <div id="status-message"></div>
    </div>
    <script>
        const ipEl=document.getElementById('ip');const serialEl=document.getElementById('serial');const pwdEl=document.getElementById('pwd');const cEl=document.getElementById('c-value');const gcCodeEl=document.getElementById('gc-code');const sendButton=document.getElementById('send-button');const statusMessageEl=document.getElementById('status-message');
        function loadData(){ipEl.value=localStorage.getItem('sendir_ip')||'192.168.1.112';serialEl.value=localStorage.getItem('sendir_serial')||'P130-C101-A0794';pwdEl.value=localStorage.getItem('sendir_pwd')||'72856898';cEl.value=localStorage.getItem('sendir_c')||'1';gcCodeEl.value=localStorage.getItem('sendir_gc_code')||'';}
        function saveData(){localStorage.setItem('sendir_ip',ipEl.value);localStorage.setItem('sendir_serial',serialEl.value);localStorage.setItem('sendir_pwd',pwdEl.value);localStorage.setItem('sendir_c',cEl.value);localStorage.setItem('sendir_gc_code',gcCodeEl.value);}
        async function sendRequest(){saveData();const ip=ipEl.value.trim();const serial=serialEl.value.trim();const pwd=pwdEl.value.trim();const c=cEl.value.trim();const gcCode=gcCodeEl.value.trim().replace(/\\s/g,'');if(!ip||!serial||!pwd||!c||!gcCode){statusMessageEl.textContent='❌ Erro: Todos os campos devem ser preenchidos.';statusMessageEl.className='status-error';return;}const url=`http://${ip}/api/device/deviceDetails/smartHomeAutoHttpControl`;const body=new URLSearchParams();body.append('serialNum',serial);body.append('verifyCode',pwd);body.append('c',c);body.append('gc',gcCode);statusMessageEl.style.display='none';statusMessageEl.className='';try{await fetch(url,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded',},body:body,mode:'no-cors'});statusMessageEl.textContent='✅ Comando enviado com sucesso para o dispositivo!';statusMessageEl.className='status-success';}catch(error){statusMessageEl.textContent=`❌ Erro ao enviar o comando. Verifique o IP e a conexão de rede. Detalhe: ${error.message}`;statusMessageEl.className='status-error';}}
        sendButton.addEventListener('click',sendRequest);document.addEventListener('DOMContentLoaded',loadData);
    </script>
</body>
</html>
"""

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
            <h2>🔧 Ferramentas IR</h2>
            <div class="btn-group">
                <a href="/tools/sendhex" class="btn">📡 Enviar IR (Pronto HEX)</a>
                <a href="/tools/sendir" class="btn">📻 Enviar IR (SendIR/GC)</a>
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


@app.route('/tools/sendhex')
def tool_sendhex():
    """Ferramenta de envio IR (Pronto HEX)."""
    return render_template_string(SENDHEX_HTML)


@app.route('/tools/sendir')
def tool_sendir():
    """Ferramenta de envio IR (SendIR/GC)."""
    return render_template_string(SENDIR_HTML)


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
    # Desabilitar logs do Werkzeug (servidor Flask) para não contaminar JSON
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    log.disabled = True
    
    logger.info("hct-api", "startup", f"Iniciando servidor web em {host}:{port}")
    app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    # Teste standalone
    logger.info("hct-api", "test", "Modo de teste - API sem updater")
    run_api()
