# MotoNode Telemetry

Native Android BLE dashboard for an ESP32 motorcycle telemetry node using:

- ESP32
- GY-NEO6MV2 / u-blox NEO-6M GPS
- GY-521 / MPU-6050 IMU
- BLE notifications at 20 Hz

## Android app

Open this folder in Android Studio Quail 3 (2026.1.3) or newer and let Gradle sync. The project is configured for Gradle 9.5.0 / JDK 17. If the IDE asks which Gradle distribution to use because a wrapper is not bundled, select Gradle 9.5.0.

Project configuration:

- Package: `com.motonode.telemetry`
- compileSdk: 37
- targetSdk: 36
- minSdk: 26
- Android Gradle Plugin: 9.3.1
- Gradle: 9.5.0
- Kotlin / Compose compiler: 2.4.10
- Compose BOM: 2026.08.00

The app scans specifically for the MotoNode BLE service and subscribes automatically after connection.

### Dashboard fields

- GPS speed
- GPS fix / satellites / HDOP
- live lean angle
- pitch
- live lean trace
- forward acceleration / braking G
- lateral G
- peak left/right lean
- peak acceleration/braking
- GPS coordinates

## ESP32 firmware

Open:

`esp32/MotoNodeTelemetry_BLE.ino`

Install Arduino libraries:

- TinyGPSPlus
- Adafruit MPU6050
- Adafruit Unified Sensor

The ESP32 Arduino core supplies the BLE headers used by the sketch.

### Wiring

| Module | Pin | ESP32 |
|---|---|---|
| NEO-6M | TX | GPIO 16 |
| NEO-6M | RX | GPIO 17 |
| NEO-6M | GND | GND |
| GY-521 | SDA | GPIO 21 |
| GY-521 | SCL | GPIO 22 |
| GY-521 | GND | GND |

For the IMU math in this firmware, mount the sensor approximately with X forward, Y left and Z up. Startup calibration removes small static mounting offsets.

## BLE protocol

Device name: `MotoNode`

Service UUID:

`6f9a0001-9c21-4b6f-8d73-5c2a1256a001`

Telemetry characteristic UUID:

`6f9a0002-9c21-4b6f-8d73-5c2a1256a001`

Telemetry is a packed, little-endian, 56-byte frame at 20 Hz.

| Offset | Type | Field |
|---:|---|---|
| 0 | uint8 | protocol version |
| 1 | uint8 | flags; bit 0 = GPS fix |
| 2 | uint16 | sequence |
| 4 | uint32 | ESP32 uptime ms |
| 8 | float32 | speed mph |
| 12 | float32 | lean degrees |
| 16 | float32 | pitch degrees |
| 20 | float32 | acceleration G |
| 24 | float32 | lateral G |
| 28 | float32 | max left lean |
| 32 | float32 | max right lean |
| 36 | float32 | max acceleration G |
| 40 | float32 | max braking G |
| 44 | float32 | latitude |
| 48 | float32 | longitude |
| 52 | uint8 | satellites |
| 53 | uint8 | reserved |
| 54 | uint16 | HDOP × 100 |

## First run

1. Flash the ESP32 firmware.
2. Keep the bike/device stationary and upright during startup calibration.
3. Install/run the Android app.
4. Grant Nearby Devices permission.
5. Press CONNECT.
6. The app finds the BLE service, negotiates the MTU, subscribes, and begins displaying notifications.

## Notes

The NEO-6M GPS data rate is slower than the IMU. The ESP32 sends the latest GPS state inside every 20 Hz BLE frame while the IMU updates at 100 Hz.
