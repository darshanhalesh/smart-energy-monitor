import json
from collections.abc import Callable

from .config import MQTT_ENABLED, MQTT_HOST, MQTT_PORT


TelemetryHandler = Callable[[str, dict], None]

mqtt_client = None
telemetry_handler: TelemetryHandler | None = None


def start_mqtt(handler: TelemetryHandler) -> None:
    global mqtt_client, telemetry_handler

    if not MQTT_ENABLED:
        return

    import paho.mqtt.client as mqtt

    telemetry_handler = handler

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()

    mqtt_client = client


def on_connect(client, userdata, flags, reason_code, properties) -> None:
    client.subscribe("energy/+/telemetry")


def on_message(client, userdata, message) -> None:
    if telemetry_handler is None:
        return

    try:
        device_id = get_device_id_from_topic(message.topic)
        data = json.loads(message.payload.decode("utf-8"))
        telemetry_handler(device_id, data)
    except Exception as error:
        print("MQTT message error:", error)


def get_device_id_from_topic(topic: str) -> str:
    parts = topic.split("/")

    if len(parts) != 3:
        raise ValueError("Invalid MQTT topic")

    return parts[1]


def publish_command(device_id: int, relay_on: bool) -> None:
    if not MQTT_ENABLED:
        return

    if mqtt_client is None:
        return

    topic = f"energy/{device_id}/command"
    message = json.dumps({"relay_on": relay_on})

    mqtt_client.publish(topic, message)
