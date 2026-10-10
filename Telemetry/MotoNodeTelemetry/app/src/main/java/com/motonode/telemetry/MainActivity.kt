package com.motonode.telemetry

import android.Manifest
import android.bluetooth.BluetoothAdapter
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.roundToInt
import kotlin.math.sin

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val permissionLauncher = registerForActivityResult(
            ActivityResultContracts.RequestMultiplePermissions()
        ) { }

        val enableBluetoothLauncher = registerForActivityResult(
            ActivityResultContracts.StartActivityForResult()
        ) { }

        setContent {
            val context = LocalContext.current
            val ble = remember { BleManager(context.applicationContext) }

            MotoNodeTheme {
                MotoNodeDashboard(
                    ble = ble,
                    requestPermissions = {
                        permissionLauncher.launch(requiredPermissions())
                    },
                    requestBluetoothEnable = {
                        enableBluetoothLauncher.launch(Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE))
                    }
                )
            }
        }
    }

    private fun requiredPermissions(): Array<String> {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            arrayOf(
                Manifest.permission.BLUETOOTH_SCAN,
                Manifest.permission.BLUETOOTH_CONNECT
            )
        } else {
            arrayOf(Manifest.permission.ACCESS_FINE_LOCATION)
        }
    }
}

private val MotoBackground = Color(0xFF090B10)
private val MotoSurface = Color(0xFF121620)
private val MotoSurface2 = Color(0xFF181E2A)
private val MotoRed = Color(0xFFFF3B30)
private val MotoCyan = Color(0xFF3DE1FF)
private val MotoGreen = Color(0xFF5EF2A0)
private val MotoText = Color(0xFFF4F7FB)
private val MotoMuted = Color(0xFF8D97A8)

@Composable
private fun MotoNodeTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = darkColorScheme(
            primary = MotoRed,
            secondary = MotoCyan,
            background = MotoBackground,
            surface = MotoSurface,
            onPrimary = Color.White,
            onBackground = MotoText,
            onSurface = MotoText
        ),
        content = content
    )
}

@Composable
private fun MotoNodeDashboard(
    ble: BleManager,
    requestPermissions: () -> Unit,
    requestBluetoothEnable: () -> Unit
) {
    val context = LocalContext.current
    val state by ble.state.collectAsStateWithLifecycle()
    val status by ble.status.collectAsStateWithLifecycle()
    val packet by ble.telemetry.collectAsStateWithLifecycle()
    val deviceName by ble.deviceName.collectAsStateWithLifecycle()
    val leanHistory = remember { mutableStateListOf<Float>() }

    LaunchedEffect(packet.sequence) {
        leanHistory.add(packet.leanDeg)
        if (leanHistory.size > 180) leanHistory.removeAt(0)
    }

    fun hasPermissions(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            ContextCompat.checkSelfPermission(context, Manifest.permission.BLUETOOTH_SCAN) == PackageManager.PERMISSION_GRANTED &&
                ContextCompat.checkSelfPermission(context, Manifest.permission.BLUETOOTH_CONNECT) == PackageManager.PERMISSION_GRANTED
        } else {
            ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
        }
    }

    LaunchedEffect(Unit) {
        if (!hasPermissions()) requestPermissions()
    }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(MotoBackground)
            .padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            Spacer(Modifier.height(10.dp))
            Header(state = state, deviceName = deviceName)
        }

        item {
            ConnectionCard(
                state = state,
                status = status,
                onConnect = {
                    when {
                        !hasPermissions() -> requestPermissions()
                        ble.adapter?.isEnabled != true -> requestBluetoothEnable()
                        else -> ble.startScan()
                    }
                },
                onDisconnect = { ble.disconnect() }
            )
        }

        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                SpeedCard(packet.speedMph, Modifier.weight(1f))
                GpsCard(packet, Modifier.weight(1f))
            }
        }

        item {
            LeanCard(packet.leanDeg, packet.pitchDeg)
        }

        item {
            LeanTrace(leanHistory)
        }

        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                MetricCard("ACCEL", packet.accelG, "G", MotoGreen, Modifier.weight(1f))
                MetricCard("LATERAL", packet.lateralG, "G", MotoCyan, Modifier.weight(1f))
            }
        }

        item {
            PeakCard(packet)
        }

        item {
            PositionCard(packet)
        }

        item { Spacer(Modifier.height(24.dp)) }
    }
}

