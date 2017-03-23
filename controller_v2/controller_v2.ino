#include <ArduinoJson.h>
#include <String.h>

#define redLed 10
#define greenLed 9
#define blueLed 6

const bool animateColor = false;
const unsigned int delayVal = 1;
const unsigned int baudRate = 9600;
const unsigned int fadeSpeed = (animateColor) ? 5 : 9;

unsigned int colorStep = 1;
unsigned int speedCounter = 0;

int ledColor[3] = {0, 255, 0};
int ledColorHSV[3] = {0, 255, 255};

void setLedState(int* color) {
    analogWrite(redLed, color[0]);
    analogWrite(greenLed, color[1]);
    analogWrite(blueLed, color[2]);
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
        int c_on[3] = {75, 0, 0};
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
    double mid_value = root["m"];

    colorStep = (int) (7.5 * mid_value) + 1;

    speedCounter++;

    if (speedCounter >= fadeSpeed) {

        if (ledColorHSV[0] >= 359) {
            ledColorHSV[0] = 0;
        } else {
            int hue = ledColorHSV[0] + colorStep;
            ledColorHSV[0] = (hue > 359) ? hue - (hue % 359) : hue;
        }

        getRGB(ledColorHSV[0], ledColorHSV[1], ledColorHSV[2], ledColor);
        int* scaledColor = getScaledColor(ledColor, low_value);
        setLedState(scaledColor);
        free(scaledColor);

        speedCounter = 0;
    }
}

void getRGB(int hue, int sat, int val, int* colors) {

    int r;
    int g;
    int b;
    int base;

    if (sat == 0) {
        colors[0]=val;
        colors[1]=val;
        colors[2]=val;
    } else {

        base = ((255 - sat) * val)>>8;

        switch(hue/60) {
            case 0:
            r = val;
            g = (((val-base)*hue)/60)+base;
            b = base;
            break;

            case 1:
            r = (((val-base)*(60-(hue%60)))/60)+base;
            g = val;
            b = base;
            break;

            case 2:
            r = base;
            g = val;
            b = (((val-base)*(hue%60))/60)+base;
            break;

            case 3:
            r = base;
            g = (((val-base)*(60-(hue%60)))/60)+base;
            b = val;
            break;

            case 4:
            r = (((val-base)*(hue%60))/60)+base;
            g = base;
            b = val;
            break;

            case 5:
            r = val;
            g = base;
            b = (((val-base)*(60-(hue%60)))/60)+base;
            break;
        }

        colors[0]=r;
        colors[1]=g;
        colors[2]=b;
    }
}
