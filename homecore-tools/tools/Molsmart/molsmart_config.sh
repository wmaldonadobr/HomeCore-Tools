#!/bin/bash
# =====================================================
# Script: mqtt_discover.sh
# Autor: William Magna (ajustado via ChatGPT)
# Função: Registrar automaticamente as entidades MolSmart no MQTT Discovery
# =====================================================

set -euo pipefail

CONFIG_FILE="${CONFIG_FILE:-/config/hc-tools/molsmart_boards.yaml}"
BROKER="${BROKER:-127.0.0.1}"
PORT="${PORT:-1883}"
USER="${USER:-homecoresys}"
PASS="${PASS:-haoshomecore}"
QOS="${QOS:-1}"
RETAIN="${RETAIN:-true}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v mosquitto_pub >/dev/null 2>&1; then
  echo "❌ mosquitto_pub não encontrado. Instale o mosquitto-clients antes de continuar." >&2
  exit 1
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "❌ Interpretador Python não encontrado: $PYTHON_BIN" >&2
  exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
  echo "❌ Arquivo de configuração não encontrado: $CONFIG_FILE" >&2
  exit 1
fi

RETAIN_FLAG=""
if [ "${RETAIN,,}" = "true" ]; then
  RETAIN_FLAG="-r"
fi

"$PYTHON_BIN" - <<'PY' \
  "$CONFIG_FILE" "$BROKER" "$PORT" "$USER" "$PASS" "$QOS" "$RETAIN_FLAG"
import json
import os
import subprocess
import sys

try:
    import yaml
except ImportError as exc:
    sys.stderr.write(f"❌ Dependência PyYAML não encontrada: {exc}\n")
    sys.exit(1)

args = sys.argv[1:]
if len(args) < 6:
    sys.stderr.write("❌ Argumentos insuficientes fornecidos ao script auxiliar.\n")
    sys.exit(1)

config_path, broker, port, user, password, qos, *rest = args
retain_flag = rest[0] if rest else ""

with open(config_path, "r", encoding="utf-8") as fh:
    data = yaml.safe_load(fh) or {}

boards = data.get("boards", [])
if not boards:
    print("⚠️ Nenhuma entidade encontrada para registrar.")
    sys.exit(0)

def publish(topic: str, payload: dict) -> None:
    command = [
        "mosquitto_pub",
        "-h", broker,
        "-p", port,
        "-u", user,
        "-P", password,
        "-q", qos,
        "-t", topic,
        "-m", json.dumps(payload, ensure_ascii=False),
    ]
    if retain_flag:
        command.append(retain_flag)
    subprocess.run(command, check=True)

count = 0
domain_map = {
    "light": "light",
    "switch": "switch",
    "siren": "siren",
    "lock": "lock",
    "cover": "cover",
    "valve": "valve",
}

def ensure_string(value):
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)

def first_value(value, defaults):
    if value is None:
        value = defaults
    if isinstance(value, (list, tuple, set)):
        for item in value:
            if item:
                return str(item)
        return defaults[0]
    return str(value)