@Composable
private fun Header(state: BleConnectionState, deviceName: String?) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Column {
            Text(
                text = "MOTONODE",
                color = MotoText,
                fontSize = 26.sp,
                fontWeight = FontWeight.Black,
                letterSpacing = 2.sp
            )
            Text(
                text = "RIDE TELEMETRY",
                color = MotoRed,
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 3.sp
            )
        }

        Column(horizontalAlignment = Alignment.End) {
            StatusDot(state)
            if (deviceName != null) {
                Text(deviceName, color = MotoMuted, fontSize = 11.sp)
            }
        }
    }
}

@Composable
private fun StatusDot(state: BleConnectionState) {
    val connected = state == BleConnectionState.CONNECTED
    Row(verticalAlignment = Alignment.CenterVertically) {
        Canvas(Modifier.size(9.dp)) {
            drawCircle(if (connected) MotoGreen else MotoRed)
        }
        Spacer(Modifier.width(7.dp))
        Text(
            if (connected) "LIVE" else state.name,
            color = if (connected) MotoGreen else MotoMuted,
            fontWeight = FontWeight.Bold,
            fontSize = 11.sp
        )
    }
}

@Composable
private fun ConnectionCard(
    state: BleConnectionState,
    status: String,
    onConnect: () -> Unit,
    onDisconnect: () -> Unit
) {
    Card(
        colors = CardDefaults.cardColors(containerColor = MotoSurface),
        shape = RoundedCornerShape(18.dp),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(14.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text("BLE LINK", color = MotoMuted, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                Text(status, color = MotoText, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
            }
            Button(
                onClick = if (state == BleConnectionState.CONNECTED) onDisconnect else onConnect,
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (state == BleConnectionState.CONNECTED) MotoSurface2 else MotoRed
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text(if (state == BleConnectionState.CONNECTED) "DISCONNECT" else "CONNECT")
            }
        }
    }
}

@Composable
private fun SpeedCard(speedMph: Float, modifier: Modifier = Modifier) {
    Card(
        modifier = modifier.height(150.dp),
        colors = CardDefaults.cardColors(containerColor = MotoSurface),
        shape = RoundedCornerShape(18.dp)
    ) {
        Column(
            Modifier.fillMaxSize().padding(14.dp),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            Text("GPS SPEED", color = MotoMuted, fontSize = 11.sp, fontWeight = FontWeight.Bold)
            Row(verticalAlignment = Alignment.Bottom) {
                Text(
                    speedMph.roundToInt().toString(),
                    color = MotoText,
                    fontSize = 52.sp,
                    fontWeight = FontWeight.Black
                )
                Text(" mph", color = MotoRed, fontSize = 14.sp, modifier = Modifier.padding(bottom = 10.dp))
            }
        }
    }
}

@Composable
private fun GpsCard(packet: TelemetryPacket, modifier: Modifier = Modifier) {
    Card(
        modifier = modifier.height(150.dp),
        colors = CardDefaults.cardColors(containerColor = MotoSurface),
        shape = RoundedCornerShape(18.dp)
    ) {
        Column(
            Modifier.fillMaxSize().padding(14.dp),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            Text("GPS LOCK", color = MotoMuted, fontSize = 11.sp, fontWeight = FontWeight.Bold)
            Text(
                if (packet.gpsFix) "FIX" else "NO FIX",
                color = if (packet.gpsFix) MotoGreen else MotoRed,
                fontSize = 26.sp,
                fontWeight = FontWeight.Black
            )
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Column {
                    Text("SAT", color = MotoMuted, fontSize = 9.sp)
                    Text(packet.satellites.toString(), color = MotoText, fontWeight = FontWeight.Bold)
                }
                Column {
                    Text("HDOP", color = MotoMuted, fontSize = 9.sp)
                    Text("%.2f".format(packet.hdop), color = MotoText, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

@Composable
private fun LeanCard(lean: Float, pitch: Float) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MotoSurface),
        shape = RoundedCornerShape(18.dp)
    ) {
        Column(
            Modifier.fillMaxWidth().padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text("LEAN ANGLE", color = MotoMuted, fontSize = 11.sp, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(4.dp))
            LeanGauge(lean)
            Text(
                text = "%+.1f°".format(lean),
                color = if (abs(lean) >= 40f) MotoRed else MotoText,
                fontSize = 36.sp,
                fontWeight = FontWeight.Black
            )
            Text("Pitch %+.1f°".format(pitch), color = MotoMuted, fontSize = 12.sp)
        }
    }
}

@Composable
private fun LeanGauge(lean: Float) {
    Canvas(
        modifier = Modifier
            .fillMaxWidth()
            .height(105.dp)
            .padding(horizontal = 10.dp)
    ) {
        val center = Offset(size.width / 2f, size.height * 0.92f)
        val radius = size.width.coerceAtMost(size.height * 2.0f) * 0.43f
        val start = 200f
        val sweep = 140f

        drawArc(
            color = MotoSurface2,
            startAngle = start,
            sweepAngle = sweep,
            useCenter = false,
            topLeft = Offset(center.x - radius, center.y - radius),
            size = Size(radius * 2f, radius * 2f),
            style = Stroke(width = 10.dp.toPx(), cap = StrokeCap.Round)
        )

        val clamped = lean.coerceIn(-60f, 60f)
        val angleDeg = 270f + clamped / 60f * 70f
        val angleRad = Math.toRadians(angleDeg.toDouble())
        val needleEnd = Offset(
            center.x + cos(angleRad).toFloat() * radius * 0.88f,
            center.y + sin(angleRad).toFloat() * radius * 0.88f
        )

        drawLine(
            color = if (abs(clamped) >= 40f) MotoRed else MotoCyan,
            start = center,
            end = needleEnd,
            strokeWidth = 4.dp.toPx(),
            cap = StrokeCap.Round
        )
        drawCircle(MotoText, radius = 5.dp.toPx(), center = center)
    }
}

@Composable
private fun LeanTrace(history: List<Float>) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MotoSurface),
        shape = RoundedCornerShape(18.dp)
    ) {
        Column(Modifier.padding(14.dp)) {
            Text("LEAN TRACE", color = MotoMuted, fontSize = 11.sp, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(8.dp))
            Canvas(Modifier.fillMaxWidth().height(90.dp)) {
                val mid = size.height / 2f
                drawLine(MotoSurface2, Offset(0f, mid), Offset(size.width, mid), strokeWidth = 1.dp.toPx())
                if (history.size > 1) {
                    val maxLean = 60f
                    val dx = size.width / (history.size - 1).coerceAtLeast(1)
                    for (i in 1 until history.size) {
                        val x1 = (i - 1) * dx
                        val x2 = i * dx
                        val y1 = mid - (history[i - 1].coerceIn(-maxLean, maxLean) / maxLean) * mid
                        val y2 = mid - (history[i].coerceIn(-maxLean, maxLean) / maxLean) * mid
                        drawLine(MotoCyan, Offset(x1, y1), Offset(x2, y2), strokeWidth = 2.dp.toPx())
                    }
                }
            }
        }
    }
}

