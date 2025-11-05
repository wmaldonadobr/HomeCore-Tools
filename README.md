# HomeCore Tools Add-on

Add-on HomeCore Tools centraliza os fluxos de atualização da plataforma HomeCore em um único serviço HTTP.  
Ele roda dentro do Home Assistant Supervisor, com acesso controlado ao `/config`, `/ssl` e `/data`.

## Recursos
- API interna para solicitar atualizações do HomeCore (`api`, `core`, `hcc`).
- Downloads com retries, validação opcional de checksum e criação automática de backups.
- Registro de logs estruturados em `/data/logs` e status da última execução em `/data/status.json`.
- Endpoint de saúde (`/health`) para integrações de monitoramento.

## Instalação
1. Adicione o repositório do add-on no Home Assistant (Settings → Add-ons → Add-on Store → ••• → Repositories).  
   `https://github.com/homecore/homecore-tools-addon`
2. Instale o add-on **HomeCore Tools**.
3. Configure as opções conforme necessário (ver seção a seguir).
4. Inicie o add-on e verifique os logs iniciais.

## Configuração (`config.json`)

| Campo | Descrição | Default |
| --- | --- | --- |
| `api_base_url` | Endpoint remoto para atualizar os artefatos `api`. | `https://homecore.com.br/api/sync/beacon.php` |
| `core_base_url` | Endpoint remoto do pacote `core`. | `https://homecore.com.br/api/update/core` |
| `hcc_base_url` | Endpoint remoto do pacote `hcc`. | `https://homecore.com.br/api/hcc` |
| `auth_token` | Token necessário no header `Authorization: Bearer`. Altere antes de habilitar produção. | `change-me` |
| `log_retention_days` | Dias de retenção dos arquivos de log em `/data/logs`. | `7` |

Os diretórios padrão criados pelo add-on:
- `/config/homecore/{api,core,hcc}` para aplicação dos artefatos.
- `/data/backups/{api,core,hcc}` para os artefatos baixados.
- `/data/logs` para logs individuais por execução.

## API HTTP

Todos os endpoints (exceto `/health`) exigem `Authorization: Bearer <auth_token>`.

| Método | Caminho | Descrição |
| --- | --- | --- |
| `GET` | `/health` | Retorna `{"status": "ok"}` para verificação de vida. |
| `POST` | `/update/api` | Dispara atualização da camada API. |
| `POST` | `/update/core` | Dispara atualização do núcleo. |
| `POST` | `/update/hcc` | Dispara atualização do HomeCore Controller. |
| `GET` | `/logs?type=<api|core|hcc>` | Lista logs recentes por tipo. |
| `GET` | `/status` | Último status registrado de cada componente. |

### Payload de atualização

```json
{
  "token": "cliente-xyz",
  "client_id": "opcional",
  "force": false
}
```

- `token`: obrigatório (via payload ou arquivo `/config/homecore/client_token`).
- `force`: define se a versão deve ser reaplicada mesmo se já estiver atualizada.

### Resposta padrão (`UpdateResponse`)

```json
{
  "status": "ok",
  "message": "Update api aplicado (versão 1.2.3)",
  "version": "1.2.3",
  "log_path": "/data/logs/20250101T120000_api_update.log",
  "started_at": "2025-01-01T12:00:00Z",
  "finished_at": "2025-01-01T12:01:07Z",
  "exit_code": 0
}
```

`status` pode ser `ok`, `no_update` ou `error`.

## Exemplo de Automação (`rest_command`)

```yaml
rest_command:
  homecore_update_api:
    url: "http://homeassistant.local:8125/update/api"
    method: POST
    headers:
      Authorization: "Bearer !secret homecore_tools_token"
      Content-Type: "application/json"
    payload: >
      {
        "token": "{{ states('input_text.homecore_client_token') }}",
        "client_id": "{{ states('sensor.homecore_client_id') }}",
        "force": {{ 'true' if is_state('input_boolean.homecore_force_update', 'on') else 'false' }}
      }
```

Chame `rest_command.homecore_update_api` a partir de uma automação, script ou do painel de serviços.

## Desenvolvimento
- Aplicação escrita em FastAPI 0.110 rodando via `uvicorn`.
- Dependências listadas em `requirements.txt`.
- Execute o servidor localmente com `uvicorn app.main:app --reload --port 8125`.

## Licença
Este projeto segue a licença da organização HomeCore. Consulte o responsável pela distribuição para detalhes.
