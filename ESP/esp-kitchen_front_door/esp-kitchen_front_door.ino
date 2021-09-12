//On ESP8266,  PIN 1 is tied to the blue LED light on the board and TX
// PinOUT  From the bottom with pinouts on the left.
//  3V3 (+) |    RX  (3)
//  RST     |    IO0 (0)
//  EN  (+) |    IO2 (2)
//  TX  (1) |    GND (-)

#if defined(ARDUINO_ARCH_ESP8266)
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#define GET_CHIPID()  (ESP.getChipId())
#elif defined(ARDUINO_ARCH_ESP32)

#include <WiFi.h>
#include <SPIFFS.h>
#include <HTTPClient.h>
#define GET_CHIPID()  ((uint16_t)(ESP.getEfuseMac()>>32))
#endif
#include <PubSubClient.h>
#include <AutoConnect.h>
#include <ArduinoJson.h>

#include <MySQL_Connection.h>
#include <MySQL_Cursor.h>

#if defined(ARDUINO_ARCH_ESP8266)
typedef ESP8266WebServer  WiFiWebServer;
#elif defined(ARDUINO_ARCH_ESP32)
typedef WebServer WiFiWebServer;
#endif


ESP8266WebServer server;
AutoConnect portal(server);
AutoConnectAux Input;
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);


IPAddress database_server(192,168,50,173);                // NEED TO MAKE THIS DYNAMIC

// ************************************************** Sensor Libraries *************************************************
// ************* Adafruit DHT11 sensor libraries
#include <Adafruit_Sensor.h>
#include <DHT.h>
#include <DHT_U.h>


// ************************************************** Define PINs ******************************************************

// ************* PIR sensor setup 
#define motion1 3 //Motion Sensor

// ************* Magentic Reed setup
#define magnet1 0 //Door Sensor

// ************* Adafruit DHT11 sensor setup
#define DHTsensor 2
#define DHTTYPE    DHT11
DHT_Unified dht(DHTsensor, DHTTYPE);


// ************************************************** Input Page *******************************************************

const static char InputPage[] PROGMEM = R"r(
{
  "title": "Channels",
  "uri": "/channels", 
  "menu": true, 
  "element": [
    { 
      "name": "base", 
      "type": "ACInput", 
      "value": "home/rooms/{{room}}/things/{{thing}}/"
    },

    { 
      "name": "room", 
      "type": "ACInput", 
      "value": "Kitchen"
    },

    { 
      "name": "thing", 
      "type": "ACInput", 
      "value": "Front Door"
    },

    { 
      "name": "host_ip", 
      "type": "ACInput", 
      "value": "192.168.50.173"
    }, 
    {
      "name": "save",
      "type": "ACSubmit",
      "value": "SAVE",
      "uri": "/"
    }
  ]
}
)r";

// ********************************************* Mosquitto Connect *****************************************************

bool mqttConnect() {
    // Connect to Mosquitto broker if not connect. Returns True if Connected. False if not.

  String value1 = Input["host_ip"].value;             // get Mosquitto broker IP address

  static const char alphanum[] = "0123456789"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz";                     // Used to Generate random Client IP
  char    clientId[9];

  uint8_t retry = 3;
  while (!mqttClient.connected()) {                   // Do while not connected to mosquitto broker
    if (value1.length() <= 0)
      break;

    mqttClient.setServer(value1.c_str(), 1883);       // Connect to mosquitto broker using IP address
    Serial.println(String("Attempting MQTT broker:") + value1);

    for (uint8_t i = 0; i < 8; i++) {                 // Generate random client ID
      clientId[i] = alphanum[random(62)];
    }
    clientId[8] = '\0';

    if (mqttClient.connect(clientId)) {               // Print to serial successful connection
      Serial.println("Established:" + String(clientId));
      return true;
    }
    else {
      Serial.println("Connection failed:" + String(mqttClient.state()));
      if (!--retry)
        break;
      delay(3000);
    }
  }
  return false;
}

// ************************************************** Root Page ********************************************************

void onRoot() {
// An on-page handler for '/' access

  String  content =
  "<html>"
  "<head><meta name='viewport' content='width=device-width, initial-scale=1'></head>"
  "<body><div>Base MQTT Channel: {{value1}}</div></body>"
  "</html>";
        

  Input.fetchElement();                               // Get saved variables

  String value1 = Input["base"].value;                // Test print variables
  content.replace("{{value1}}", value1);              // Format root page
  server.send(200, "text/html", content);
}

