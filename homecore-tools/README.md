# HomeCore Tools Add-on

[![GitHub Release](https://img.shields.io/github/release/homecore/homecore-tools-addon.svg?style=flat-square)](https://github.com/homecore/homecore-tools-addon/releases)
[![License](https://img.shields.io/github/license/homecore/homecore-tools-addon.svg?style=flat-square)](LICENSE)

Add-on para Home Assistant que fornece ferramentas de manutenção e atualização automática para sistemas HomeCore.

## Sobre

O **HomeCore Tools** é um add-on completo que gerencia atualizações automáticas de configurações, scripts e ferramentas do ecossistema HomeCore. Ele se integra perfeitamente com a integração HomeCore Beacon para fornecer uma experiência de manutenção totalmente automatizada.

## Funcionalidades

- ✅ Verificação automática de atualizações via sistema de manifests
- ✅ Aplicação automática de atualizações (configurável)
- ✅ Backup automático antes de cada atualização
- ✅ Rollback automático em caso de falha
- ✅ Notificações persistentes sobre atualizações
- ✅ Dashboard web para monitoramento e controle
- ✅ Logs estruturados em JSON
- ✅ Integração com HomeCore Beacon

## Instalação

### Via Repositório

1. Adicione o repositório no Home Assistant:
   ```
   https://github.com/homecore/homecore-tools-addon
   ```

2. Instale o add-on "HomeCore Tools"

3. Configure conforme necessário

4. Inicie o add-on

### Requisitos

- Home Assistant OS 2024.1.0+
- Integração HomeCore Beacon instalada e configurada

## Configuração

```yaml
log_level: info
check_interval: 3600
auto_update: true
backup_before_update: true
notify_on_update: true
```

Veja [DOCS.md](DOCS.md) para documentação completa.

## Arquitetura

```
homecore-tools/
├── config.yaml          # Configuração do add-on
├── build.yaml           # Build multi-arch
├── Dockerfile           # Imagem Docker
├── run.sh              # Script de inicialização
├── rootfs/
│   └── usr/bin/
│       ├── hct-daemon.py    # Daemon principal
│       ├── hct-updater.py   # Sistema de atualização
│       ├── hct-logger.py    # Sistema de logs
│       └── hct-api.py       # API REST e dashboard
└── tools/              # Scripts bash hc-tools
```

### Componentes

#### HCT Daemon (`hct-daemon.py`)

Daemon principal que:
- Obtém token da integração HomeCore Beacon
- Verifica periodicamente por atualizações
- Aplica atualizações automaticamente (se habilitado)
- Envia notificações ao usuário

#### HCT Updater (`hct-updater.py`)

Sistema de atualização que:
- Busca manifests remotos
- Compara versões local vs remota
- Baixa pacotes de atualização
- Verifica checksums
- Cria backups
- Aplica atualizações
- Faz rollback em caso de falha

#### HCT Logger (`hct-logger.py`)

Sistema de logs que:
- Gera logs estruturados em JSON
- Rotação automática de logs
- Integração com logger do HA
- Níveis configuráveis (debug, info, warning, error)

#### HCT API (`hct-api.py`)

API REST e dashboard web que:
- Fornece interface web via Ingress
- Endpoints REST para status e controle
- Visualização de logs
- Controle manual de atualizações

## Sistema de Manifests

O add-on gerencia três tipos de manifests:

### 1. Core Manifest

Atualizações do núcleo do sistema HomeCore.

**Exemplo:**
```json
{
  "name": "HomeCore Core",
  "version": "1.1.0",
  "description": "Atualização do núcleo",
  "checksum": "sha256:abc123...",
  "download_url": "https://homecore.com.br/api/core_update.php",
  "updated_at": "2025-11-05T19:00:00Z"
}
```

### 2. HCC Manifest

Configurações personalizadas do cliente.

### 3. MolSmart Manifest

Configurações específicas para dispositivos MolSmart.

## Desenvolvimento

### Estrutura de Diretórios

```
homecore-tools/
├── config.yaml                 # Configuração do add-on
├── build.yaml                  # Build multi-arch
├── Dockerfile                  # Imagem Docker
├── run.sh                      # Script de inicialização
├── DOCS.md                     # Documentação do usuário
├── README.md                   # Este arquivo
├── CHANGELOG.md                # Histórico de versões
├── translations/
│   ├── en.yaml                 # Traduções inglês
│   └── pt-BR.yaml              # Traduções português
├── rootfs/
│   ├── etc/services.d/
│   │   └── hct-daemon/
│   │       ├── run             # Script S6
│   │       └── finish          # Finalização S6
│   └── usr/bin/
│       ├── hct-daemon.py       # Daemon principal
│       ├── hct-updater.py      # Sistema de atualização
│       ├── hct-logger.py       # Sistema de logs
│       └── hct-api.py          # API REST
└── tools/                      # Scripts bash
    ├── hcc_update.sh
    ├── core_update.sh
    └── Molsmart/
```

### Build Local

```bash
# Build para arquitetura local
docker build -t homecore-tools .

# Build multi-arch (requer buildx)
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  -t homecore/homecore-tools:latest \
  .
```

### Teste Local

```bash
# Executar container localmente
docker run --rm \
  -v /path/to/config:/config \
  -v /path/to/data:/data \
  -e SUPERVISOR_TOKEN=test_token \
  -e HCT_LOG_LEVEL=debug \
  -p 8099:8099 \
  homecore-tools
```

### Estrutura de Logs

```json
{
  "timestamp": "2025-11-05T19:30:00Z",
  "level": "INFO",
  "component": "hct-updater",
  "action": "update_applied",
  "details": {
    "package": "HomeCore Custom",
    "version": "1.2.0",
    "duration_seconds": 45
  },
  "status": "success"
}
```

## API REST

### Endpoints

#### `GET /api/status`

Retorna status do sistema.

**Response:**
```json
{
  "token": true,
  "last_check": "2025-11-05T19:30:00Z",
  "auto_update": true,
  "check_interval": 3600,
  "log_level": "INFO"
}
```

#### `GET /api/manifests`

Retorna atualizações disponíveis.

**Response:**
```json
{
  "updates": [
    {
      "type": "hcc",
      "current": "1.0.0",
      "available": "1.1.0",
      "manifest": { ... }
    }
  ]
}
```

#### `GET /api/logs?limit=100`

Retorna logs recentes.

**Response:**
```json
{
  "logs": [
    {
      "timestamp": "2025-11-05T19:30:00Z",
      "level": "INFO",
      "component": "hct-daemon",
      "action": "startup",
      "details": { ... }
    }
  ]
}
```

#### `POST /api/update/check`

Força verificação de atualizações.

**Response:**
```json
{
  "success": true,
  "updates": [ ... ]
}
```

#### `POST /api/update/apply`

Aplica atualizações disponíveis.

**Response:**
```json
{
  "success": true,
  "success_count": 2,
  "failed_count": 0
}
```

## Integração com HomeCore Beacon

O add-on se integra com a integração HomeCore Beacon para:

1. **Obter Token**: Busca automaticamente o token via Supervisor API
2. **Compartilhar Logs**: Logs podem ser enviados ao backend HomeCore
3. **Sincronizar Estado**: Estado de atualizações é sincronizado

### Obtenção do Token

```python
# Via Supervisor API
GET http://supervisor/core/api/config_entries
Authorization: Bearer ${SUPERVISOR_TOKEN}

# Procura por domain == 'homecore'
# Extrai entry['data']['token']
```

## Segurança

### Permissões Necessárias

- `hassio_api: true` - Acesso à API do Supervisor
- `hassio_role: manager` - Permissões de gerenciamento
- `homeassistant_api: true` - Acesso à API do HA
- `map: homeassistant_config (read_only: false)` - Escrita em /config

### Validações

- ✅ Checksum de pacotes baixados
- ✅ HTTPS obrigatório para APIs
- ✅ Validação de token
- ✅ Backup antes de alterações
- ✅ Rollback automático

## Troubleshooting

### Logs

```bash
# Via CLI
ha addons logs homecore-tools

# Via UI
Supervisor > HomeCore Tools > Log
```

### Debug Mode

```yaml
log_level: debug
```

### Problemas Comuns

1. **Token não encontrado**: Verifique se integração HomeCore Beacon está instalada
2. **Atualizações não aplicadas**: Verifique `auto_update` nas configurações
3. **Erro de permissão**: Verifique mapeamento de volumes no config.yaml

## Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o repositório
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## Changelog

Veja [CHANGELOG.md](CHANGELOG.md) para histórico de versões.

## Licença

Este projeto é licenciado sob os termos da licença MIT. Veja [LICENSE](LICENSE) para detalhes.

## Suporte

- **Email**: suporte@homecore.com.br
- **Website**: https://homecore.com.br
- **GitHub Issues**: https://github.com/homecore/homecore-tools-addon/issues
- **Comunidade**: https://community.homecore.com.br

## Créditos

Desenvolvido por [HomeCore](https://homecore.com.br)

---

**Versão:** 1.0.0  
**Última Atualização:** 2025-11-05
