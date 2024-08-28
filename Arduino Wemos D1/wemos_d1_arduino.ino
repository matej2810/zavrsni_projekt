#include "ESP8266WiFi.h"
#include <ESP8266HTTPClient.h>
#include <SPI.h>
#include <MFRC522.h>

#define RST_PIN D3          // Configurable, see typical pin layout above
#define SS_PIN D8           // Configurable, see typical pin layout above

#define GREEN_LED_PIN D2    // Green LED connected to D2
#define RED_LED_PIN D1      // Red LED connected to D1

MFRC522 mfrc522(SS_PIN, RST_PIN);  // Create MFRC522 instance

const char* ssid = "iPhone 14";  // SSID of the Raspberry Pi Hotspot
const char* password = "neznamlozinku";  // Password of the Raspberry Pi Hotspot

const char* server = "http://172.20.10.5:5000/check_uid";  // Flask API endpoint on Raspberry Pi

WiFiClient wifiClient;

void setup() {
  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  Serial.begin(9600);
  SPI.begin();          // Init SPI bus
  mfrc522.PCD_Init();   // Init MFRC522
  delay(1000);

  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("Connected to WiFi");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  // Look for new cards
  if (!mfrc522.PICC_IsNewCardPresent()) {
    return;
  }

  // Select one of the cards
  if (!mfrc522.PICC_ReadCardSerial()) {
    return;
  }

  // Prepare the UID string with exactly 8 characters
  String uidString = "";
  for (byte i = 0; i < mfrc522.uid.size && i < 4; i++) {  // Limit to first 4 bytes
    uidString += String(mfrc522.uid.uidByte[i] < 0x10 ? "0" : "");
    uidString += String(mfrc522.uid.uidByte[i], HEX);
  }

  Serial.print("Card UID: ");
  Serial.println(uidString);

  // Make the HTTP GET request to the server
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    String url = String(server) + "?uid=" + uidString;
    Serial.print("Requesting URL: ");
    Serial.println(url);

    http.begin(wifiClient, url);  // Initialize the HTTP request

    int httpCode = http.GET();    // Send the request

    if (httpCode > 0) {  // If the request was successful
      Serial.print("HTTP Code: ");
      Serial.println(httpCode);
      String payload = http.getString();
      Serial.println("Response from server: " + payload);

      if (payload.indexOf("allow") > -1) {
        digitalWrite(GREEN_LED_PIN, HIGH);
        delay(500);
        digitalWrite(GREEN_LED_PIN, LOW);
        delay(500);
        Serial.println("Access Granted");
      } else if (payload.indexOf("deny") > -1) {
        digitalWrite(RED_LED_PIN, HIGH);
        delay(500);
        digitalWrite(RED_LED_PIN, LOW);
        delay(500);
        Serial.println("Access Denied");
      }
    } else {
      Serial.print("Error on HTTP request, code: ");
      Serial.println(httpCode);
    }

    http.end();  // Close the connection
  } else {
    Serial.println("WiFi not connected");
  }

  // Halt PICC to stop it from being active
  mfrc522.PICC_HaltA();
}
