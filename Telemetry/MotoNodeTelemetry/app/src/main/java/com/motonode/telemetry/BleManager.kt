package com.motonode.telemetry

import android.annotation.SuppressLint
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothGatt
import android.bluetooth.BluetoothGattCallback
import android.bluetooth.BluetoothGattCharacteristic
import android.bluetooth.BluetoothGattDescriptor
import android.bluetooth.BluetoothGattService
import android.bluetooth.BluetoothManager
import android.bluetooth.BluetoothProfile
import android.bluetooth.le.BluetoothLeScanner
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanFilter
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.Context
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.ParcelUuid
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.util.UUID

enum class BleConnectionState {
    IDLE,
    SCANNING,
    CONNECTING,
    DISCOVERING,
    CONNECTED,
    DISCONNECTED,
    ERROR
}

class BleManager(private val context: Context) {

    companion object {
        val SERVICE_UUID: UUID = UUID.fromString("6f9a0001-9c21-4b6f-8d73-5c2a1256a001")
        val TELEMETRY_UUID: UUID = UUID.fromString("6f9a0002-9c21-4b6f-8d73-5c2a1256a001")
        val CCCD_UUID: UUID = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")
        private const val SCAN_TIMEOUT_MS = 10_000L
    }

    private val bluetoothManager = context.getSystemService(BluetoothManager::class.java)
    val adapter: BluetoothAdapter? get() = bluetoothManager?.adapter
    private val scanner: BluetoothLeScanner? get() = adapter?.bluetoothLeScanner
    private val handler = Handler(Looper.getMainLooper())

    private var gatt: BluetoothGatt? = null
    private var scanning = false

    private val _state = MutableStateFlow(BleConnectionState.IDLE)
    val state: StateFlow<BleConnectionState> = _state.asStateFlow()

    private val _status = MutableStateFlow("Ready")
    val status: StateFlow<String> = _status.asStateFlow()

    private val _telemetry = MutableStateFlow(TelemetryPacket())
    val telemetry: StateFlow<TelemetryPacket> = _telemetry.asStateFlow()

    private val _deviceName = MutableStateFlow<String?>(null)
    val deviceName: StateFlow<String?> = _deviceName.asStateFlow()

    private val stopScanRunnable = Runnable {
        if (scanning) {
            stopScan()
            if (_state.value == BleConnectionState.SCANNING) {
                _state.value = BleConnectionState.DISCONNECTED
                _status.value = "MotoNode not found"
            }
        }
    }

    @SuppressLint("MissingPermission")
    fun startScan() {
        if (adapter == null) {
            _state.value = BleConnectionState.ERROR
            _status.value = "Bluetooth unavailable"
            return
        }
        if (adapter?.isEnabled != true) {
            _state.value = BleConnectionState.ERROR
            _status.value = "Bluetooth is off"
            return
        }

        disconnect()

        val filter = ScanFilter.Builder()
            .setServiceUuid(ParcelUuid(SERVICE_UUID))
            .build()
        val settings = ScanSettings.Builder()
            .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
            .build()

        scanning = true
        _state.value = BleConnectionState.SCANNING
        _status.value = "Scanning for MotoNode…"
        scanner?.startScan(listOf(filter), settings, scanCallback)
        handler.postDelayed(stopScanRunnable, SCAN_TIMEOUT_MS)
    }

    @SuppressLint("MissingPermission")
    private fun stopScan() {
        if (!scanning) return
        scanner?.stopScan(scanCallback)
        scanning = false
        handler.removeCallbacks(stopScanRunnable)
    }

    @SuppressLint("MissingPermission")
    fun disconnect() {
        stopScan()
        gatt?.disconnect()
        gatt?.close()
        gatt = null
        if (_state.value != BleConnectionState.IDLE) {
            _state.value = BleConnectionState.DISCONNECTED
            _status.value = "Disconnected"
        }
    }

    @SuppressLint("MissingPermission")
    private fun connect(result: ScanResult) {
        stopScan()
        _state.value = BleConnectionState.CONNECTING
        _deviceName.value = result.device.name ?: "MotoNode"
        _status.value = "Connecting to ${_deviceName.value}…"
        gatt = result.device.connectGatt(context, false, gattCallback, BluetoothGatt.TRANSPORT_LE)
    }

