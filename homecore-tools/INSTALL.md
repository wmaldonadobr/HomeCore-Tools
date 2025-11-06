# Guia de Instalação Rápida - HomeCore Tools

## Pré-requisitos

✅ Home Assistant OS 2024.1.0 ou superior  
✅ Integração HomeCore Beacon instalada e configurada  
✅ Conexão estável com a internet  

## Instalação em 5 Passos

### 1️⃣ Adicionar Repositório

No Home Assistant, navegue até:

```
Configurações > Add-ons > Loja de Add-ons > ⋮ (menu superior direito) > Repositórios
```

Cole a URL do repositório:

```
https://github.com/homecore/homecore-tools-addon
```

Clique em **"Adicionar"**.

### 2️⃣ Instalar Add-on

1. Volte para a Loja de Add-ons
2. Procure por **"HomeCore Tools"**
3. Clique no add-on
4. Clique em **"Instalar"**
5. Aguarde a conclusão (pode levar alguns minutos)

### 3️⃣ Configurar (Opcional)

As configurações padrão funcionam para a maioria dos casos. Se desejar personalizar:

```yaml
log_level: info              # debug, info, warning, error
check_interval: 3600         # Segundos (1 hora)
auto_update: true            # Aplicar atualizações automaticamente
backup_before_update: true   # Criar backup antes de atualizar
notify_on_update: true       # Enviar notificações
```

### 4️⃣ Iniciar Add-on

1. Clique em **"Iniciar"**
2. Aguarde alguns segundos
3. Verifique os logs para confirmar inicialização

Você deve ver:

```
[INFO] Iniciando HomeCore Tools...
[INFO] Configurações carregadas
[SUCCESS] Supervisor disponível
[SUCCESS] Token obtido com sucesso
[INFO] Updater inicializado
```

### 5️⃣ Verificar Dashboard

1. No menu lateral do HA, clique em **"HomeCore Tools"**
2. Ou vá em: **Configurações > Add-ons > HomeCore Tools > "Abrir Interface Web"**

Você verá:
- ✅ Status do sistema
- 🔄 Atualizações disponíveis (se houver)
- 📝 Logs recentes

## Pronto! 🎉

O add-on está funcionando e verificará atualizações automaticamente a cada 1 hora (ou conforme configurado).

## Próximos Passos

### Habilitar no Painel Lateral

Para acesso rápido ao dashboard:

1. **Configurações > Add-ons > HomeCore Tools**
2. Ative **"Mostrar no painel lateral"**

### Configurar Notificações

As notificações já estão habilitadas por padrão. Você receberá alertas sobre:
- ✅ Add-on iniciado
- 🔄 Atualizações disponíveis
- ✅ Atualizações aplicadas
- ❌ Erros (se houver)

### Verificar Primeira Atualização

O add-on faz uma verificação inicial imediatamente após iniciar. Se houver atualizações:

1. Você receberá uma notificação
2. Se `auto_update: true`, elas serão aplicadas automaticamente
3. Se `auto_update: false`, você pode aplicá-las manualmente via dashboard

## Troubleshooting

### ❌ Add-on não inicia

**Verifique:**
1. Integração HomeCore Beacon está instalada?
2. Token está configurado na integração?
3. Logs do add-on mostram algum erro?

**Solução:**
```
Configurações > Dispositivos e Serviços > Integrações > HomeCore
```

Verifique se a integração está ativa e com token configurado.

### ❌ Token não encontrado

**Erro nos logs:**
```
[ERROR] Não foi possível obter token da integração HomeCore
```

**Solução:**
1. Instale a integração HomeCore Beacon
2. Configure o token na integração
3. Reinicie o add-on

### ❌ Dashboard não abre

**Verifique:**
1. Add-on está rodando?
2. Ingress está habilitado?

**Solução:**
```
Configurações > Add-ons > HomeCore Tools > Reiniciar
```

## Suporte

📧 **Email:** suporte@homecore.com.br  
🌐 **Website:** https://homecore.com.br  
📚 **Documentação Completa:** [DOCS.md](DOCS.md)  
🐛 **Reportar Bug:** https://github.com/homecore/homecore-tools-addon/issues

## Configurações Avançadas

### Desabilitar Auto-Update

Se preferir aplicar atualizações manualmente:

```yaml
auto_update: false
```

Você ainda receberá notificações e poderá aplicar via dashboard.

### Aumentar Intervalo de Verificação

Para verificar a cada 6 horas:

```yaml
check_interval: 21600
```

### Modo Debug

Para troubleshooting detalhado:

```yaml
log_level: debug
```

⚠️ **Atenção:** Modo debug gera muitos logs. Use apenas temporariamente.

## Backup e Segurança

### Backups Automáticos

O add-on cria backups automaticamente antes de cada atualização em:

```
/data/backups/hc-tools_backup_YYYYMMDDTHHMMSS/
```

### Rollback Manual

Se algo der errado, restaure manualmente:

```bash
# Via Terminal/SSH
cd /config
cp -r /data/backups/hc-tools_backup_YYYYMMDDTHHMMSS/* .
```

Depois reinicie o Home Assistant.

## Atualizações do Add-on

O próprio add-on é atualizado via Supervisor:

```
Configurações > Add-ons > HomeCore Tools > Atualizar
```

Ou habilite atualizações automáticas de add-ons:

```
Configurações > Sistema > Atualizações > Configurações > Atualizar automaticamente add-ons
```

---

**Versão:** 1.0.0  
**Última Atualização:** 2025-11-05

Para documentação completa, veja [DOCS.md](DOCS.md)
