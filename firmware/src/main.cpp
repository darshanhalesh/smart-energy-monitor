#include <Arduino.h>
#include <PZEM004Tv30.h>
#include <PubSubClient.h>
#include <WiFi.h>

#include "secrets.h"


const int RELAY_PIN = 26;
const int PZEM_RX_PIN = 16;
const int PZEM_TX_PIN = 17;
const unsigned long SEND_INTERVAL_MS = 5000;

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

HardwareSerial pzemSerial(2);
PZEM004Tv30 pzem(pzemSerial, PZEM_RX_PIN, PZEM_TX_PIN);

bool relayOn = true;
unsigned long lastReadingTime = 0;


void connectToWifi() {
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
}


String commandTopic() {
  return "energy/" + String(DEVICE_ID) + "/command";
}


String telemetryTopic() {
  return "energy/" + String(DEVICE_ID) + "/telemetry";
}


void connectToMqtt() {
  while (!mqttClient.connected()) {
    String clientName = "energy-" + String(DEVICE_ID);

    if (mqttClient.connect(clientName.c_str())) {
      String topic = commandTopic();
      mqttClient.subscribe(topic.c_str());
      return;
    }

    delay(2000);
  }
}


String messageFromPayload(byte* payload, unsigned int length) {
  String message = "";

  for (unsigned int index = 0; index < length; index++) {
    message += static_cast<char>(payload[index]);
  }

  return message;
}


void applyRelayState(bool turnOn) {
  relayOn = turnOn;
  digitalWrite(RELAY_PIN, relayOn ? HIGH : LOW);
}


void handleMqttMessage(char* topic, byte* payload, unsigned int length) {
  String message = messageFromPayload(payload, length);

  if (message.indexOf("\"relay_on\":true") >= 0) {
    applyRelayState(true);
    return;
  }

  if (message.indexOf("\"relay_on\":false") >= 0) {
    applyRelayState(false);
  }
}


String buildTelemetryJson(
  float voltage,
  float current,
  float power,
  float energy,
  float frequency,
  float powerFactor
) {
  String json = "{";
  json += "\"voltage\":" + String(voltage, 2) + ",";
  json += "\"current\":" + String(current, 2) + ",";
  json += "\"power\":" + String(power, 2) + ",";
  json += "\"energy_kwh\":" + String(energy, 3) + ",";
  json += "\"frequency\":" + String(frequency, 2) + ",";
  json += "\"power_factor\":" + String(powerFactor, 2) + ",";
  json += "\"relay_on\":";
  json += relayOn ? "true" : "false";
  json += "}";

  return json;
}


void sendReading() {
  float voltage = pzem.voltage();
  float current = pzem.current();
  float power = pzem.power();
  float energy = pzem.energy();
  float frequency = pzem.frequency();
  float powerFactor = pzem.pf();

  if (isnan(voltage) || isnan(power)) {
    return;
  }

  String payload = buildTelemetryJson(
    voltage,
    current,
    power,
    energy,
    frequency,
    powerFactor
  );

  String topic = telemetryTopic();
  mqttClient.publish(topic.c_str(), payload.c_str());
}


void setup() {
  pinMode(RELAY_PIN, OUTPUT);
  applyRelayState(true);

  pzemSerial.begin(9600, SERIAL_8N1, PZEM_RX_PIN, PZEM_TX_PIN);

  connectToWifi();

  mqttClient.setServer(MQTT_HOST, MQTT_PORT);
  mqttClient.setCallback(handleMqttMessage);
}


void loop() {
  if (!mqttClient.connected()) {
    connectToMqtt();
  }

  mqttClient.loop();

  unsigned long currentTime = millis();

  if (currentTime - lastReadingTime >= SEND_INTERVAL_MS) {
    sendReading();
    lastReadingTime = currentTime;
  }
}
