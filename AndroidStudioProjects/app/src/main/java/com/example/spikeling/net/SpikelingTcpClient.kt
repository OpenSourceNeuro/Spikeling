package org.opensourceneuro.spikelinglite.net

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.BufferedInputStream
import java.io.BufferedOutputStream
import java.net.InetSocketAddress
import java.net.Socket
import java.util.concurrent.atomic.AtomicBoolean

sealed class ConnectionState {
    data object Disconnected : ConnectionState()
    data class Connecting(val host: String, val port: Int) : ConnectionState()
    data class Connected(val host: String, val port: Int) : ConnectionState()
    data class Error(val message: String) : ConnectionState()
}

/**
 * Simple TCP client:
 * - Reads binary frames: 0xAA 0x55 + 16 bytes payload (8×int16 LE)
 * - Sends newline-terminated ASCII commands (e.g., "IC1 0.2\n")
 */
class SpikelingTcpClient(
    private val scope: CoroutineScope,
    private val onConnectionState: (ConnectionState) -> Unit,
    private val onVmSample: (Float) -> Unit,
) {
    private var socket: Socket? = null
    private var inStream: BufferedInputStream? = null
    private var outStream: BufferedOutputStream? = null

    private var readerJob: Job? = null
    private val connected = AtomicBoolean(false)

    suspend fun connect(host: String, port: Int) {
        if (connected.get()) return
        onConnectionState(ConnectionState.Connecting(host, port))

        withContext(Dispatchers.IO) {
            try {
                val s = Socket()
                s.tcpNoDelay = true
                s.connect(InetSocketAddress(host, port), 3000) // 3s connect timeout

                socket = s
                inStream = BufferedInputStream(s.getInputStream(), 8192)
                outStream = BufferedOutputStream(s.getOutputStream(), 1024)

                connected.set(true)
                onConnectionState(ConnectionState.Connected(host, port))

                readerJob = scope.launch(Dispatchers.IO) {
                    try {
                        readLoop()
                    } catch (e: Exception) {
                        if (connected.get()) {
                            onConnectionState(ConnectionState.Error(e.message ?: "Read error"))
                        }
                    } finally {
                        disconnect()
                    }
                }
            } catch (e: Exception) {
                connected.set(false)
                onConnectionState(ConnectionState.Error(e.message ?: "Connect error"))
                disconnect()
            }
        }
    }

    fun disconnect() {
        scope.launch(Dispatchers.IO) {
            connected.set(false)
            try {
                readerJob?.cancel()
                readerJob = null
            } catch (_: Exception) {}

            try { inStream?.close() } catch (_: Exception) {}
            try { outStream?.close() } catch (_: Exception) {}
            try { socket?.close() } catch (_: Exception) {}

            inStream = null
            outStream = null
            socket = null

            onConnectionState(ConnectionState.Disconnected)
        }
    }

    fun sendLine(cmd: String) {
        val os = outStream ?: return
        if (!connected.get()) return
        scope.launch(Dispatchers.IO) {
            try {
                val line = if (cmd.endsWith("\n")) cmd else "$cmd\n"
                os.write(line.toByteArray(Charsets.US_ASCII))
                os.flush()
            } catch (e: Exception) {
                onConnectionState(ConnectionState.Error(e.message ?: "Send error"))
                disconnect()
            }
        }
    }

    private fun readLoop() {
        val input = inStream ?: return

        // State machine:
        // 0: waiting for 0xAA
        // 1: waiting for 0x55
        // 2: reading 16-byte payload
        var state = 0
        val payload = ByteArray(16)
        var payloadIdx = 0

        while (connected.get()) {
            val b = input.read()
            if (b < 0) throw RuntimeException("Socket closed")

            val ub = b and 0xFF

            when (state) {
                0 -> {
                    if (ub == 0xAA) state = 1
                }
                1 -> {
                    if (ub == 0x55) {
                        state = 2
                        payloadIdx = 0
                    } else {
                        // false start; if current byte is 0xAA, stay in state 1, else reset
                        state = if (ub == 0xAA) 1 else 0
                    }
                }
                2 -> {
                    payload[payloadIdx++] = ub.toByte()
                    if (payloadIdx >= 16) {
                        val s = decodeSample(payload)
                        // We only forward Vm for the lightweight oscilloscope view.
                        onVmSample(s.v_mV)
                        state = 0
                    }
                }
            }
        }
    }
}
