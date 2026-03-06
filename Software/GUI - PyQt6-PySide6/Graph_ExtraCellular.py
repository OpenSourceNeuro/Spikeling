
from PySide6.QtCore import QObject, QTimer
import pyqtgraph as pg
import numpy as np
import pandas as pd
import collections

import Parameters_Settings as Settings
from serial_manager import serial_manager


# =============================================================================
# Constants
# =============================================================================



# =============================================================================
# ExtraCellular Graph
# =============================================================================

class ExtraCellularGraph(QObject):
    """
    Controller class for tetrode-like recording simulation and plotting.
    """

    # -------------------------------------------------------------------------
    # Initialization & Lifecycle
    # -------------------------------------------------------------------------

    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent
        self.ui = parent.ui

        # -------------------------
        # Data source control
        # -------------------------
        self.source_mode = "spikeling"   # "spikeling", "emulator", "none"
        self.last_valid_data = None
        self._t_last_ms = None
        self._t_abs_ms = 0.0             # fallback clock when hardware provides no timestamp

    def SignalMode(self):
        pass