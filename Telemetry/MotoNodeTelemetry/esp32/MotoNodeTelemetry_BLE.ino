#include <Wire.h>
#include <TinyGPSPlus.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// ============================================================
// MOTONODE ESP32 TELEMETRY
// NEO-6M GPS + GY-521 MPU6050 + BLE
// ============================================================

#define GPS_RX_PIN 16
#define GPS_TX_PIN 17
#define SDA_PIN 21
#define SCL_PIN 22
#define GPS_BAUD 9600

#define DEVICE_NAME "MotoNode"
#define SERVICE_UUID "6f9a0001-9c21-4b6f-8d73-5c2a1256a001"
#define TELEMETRY_UUID "6f9a0002-9c21-4b6f-8d73-5c2a1256a001"

const float GRAVITY = 9.80665f;
const float RAD_TO_DEG_F = 180.0f / PI;
const float DEG_TO_RAD_F = PI / 180.0f;

const uint32_t IMU_PERIOD_US = 10000;       // 100 Hz
const uint32_t BLE_PERIOD_MS = 50;          // 20 Hz
const float MIN_DYNAMIC_SPEED_MS = 3.0f;
const float DYNAMIC_LEAN_BLEND = 0.65f;

TinyGPSPlus gps;
HardwareSerial GPSSerial(2);
Adafruit_MPU6050 mpu;

BLEServer *bleServer = nullptr;
BLECharacteristic *telemetryCharacteristic = nullptr;
bool bleConnected = false;

// ---------------- QUATERNION ----------------
float q0 = 1.0f;
float q1 = 0.0f;
float q2 = 0.0f;
float q3 = 0.0f;

float integralX = 0;
float integralY = 0;
float integralZ = 0;
float Kp = 2.0f;
float Ki = 0.005f;

// ---------------- CALIBRATION ----------------
float gyroBiasX = 0;
float gyroBiasY = 0;
float gyroBiasZ = 0;
float rollZero = 0;
float pitchZero = 0;

// ---------------- SENSOR STATE ----------------
float ax = 0, ay = 0, az = 0;
float gx = 0, gy = 0, gz = 0;
float roll = 0, pitch = 0, yaw = 0;
float correctedRoll = 0, correctedPitch = 0;

// ---------------- GPS ----------------
double latitude = 0;
double longitude = 0;
float speedMPS = 0;
float speedMPH = 0;
uint32_t satellites = 0;
float hdop = 99;

// ---------------- RIDE TELEMETRY ----------------
float forwardG = 0;
float lateralG = 0;
float estimatedLean = 0;
float coordinatedLean = 0;
float filteredForwardG = 0;
float filteredLateralG = 0;
float filteredLean = 0;
float maxLeftLean = 0;
float maxRightLean = 0;
float maxAccelerationG = 0;
float maxBrakingG = 0;

uint32_t previousIMUTime = 0;
uint32_t lastBLETime = 0;
uint16_t packetSequence = 0;

#pragma pack(push, 1)
struct TelemetryPacket {
  uint8_t version;
  uint8_t flags;          // bit0 = GPS fix
  uint16_t sequence;
  uint32_t uptimeMs;

  float speedMph;
  float leanDeg;
  float pitchDeg;
  float accelG;
  float lateralG;
  float maxLeftLeanDeg;
  float maxRightLeanDeg;
  float maxAccelG;
  float maxBrakeG;
  float latitude;
  float longitude;

  uint8_t satellites;
  uint8_t reserved;
  uint16_t hdopX100;
};
#pragma pack(pop)

static_assert(sizeof(TelemetryPacket) == 56, "Telemetry packet size must remain 56 bytes");

class ServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer *server) override {
    bleConnected = true;
    Serial.println("BLE client connected");
  }

  void onDisconnect(BLEServer *server) override {
    bleConnected = false;
    Serial.println("BLE client disconnected");
    BLEDevice::startAdvertising();
  }
};

float constrainAngle(float angle) {
  while (angle > 180.0f) angle -= 360.0f;
  while (angle < -180.0f) angle += 360.0f;
  return angle;
}