    private val scanCallback = object : ScanCallback() {
        @SuppressLint("MissingPermission")
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            connect(result)
        }

        override fun onScanFailed(errorCode: Int) {
            scanning = false
            _state.value = BleConnectionState.ERROR
            _status.value = "BLE scan failed: $errorCode"
        }
    }

    private val gattCallback = object : BluetoothGattCallback() {
        @SuppressLint("MissingPermission")
        override fun onConnectionStateChange(gatt: BluetoothGatt, status: Int, newState: Int) {
            if (status != BluetoothGatt.GATT_SUCCESS) {
                _state.value = BleConnectionState.ERROR
                _status.value = "BLE connection error: $status"
                gatt.close()
                return
            }

            when (newState) {
                BluetoothProfile.STATE_CONNECTED -> {
                    _state.value = BleConnectionState.DISCOVERING
                    _status.value = "Connected — negotiating BLE link…"
                    val mtuStarted = gatt.requestMtu(128)
                    if (!mtuStarted) gatt.discoverServices()
                }
                BluetoothProfile.STATE_DISCONNECTED -> {
                    _state.value = BleConnectionState.DISCONNECTED
                    _status.value = "Disconnected"
                    gatt.close()
                }
            }
        }

        @SuppressLint("MissingPermission")
        override fun onMtuChanged(gatt: BluetoothGatt, mtu: Int, status: Int) {
            _status.value = if (status == BluetoothGatt.GATT_SUCCESS) {
                "BLE MTU $mtu — discovering telemetry service…"
            } else {
                "Discovering telemetry service…"
            }
            gatt.discoverServices()
        }

        @SuppressLint("MissingPermission")
        override fun onServicesDiscovered(gatt: BluetoothGatt, status: Int) {
            if (status != BluetoothGatt.GATT_SUCCESS) {
                _state.value = BleConnectionState.ERROR
                _status.value = "GATT service discovery failed: $status"
                return
            }

            val service: BluetoothGattService? = gatt.getService(SERVICE_UUID)
            val characteristic = service?.getCharacteristic(TELEMETRY_UUID)

            if (characteristic == null) {
                _state.value = BleConnectionState.ERROR
                _status.value = "MotoNode telemetry characteristic missing"
                return
            }

            val enabled = gatt.setCharacteristicNotification(characteristic, true)
            if (!enabled) {
                _state.value = BleConnectionState.ERROR
                _status.value = "Could not enable telemetry notifications"
                return
            }

            val cccd = characteristic.getDescriptor(CCCD_UUID)
            if (cccd == null) {
                _state.value = BleConnectionState.ERROR
                _status.value = "BLE notification descriptor missing"
                return
            }

            val writeStarted = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                gatt.writeDescriptor(cccd, BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE) == 0
            } else {
                @Suppress("DEPRECATION")
                run {
                    cccd.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
                    gatt.writeDescriptor(cccd)
                }
            }

            if (!writeStarted) {
                _state.value = BleConnectionState.ERROR
                _status.value = "Could not subscribe to telemetry"
            }
        }

        override fun onDescriptorWrite(gatt: BluetoothGatt, descriptor: BluetoothGattDescriptor, status: Int) {
            if (descriptor.uuid == CCCD_UUID && status == BluetoothGatt.GATT_SUCCESS) {
                _state.value = BleConnectionState.CONNECTED
                _status.value = "Live telemetry"
            } else if (status != BluetoothGatt.GATT_SUCCESS) {
                _state.value = BleConnectionState.ERROR
                _status.value = "Telemetry subscription failed: $status"
            }
        }

        @Deprecated("Deprecated in API 33")
        override fun onCharacteristicChanged(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic
        ) {
            @Suppress("DEPRECATION")
            handleTelemetry(characteristic.value)
        }

        override fun onCharacteristicChanged(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic,
            value: ByteArray
        ) {
            handleTelemetry(value)
        }
    }

    private fun handleTelemetry(value: ByteArray) {
        TelemetryPacket.decode(value)?.let { packet ->
            _telemetry.value = packet
            if (packet.version != 1) {
                _status.value = "Telemetry protocol v${packet.version}"
            }
        }
    }
}