// ************************************************ Sensor Functions ***************************************************

int motion(){
    // Read Motion sensor value and return as char
  return digitalRead(motion1);                          // Return motion value (motion / no motion)
}

int magnet(){
    // Read Motion sensor value
  return digitalRead(magnet1);                          // Return magnet value (open / close)
}

int temperature(){
  // Read Temperature sensor value
  
  sensors_event_t event;                                  // Start sensor event
  dht.temperature().getEvent(&event);                     // Query temperature
   if (isnan(event.temperature)) {                        // If no reading, return error
    Serial.println(F("Error reading temperature!"));
  }
  else {
    Serial.print(F("Temperature: "));                     // Serial print temperature
    Serial.print(event.temperature);                      // Serial print reading
    Serial.println(F("°C"));                              // Serial print unit
    return event.temperature;                             // Return reading
  }
}

int humidity(){
  sensors_event_t event;                                  // Start sensor event
  dht.humidity().getEvent(&event);                        // Query humidity
  if (isnan(event.relative_humidity)) {                   // If no reading, return error
    Serial.println(F("Error reading humidity!"));         
  }
  else {
    Serial.print(F("Humidity: "));                        // Serial print humidity
    Serial.print(event.relative_humidity);                // Serial print reading
    Serial.println(F("%"));                               // Serial print unit
    return event.relative_humidity;                       // Return reading
  }
}

// ********************************************* Interrupt Callbacks ***************************************************

ICACHE_RAM_ATTR void door_detect(){
  String topic = build_topic("interrupt");
  String content = 
  "{"
    "'thing_id': '{{thing_id}}',"
    "'thing_name': '{{thing_name}}',"
    "'interrupt': "
        "{"
          "'sensor_name': '{{magnet_name}}',"
          "'sensor_type': 'magnet',"
          "'sensor_pin': {{magnet_pin}},"
          "'sensor_value': {{magnet}}"
        "}"
  "}";
  int val_magnet = magnet();
  if (val_magnet == 1) {
      
    content.replace("{{thing_name}}",Input["thing"].value);
    content.replace("{{thing_id}}",String(GET_CHIPID()));
    content.replace("{{magnet_name}}","front_door");
    content.replace("{{magnet_pin}}",String(magnet1));
    content.replace("{{magnet}}",String(val_magnet));
  
    mqttPublish(content, topic);

  }
}

ICACHE_RAM_ATTR void motion_detect(){
  String topic = build_topic("interrupt");
  String content = 
  "{"
    "'thing_id': '{{thing_id}}',"
    "'thing_name': '{{thing_name}}',"
    "'interrupt': "
        "{"
          "'sensor_name': '{{motion_name}}',"
          "'sensor_type': 'motion',"
          "'sensor_pin': {{motion_pin}},"
          "'sensor_value': {{motion}}"
        "}"
  "}";
  int val_motion = motion();
  if (val_motion == 1) {
      
    content.replace("{{thing_name}}",Input["thing"].value);
    content.replace("{{thing_id}}",String(GET_CHIPID()));
    content.replace("{{motion_name}}","front_door_motion1");
    content.replace("{{motion_pin}}",String(motion1));
    content.replace("{{motion}}",String(val_motion));
  
    mqttPublish(content, topic);

  }
}

//
// ********************************************* Mosquitto Publish *****************************************************

void mqttPublish(String msg, String path) {
    // Mosquitto broadcast wrapper function
  Serial.print("Sending ");                           // Inform Serial mqtt is about to send
  Serial.print(msg);                                  // Print message to serial
  Serial.print(" to...");
  Serial.print(path);                                 // Print channel to serial
  mqttClient.publish(path.c_str(), msg.c_str());      // Publish payload to topic  
}

// ********************************************* Mosquitto Subcribe ****************************************************

void subscribe_to_channels() {
    // Connect/ Reconnect to Mosquitto Broker.
      String requests = build_topic("requests");
      mqttClient.subscribe(requests.c_str(),1);           // Subscribe to commands channel
}

// ********************************************* Mosquitto Callback ****************************************************