void updateMahony(float gxIn, float gyIn, float gzIn,
                  float axIn, float ayIn, float azIn,
                  float dt) {
  float norm = sqrtf(axIn * axIn + ayIn * ayIn + azIn * azIn);

  if (norm > 0.001f) {
    axIn /= norm;
    ayIn /= norm;
    azIn /= norm;

    float halfvx = q1 * q3 - q0 * q2;
    float halfvy = q0 * q1 + q2 * q3;
    float halfvz = q0 * q0 - 0.5f + q3 * q3;

    float halfex = ayIn * halfvz - azIn * halfvy;
    float halfey = azIn * halfvx - axIn * halfvz;
    float halfez = axIn * halfvy - ayIn * halfvx;

    integralX += Ki * halfex * dt;
    integralY += Ki * halfey * dt;
    integralZ += Ki * halfez * dt;

    gxIn += integralX + Kp * halfex;
    gyIn += integralY + Kp * halfey;
    gzIn += integralZ + Kp * halfez;
  }

  float qa = q0;
  float qb = q1;
  float qc = q2;

  gxIn *= 0.5f * dt;
  gyIn *= 0.5f * dt;
  gzIn *= 0.5f * dt;

  q0 += (-qb * gxIn - qc * gyIn - q3 * gzIn);
  q1 += (qa * gxIn + qc * gzIn - q3 * gyIn);
  q2 += (qa * gyIn - qb * gzIn + q3 * gxIn);
  q3 += (qa * gzIn + qb * gyIn - qc * gxIn);

  norm = sqrtf(q0*q0 + q1*q1 + q2*q2 + q3*q3);
  if (norm > 0.001f) {
    q0 /= norm;
    q1 /= norm;
    q2 /= norm;
    q3 /= norm;
  }
}

void calculateEuler() {
  float sinr = 2.0f * (q0 * q1 + q2 * q3);
  float cosr = 1.0f - 2.0f * (q1 * q1 + q2 * q2);
  roll = atan2f(sinr, cosr) * RAD_TO_DEG_F;

  float sinp = 2.0f * (q0 * q2 - q3 * q1);
  pitch = fabsf(sinp) >= 1.0f
    ? copysignf(90.0f, sinp)
    : asinf(sinp) * RAD_TO_DEG_F;

  float siny = 2.0f * (q0 * q3 + q1 * q2);
  float cosy = 1.0f - 2.0f * (q2 * q2 + q3 * q3);
  yaw = atan2f(siny, cosy) * RAD_TO_DEG_F;

  correctedRoll = constrainAngle(roll - rollZero);
  correctedPitch = constrainAngle(pitch - pitchZero);
}

void calibrateGyroscope() {
  Serial.println("Keep MotoNode stationary: calibrating gyro...");

  const int samples = 1200;
  double sx = 0, sy = 0, sz = 0;
  sensors_event_t a, g, temp;

  for (int i = 0; i < samples; i++) {
    mpu.getEvent(&a, &g, &temp);
    sx += g.gyro.x;
    sy += g.gyro.y;
    sz += g.gyro.z;
    delay(2);
  }

  gyroBiasX = sx / samples;
  gyroBiasY = sy / samples;
  gyroBiasZ = sz / samples;

  Serial.println("Gyro calibrated");
}

void calibrateMountingAngle() {
  Serial.println("Keep bike upright and stationary: calibrating mounting angle...");

  float sumRoll = 0;
  float sumPitch = 0;
  const int samples = 300;
  const int settleSamples = 100;
  int accepted = 0;

  previousIMUTime = micros();

  for (int i = 0; i < samples;) {
    uint32_t now = micros();
    if (now - previousIMUTime < IMU_PERIOD_US) continue;

    float dt = (now - previousIMUTime) / 1000000.0f;
    previousIMUTime = now;

    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);

    updateMahony(
      g.gyro.x - gyroBiasX,
      g.gyro.y - gyroBiasY,
      g.gyro.z - gyroBiasZ,
      a.acceleration.x,
      a.acceleration.y,
      a.acceleration.z,
      dt
    );

    calculateEuler();

    if (i >= settleSamples) {
      sumRoll += roll;
      sumPitch += pitch;
      accepted++;
    }
    i++;
  }

  rollZero = sumRoll / accepted;
  pitchZero = sumPitch / accepted;

  Serial.printf("Mount offsets: roll %.2f, pitch %.2f\n", rollZero, pitchZero);
}

void updateGPS() {
  while (GPSSerial.available()) {
    gps.encode(GPSSerial.read());
  }

  if (gps.location.isValid()) {
    latitude = gps.location.lat();
    longitude = gps.location.lng();
  }
  if (gps.speed.isValid()) {
    speedMPS = gps.speed.mps();
    speedMPH = gps.speed.mph();
  }
  if (gps.satellites.isValid()) satellites = gps.satellites.value();
  if (gps.hdop.isValid()) hdop = gps.hdop.hdop();
}

