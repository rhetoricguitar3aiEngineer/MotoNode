package com.motonode.telemetry

import java.nio.ByteBuffer
import java.nio.ByteOrder

data class TelemetryPacket(
    val version: Int = 1,
    val gpsFix: Boolean = false,
    val sequence: Int = 0,
    val uptimeMs: Long = 0,
    val speedMph: Float = 0f,
    val leanDeg: Float = 0f,
    val pitchDeg: Float = 0f,
    val accelG: Float = 0f,
    val lateralG: Float = 0f,
    val maxLeftLeanDeg: Float = 0f,
    val maxRightLeanDeg: Float = 0f,
    val maxAccelG: Float = 0f,
    val maxBrakeG: Float = 0f,
    val latitude: Float = 0f,
    val longitude: Float = 0f,
    val satellites: Int = 0,
    val hdop: Float = 99f,
) {
    companion object {
        const val PACKET_SIZE = 56

        fun decode(bytes: ByteArray): TelemetryPacket? {
            if (bytes.size < PACKET_SIZE) return null

            val b = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN)
            val version = b.get().toInt() and 0xFF
            val flags = b.get().toInt() and 0xFF
            val sequence = b.short.toInt() and 0xFFFF
            val uptimeMs = b.int.toLong() and 0xFFFFFFFFL

            return TelemetryPacket(
                version = version,
                gpsFix = flags and 0x01 != 0,
                sequence = sequence,
                uptimeMs = uptimeMs,
                speedMph = b.float,
                leanDeg = b.float,
                pitchDeg = b.float,
                accelG = b.float,
                lateralG = b.float,
                maxLeftLeanDeg = b.float,
                maxRightLeanDeg = b.float,
                maxAccelG = b.float,
                maxBrakeG = b.float,
                latitude = b.float,
                longitude = b.float,
                satellites = b.get().toInt() and 0xFF,
                hdop = run {
                    b.get() // reserved
                    (b.short.toInt() and 0xFFFF) / 100f
                }
            )
        }
    }
}