void callback(char* topic, byte* payload, unsigned int length) {
    // Mosquitto Callback function. Receive messages from subscribes topics

  StaticJsonDocument <256> message;
  Serial.print("Message arrived [");                   // Announce message received
  Serial.print(topic);                                 // Print topic
  Serial.print("] ");
  deserializeJson(message, payload);

  String request_id = message["request_id"];
  String command = message["request"];
  
  Serial.println("Request ID: ");
  Serial.print(request_id);
  Serial.println(command);
  
  if (command == "status"){
    send_status(request_id);
  }

}
// ******************************************** Connection Function ****************************************************

void maintain_connection(){
  // Maintain connection to Internet and Mosquitto Broker

  if (WiFi.status() == WL_CONNECTED) {                // If Wifi is connected
      delay(1000);
    if (!mqttClient.connected()) {                    // If mosquitto broker is not connected
      mqttConnect();                                  // Connect to mosquitto broker
      subscribe_to_channels();                        // Subscribe
    }
    mqttClient.loop();
  }
}
// **************************************************** Setup **********************************************************

void setup() {
  // Setup Function. 
  Serial.begin(115200);                              // Start Serial at baud 115200
  Serial.println("ALIVE");
  Input.load(InputPage);                             // Load custom page to AutoConnect
  portal.join(Input);                                // Bind custom page to Menu
  server.on("/", onRoot);                            // Register the on-page handler
  portal.begin();                                    // Start AutoConnect
  mqttClient.setCallback(callback);                  // Set up mosquitto callback
  mqttClient.setBufferSize(1024);

  dht.begin();                                       // Start DHT11 temp/humid sensor

  pinMode(magnet1, INPUT_PULLUP);
  pinMode(motion1, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(magnet1),door_detect, RISING);
  attachInterrupt(digitalPinToInterrupt(motion1),motion_detect, RISING);

}

// ************************************************** Main Loop ********************************************************


void loop() {
  portal.handleClient();
  maintain_connection();
  delay(1000);

}

// ************************************************** Functions *********************************************************

void send_status(String request_id){
// TODO Dynamically build response string

  String topic = build_topic("response");
  String content = 
  "{"
    "'request_id': '{{request_id}}',"
    "'thing_id': '{{thing_id}}',"
    "'thing_name': '{{thing_name}}',"
    "'response': "
      "["
        "{"
          "'sensor_name': '{{dht_name}}',"
          "'sensor_type': 'temperature',"
          "'sensor_pin': {{dht_pin}},"
          "'sensor_value': {{temp}}"
        "},"
        "{"
          "'sensor_name': '{{dht_name}}',"
          "'sensor_type': 'humidity',"
          "'sensor_pin': {{dht_pin}},"
          "'sensor_value': {{humid}}"
        "},"
        "{"
          "'sensor_name': '{{magnet_name}}',"
          "'sensor_type': 'magnet',"
          "'sensor_pin': {{magnet_pin}},"
          "'sensor_value': {{magnet}}"
        "},"
        "{"
          "'sensor_name': '{{motion_name}}',"
          "'sensor_type': 'motion',"
          "'sensor_pin': {{motion_pin}},"
          "'sensor_value': {{motion}}"
        "}"
      "]"
  "}";

  content.replace("{{thing_name}}",Input["thing"].value);
  content.replace("{{thing_id}}",String(GET_CHIPID()));
  content.replace("{{request_id}}", request_id);
  
  content.replace("{{dht_name}}","temp/humid");
  content.replace("{{dht_pin}}", String(DHTsensor));
  
  content.replace("{{magnet_name}}","front_door");
  content.replace("{{magnet_pin}}",String(magnet1));
  
  content.replace("{{motion_name}}","front_door_motion1");
  content.replace("{{motion_pin}}",String(motion1));
  
  content.replace("{{motion}}",String(motion()));
  content.replace("{{temp}}", String(temperature()));
  content.replace("{{humid}}", String(humidity()));
  content.replace("{{magnet}}",String(magnet()));

  mqttPublish(content, topic);
}

String build_topic(String topic){

  String base = Input["base"].value;
  String room = Input["room"].value;
  String thing = Input["thing"].value;

  room.replace(" ","_");
  thing.replace(" ","_");
  room.toLowerCase();
  thing.toLowerCase();
  
  base.replace("{{room}}", room);
  base.replace("{{thing}}", thing);
  base = base + topic;

  return base;
}
