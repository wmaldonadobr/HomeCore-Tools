# HomeCore Tools - Documentação

## Visão Geral

O **HomeCore Tools** é um add-on para Home Assistant que fornece ferramentas de manutenção e atualização automática para sistemas HomeCore. Ele verifica periodicamente por atualizações disponíveis e pode aplicá-las automaticamente, mantendo seu sistema sempre atualizado.

## Funcionalidades

- ✅ **Verificação automática de atualizações** via sistema de manifests
- ✅ **Aplicação automática de atualizações** (configurável)
- ✅ **Backup automático** antes de cada atualização
- ✅ **Rollback automático** em caso de falha
- ✅ **Notificações persistentes** sobre atualizações disponíveis e aplicadas
- ✅ **Dashboard web** para monitoramento e controle manual
- ✅ **Logs estruturados** para auditoria e troubleshooting
- ✅ **Integração** com HomeCore Beacon para obtenção automática do token

## Requisitos

### Obrigatórios

1. **Home Assistant OS** versão 2024.1.0 ou superior
2. **Integração HomeCore Beacon** instalada e configurada
   - O add-on obtém automaticamente o token de autenticação da integração
   - Certifique-se de que a integração está funcionando corretamente antes de instalar o add-on

### Recomendados

- Backup regular do Home Assistant (o add-on cria backups locais, mas é recomendado ter backups externos)
- Conexão estável com a internet

## Instalação

### 1. Adicionar Repositório

No Home Assistant, navegue até:

```
Configurações > Add-ons > Loja de Add-ons > ⋮ (menu) > Repositórios
```

Adicione a URL do repositório HomeCore Tools:

```
https://github.com/homecore/homecore-tools-addon
```

### 2. Instalar Add-on

1. Encontre "HomeCore Tools" na lista de add-ons disponíveis
2. Clique em "Instalar"
3. Aguarde a conclusão da instalação

### 3. Configurar

Antes de iniciar, configure as opções conforme suas preferências (veja seção de Configuração abaixo).

### 4. Iniciar

1. Clique em "Iniciar"
2. Verifique os logs para confirmar que o add-on iniciou corretamente
3. O add-on irá:
   - Obter automaticamente o token da integração HomeCore
   - Verificar atualizações disponíveis
   - Enviar notificação de inicialização

## Configuração

### Opções Disponíveis

#### `log_level` (padrão: `info`)

Nível de detalhamento dos logs.

**Valores possíveis:**
- `debug`: Máximo detalhamento (para troubleshooting)
- `info`: Informações gerais (recomendado)
- `warning`: Apenas avisos e erros
- `error`: Apenas erros

**Exemplo:**
```yaml
log_level: info
```

#### `check_interval` (padrão: `3600`)

Intervalo em segundos entre verificações de atualização.

**Valores possíveis:** 300 a 86400 (5 minutos a 24 horas)

**Exemplos:**
```yaml
check_interval: 3600  # 1 hora
check_interval: 7200  # 2 horas
check_interval: 21600 # 6 horas
```

#### `auto_update` (padrão: `true`)

Se habilitado, o add-on aplica automaticamente as atualizações disponíveis. Se desabilitado, apenas notifica sobre atualizações, mas não as aplica.

**Valores possíveis:** `true` ou `false`

**Exemplo:**
```yaml
auto_update: true
```

⚠️ **Importante:** Mesmo com `auto_update: false`, você pode aplicar atualizações manualmente através do dashboard web.

#### `backup_before_update` (padrão: `true`)

Se habilitado, o add-on cria um backup completo antes de aplicar qualquer atualização.

**Valores possíveis:** `true` ou `false`

**Exemplo:**
```yaml
backup_before_update: true
```

⚠️ **Recomendação:** Mantenha sempre habilitado para segurança.

#### `notify_on_update` (padrão: `true`)

Se habilitado, o add-on envia notificações persistentes no Home Assistant sobre:
- Atualizações disponíveis
- Atualizações aplicadas com sucesso
- Erros durante atualizações

**Valores possíveis:** `true` ou `false`

**Exemplo:**
```yaml
notify_on_update: true
```

### Exemplo de Configuração Completa

```yaml
log_level: info
check_interval: 3600
auto_update: true
backup_before_update: true
notify_on_update: true
```

## Dashboard Web

O add-on fornece um dashboard web acessível através do painel do Home Assistant.

### Acessar Dashboard

1. No menu lateral do Home Assistant, clique em "HomeCore Tools"
2. Ou navegue para: Configurações > Add-ons > HomeCore Tools > "Abrir Interface Web"

### Funcionalidades do Dashboard

#### 📊 Status do Sistema

Exibe informações sobre:
- Status do token (configurado ou não)
- Última verificação de atualizações
- Status do auto-update (habilitado/desabilitado)
- Intervalo de verificação

#### 🔄 Atualizações Disponíveis

Lista todas as atualizações disponíveis com:
- Tipo de atualização (Core, HCC, MolSmart)
- Versão atual vs versão disponível

