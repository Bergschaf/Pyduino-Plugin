//
// Created by Christian on 26.09.2022.
//
#include <iostream>
#include "Serial.cpp"


using namespace std;
#include <chrono>
#include <thread>
using namespace std::chrono;
using namespace std::this_thread;


const int StartCharacter = 60; // <
const int EndCharacter = 62; // >
const int SpaceCharacter = 124; // |
const int MaxDataLength = 100;
const int MaxRequests = 50;
const int MaxMillisecondsToWaitForData = 500;



template<typename T>
class Promise {
public:
    typedef T(bytesToType)(char* bytes);
    thread *t;
    static void resolve(int requestID, bytesToType bytesToType, T* targetVariable, char Responses[MaxRequests][MaxDataLength]) {
        int millisecondsWaited = 0;
        while (Responses[requestID][0] == 0) {
            sleep_for(milliseconds(1));
            millisecondsWaited++;
            if (millisecondsWaited > MaxMillisecondsToWaitForData) {
                cout << "Error: Timeout while waiting for response" << endl;
                return;
            }
        }
        if(targetVariable == nullptr || bytesToType == nullptr) {
            Responses[requestID][0] = 0;
            return;
        }
        *targetVariable = bytesToType(Responses[requestID]);
        Responses[requestID][0] = 0;
    }

    Promise(T* targetVariable,bytesToType bytesToType, int requestID, char Responses[MaxRequests][MaxDataLength]) {
        // start a thread with the resolving function
        t = new thread(resolve, requestID, bytesToType, targetVariable, Responses);
    }

    // Destructor
    ~Promise() {
        // join the thread
        t->join();
    }
};


// Invoke:
class Arduino {

    bool Handshake() const {
        char outgoingData[2] = "*";
        char incomingData[2] = "";
        int readResult = 0;
        while (true) {
            SP->WriteData(outgoingData, 2);
            sleep_for(milliseconds(2));
            readResult = SP->ReadData(incomingData, 2);
            if (readResult > 0) {
                if (incomingData[0] == '*') {
                    outgoingData[0] = 'T';
                    SP->WriteData(outgoingData, 1);
                    readResult = SP->ReadData(incomingData, 1);
                    while (readResult > 0) {
                        readResult = SP->ReadData(incomingData, 1);
                    }
                    return true;
                }
            }

        }
    }

    char getNextRequestId() {
        for (uint8_t i = 0; i < MaxRequests; i++) {
            if (Requests[i] == 0) {
                return (char) i;
            }
        }
        return -1;
    }

// TODO implement asynchronous waiting for data
    char sendRequest(char instruction, const char *value, int valueSize) {
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
        SP->WriteData(outgoingData, 8 + valueSize);
        return requestId;
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

        outgoingData[6 + responseSize] = EndCharacter;

        SP->WriteData(outgoingData, 6 + responseSize);
    }

    void decodeResponse(const char *data, int size) {
        char requestID = data[1];
        char instruction = Requests[requestID];
        int responseSize = int(uint8_t(data[3]));

        if (responseSize > MaxDataLength) {
            cout << "Warning: response size is bigger than MaxDataLength" << endl;
            responseSize = MaxDataLength;
        } else if (responseSize == 0) {
            Requests[requestID] = 0;
            cout << "Warning: response size is 0" << endl;
            return;
        }
        if (data[2] != SpaceCharacter || data[4] != SpaceCharacter) {
            Requests[requestID] = 0;
            cout << "Error: Invalid response format" << endl;
            return;
        }
        for (int i = 0; i < responseSize; i++) {
            Responses[requestID][i+ 1] = data[5 + i];

        }
        Responses[requestID][0] = 1;

    }

    void decodeRequest(const char *data, int size) {
        char requestID = data[1];
        int valueSize = int(uint8_t(data[3]));
        char instruction = data[5];
        if (valueSize > MaxDataLength) {
            cout << "Warning: value size is bigger than MaxDataLength" << endl;
            valueSize = MaxDataLength;
        } else if (valueSize == 0) {
            cout << "Warning: value size is 0" << endl;
            return;
        }
        if (data[2] != SpaceCharacter || data[4] != SpaceCharacter) {
            cout << "Error: Invalid request format" << endl;
            return;
        }
        char value[valueSize];
        for (int i = 0; i < valueSize; i++) {
            value[i] = data[7 + i];
        }
        if(instruction == 'l'){
            cout << "[Arduino:] " <<  value;
        }

    }

    void decodeSerial(const char *data, int size) {
        int requestID = int(uint8_t (data[1]));
        if (int(requestID) <= MaxRequests) {
            decodeResponse(data, size);
        } else if (int(requestID <= MaxRequests * 2)) {
            decodeRequest(data, size);
        } else {
            cout << "Error: Invalid Request ID";
        }
    }

     // TODO VERY IMPORTANT KEEP 1 BYYTE OFFSET WHEN READING DATA, BECAUSE THE FIRST BYTE IS ALWAYS 1 as an indicator that the message is ready
    static short bytesToShort(char *bytes) {
        return (short) ((uint8_t(bytes[2]) << 8) | uint8_t(bytes[1]));
    }


    static int bytesToTypeInt(const char* bytes) {
        int v1 = int(uint8_t(bytes[0]));
        int v2 = int(uint8_t(bytes[1]));
        int v3 = int(uint8_t(bytes[2]));
        int v4 = int(uint8_t(bytes[3]));
        int x[2];
        return (v1 * 256 * 256 * 256) + (v2 * 256 * 256) + (v3 * 256) + v4;
    }
    [[noreturn]]static void listener(Arduino *arduino, Serial *SP) {
        char incomingData[MaxDataLength];
        int readResult = 0;
        char dataBuffer[2];
        while(true){
            readResult = SP->ReadData(dataBuffer, 1);
            if (readResult > 0) {
                if (dataBuffer[0] == StartCharacter) {
                    int i = 1;
                    incomingData[0] = dataBuffer[0];
                    while (true) {
                        readResult = SP->ReadData(dataBuffer, 1);
                        if (readResult > 0) {
                            incomingData[i] = dataBuffer[0];
                            if (dataBuffer[0] == EndCharacter) {
                                arduino->decodeSerial(incomingData, i);
                                break;
                            }
                            i++;
                        }
                    }
                }
            }

        }
    }


public:

    char Requests[MaxRequests]{};
    char Responses[MaxRequests][MaxDataLength]{};
    Serial *SP;
    thread *listenerThread{};
    explicit Arduino(){
        this->SP = new Serial(R"(\\.\COM5)");
        if (!SP->IsConnected()) {
                cout << "Connection Error" << endl;
        }
        cout << "Connection Established" << endl;
        if (!Handshake()) {
            cout << "Handshake Failed" << endl;
            return;
        }
        else{
            cout << "Connected to board" << endl;
        }
        listenerThread = new thread(listener, this, SP);
    }

    void analogRead(char pin, short *targetVariable) {
        char value[1] = {pin};
        char requestID = sendRequest('a', value, 1);
        delete new Promise<short>(targetVariable, bytesToShort, requestID, Responses);
        // TODO wichtig
        Requests[requestID] = 0;
    }

    void analogWrite(char pin, char value) {
        // waits for response
        char valueBytes[2] = {pin, value};
        char requestID = sendRequest('b', valueBytes, 2);
        delete new Promise<short>(nullptr, nullptr, requestID, Responses);
        Requests[requestID] = 0;

    }

    void digitalWrite(char pin, char value) {
        char data[2] = {pin, value};
        sendRequest('d', data, 2);
    }




};