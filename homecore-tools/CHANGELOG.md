# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

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
- **HCT Daemon** (`hct-daemon.py`): Daemon principal que orquestra o sistema
- **HCT Updater** (`hct-updater.py`): Sistema de download e aplicação de atualizações
- **HCT Logger** (`hct-logger.py`): Sistema de logs estruturados com rotação automática
- **HCT API** (`hct-api.py`): API REST e dashboard web

#### Integrações
- Integração automática com HomeCore Beacon para obtenção de token
- Comunicação com Supervisor API
- Comunicação com Home Assistant API
- Suporte a notificações persistentes

#### Configurações
- `log_level`: Nível de detalhamento dos logs (debug, info, warning, error)
- `check_interval`: Intervalo de verificação de atualizações (300-86400 segundos)
- `auto_update`: Habilitar/desabilitar aplicação automática
- `backup_before_update`: Criar backup antes de atualizações
- `notify_on_update`: Enviar notificações ao usuário

#### Tipos de Manifest
- **Core Manifest**: Atualizações do núcleo do sistema
- **HCC Manifest**: Configurações personalizadas do cliente
- **MolSmart Manifest**: Configurações de dispositivos MolSmart

#### Scripts Bash
- `hcc_update.sh`: Atualização do HomeCore Custom
- `core_update.sh`: Atualização do núcleo
- `api_update.sh`: Atualização da API
- `hacs_update.sh`: Atualização do HACS
- `mushroom_update.sh`: Atualização do Lovelace Mushroom
- Scripts MolSmart: `molsmart_config.sh`, `molsmart_scanner.sh`, `mqtt_update.sh`

#### Dashboard Web
- Visualização de status do sistema
- Lista de atualizações disponíveis
- Botão para verificar atualizações manualmente
- Botão para aplicar atualizações manualmente
- Visualização de logs recentes (últimos 20)
- Atualização automática a cada 30 segundos

#### Documentação
- DOCS.md: Documentação completa do usuário
- README.md: Documentação do desenvolvedor
- CHANGELOG.md: Histórico de versões
- Comentários inline no código

#### Segurança
- Verificação de checksums em downloads
- Validação de token de autenticação
- Backup antes de alterações
- Rollback automático em falhas
- Logs de auditoria

### Características Técnicas

#### Arquitetura
- Base: Alpine Linux 3.19
- Linguagem: Python 3.11
- Framework web: Flask
- Multi-arch: armhf, armv7, aarch64, amd64, i386

#### Volumes Mapeados
- `/config` (read/write): Acesso às configurações do HA
- `/share` (read/write): Compartilhamento de arquivos
- `/backup` (read-only): Acesso a backups
- `/ssl` (read-only): Certificados SSL

#### Permissões
- `hassio_api: true`: Acesso à API do Supervisor
- `hassio_role: manager`: Permissões de gerenciamento
- `homeassistant_api: true`: Acesso à API do HA

#### Performance
- Verificação assíncrona de atualizações
- Cache de manifests (5 minutos)
- Rotação automática de logs (10 MB por arquivo, 5 backups)
- Download com retry (3 tentativas, 5 segundos de delay)

### Notas de Lançamento

Esta é a primeira versão estável do HomeCore Tools Add-on. O sistema foi projetado para ser:

- **Seguro**: Backups automáticos e rollback em caso de falha
- **Confiável**: Logs estruturados e tratamento robusto de erros
- **Fácil de usar**: Dashboard web intuitivo e notificações claras
- **Automatizado**: Verificação e aplicação automática de atualizações
- **Flexível**: Configurações ajustáveis para diferentes necessidades

### Requisitos

- Home Assistant OS 2024.1.0 ou superior
- Integração HomeCore Beacon instalada e configurada
- Conexão estável com a internet
- Espaço em disco: ~200 MB (incluindo logs e backups)

### Instalação

Veja [DOCS.md](DOCS.md) para instruções completas de instalação e configuração.

### Problemas Conhecidos

Nenhum problema conhecido nesta versão.

### Próximas Versões

Planejado para versões futuras:

- [ ] Suporte a webhooks para notificações externas
- [ ] Agendamento de atualizações (aplicar em horário específico)
- [ ] Comparação semântica de versões (SemVer)
- [ ] Compressão automática de backups antigos
- [ ] Métricas de performance no dashboard
- [ ] Exportação de logs em diferentes formatos
- [ ] Suporte a múltiplos idiomas no dashboard
- [ ] Integração com Home Assistant Supervisor backups

---

## Formato do Changelog

### Tipos de Mudanças

- **Adicionado**: Para novas funcionalidades
- **Modificado**: Para mudanças em funcionalidades existentes
- **Descontinuado**: Para funcionalidades que serão removidas
- **Removido**: Para funcionalidades removidas
- **Corrigido**: Para correções de bugs
- **Segurança**: Para correções de vulnerabilidades

### Versionamento

Este projeto segue o [Versionamento Semântico](https://semver.org/lang/pt-BR/):

- **MAJOR**: Mudanças incompatíveis na API
- **MINOR**: Novas funcionalidades compatíveis
- **PATCH**: Correções de bugs compatíveis

Exemplo: `1.2.3`
- `1` = MAJOR
- `2` = MINOR
- `3` = PATCH

---

[1.0.0]: https://github.com/homecore/homecore-tools-addon/releases/tag/v1.0.0
