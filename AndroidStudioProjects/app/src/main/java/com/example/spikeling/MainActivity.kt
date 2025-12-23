package com.example.spikeling.ui

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import org.opensourceneuro.spikelinglite.ui.SpikelingScreen

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            val vm: SpikelingViewModel = viewModel()
            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    SpikelingScreen(vm)
                }
            }
        }
    }
}
