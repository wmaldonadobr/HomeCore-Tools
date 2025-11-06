# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [1.0.5] - 2025-11-06

### Corrigido

- **Add-on totalmente funcional**: Todas as correções aplicadas e testadas com sucesso
  - Arquivos Python restaurados em `rootfs/usr/bin/` após deleção acidental
  - Adicionado `python3` explicitamente na chamada dos scripts Python
  - Corrigidos caminhos em `run.sh` e scripts de serviço
  - Sistema de logs estruturados em JSON funcionando
  - Notificações persistentes no Home Assistant operacionais
  - Dashboard web via Ingress disponível
  - Daemon principal executando corretamente

### Adicionado

- Ícones personalizados (icon.png e logo.png)
- Documentação completa de instalação e uso

## [1.0.4] - 2025-11-06

### Corrigido

- **Rebuild forçado**: Versão incrementada para forçar rebuild completo sem cache
  - Garantir que todas as mudanças de v1.0.3 sejam aplicadas
  - Mesmas correções de v1.0.3 (arquivos Python com underscore)

## [1.0.3] - 2025-11-06

### Corrigido

- **Erro de importação de módulos Python**: Corrigido ModuleNotFoundError para hct_logger
  - Renomeados arquivos Python de `hct-*.py` para `hct_*.py` (hífen para underscore)
  - Python não permite importar módulos com hífen no nome
  - Atualizado script de serviço para chamar `python3 /usr/bin/hct_daemon.py`
  - Atualizado Dockerfile para dar permissões aos arquivos corretos
  - Add-on agora inicia corretamente

## [1.0.2] - 2025-11-06

### Corrigido

- **Erro de cópia do run.sh**: Corrigido caminho de cópia do arquivo `run.sh` no Dockerfile
  - Adicionado `COPY run.sh /run.sh` explicitamente
  - O arquivo estava na raiz da pasta do add-on mas não estava sendo copiado corretamente
  - Build agora completa com sucesso

## [1.0.1] - 2025-11-06

### Corrigido

- **Erro de build do Docker**: Corrigido erro PEP 668 (externally-managed-environment) no Alpine Linux 3.19
  - Alterado Dockerfile para instalar pacotes Python via `apk` quando disponíveis
  - Adicionado `py3-yaml` e `py3-requests` via apk
  - Usado `--break-system-packages` apenas para `flask-cors` que não está disponível via apk
  - Build agora funciona corretamente em todas as arquiteturas

## [1.0.0] - 2025-11-05

### Adicionado

#### Funcionalidades Principais
- Sistema de verificação automática de atualizações via manifests
- Aplicação automática de atualizações (configurável)
- Backup automático antes de cada atualização
- Rollback automático em caso de falha
- Notificações persistentes no Home Assistant
- Dashboard web via Ingress para monitoramento e controle
- Sistema de logs estruturados em JSON

#### Componentes
- **HCT Daemon** (`hct_daemon.py`): Daemon principal que orquestra o sistema
- **HCT Updater** (`hct_updater.py`): Sistema de download e aplicação de atualizações
- **HCT Logger** (`hct_logger.py`): Sistema de logs estruturados com rotação automática
- **HCT API** (`hct_api.py`): API REST e dashboard web

#### Integrações
- Integração automática com HomeCore Beacon para obtenção de token
- Comunicação com Supervisor API
- Comunicação com Home Assistant API
- Notificações persistentes no HA

#### Scripts de Ferramentas
- `hcc_update.sh`: Atualização do HomeCore Control
- `core_update.sh`: Atualização do Home Assistant Core
- `hacs_update.sh`: Atualização do HACS
- `api_install.sh`: Instalação da API HomeCore
- `api_update.sh`: Atualização da API HomeCore
- `mushroom_update.sh`: Atualização do Mushroom Cards
- Scripts Molsmart (configuração, scanner, MQTT)

#### Configurações
- Nível de log configurável (debug, info, warning, error)
- Intervalo de verificação ajustável (300-86400 segundos)
- Atualização automática habilitável/desabilitável
- Backup antes de atualização configurável
- Notificações configuráveis

#### Segurança
- Backup automático antes de alterações
- Rollback automático em caso de falha
- Validação de checksums de downloads
- Logs de auditoria completos
- Acesso via Ingress (autenticação do HA)

#### Suporte Multi-arquitetura
- armhf
- armv7
- aarch64
- amd64
- i386

### Documentação
- README.md com visão geral
- DOCS.md com documentação completa
- INSTALL.md com guia de instalação
- Traduções em português (pt-BR) e inglês (en)
- Exemplos de uso e configuração
- FAQ e troubleshooting