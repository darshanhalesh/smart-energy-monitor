# Architecture

The project has four main parts.

```text
ESP32 -> MQTT -> FastAPI -> Database
                    |
                    v
              React dashboard
```

## Reading flow

1. The PZEM sensor measures electricity values.
2. The ESP32 reads those values.
3. The ESP32 publishes a JSON message to MQTT.
4. FastAPI receives the message.
5. FastAPI saves the reading in the database.
6. The dashboard asks FastAPI for the saved data.
7. The browser displays the values and chart.

## Relay flow

1. The user presses the relay button on the dashboard.
2. The dashboard sends a request to FastAPI.
3. FastAPI changes the stored relay state.
4. FastAPI publishes the new state to MQTT.
5. The ESP32 receives the command and changes the relay pin.

## Demo mode

When demo mode is on, the backend creates a demo user, one device and historical readings. It also adds a new demo reading every five seconds.