@Composable
private fun MetricCard(
    label: String,
    value: Float,
    unit: String,
    accent: Color,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.height(115.dp),
        colors = CardDefaults.cardColors(containerColor = MotoSurface),
        shape = RoundedCornerShape(18.dp)
    ) {
        Column(
            Modifier.fillMaxSize().padding(14.dp),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            Text(label, color = MotoMuted, fontSize = 11.sp, fontWeight = FontWeight.Bold)
            Row(verticalAlignment = Alignment.Bottom) {
                Text("%+.2f".format(value), color = MotoText, fontSize = 29.sp, fontWeight = FontWeight.Black)
                Text(" $unit", color = accent, fontSize = 12.sp, modifier = Modifier.padding(bottom = 5.dp))
            }
        }
    }
}

@Composable
private fun PeakCard(packet: TelemetryPacket) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MotoSurface),
        shape = RoundedCornerShape(18.dp)
    ) {
        Column(Modifier.padding(14.dp)) {
            Text("RIDE PEAKS", color = MotoMuted, fontSize = 11.sp, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(12.dp))
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                PeakValue("LEFT", "%.1f°".format(packet.maxLeftLeanDeg))
                PeakValue("RIGHT", "%.1f°".format(abs(packet.maxRightLeanDeg)))
                PeakValue("ACCEL", "%.2fG".format(packet.maxAccelG))
                PeakValue("BRAKE", "%.2fG".format(abs(packet.maxBrakeG)))
            }
        }
    }
}

@Composable
private fun PeakValue(label: String, value: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(label, color = MotoMuted, fontSize = 9.sp)
        Text(value, color = MotoText, fontSize = 16.sp, fontWeight = FontWeight.Bold)
    }
}

@Composable
private fun PositionCard(packet: TelemetryPacket) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MotoSurface),
        shape = RoundedCornerShape(18.dp)
    ) {
        Column(Modifier.padding(14.dp)) {
            Text("POSITION", color = MotoMuted, fontSize = 11.sp, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(8.dp))
            Text(
                if (packet.gpsFix) "%.6f, %.6f".format(packet.latitude, packet.longitude) else "Waiting for GPS fix",
                color = MotoText,
                fontSize = 16.sp,
                fontWeight = FontWeight.SemiBold
            )
            Text("Protocol v${packet.version}  •  Packet ${packet.sequence}", color = MotoMuted, fontSize = 10.sp)
        }
    }
}