**Ações:**
- **Verificar Atualizações**: Força uma verificação imediata
- **Aplicar Atualizações**: Aplica manualmente as atualizações disponíveis

#### 📝 Logs Recentes

Exibe os últimos 20 logs do sistema com:
- Timestamp
- Componente
- Ação
- Detalhes

Os logs são atualizados automaticamente a cada 30 segundos.

## Tipos de Atualização

O add-on gerencia três tipos de atualizações:

### 1. Core (`core_manifest.json`)

Atualizações do núcleo do sistema HomeCore:
- Scripts principais
- Configurações base
- Ferramentas de sistema

### 2. HCC - HomeCore Custom (`hcc_manifest.json`)

Configurações personalizadas do cliente:
- Temas customizados
- Dashboards específicos
- Automações personalizadas
- Pacotes de configuração

### 3. MolSmart (`molsmart_manifest.json`)

Configurações específicas para dispositivos MolSmart:
- Scripts de descoberta
- Configurações MQTT
- Templates de dispositivos

## Sistema de Backup

### Backup Automático

Antes de cada atualização, o add-on cria automaticamente um backup contendo:

- Diretório `/config/hc-tools/` completo
- Arquivos sensíveis:
  - `configuration.yaml`
  - `automations.yaml`
  - `scripts.yaml`
  - `scenes.yaml`

### Localização dos Backups

Os backups são armazenados em:

```
/data/backups/hc-tools_backup_YYYYMMDDTHHMMSS/
```

**Exemplo:**
```
/data/backups/hc-tools_backup_20251105T193000/
```

### Rollback Automático

Em caso de falha durante a aplicação de uma atualização, o add-on automaticamente:

1. Detecta a falha
2. Restaura o backup mais recente
3. Registra o erro nos logs
4. Envia notificação ao usuário

### Limpeza de Backups

⚠️ Os backups **não são removidos automaticamente**. Recomenda-se:

1. Verificar periodicamente a pasta `/data/backups/`
2. Remover backups antigos manualmente para liberar espaço
3. Manter pelo menos os 3 backups mais recentes

## Notificações

O add-on envia notificações persistentes para o Home Assistant nos seguintes eventos:

### 1. Inicialização

Quando o add-on inicia com sucesso:

```
🛠️ HomeCore Tools Iniciado

O sistema de atualização automática está ativo.

Verificações a cada 60 minutos.
Auto-update: Habilitado
```

### 2. Atualizações Disponíveis

Quando novas atualizações são detectadas:

```
🔄 Atualizações HomeCore Disponíveis

Foram encontradas 2 atualização(ões):

- core: 1.0.0 → 1.1.0
- hcc: 2.3.0 → 2.4.0
```

### 3. Atualizações Aplicadas

Quando atualizações são aplicadas com sucesso:

```
✅ Atualizações HomeCore Aplicadas

2 atualização(ões) aplicada(s) com sucesso.

⚠️ Reinicie o Home Assistant para aplicar as configurações.
```

### 4. Erros

Quando ocorrem erros:

```
❌ HomeCore Tools - Erro

Não foi possível obter token da integração HomeCore.
Certifique-se de que a integração está instalada e configurada.
```

## Logs

### Logs Estruturados

O add-on mantém logs estruturados em formato JSON em:

```
/data/logs/hct.json.log
```

Cada entrada de log contém:

```json
{
  "timestamp": "2025-11-05T19:30:00Z",
  "level": "INFO",
  "component": "hct-updater",
  "action": "update_applied",
  "details": {
    "package": "HomeCore Custom",
    "version": "1.2.0",
    "duration_seconds": 45,
    "files_updated": 12
  },
  "status": "success"
}
```

### Logs do Home Assistant

Os logs também são enviados para o log padrão do Home Assistant:

```
Supervisor > System > Logs
```

Ou via CLI:

```bash
ha addons logs homecore-tools
```

### Rotação de Logs

- Tamanho máximo por arquivo: 10 MB
- Arquivos de backup mantidos: 5
- Total máximo: ~50 MB

## Troubleshooting

### Add-on não inicia

**Problema:** O add-on não inicia ou para imediatamente.

**Soluções:**

1. Verifique os logs do add-on:
   ```
   Supervisor > HomeCore Tools > Log
   ```

2. Certifique-se de que a integração HomeCore Beacon está instalada:
   ```
   Configurações > Dispositivos e Serviços > Integrações
   ```

3. Verifique se o token está configurado na integração

4. Reinicie o add-on:
   ```
   Supervisor > HomeCore Tools > Reiniciar
   ```

### Token não encontrado

**Problema:** Logs mostram "Não foi possível obter token da integração HomeCore".

**Soluções:**

1. Verifique se a integração HomeCore Beacon está instalada e configurada
2. Reconfigure a integração se necessário
3. Reinicie o add-on após configurar a integração

### Atualizações não são aplicadas

**Problema:** O add-on detecta atualizações mas não as aplica.

