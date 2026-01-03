package com.example.spikeling.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.weight
import androidx.compose.material3.Button
import androidx.compose.material3.Divider
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.spikeling.SpikelingViewModel
import com.example.spikeling.net.ConnectionState


@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SpikelingScreen(vm: SpikelingViewModel) {
    val host by vm.host.collectAsState()
    val port by vm.port.collectAsState()
    val conn by vm.connState.collectAsState()

    val trace by vm.vmTrace.collectAsState()
    val lastVm by vm.lastVmMv.collectAsState()

    val clampEnabled by vm.clampEnabled.collectAsState()
    val clampValue by vm.clampValue.collectAsState()

    val noiseEnabled by vm.noiseEnabled.collectAsState()
    val noiseValue by vm.noiseValue.collectAsState()

    val ledEnabled by vm.ledEnabled.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(title = { Text("Spikeling Lite") })
        }
    ) { pad ->
        Column(
            modifier = Modifier
                .padding(pad)
                .padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // Connection block
            Text("Connection", style = MaterialTheme.typography.titleMedium)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                OutlinedTextField(
                    value = host,
                    onValueChange = vm::setHost,
                    label = { Text("Host") },
                    singleLine = true,
                    modifier = Modifier.weight(1f)
                )
                OutlinedTextField(
                    value = port,
                    onValueChange = vm::setPort,
                    label = { Text("Port") },
                    singleLine = true,
                    modifier = Modifier.weight(0.6f)
                )
            }

            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                val isConnected = conn is ConnectionState.Connected
                Button(onClick = { if (isConnected) vm.disconnect() else vm.connect() }) {
                    Text(if (isConnected) "Disconnect" else "Connect")
                }
                Button(onClick = vm::clearPlot) { Text("Clear") }
                Text(
                    when (conn) {
                        is ConnectionState.Disconnected -> "Disconnected"
                        is ConnectionState.Connecting -> "Connecting…"
                        is ConnectionState.Connected -> "Connected"
                        is ConnectionState.Error -> "Error"
                    }
                )
            }

            if (conn is ConnectionState.Error) {
                Text((conn as ConnectionState.Error).message, color = MaterialTheme.colorScheme.error)
            }

            Divider()

            // Live plot
            Text("Live Vm", style = MaterialTheme.typography.titleMedium)
            Text("Last Vm: ${lastVm?.let { "%.2f mV".format(it) } ?: "—"}")

            OscilloscopePlot(
                samples = trace,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(220.dp)
            )

            Divider()

            // Controls
            Text("Controls", style = MaterialTheme.typography.titleMedium)

            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("Clamp current (IC)")
                Switch(checked = clampEnabled, onCheckedChange = vm::setClampEnabled)
            }
            Text("Clamp value: ${"%.3f".format(clampValue)}")
            Slider(
                value = clampValue,
                onValueChange = vm::setClampValue,
                valueRange = 0f..1f
            )

            Spacer(modifier = Modifier.height(6.dp))

            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("Noise (NO)")
                Switch(checked = noiseEnabled, onCheckedChange = vm::setNoiseEnabled)
            }
            Text("Noise value: ${"%.3f".format(noiseValue)}")
            Slider(
                value = noiseValue,
                onValueChange = vm::setNoiseValue,
                valueRange = 0f..1f
            )

            Spacer(modifier = Modifier.height(6.dp))

            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("LED")
                Switch(checked = ledEnabled, onCheckedChange = vm::setLedEnabled)
            }

            Divider()

            // Raw command helper (useful while you add new controls)
            RawCommandBox(onSend = vm::sendCommand)
        }
    }
}

@Composable
private fun RawCommandBox(onSend: (String) -> Unit) {
    val cmdState = androidx.compose.runtime.remember { androidx.compose.runtime.mutableStateOf("") }

    Text("Raw command", style = MaterialTheme.typography.titleSmall)
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
        OutlinedTextField(
            value = cmdState.value,
            onValueChange = { cmdState.value = it },
            label = { Text("e.g. NEU 0") },
            singleLine = true,
            modifier = Modifier.weight(1f)
        )
        Button(onClick = {
            val t = cmdState.value.trim()
            if (t.isNotEmpty()) onSend(t)
        }) { Text("Send") }
    }
}
