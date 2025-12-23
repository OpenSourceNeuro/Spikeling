package org.opensourceneuro.spikelinglite.util

/**
 * Fixed-size ring buffer for floats. Optimized for oscilloscope-style plotting.
 */
class FloatRingBuffer(private val capacity: Int) {
    private val data = FloatArray(capacity)
    private var writeIdx = 0
    private var count = 0
    var totalSamples: Long = 0
        private set

    fun add(v: Float) {
        data[writeIdx] = v
        writeIdx = (writeIdx + 1) % capacity
        if (count < capacity) count++
        totalSamples++
    }

    fun clear() {
        writeIdx = 0
        count = 0
        totalSamples = 0
    }

    fun snapshot(): List<Float> {
        if (count == 0) return emptyList()

        val out = ArrayList<Float>(count)
        val start = if (count < capacity) 0 else writeIdx
        for (i in 0 until count) {
            val idx = (start + i) % capacity
            out.add(data[idx])
        }
        return out
    }
}
