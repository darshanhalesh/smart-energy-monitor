# Quick code walkthrough

## Backend

- `app/main.py` starts FastAPI, the database, demo mode and MQTT.
- `app/config.py` reads settings from environment variables.
- `app/db.py` creates the database connection.
- `app/models.py` contains the database tables.
- `app/schemas.py` describes API input and output data.
- `app/security.py` handles passwords and login tokens.
- `app/mqtt.py` receives ESP32 readings and sends relay commands.
- `app/analytics.py` checks unusual power values and creates a simple forecast.
- `app/demo.py` creates fake readings when there is no hardware.
- `app/routers/` contains the API endpoints.

## Frontend

- `src/api.ts` is the only file that talks to the backend API.
- `src/types.ts` contains the data shapes used by TypeScript.
- `src/App.tsx` contains the login page and dashboard components.
- `src/styles.css` contains the page styling.

## Firmware

- `src/main.cpp` connects the ESP32 to Wi-Fi and MQTT, reads the PZEM sensor, sends readings and controls the relay.

## Running

- `docker-compose.yml` tells Docker which services to run.
- `start.bat` is the easiest Windows start file.
