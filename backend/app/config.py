import os


def read_boolean_setting(name: str, default: bool) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.lower() in ["1", "true", "yes", "on"]


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./energy.db")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me-please-32-bytes")

MQTT_ENABLED = read_boolean_setting("MQTT_ENABLED", False)
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

DEMO_MODE = read_boolean_setting("DEMO_MODE", True)
DEMO_EMAIL = os.getenv("DEMO_EMAIL", "demo@smartenergy.local")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "Demo123!")
