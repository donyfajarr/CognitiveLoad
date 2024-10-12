#include "BLEDevice.h"
#include <Wire.h>
// #include "Adafruit_MCP9808.h"
#include <Firebase_ESP_Client.h>
#include "addons/TokenHelper.h"
#include "addons/RTDBHelper.h"
#include <Adafruit_MLX90614.h>

// Adafruit_MCP9808 tempsensor = Adafruit_MCP9808();
Adafruit_MLX90614 mlx = Adafruit_MLX90614();

#define WIFI_SSID "LOSIK"
#define WIFI_PASSWORD "12345678"
#define API_KEY "AIzaSyDcmvBVTt3zT0eJUf97tFkX50u9KyqHzlo"
#define DATABASE_URL "https://cognitive-load-default-rtdb.asia-southeast1.firebasedatabase.app/"

FirebaseData fbdo;
FirebaseAuth auth;
FirebaseConfig config;
FirebaseJson json;


#include "time.h"
#include "sntp.h"


const char* ntpServer1 = "pool.ntp.org";
const char* ntpServer2 = "time.nist.gov";
const long gmtOffset_sec = 25200;
const int daylightOffset_sec = 3600;

const char* time_zone = "CET-1CEST,M3.5.0,M10.5.0/3";

bool signupOK = false;



// The remote service we wish to connect to.
static BLEUUID serviceUUID("0000180D-0000-1000-8000-00805F9B34FB");
// The characteristic of the remote service we are interested in.
static BLEUUID charUUID("00002A37-0000-1000-8000-00805F9B34FB");

static boolean doConnect = false;
static boolean connected = false;
static boolean doScan = false;
static BLERemoteCharacteristic* pRemoteCharacteristic;
uint8_t intValue = 0;

String printLocalTime() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    Serial.println("No time available (yet)");
    return String("");
    ;
  }
  char timeString[40];
  strftime(timeString, sizeof(timeString), "%A, %B %d %H:%M:%S", &timeinfo);
  return String(timeString);
}

void timeavailable(struct timeval* t) {
  Serial.println("Got time adjustment from NTP!");
  printLocalTime();
}

static BLEAdvertisedDevice* myDevice;

static void notifyCallback(
  BLERemoteCharacteristic* pBLERemoteCharacteristic,
  uint8_t* pData,
  size_t length,
  bool isNotify) {
  for (size_t i = 0; i < length; i++) {
    intValue = pData[i];
  }
}

class MyClientCallback : public BLEClientCallbacks {
  void onConnect(BLEClient* pclient) {
  }

  void onDisconnect(BLEClient* pclient) {
    connected = false;
    if (myDevice) {
      delete myDevice;
      myDevice = nullptr;
    }


    Serial.println("onDisconnect");
  }
};

bool connectToServer() {
  Serial.print("Forming a connection to ");
  Serial.println(myDevice->getAddress().toString().c_str());

  BLEClient* pClient = BLEDevice::createClient();
  Serial.println(" - Created client");

  pClient->setClientCallbacks(new MyClientCallback());

  // Connect to the remove BLE Server.
  pClient->connect(myDevice);  // if you pass BLEAdvertisedDevice instead of address, it will be recognized type of peer device address (public or private)
  Serial.println(" - Connected to server");
  // Obtain a reference to the service we are after in the remote BLE server.
  BLERemoteService* pRemoteService = pClient->getService(serviceUUID);
  if (pRemoteService == nullptr) {
    Serial.print("Failed to find our service UUID: ");
    Serial.println(serviceUUID.toString().c_str());
    pClient->disconnect();
    return false;
  }
  Serial.println(" - Found our service");


  // Obtain a reference to the characteristic in the service of the remote BLE server.
  pRemoteCharacteristic = pRemoteService->getCharacteristic(charUUID);
  if (pRemoteCharacteristic == nullptr) {
    Serial.print("Failed to find our characteristic UUID: ");
    Serial.println(charUUID.toString().c_str());
    pClient->disconnect();
    return false;
  }
  Serial.println(" - Found our characteristic");

  if (pRemoteCharacteristic->canNotify())
    pRemoteCharacteristic->registerForNotify(notifyCallback);
  Serial.println("Jalan");
  return true;
}

class MyAdvertisedDeviceCallbacks : public BLEAdvertisedDeviceCallbacks {
  /**
   * Called for each advertising BLE server.
   */
  void onResult(BLEAdvertisedDevice advertisedDevice) {
    Serial.print("BLE Advertised Device found: ");
    Serial.println(advertisedDevice.toString().c_str());

    // We have found a device, let us now see if it contains the service we are looking for.
    if (advertisedDevice.haveServiceUUID() && advertisedDevice.isAdvertisingService(serviceUUID)) {

      BLEDevice::getScan()->stop();
      if (myDevice) {
        delete myDevice;
      }
      myDevice = new BLEAdvertisedDevice(advertisedDevice);

      doConnect = true;
      doScan = true;

    }  // Found our server
  }    // onResult
};     // MyAdvertisedDeviceCallbacks


void setup() {
  Serial.begin(115200);
  Serial.println("Starting Arduino BLE Client application...");
  BLEDevice::init("");
  BLEScan* pBLEScan = BLEDevice::getScan();
  pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
  pBLEScan->setInterval(1349);
  pBLEScan->setWindow(449);
  pBLEScan->setActiveScan(true);
  pBLEScan->start(5, false);

  // TIME SETUP
  sntp_set_time_sync_notification_cb(timeavailable);
  sntp_servermode_dhcp(1);  // (optional)
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer1, ntpServer2);

  // WIFI SETUP

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(300);
  }
  Serial.println("Connected with IP:");
  Serial.println(WiFi.localIP());

  config.api_key = API_KEY;
  config.database_url = DATABASE_URL;
  if (Firebase.signUp(&config, &auth, "", "")) {
    Serial.println("signUp OK");
    signupOK = true;
  } else {
    Serial.printf("%s\n", config.signer.signupError.message.c_str());
  }
  config.token_status_callback = tokenStatusCallback;
  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);

  // Initialize sensor
  Serial.println("Adafruit MLX90614 test");

  if (!mlx.begin()) {
    Serial.println("Error connecting to MLX sensor. Check wiring.");
    while (1)
      ;
  };
}


// This is the Arduino main loop function.
void loop() {
  Firebase.ready();
  if (doConnect == true) {
    if (connectToServer()) {
      Serial.println("We are now connected to the BLE Server.");
      connected = true;
    } else {
      Serial.println("We have failed to connect to the server; there is nothin more we will do.");
    }
    doConnect = false;
  }

  if (connected) {
    float c = mlx.readObjectTempC();
    Serial.print("BPM");
    Serial.println(intValue);
    Serial.print("temperatureC=");
    Serial.println(c);

    if (intValue >= 50 && intValue <= 200) {

      String timestamp = printLocalTime();
      String parent = "Data/" + timestamp;
      String path = "/Temp";
      String path2 = "/BPM";
      json.set(path.c_str(), c);
      json.set(path2.c_str(), intValue);
      Serial.printf("Set json... %s\n", Firebase.RTDB.setJSON(&fbdo, parent.c_str(), &json) ? "ok" : fbdo.errorReason().c_str());
    }

  } else if (doScan) {
    BLEDevice::getScan()->start(0);
  }
}
