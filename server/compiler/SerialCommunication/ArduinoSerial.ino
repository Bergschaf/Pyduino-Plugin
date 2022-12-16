
using namespace std;

const int StartCharacter = 60;   // <
const int EndCharacter = 62;     // >
const int SpaceCharacter = 124;  // |
const int MaxDataLength = 100;
const int MaxRequests = 100;
const int MaxMillisecondsToWaitForData = 2000;
const byte analogPorts[6] = {A0, A1, A2, A3, A4, A5};
char Requests[MaxRequests];
char Responses[MaxRequests][MaxDataLength];


bool Handshake() {
    analogWrite(10,255);
    while (true) {
        delay(1);
        if (Serial.available() > 0) {
            char incomingData = Serial.read();
            analogWrite(10,100);
            if (incomingData == '*') {
                Serial.write('*');
                while (true) {
                    Serial.write('*');
                    delay(1);
                    if (Serial.available() > 0) {
                        analogWrite(10,0);

                        incomingData = Serial.read();
                        if (incomingData == 'T') {
                            return true;
                        } else {
                            return false;
                        }
                    }
                }
            }
        }
    }
}

void checkSerial(){
    if (Serial.available()) {
        byte data = Serial.read();
        int incomingDataSize = 0;
        byte incomingData[MaxDataLength];
        if (data == StartCharacter) {
            incomingDataSize = 1;
            incomingData[0] = data;
            while (incomingDataSize < MaxDataLength) {
                if (Serial.available()) {
                    data = Serial.read();

                    if (data == EndCharacter) {
                        incomingData[incomingDataSize] = data;
                        decodeSerial(incomingData, incomingDataSize);
                        incomingDataSize = 0;
                        break;
                    } else {
                        incomingData[incomingDataSize] = data;
                        incomingDataSize++;
                    }
                }
            }
        }
    }
}

char getNextRequestId() {
    for (uint8_t i = 51; i < MaxRequests; i++) {
        if (Requests[i] == 0) {
            return (byte) i;
        }
    }}
}

// TODO implement asynchronous waiting for data
void sendRequest(char instruction, const char *value, int valueSize) {
    char outgoingData[8 + valueSize];
    outgoingData[0] = StartCharacter;

    char requestId = getNextRequestId();
    outgoingData[1] = requestId;
    Requests[requestId] = instruction;

    outgoingData[2] = SpaceCharacter;

    outgoingData[3] = (char) valueSize;

    outgoingData[4] = SpaceCharacter;

    outgoingData[5] = instruction;

    outgoingData[6] = SpaceCharacter;

    for (int i = 0; i < valueSize; i++) {
        outgoingData[7 + i] = value[i];
    }

    outgoingData[7 + valueSize] = EndCharacter;

    Serial.write(outgoingData, 8 + valueSize);
}

void sendResponse(char requestID, const char *response, int responseSize) {
    char outgoingData[6 + responseSize];
    outgoingData[0] = StartCharacter;

    outgoingData[1] = requestID;

    outgoingData[2] = SpaceCharacter;

    outgoingData[3] = (char) responseSize;

    outgoingData[4] = SpaceCharacter;

    for (int i = 0; i < responseSize; i++) {
        outgoingData[5 + i] = response[i];
    }

    outgoingData[5 + responseSize] = EndCharacter;

    Serial.write(outgoingData, 6 + responseSize);
}

void decodeResponse(const byte *data, int size) {
    char requestID = data[1];
    char instruction = Requests[requestID];
    int responseSize = int(uint8_t(data[3]));
    if (responseSize > MaxDataLength) {
        //cout << "Warning: response size is bigger than MaxDataLength" << endl;
        responseSize = MaxDataLength;
    } else if (responseSize == 0) {
        Requests[requestID] = 0;
        //cout << "Warning: response size is 0" << endl;
        return;
    }
    if (data[3] != SpaceCharacter || data[5] != SpaceCharacter) {
        Requests[requestID] = 0;
        //cout << "Error: Invalid response format" << endl;
        return;
    }
    for (int i = 0; i < responseSize; i++) {
        Responses[requestID][i] = data[5 + i];
    }
}

void decodeRequest(const byte *data, int size) {
    char requestID = data[1];
    char instruction = data[5];
    int valueSize = int(uint8_t(data[3]));

    if (valueSize > MaxDataLength) {
        Serial.write("E1");
        //cout << "Warning: value size is bigger than MaxDataLength" << endl;
        valueSize = MaxDataLength;
    } else if (valueSize == 0) {
        Requests[requestID] = 0;
        Serial.write("E2");

        //cout << "Warning: value size is 0" << endl;
        return;
    }
    if (data[2] != SpaceCharacter || data[4] != SpaceCharacter || data[6] != SpaceCharacter) {
        Requests[requestID] = 0;
        Serial.write("E3");

        //cout << "Error: Invalid request format" << endl;
        return;
    }
    char value[valueSize];
    for (int i = 0; i < valueSize; i++) {
        value[i] = data[7 + i];
    }
    if (instruction == 'a') {
        if (valueSize == 1) {
            short read = analogRead(analogPorts[value[0]]);
            const char response[2] = {(char) (read & 0xFF), (char) ((read >> 8) & 0xFF)};
            sendResponse(requestID, response, 2);
        }
    } else if (instruction == 'b') {
        if (valueSize == 2) {
            analogWrite(value[0], int(uint8_t(value[1])));
            sendResponse(requestID, new char[1]{' '}, 1);
        }
    } else if (instruction == 'c') {
        if (valueSize == 1) {
            digitalWrite(int(value[0]), 1);
        } else if (valueSize == 2) {
            digitalWrite(int(value[0]), value[1]);
        } else {
            Serial.write("E4");
        }
    }


}

void decodeSerial(const byte *data, int size) {
    char requestID = data[1];
    if (int(requestID) <= MaxRequests) {
        decodeRequest(data, size);
    } else if (int(requestID <= MaxRequests * 2)) {
        decodeResponse(data, size);
    } else {
        //cout << "Error: Invalid Request ID";
    }
}

void do_print(const String data[], int size, bool newline) {
    int len = 0;
    for (int i = 0; i < size; ++i) {
        len += data[i].length() + 1;
    }
    if (newline) {
        len++;
    }
    char data_char[len];
    int index = 0;
    for (int i = 0; i < size; ++i) {
        for (int j = 0; j < data[i].length(); ++j) {
            data_char[index] = data[i][j];
            index++;
        }
        data_char[index] = ' ';
        index++;
    }
    if (newline) {
        data_char[index] = '\n';}
    sendRequest('l', data_char, len);
}

void innit_serial() {
    Serial.begin(256000);
    byte incomingData[MaxDataLength] = "";
    int incomingDataSize = 0;
    Handshake();
    checkSerial();

}
