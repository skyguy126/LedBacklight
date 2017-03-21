#include <ArduinoJson.h>
#include <String.h>

#define redLed 10
#define greenLed 9
#define blueLed 6

const int baudRate = 9600;
const int fadeSpeed = 1;
const int delayVal = 1;

int speedCounter = 0;
int ledColor[3] = {0, 255, 0};
int colorStep = 0;

void setLedState(int* color) {
    analogWrite(redLed, color[0]);
    analogWrite(greenLed, color[1]);
    analogWrite(blueLed, color[2]);
}

void stepColor(int* color) {
    if (color[0] >= 255) {
        colorStep = 0;
    } else if (color[1] >= 255) {
        colorStep = 1;
    } else if (color[2] >= 255) {
        colorStep = 2;
    }

    if (colorStep == 0) {
        color[0]--;
        color[1]++;
    } else if (colorStep == 1) {
        color[1]--;
        color[2]++;
    } else if (colorStep == 2) {
        color[2]--;
        color[0]++;
    }
}

int* getScaledColor(int* color, double percent) {
    int* scale = (int*) malloc(3 * sizeof(int));

    scale[0] = (int) (color[0] * percent);
    scale[1] = (int) (color[1] * percent);
    scale[2] = (int) (color[2] * percent);

    return scale;
}

void flashError() {
    for (int i = 0; i < 4; i++) {
        int c_on[3] = {50, 0, 0};
        setLedState(c_on);
        delay(200);

        int c_off[3] = {0, 0, 0};
        setLedState(c_off);
        delay(200);
    }

    delay(500);
}

void setup() {
    Serial.begin(baudRate);
    TXLED0;

    pinMode(redLed, OUTPUT);
    pinMode(greenLed, OUTPUT);
    pinMode(blueLed, OUTPUT);

    setLedState(ledColor);
}

void loop() {

    if (Serial.available() < 1)
        return;

    String data_str = Serial.readStringUntil('\n');
    StaticJsonBuffer<128> jsonBuffer;
    JsonObject& root = jsonBuffer.parseObject(data_str);

    if (!root.success()) {
        flashError();
        return;
    }

    double low_value = root["l"];
    speedCounter++;

    if (speedCounter >= fadeSpeed) {
        stepColor(ledColor);
        int* scaledColor = getScaledColor(ledColor, low_value);
        setLedState(scaledColor);
        free(scaledColor);
        speedCounter = 0;
    }
}
