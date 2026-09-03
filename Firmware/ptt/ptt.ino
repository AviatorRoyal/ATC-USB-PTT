#include <Keyboard.h>
#include <EEPROM.h>
#include <Adafruit_NeoPixel.h>
#include "pico/bootrom.h"
#include "hardware/watchdog.h"

#define FW_VERSION "1.0.1"
#define DEFAULT_KEY KEY_LEFT_CTRL_ID
#define DEFAULT_BRIGHTNESS 100
#define MAX_LED_BRIGHTNESS 204

const int BUTTON = 13;
const int LED = 16;
const int LED_COUNT = 1;

bool pressed = false;
bool lastButton = false;

uint8_t currentKey;
uint8_t currentBrightness;

Adafruit_NeoPixel statusLed(LED_COUNT, LED, NEO_GRB + NEO_KHZ800);

uint32_t displayedColor = 0xFFFFFFFF;

void setBrightness(uint8_t brightness)
{
  currentBrightness = brightness;
  statusLed.setBrightness((currentBrightness * MAX_LED_BRIGHTNESS + 50) / 100);
  displayedColor = 0xFFFFFFFF;
}

// The button state takes precedence over a connected configurator.
void setStatusLed(uint8_t red, uint8_t green, uint8_t blue)
{
  uint32_t color = statusLed.Color(red, green, blue);

  if (color == displayedColor)
    return;

  statusLed.setPixelColor(0, color);
  statusLed.show();
  displayedColor = color;
}

void updateStatusLed()
{
  if (pressed)
  {
    setStatusLed(0, 0, 255);       // Blue: PTT button held
  }
  else if (Serial.dtr())
  {
    setStatusLed(255, 0, 0);       // Red: configurator serial port open
  }
  else
  {
    setStatusLed(0, 255, 0);       // Green: device running
  }
}

void startupLedTest()
{
  setStatusLed(255, 0, 0);
  delay(20);
  setStatusLed(0, 255, 0);
  delay(20);
  setStatusLed(0, 0, 255);
  delay(20);
  displayedColor = 0xFFFFFFFF;
}

//-------------------------------
// Key IDs
//-------------------------------
enum
{
  KEY_LEFT_CTRL_ID = 0,
  KEY_RIGHT_CTRL_ID,
  KEY_LEFT_SHIFT_ID,
  KEY_RIGHT_SHIFT_ID,
  KEY_LEFT_ALT_ID,
  KEY_RIGHT_ALT_ID,
  KEY_F13_ID,
  KEY_F14_ID,
  KEY_A_ID,
  KEY_B_ID
};

//-------------------------------

uint8_t keyTable[] =
{
  KEY_LEFT_CTRL,
  KEY_RIGHT_CTRL,
  KEY_LEFT_SHIFT,
  KEY_RIGHT_SHIFT,
  KEY_LEFT_ALT,
  KEY_RIGHT_ALT,
  KEY_F13,
  KEY_F14,
  'a',
  'b'
};

//--------------------------------

void saveConfig()
{
  EEPROM.write(0, 0x55);
  EEPROM.write(1, currentKey);
  EEPROM.write(2, currentBrightness);
  EEPROM.commit();
}

void loadConfig()
{
    EEPROM.begin(16);

    if (EEPROM.read(0) == 0x55)
    {
        currentKey = EEPROM.read(1);

        if (currentKey >= (sizeof(keyTable) / sizeof(keyTable[0])))
            currentKey = DEFAULT_KEY;

        currentBrightness = EEPROM.read(2);

        if (currentBrightness > 100)
            currentBrightness = DEFAULT_BRIGHTNESS;
    }
    else
    {
        currentKey = DEFAULT_KEY;
        currentBrightness = DEFAULT_BRIGHTNESS;
        saveConfig();
    }
}

void factoryReset()
{
    currentKey = DEFAULT_KEY;
    currentBrightness = DEFAULT_BRIGHTNESS;

    saveConfig();

    Serial.println("OK");
}

void sendCurrentKey()
{
    Serial.print("KEY:");
    Serial.println(currentKey);
}

void sendCurrentBrightness()
{
    Serial.print("BRIGHTNESS:");
    Serial.println(currentBrightness);
}

void sendInfo()
{
    Serial.println("READY");

    Serial.print("VERSION:");
    Serial.println(FW_VERSION);

    sendCurrentKey();
    sendCurrentBrightness();

    Serial.print("BTN:");
    Serial.println(!digitalRead(BUTTON) ? 1 : 0);
}

//--------------------------------

void handleCommand(String cmd)
{
  cmd.trim();

  if (cmd == "PING")
  {
    Serial.println("PONG");
    return;
  }

  if (cmd == "FACTORYRESET")
  {
      factoryReset();
      return;
  }

  if (cmd == "GETINFO")
  {
    sendInfo();
    return;
  }

  if (cmd == "GETKEY")
  {
    sendCurrentKey();
    return;
  }

  if (cmd == "GETBRIGHTNESS")
  {
    sendCurrentBrightness();
    return;
  }

  if (cmd == "SAVE")
  {
    saveConfig();
    Serial.println("OK");
    return;
  }

  if (cmd == "RESET")
  {
    Serial.println("OK");
    delay(100);
    watchdog_reboot(0, 0, 0);
    while (1);
  }

  if (cmd == "BOOTSEL")
  {
    Serial.println("OK");
    delay(100);
    reset_usb_boot(0,0);
  }

  const int NUM_KEYS = sizeof(keyTable) / sizeof(keyTable[0]);

  if (cmd.startsWith("SETKEY:"))
  {
      int keyID = cmd.substring(7).toInt();

      if (keyID >= 0 && keyID < NUM_KEYS)
      {
          currentKey = keyID;
          Serial.println("OK");
      }
      else
      {
          Serial.println("ERROR");
      }

      return;
  }

  if (cmd.startsWith("SETBRIGHTNESS:"))
  {
      int brightness = cmd.substring(14).toInt();

      if (brightness >= 0 && brightness <= 100)
      {
          setBrightness(brightness);
          Serial.println("OK");
      }
      else
      {
          Serial.println("ERROR");
      }

      return;
  }
}

//--------------------------------

void setup()
{
  pinMode(BUTTON, INPUT_PULLUP);

  statusLed.begin();
  statusLed.clear();
  statusLed.show();

  Serial.begin(115200);

  Keyboard.begin();

  loadConfig();
  setBrightness(currentBrightness);
  startupLedTest();

  delay(1000);

  Serial.println("READY");

  Serial.print("VERSION:");
  Serial.println(FW_VERSION);

  sendCurrentKey();
  sendCurrentBrightness();
  updateStatusLed();
}

//--------------------------------

void loop()
{
  bool state = !digitalRead(BUTTON);

  if(state != lastButton)
  {
    lastButton = state;

    Serial.print("BTN:");
    Serial.println(state ? "1" : "0");
  }

  if(state && !pressed)
  {
    Keyboard.press(keyTable[currentKey]);
    pressed = true;
  }

  if(!state && pressed)
  {
    Keyboard.release(keyTable[currentKey]);
    pressed = false;
  }

  while(Serial.available())
  {
    String cmd = Serial.readStringUntil('\n');
    handleCommand(cmd);
  }

  updateStatusLed();

  delay(5);
}
