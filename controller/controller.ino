#include <ArduinoJson.h>
#include <String.h>

#define redLed 9
#define greenLed 10
#define blueLed 6
#define baudRate 9600
#define fadeSpeed 1

int ledColor[3] = {255, 0, 0};
int speedCounter = 0;
int colorStep = 0;
int mode = 0;

void setLedState(int* color) {
    analogWrite(redLed, color[0]);
    analogWrite(greenLed, color[1]);
    analogWrite(blueLed, color[2]);
}

void smoothShiftColor(int* color) {
    int rDif = color[0] - ledColor[0];
    int gDif = color[1] - ledColor[1];
    int bDif = color[2] - ledColor[2];

    int steps = 500;

    double rMult = (double) rDif / steps;
    double gMult = (double) gDif / steps;
    double bMult = (double) bDif / steps;

    double shift[3] = {(double) ledColor[0], (double) ledColor[1], (double) ledColor[2]};

    for (int i = 0; i < steps; i++) {

        shift[0] += rMult;
        shift[1] += gMult;
        shift[2] += bMult;

        ledColor[0] = (int) shift[0];
        ledColor[1] = (int) shift[1];
        ledColor[2] = (int) shift[2];

        setLedState(ledColor);
        delay(1);
    }

    shift[0] = (int) (shift[0] + 0.5);
    shift[1] = (int) (shift[1] + 0.5);
    shift[2] = (int) (shift[2] + 0.5);

    ledColor[0] = (int) shift[0];
    ledColor[1] = (int) shift[1];
    ledColor[2] = (int) shift[2];

    setLedState(ledColor);
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

void audioReact(double low_value) {
    speedCounter++;

    if (speedCounter >= fadeSpeed) {
        stepColor(ledColor);
        int* scaledColor = getScaledColor(ledColor, low_value);
        setLedState(scaledColor);
        free(scaledColor);
        speedCounter = 0;
    }
}

void flashError(int* color) {
    for (int i = 0; i < 4; i++) {
        setLedState(color);
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
    StaticJsonBuffer<256> jsonBuffer;
    JsonObject& root = jsonBuffer.parseObject(data_str);

    if (!root.success()) {
        int c_err[3] = {50, 0, 0};
        flashError(c_err);
        return;
    }

    if (root["cmd"]) {
        mode = root["mode"];
        int c_mode[3] = {0, 50, 0};
        flashError(c_mode);
        return;
    }

    if (mode == 1) {
        audioReact(root["low"]);
    } else if (mode == 2) {
        int color[3];
        color[0] = root["r"];
        color[1] = root["g"];
        color[2] = root["b"];

        setLedState(ledColor);
        smoothShiftColor(color);
    }
}
