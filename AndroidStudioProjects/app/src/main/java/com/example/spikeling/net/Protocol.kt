package org.opensourceneuro.spikelinglite.net

import java.nio.ByteBuffer
import java.nio.ByteOrder

data class Sample(
    val v_mV: Float,
    val stimState: Int,
    val itot: Float,
    val syn1Vm: Float,
    val isyn1: Float,
    val syn2Vm: Float,
    val isyn2: Float,
    val trigger: Int
)

/**
 * Spikeling V3 default scaling constants (adjust if you changed the firmware).
 */
private const val V_SCALE = 100.0f
private const val I_SCALE = 100.0f

fun decodeSample(payload16: ByteArray): Sample {
    require(payload16.size == 16) { "Expected 16-byte payload, got ${payload16.size}" }
    val bb = ByteBuffer.wrap(payload16).order(ByteOrder.LITTLE_ENDIAN)

    val v_q        = bb.short.toInt()
    val stim_state = bb.short.toInt()
    val itot_q     = bb.short.toInt()
    val syn1_vm_q  = bb.short.toInt()
    val isyn1_q    = bb.short.toInt()
    val syn2_vm_q  = bb.short.toInt()
    val isyn2_q    = bb.short.toInt()
    val trig_q     = bb.short.toInt()

    return Sample(
        v_mV = v_q / V_SCALE,
        stimState = stim_state,
        itot = itot_q / I_SCALE,
        syn1Vm = syn1_vm_q.toFloat(),
        isyn1 = isyn1_q / I_SCALE,
        syn2Vm = syn2_vm_q.toFloat(),
        isyn2 = isyn2_q / I_SCALE,
        trigger = trig_q
    )
}