void updateIMU() {
  uint32_t now = micros();
  if (now - previousIMUTime < IMU_PERIOD_US) return;

  float dt = (now - previousIMUTime) / 1000000.0f;
  previousIMUTime = now;
  if (dt <= 0.0f || dt > 0.1f) dt = 0.01f;

  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  ax = a.acceleration.x;
  ay = a.acceleration.y;
  az = a.acceleration.z;

  gx = g.gyro.x - gyroBiasX;
  gy = g.gyro.y - gyroBiasY;
  gz = g.gyro.z - gyroBiasZ;

  updateMahony(gx, gy, gz, ax, ay, az, dt);
  calculateEuler();

  // X = bike forward, Y = left, Z = up
  const float accelAlpha = 0.10f;
  filteredForwardG += accelAlpha * ((ax / GRAVITY) - filteredForwardG);
  filteredLateralG += accelAlpha * ((ay / GRAVITY) - filteredLateralG);

  float rollRad = correctedRoll * DEG_TO_RAD_F;
  float pitchRad = correctedPitch * DEG_TO_RAD_F;

  float gravityX = -sinf(pitchRad);
  float gravityY = sinf(rollRad) * cosf(pitchRad);

  forwardG = filteredForwardG - gravityX;
  lateralG = filteredLateralG - gravityY;

  float calculatedLatAccel = speedMPS * gz;

  if (speedMPS > MIN_DYNAMIC_SPEED_MS) {
    coordinatedLean = atan2f(calculatedLatAccel, GRAVITY) * RAD_TO_DEG_F;
  } else {
    coordinatedLean = correctedRoll;
  }

  float leanTarget = correctedRoll;
  if (speedMPS > MIN_DYNAMIC_SPEED_MS) {
    leanTarget = correctedRoll * (1.0f - DYNAMIC_LEAN_BLEND)
               + coordinatedLean * DYNAMIC_LEAN_BLEND;
  }

  filteredLean += 0.15f * (leanTarget - filteredLean);
  estimatedLean = filteredLean;

  if (estimatedLean > maxLeftLean) maxLeftLean = estimatedLean;
  if (estimatedLean < maxRightLean) maxRightLean = estimatedLean;
  if (forwardG > maxAccelerationG) maxAccelerationG = forwardG;
  if (forwardG < maxBrakingG) maxBrakingG = forwardG;
}

void setupBLE() {
  BLEDevice::init(DEVICE_NAME);
  BLEDevice::setMTU(128);

  bleServer = BLEDevice::createServer();
  bleServer->setCallbacks(new ServerCallbacks());

  BLEService *service = bleServer->createService(SERVICE_UUID);

  telemetryCharacteristic = service->createCharacteristic(
    TELEMETRY_UUID,
    BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
  );

  telemetryCharacteristic->addDescriptor(new BLE2902());
  service->start();

  BLEAdvertising *advertising = BLEDevice::getAdvertising();
  advertising->addServiceUUID(SERVICE_UUID);
  advertising->setScanResponse(true);
  BLEDevice::startAdvertising();

  Serial.println("BLE advertising as MotoNode");
}

void sendBLETelemetry() {
  if (!bleConnected) return;
  if (millis() - lastBLETime < BLE_PERIOD_MS) return;
  lastBLETime = millis();

  TelemetryPacket packet = {};
  packet.version = 1;

  bool gpsFix = gps.location.isValid() && gps.location.age() < 2500;
  packet.flags = gpsFix ? 0x01 : 0x00;
  packet.sequence = packetSequence++;
  packet.uptimeMs = millis();

  packet.speedMph = speedMPH;
  packet.leanDeg = estimatedLean;
  packet.pitchDeg = correctedPitch;
  packet.accelG = forwardG;
  packet.lateralG = lateralG;
  packet.maxLeftLeanDeg = maxLeftLean;
  packet.maxRightLeanDeg = maxRightLean;
  packet.maxAccelG = maxAccelerationG;
  packet.maxBrakeG = maxBrakingG;
  packet.latitude = (float)latitude;
  packet.longitude = (float)longitude;
  packet.satellites = (uint8_t)min((uint32_t)255, satellites);
  packet.reserved = 0;
  packet.hdopX100 = (uint16_t)constrain((int)(hdop * 100.0f), 0, 65535);

  telemetryCharacteristic->setValue((uint8_t *)&packet, sizeof(packet));
  telemetryCharacteristic->notify();
}

void setup() {
  Serial.begin(115200);
  delay(700);

  Serial.println("MotoNode Telemetry starting...");

  GPSSerial.begin(GPS_BAUD, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(400000);

  if (!mpu.begin()) {
    Serial.println("ERROR: MPU6050 not found");
    while (true) delay(1000);
  }

  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);

  calibrateGyroscope();
  calibrateMountingAngle();
  previousIMUTime = micros();

  setupBLE();

  Serial.println("MotoNode ready");
}

void loop() {
  updateGPS();
  updateIMU();
  sendBLETelemetry();
}
