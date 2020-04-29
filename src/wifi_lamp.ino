#include "Secrets.h"

#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <DNSServer.h>
#include <ESP8266WebServer.h>
#include <WiFiManager.h>
#include <Ticker.h>
#include <PubSubClient.h>
#include <FastLED.h>

#include "../ESP8266_new_pwm/pwm.c"

enum DeviceMode {
  booting = 0,
  normal,
  wifi_setup
};

#define PWM_CHANNELS 2
const uint32_t period = 256; // * 200ns ^= 19 kHz

// PWM setup
uint32 io_info[PWM_CHANNELS][3] = {
	// MUX, FUNC, PIN
	{PERIPHS_IO_MUX_GPIO0_U,  FUNC_GPIO0, 0},
	{PERIPHS_IO_MUX_GPIO4_U,  FUNC_GPIO4, 4},
};

// initial duty: all off
uint32 pwm_duty_init[PWM_CHANNELS] = {0, 0};

const static uint8_t STATUS_LED = 5;
const static uint8_t LIGHT_2700K_PIN = 4;
const static uint8_t LIGHT_4000K_PIN = 0;

WiFiManager wifiManager;
Ticker animationTicker;

#ifdef LANTERN_USE_SSL
BearSSL::WiFiClientSecure wifi;
#else
WiFiClient wifi;
#endif

PubSubClient client(wifi);

uint8_t color_fade = 0;
uint8_t brightness = 255;
bool on = 0;
bool dirty = 0;

uint8_t mac[WL_MAC_ADDR_LENGTH];
char device_id[9];
std::string light_id;
std::string light_id_all;
std::string light_id_availability;

DeviceMode device_mode = booting;

void configModeCallback(WiFiManager *myWiFiManager) {
  device_mode = wifi_setup;
  digitalWrite(STATUS_LED, 0);
}

void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  std::string payload_str ((char *)payload, length);
  std::string topic_str (topic, strlen(topic));
  char buf[5];

  if (topic_str.find(light_id) == 0 &&
      topic_str.length() > light_id.length()) {
    std::string subpath = topic_str.substr(light_id.length());

    if (subpath.compare("/switch/on") == 0) {
      on = payload_str.compare("on") == 0;
      client.publish((light_id + "/switch/status").c_str(), on ? "on" : "off", 1);
      dirty = true;
    } else if (subpath.compare("/brightness/set") == 0) {
      brightness = max(0, min(255, (int)(strtol(payload_str.c_str(), nullptr, 10))));
      sprintf(buf,"%d", brightness);
      client.publish((light_id + "/brightness/status").c_str(), buf, 1);
      dirty = true;
    } else if (subpath.compare("/temperature/set") == 0) {
      int color_fade_input = max(250, min(370, (int)(strtol(payload_str.c_str(), nullptr, 10))));
      sprintf(buf,"%d", color_fade_input);
      client.publish((light_id + "/temperature/status").c_str(), buf, 1);
      color_fade = map(color_fade_input, 250, 370, 0, 255);
      dirty = true;
    }
  }
}

void setup() {
  pinMode(STATUS_LED, OUTPUT);
  pinMode(LIGHT_2700K_PIN, OUTPUT);
  pinMode(LIGHT_4000K_PIN, OUTPUT);
  digitalWrite(STATUS_LED, 1);

  pwm_init(period, pwm_duty_init, PWM_CHANNELS, io_info);
  pwm_start();

  wifiManager.setAPCallback(configModeCallback);

  if (!wifiManager.autoConnect("WorkbenchLamp")) {
    ESP.reset();
    delay(1000);
  }

  if (device_mode == wifi_setup) {
    device_mode = normal;
    digitalWrite(STATUS_LED, 1);
  }

  wifi.setInsecure();

  WiFi.macAddress(mac);
  sprintf(device_id, "%02x%02x%02x%02x", mac[2], mac[3], mac[4], mac[5]);
  light_id = "lamp/" + std::string(device_id);
  light_id_all = light_id + "/#";
  light_id_availability = light_id + "/availability";

  client.setServer(mqtt_host, mqtt_port);
  client.setCallback(mqtt_callback);
}

void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    // Create a random client ID
    String clientId = "lamp-";
    clientId += device_id;

    bool connected;
    if (strlen(mqtt_user) == 0) {
      connected = client.connect(clientId.c_str(), light_id_availability.c_str(),
                                 0, 1, "offline");
    } else {
      connected = client.connect(clientId.c_str(), mqtt_user, mqtt_password,
                                 light_id_availability.c_str(), 0, 1, "offline");
    }

    if (connected) {
      digitalWrite(STATUS_LED, 0);
      client.subscribe(light_id_all.c_str());

      // Once connected, publish an announcement...
      client.publish(light_id_availability.c_str(), "online", 1);
    } else {
      digitalWrite(STATUS_LED, 1);
      // don't thrash reconnects
      delay(1000);
    }
  }
}

void loop() {
  while (!client.connected()) {
    reconnect();
  }

  client.loop();

  if (dirty) {
    if (on) {
      if (color_fade < 255) {
        pwm_set_duty(scale8(min(255, (255 - color_fade) * 2), brightness) + 1, 0);
      } else {
        pwm_set_duty(0, 0);
      }

      if (color_fade > 0) {
        pwm_set_duty(scale8(min(255, color_fade * 2), brightness) + 1, 1);
      } else {
        pwm_set_duty(0, 1);
      }
      pwm_start();
    } else {
      pwm_set_duty(0, 0);
      pwm_set_duty(0, 1);
      pwm_start();
    }
    dirty = false;
  }
  delay(10);
}
