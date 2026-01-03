package org.opensourceneuro.spikelinglite

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import org.opensourceneuro.spikelinglite.net.ConnectionState
import org.opensourceneuro.spikelinglite.net.SpikelingTcpClient
import org.opensourceneuro.spikelinglite.util.FloatRingBuffer

class SpikelingViewModel : ViewModel() {

    // Connection parameters
    private val _host = MutableStateFlow("192.168.4.1")
    val host: StateFlow<String> = _host.asStateFlow()

    private val _port = MutableStateFlow("7777")
    val port: StateFlow<String> = _port.asStateFlow()

    fun setHost(v: String) { _host.value = v }
    fun setPort(v: String) { _port.value = v.filter { it.isDigit() } }

    // Connection state
    private val _connState = MutableStateFlow<ConnectionState>(ConnectionState.Disconnected)
    val connState: StateFlow<ConnectionState> = _connState.asStateFlow()

    // Live data (plot)
    private val ring = FloatRingBuffer(capacity = 1500) // ~7.5s at 200Hz
    private val _vmTrace = MutableStateFlow<List<Float>>(emptyList())
    val vmTrace: StateFlow<List<Float>> = _vmTrace.asStateFlow()

    private val _lastVmMv = MutableStateFlow<Float?>(null)
    val lastVmMv: StateFlow<Float?> = _lastVmMv.asStateFlow()

    // Controls
    private val _clampEnabled = MutableStateFlow(false)
    val clampEnabled: StateFlow<Boolean> = _clampEnabled.asStateFlow()

    private val _clampValue = MutableStateFlow(0.20f)
    val clampValue: StateFlow<Float> = _clampValue.asStateFlow()

    private val _noiseEnabled = MutableStateFlow(false)
    val noiseEnabled: StateFlow<Boolean> = _noiseEnabled.asStateFlow()

    private val _noiseValue = MutableStateFlow(0.10f)
    val noiseValue: StateFlow<Float> = _noiseValue.asStateFlow()

    private val _ledEnabled = MutableStateFlow(false)
    val ledEnabled: StateFlow<Boolean> = _ledEnabled.asStateFlow()

    private val client = SpikelingTcpClient(
        scope = viewModelScope,
        onConnectionState = { _connState.value = it },
        onVmSample = { vmMv ->
            _lastVmMv.value = vmMv
            ring.add(vmMv)
            // Update UI at a limited rate (avoid recomposing on every sample)
            if (ring.totalSamples % 3 == 0L) {
                _vmTrace.value = ring.snapshot()
            }
        }
    )

    fun connect() {
        val p = _port.value.toIntOrNull() ?: 7777
        viewModelScope.launch {
            client.connect(_host.value.trim(), p)
        }
    }

    fun disconnect() {
        client.disconnect()
    }

    fun setClampEnabled(enabled: Boolean) {
        _clampEnabled.value = enabled
        if (enabled) {
            sendClampNow()
        } else {
            sendCommand("IC0")
        }
    }

    fun setClampValue(v: Float) {
        _clampValue.value = v
        if (_clampEnabled.value) {
            sendClampNow()
        }
    }

    private fun sendClampNow() {
        // Firmware expects: IC1 <float>
        // Adjust range mapping as needed for your lab/teaching scale.
        val v = _clampValue.value
        sendCommand("IC1 ${"%.3f".format(v)}")
    }

    fun setNoiseEnabled(enabled: Boolean) {
        _noiseEnabled.value = enabled
        if (enabled) {
            sendNoiseNow()
        } else {
            sendCommand("NO0")
        }
    }

    fun setNoiseValue(v: Float) {
        _noiseValue.value = v
        if (_noiseEnabled.value) {
            sendNoiseNow()
        }
    }

    private fun sendNoiseNow() {
        val v = _noiseValue.value
        sendCommand("NO1 ${"%.3f".format(v)}")
    }

    fun setLedEnabled(enabled: Boolean) {
        _ledEnabled.value = enabled
        sendCommand(if (enabled) "LED1" else "LED0")
    }

    fun sendCommand(cmd: String) {
        client.sendLine(cmd)
    }

    fun clearPlot() {
        ring.clear()
        _vmTrace.value = emptyList()
        _lastVmMv.value = null
    }
}
