package com.example.spikeling.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp
import kotlin.math.max
import kotlin.math.min

@Composable
fun OscilloscopePlot(
    samples: List<Float>,
    modifier: Modifier = Modifier,
) {
    // IMPORTANT: read theme colors in @Composable context (here), not inside Canvas draw lambda
    val bgColor = MaterialTheme.colorScheme.surfaceVariant
    val lineColor = MaterialTheme.colorScheme.onSurfaceVariant
    val axisColor = MaterialTheme.colorScheme.outline

    Box(
        modifier = modifier
            .background(bgColor)
            .padding(8.dp)
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            if (samples.size < 2) return@Canvas

            // Auto-scale Y
            var minY = Float.POSITIVE_INFINITY
            var maxY = Float.NEGATIVE_INFINITY
            for (v in samples) {
                minY = min(minY, v)
                maxY = max(maxY, v)
            }
            if (minY == maxY) {
                minY -= 1f
                maxY += 1f
            } else {
                val pad = 0.08f * (maxY - minY)
                minY -= pad
                maxY += pad
            }

            fun xOf(i: Int): Float =
                (i.toFloat() / (samples.size - 1).toFloat()) * size.width

            fun yOf(v: Float): Float {
                val t = (v - minY) / (maxY - minY) // 0..1
                return (1f - t) * size.height
            }

            val path = Path().apply {
                moveTo(xOf(0), yOf(samples[0]))
                for (i in 1 until samples.size) {
                    lineTo(xOf(i), yOf(samples[i]))
                }
            }

            drawPath(
                path = path,
                color = lineColor,
                style = Stroke(width = 2f)
            )

            // Center reference line
            val y0 = yOf((minY + maxY) * 0.5f)
            drawLine(
                color = axisColor,
                start = Offset(0f, y0),
                end = Offset(size.width, y0),
                strokeWidth = 1f
            )
        }
    }
}