for board in boards:
    serial = board.get("serial")
    if not serial:
        continue

    device_name = board.get("name") or board.get("device_name") or serial
    manufacturer = board.get("manufacturer") or "MolSmart"

    # Saídas (channels) tratadas como switches ou lights
    for channel in board.get("channels", []):
        chan_type = (channel.get("type") or "switch").lower()
        chan_id = channel.get("id")
        if not chan_id:
            continue

        friendly_name = channel.get("friendly_name") or channel.get("name") or f"Canal {chan_id}"
        command_topic = channel.get("command_topic") or f"molsmart/{serial}/in/control"
        state_topic = channel.get("state_topic") or f"molsmart/{serial}/out/relay{chan_id}"
        unique_id = channel.get("unique_id") or f"{serial}_relay{chan_id}"
        value_template = channel.get("value_template") or "{{ 'on' if value_json.status == 'ON' else 'off' }}"
        device_class = channel.get("device_class")
        icon = channel.get("icon")

        payload_on = channel.get("payload_on") or {
            "type": "ON/OFF",
            "idx": str(chan_id),
            "status": "ON",
            "time": "0",
            "pass": "0",
        }
        payload_off = channel.get("payload_off") or {
            "type": "ON/OFF",
            "idx": str(chan_id),
            "status": "OFF",
            "time": "0",
            "pass": "0",
        }

        domain = domain_map.get(chan_type, "switch")
        discovery_topic = f"homeassistant/{domain}/{unique_id}/config"

        payload = {
            "name": friendly_name,
            "state_topic": state_topic,
            "unique_id": unique_id,
            "device": {
                "identifiers": [serial],
                "name": device_name,
                "manufacturer": manufacturer,
            },
        }
        if icon:
            payload["icon"] = icon

        if domain in {"light", "switch", "siren"}:
            payload.update(
                {
                    "command_topic": command_topic,
                    "payload_on": ensure_string(payload_on),
                    "payload_off": ensure_string(payload_off),
                    "value_template": value_template,
                }
            )
            if device_class:
                payload["device_class"] = device_class

        elif domain == "cover":
            payload_open = channel.get("payload_open") or payload_on
            payload_close = channel.get("payload_close") or payload_off
            payload_stop = channel.get("payload_stop")
            payload.update(
                {
                    "command_topic": command_topic,
                    "payload_open": ensure_string(payload_open),
                    "payload_close": ensure_string(payload_close),
                    "value_template": value_template,
                    "state_open": first_value(channel.get("state_open") or channel.get("state_open_values"), ["OPEN", "ON"]),
                    "state_closed": first_value(channel.get("state_closed") or channel.get("state_closed_values"), ["CLOSED", "OFF"]),
                }
            )
            if payload_stop is not None:
                payload["payload_stop"] = ensure_string(payload_stop)
            if device_class:
                payload["device_class"] = device_class

        elif domain == "lock":
            payload_lock = channel.get("payload_lock") or payload_on
            payload_unlock = channel.get("payload_unlock") or payload_off
            payload.update(
                {
                    "command_topic": command_topic,
                    "payload_lock": ensure_string(payload_lock),
                    "payload_unlock": ensure_string(payload_unlock),
                    "state_locked": first_value(channel.get("state_locked") or channel.get("state_locked_values"), ["LOCKED", "ON"]),
                    "state_unlocked": first_value(channel.get("state_unlocked") or channel.get("state_unlocked_values"), ["UNLOCKED", "OFF"]),
                    "value_template": value_template,
                }
            )
            if device_class:
                payload["device_class"] = device_class

        elif domain == "valve":
            payload_open = channel.get("payload_open") or payload_on
            payload_close = channel.get("payload_close") or payload_off
            payload_stop = channel.get("payload_stop")
            payload.update(
                {
                    "command_topic": command_topic,
                    "payload_open": ensure_string(payload_open),
                    "payload_close": ensure_string(payload_close),
                    "value_template": value_template,
                    "state_open": first_value(channel.get("state_open") or channel.get("state_open_values"), ["OPEN", "ON"]),
                    "state_closed": first_value(channel.get("state_closed") or channel.get("state_closed_values"), ["CLOSED", "OFF"]),
                }
            )
            if payload_stop is not None:
                payload["payload_stop"] = ensure_string(payload_stop)
            if device_class:
                payload["device_class"] = device_class

        else:
            # Fallback to switch schema
            payload.update(
                {
                    "command_topic": command_topic,
                    "payload_on": ensure_string(payload_on),
                    "payload_off": ensure_string(payload_off),
                    "value_template": value_template,
                }
            )
            if device_class:
                payload["device_class"] = device_class

        publish(discovery_topic, payload)
        count += 1
        print(f"✅ {domain.capitalize()} {friendly_name} registrado (unique_id: {unique_id})")

    # Entradas digitais
    for index, sensor in enumerate(board.get("inputs", []), start=1):
        sensor_id = sensor.get("id") or index
        state_topic = sensor.get("state_topic") or f"molsmart/{serial}/out/input{sensor_id}"
        unique_id = sensor.get("unique_id") or f"{serial}_input{sensor_id}"
        device_class = sensor.get("device_class") or "motion"
        friendly_name = sensor.get("friendly_name") or sensor.get("name") or f"Entrada {sensor_id}"
        value_template = sensor.get("value_template") or "{{ 'on' if value_json.status == 'LOW' else 'off' }}"
        icon = sensor.get("icon")

        payload = {
            "name": friendly_name,
            "state_topic": state_topic,
            "value_template": value_template,
            "unique_id": unique_id,
            "device_class": device_class,
            "device": {
                "identifiers": [serial],
                "name": device_name,
                "manufacturer": manufacturer,
            },
        }
        if icon:
            payload["icon"] = icon

        discovery_topic = f"homeassistant/binary_sensor/{unique_id}/config"
        publish(discovery_topic, payload)
        count += 1
        print(f"✅ Binary Sensor {friendly_name} registrado (unique_id: {unique_id})")

if count == 0:
    print("⚠️ Nenhuma entidade encontrada para registrar.")
else:
    print("🎉 Todos os dispositivos MolSmart foram Configurados via MQTT!")
PY