**Soluções:**

1. Verifique se `auto_update` está habilitado nas configurações
2. Verifique os logs para erros durante o download ou aplicação
3. Tente aplicar manualmente via dashboard web
4. Verifique a conexão com a internet
5. Verifique se há espaço em disco suficiente

### Erro durante atualização

**Problema:** Atualização falha e sistema não é restaurado.

**Soluções:**

1. Verifique os logs para detalhes do erro
2. Restaure manualmente o backup mais recente:
   ```bash
   # Via SSH ou Terminal
   cd /config
   cp -r /data/backups/hc-tools_backup_YYYYMMDDTHHMMSS/* .
   ```
3. Reinicie o Home Assistant
4. Reporte o erro para suporte HomeCore

### Dashboard não carrega

**Problema:** Interface web não abre ou mostra erro.

**Soluções:**

1. Verifique se o add-on está rodando
2. Verifique os logs para erros na API
3. Tente acessar via URL direta (se Ingress estiver habilitado)
4. Reinicie o add-on

### Espaço em disco insuficiente

**Problema:** Erro "No space left on device" durante atualização.

**Soluções:**

1. Limpe backups antigos:
   ```bash
   rm -rf /data/backups/hc-tools_backup_*
   ```

2. Limpe logs antigos do Home Assistant

3. Remova snapshots antigos do Supervisor

4. Considere expandir o armazenamento

## Perguntas Frequentes (FAQ)

### O add-on pode quebrar meu Home Assistant?

Não. O add-on:
- Cria backup antes de qualquer alteração
- Faz rollback automático em caso de falha
- Apenas modifica arquivos em `/config/hc-tools/` e configurações HomeCore
- Não modifica o core do Home Assistant

### Preciso reiniciar o HA após cada atualização?

Sim. Muitas atualizações modificam arquivos de configuração (`configuration.yaml`, `automations.yaml`, etc.) que só são carregados na inicialização do Home Assistant.

### Posso desabilitar atualizações automáticas?

Sim. Configure `auto_update: false` nas opções do add-on. Você ainda receberá notificações sobre atualizações disponíveis e poderá aplicá-las manualmente via dashboard.

### Quanto espaço em disco o add-on usa?

- Add-on em si: ~50 MB
- Logs: ~50 MB (com rotação)
- Backups: Varia, geralmente 10-50 MB por backup
- Total estimado: 100-200 MB

### O add-on funciona com Home Assistant Container/Core?

Não. O add-on é projetado especificamente para **Home Assistant OS** e requer o Supervisor. Para outras instalações, use os scripts bash diretamente.

### Como faço para atualizar o próprio add-on?

O add-on é atualizado através do Supervisor:

```
Supervisor > HomeCore Tools > Atualizar
```

Ou automaticamente se você habilitou atualizações automáticas de add-ons no Supervisor.

### Posso executar scripts manualmente?

Sim. Os scripts bash estão disponíveis em `/tools/` dentro do container. Você pode executá-los via SSH ou Terminal:

```bash
docker exec addon_homecore-tools /tools/hcc_update.sh
```

### O que acontece se a internet cair durante uma atualização?

O add-on:
1. Detecta a falha no download
2. Tenta novamente (até 3 tentativas)
3. Se todas falharem, aborta a atualização
4. Mantém o sistema no estado anterior (seguro)

## Suporte

### Documentação

- **Documentação completa**: https://homecore.com.br/docs/addon
- **GitHub**: https://github.com/homecore/homecore-tools-addon
- **Changelog**: Veja `CHANGELOG.md` no repositório

### Reportar Problemas

Para reportar bugs ou solicitar funcionalidades:

1. Colete os logs do add-on
2. Descreva o problema detalhadamente
3. Abra uma issue no GitHub: https://github.com/homecore/homecore-tools-addon/issues

### Contato

- **Email**: suporte@homecore.com.br
- **Website**: https://homecore.com.br
- **Comunidade**: https://community.homecore.com.br

## Segurança e Privacidade

### Dados Coletados

O add-on **não coleta** dados pessoais. Apenas:
- Verifica manifests remotos (usando token de autenticação)
- Baixa pacotes de atualização
- Envia logs de erro (se configurado)

### Token de Autenticação

- O token é obtido automaticamente da integração HomeCore Beacon
- É usado apenas para autenticar requisições às APIs HomeCore
- Não é compartilhado com terceiros
- É armazenado apenas em memória (não persiste em disco)

### Permissões

O add-on requer:
- **Acesso de escrita a `/config`**: Para aplicar atualizações
- **Acesso à API do Supervisor**: Para obter token da integração
- **Acesso à API do Home Assistant**: Para enviar notificações

Todas as permissões são necessárias para o funcionamento correto do add-on.

## Licença

Este add-on é fornecido pela HomeCore e está sujeito aos termos de serviço da plataforma HomeCore.

---

**Versão da Documentação:** 1.0.0  
**Última Atualização:** 2025-11-05
