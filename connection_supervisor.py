"""
Automatic connection, loss detection and reconnection for the Spikeling board.

The supervisor replaces manual COM-port browsing with a polling state machine:

``SEARCHING`` -> a matching USB descriptor appears -> ``CONNECTED`` -> the cable
is pulled -> ``LOST`` -> the board re-enumerates -> ``CONNECTED`` again, with the
GUI event loop never interrupted.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Callable, Optional

from PySide6.QtCore import QObject, QTimer, Signal

from spikeling_discovery import SpikelingPort, discover_spikeling_ports


class ConnectionState(Enum):
    """Lifecycle of the host-to-board serial link."""

    IDLE = auto()
    SEARCHING = auto()
    CONNECTED = auto()
    LOST = auto()


class SpikelingConnectionSupervisor(QObject):
    """
    Keep exactly one Spikeling board connected, re-attaching after hot-plugs.

    Parameters
    ----------
    manager : serial_manager.SerialPortManager
        The singleton serial manager that owns the ``QSerialPort``.
    poll_interval_ms : int, optional
        USB re-enumeration polling period. 750 ms is imperceptible to the user
        and costs a few hundred microseconds of CPU per tick.
    settle_delay_ms : int, optional
        Delay between a port appearing and the open attempt. USB CDC endpoints
        are advertised slightly before the host driver finishes binding them.
    pin_to_serial_number : bool, optional
        Reconnect only to the board that was originally opened, identified by
        its USB serial number (the ESP32 MAC address).

    Attributes
    ----------
    state : ConnectionState
        Current state of the link.

    Signals
    -------
    connected(SpikelingPort)
        A board was opened; the GUI should push its parameter state.
    disconnected(str)
        The link died unexpectedly; the argument is a user-facing reason.
    reconnected(SpikelingPort)
        The same board came back after a loss.
    state_changed(ConnectionState)
        Emitted on every transition, for status-bar wiring.
    """

    connected = Signal(object)
    disconnected = Signal(str)
    reconnected = Signal(object)
    state_changed = Signal(object)

    def __init__(self, manager, poll_interval_ms: int = 750,
                 settle_delay_ms: int = 400, pin_to_serial_number: bool = True,
                 parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._manager = manager
        self._settle_delay_ms = int(settle_delay_ms)
        self._pin_to_serial_number = bool(pin_to_serial_number)

        self._state = ConnectionState.IDLE
        self._pinned_serial_number = ""
        self._recovering = False
        self._awaiting_reenumeration = False
        self._open_in_flight = False
        self._state_restorers: list[Callable[[], None]] = []

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(int(poll_interval_ms))
        self._poll_timer.timeout.connect(self._poll)

        self._manager.device_lost.connect(self._on_device_lost)

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------
    @property
    def state(self) -> ConnectionState:
        """Current link state."""
        return self._state

    def register_state_restorer(self, callback: Callable[[], None]) -> None:
        """
        Register a callback replaying GUI parameters onto a freshly opened board.

        The firmware boots with potentiometer control enabled, so every slider
        override (``DT``, ``NEU``, ``SG11``, ...) must be re-sent after a
        reconnection for the session to be reproducible.
        """
        if callback not in self._state_restorers:
            self._state_restorers.append(callback)

    def start(self) -> None:
        """Begin searching for a board and keep the link alive from now on."""
        if self._state is ConnectionState.CONNECTED:
            return
        self._set_state(ConnectionState.SEARCHING)
        self._poll_timer.start()
        self._poll()

    def stop(self) -> None:
        """Stop supervising and close the port; no reconnection is attempted."""
        self._poll_timer.stop()
        self._recovering = False
        self._awaiting_reenumeration = False
        if self._manager.is_open:
            self._manager.close()
        self._set_state(ConnectionState.IDLE)

    def force_rescan(self) -> None:
        """Trigger an immediate discovery pass, e.g. from a *Refresh* button."""
        self._poll()

    # -------------------------------------------------------------------------
    # State machine
    # -------------------------------------------------------------------------
    def _set_state(self, state: ConnectionState) -> None:
        if state is self._state:
            return
        self._state = state
        self.state_changed.emit(state)

    def _poll(self) -> None:
        """Polling tick: verify an existing link or try to establish a new one."""
        if self._open_in_flight:
            return

        if self._manager.is_open:
            # Windows can keep a handle valid on a removed device until the
            # first failed transfer; enumeration is the reliable ground truth.
            if self._pinned_serial_number and not self._manager.is_device_still_present():
                self._on_device_lost("Device no longer enumerated")
            return

        candidates = discover_spikeling_ports(self._pinned_serial_number)

        if self._awaiting_reenumeration:
            if any(port.serial_number == self._pinned_serial_number for port in candidates):
                self._awaiting_reenumeration = False
            else:
                return

        target = self._select_target(candidates)
        if target is None:
            return

        self._open_in_flight = True
        QTimer.singleShot(self._settle_delay_ms, lambda: self._attempt_open(target))

    def _select_target(self, candidates: list[SpikelingPort]) -> Optional[SpikelingPort]:
        """Pick the port to open, honouring the pinned serial number."""
        if not candidates:
            return None
        if self._pin_to_serial_number and self._pinned_serial_number:
            for port in candidates:
                if port.serial_number == self._pinned_serial_number:
                    return port
            return None
        return candidates[0]

    def _attempt_open(self, port: SpikelingPort) -> None:
        """Open ``port`` and replay the GUI state; silent on failure, retried next tick."""
        self._open_in_flight = False
        if self._manager.is_open:
            return
        if not self._manager.open_port(port):
            return

        self._pinned_serial_number = port.serial_number or self._pinned_serial_number
        self._awaiting_reenumeration = False

        for restore in self._state_restorers:
            try:
                restore()
            except Exception as error:  # a broken restorer must not kill the link
                print(f"State restore failed: {error}")

        was_recovering = self._recovering
        self._recovering = False
        self._set_state(ConnectionState.CONNECTED)
        self.reconnected.emit(port) if was_recovering else self.connected.emit(port)

    def _on_device_lost(self, reason: str) -> None:
        """Handle an unexpected loss and arm the reconnection sequence."""
        if self._state is ConnectionState.LOST:
            return
        if self._manager.is_open:
            self._manager.close()

        self._recovering = True
        # Require the node to vanish before retrying, otherwise a stale handle
        # on the same COM name is reopened and fails immediately.
        self._awaiting_reenumeration = bool(self._pinned_serial_number)
        self._set_state(ConnectionState.LOST)
        self.disconnected.emit(reason)

        if not self._poll_timer.isActive():
            self._poll_timer.start()
