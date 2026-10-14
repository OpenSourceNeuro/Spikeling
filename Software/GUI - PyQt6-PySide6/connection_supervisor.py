"""
Automatic connection, loss detection and reconnection for the Spikeling board.

The supervisor replaces manual COM-port browsing with a polling state machine:

``SEARCHING`` -> a matching USB descriptor appears -> ``CONNECTED`` -> the cable
is pulled -> ``LOST`` -> the board re-enumerates -> ``CONNECTED`` again, with the
GUI event loop never interrupted.
"""

from __future__ import annotations

import sys
from enum import Enum, auto
from typing import Callable, Optional

from PySide6.QtCore import QObject, QTimer, Signal

from spikeling_discovery import SpikelingPort, discover_spikeling_ports


# Windows registers a COM port before usbser.sys will accept CreateFile, so
# the settle delay must absorb driver binding, not merely enumeration.
DEFAULT_SETTLE_DELAY_MS = 900 if sys.platform.startswith("win") else 400

# An open handle proves nothing: the board emits bytes only while the host
# asserts DTR. Require observed traffic before declaring the link up.
HANDSHAKE_TIMEOUT_MS = 2500

# Consecutive validated-open failures before the user is asked to intervene.
FAILURES_BEFORE_HINT = 4

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
    manual_action_required = Signal(str)

    def __init__(self, manager, poll_interval_ms: int = 750,
                 settle_delay_ms: int = DEFAULT_SETTLE_DELAY_MS,
                 pin_to_serial_number: bool = True,
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

        # Port opened but not yet proven to stream.
        self._probationary: Optional[SpikelingPort] = None

        # Round-robin cursor. With handshake validation a bad candidate is
        # now rejected rather than accepted, so returning candidates[0] on
        # every tick would retry the same dead port forever.
        self._candidate_cursor = 0
        self._failed_ports: set[str] = set()
        self._consecutive_failures = 0
        self._hint_emitted = False

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(int(poll_interval_ms))
        self._poll_timer.timeout.connect(self._poll)

        self._handshake_timer = QTimer(self)
        self._handshake_timer.setSingleShot(True)
        self._handshake_timer.timeout.connect(self._on_handshake_timeout)

        self._manager.device_lost.connect(self._on_device_lost)
        self._manager.data_received.connect(self._on_packet_received)

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
        self._handshake_timer.stop()
        self._recovering = False
        self._awaiting_reenumeration = False
        self._probationary = None
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
        if self._open_in_flight or self._handshake_timer.isActive():
            return

        if self._manager.is_open:
            # Unconditional: gating this on a pinned serial number disabled
            # liveness checking entirely whenever the OS reported no serial
            # string for the device.
            if not self._manager.is_device_still_present():
                self._on_device_lost("Device no longer enumerated")
            return

        candidates = discover_spikeling_ports(self._pinned_serial_number)

        if self._awaiting_reenumeration:
            if any(port.serial_number == self._pinned_serial_number
                   for port in candidates):
                self._awaiting_reenumeration = False
            else:
                return

        target = self._select_target(candidates)
        if target is None:
            return

        self._open_in_flight = True
        QTimer.singleShot(self._settle_delay_ms, lambda: self._attempt_open(target))

    def _select_target(self, candidates: list[SpikelingPort]) -> Optional[SpikelingPort]:
        """
        Pick the next port to probe, honouring the pin and rotating otherwise.

        Parameters
        ----------
        candidates : list of SpikelingPort
            Ports from discovery, best match first.

        Returns
        -------
        SpikelingPort or None
            Port to try, or ``None`` when nothing is eligible.

        Notes
        -----
        Ports that failed their handshake are deprioritised but not banned
        permanently: the set is cleared once every candidate has failed, so a
        board that was merely slow to bind is retried.
        """
        if not candidates:
            self._candidate_cursor = 0
            return None

        if self._pin_to_serial_number and self._pinned_serial_number:
            for port in candidates:
                if port.serial_number == self._pinned_serial_number:
                    return port
            return None

        viable = [p for p in candidates if p.port_name not in self._failed_ports]
        if not viable:
            self._failed_ports.clear()
            viable = candidates

        port = viable[self._candidate_cursor % len(viable)]
        self._candidate_cursor += 1
        return port

    def _attempt_open(self, port: SpikelingPort) -> None:
        """
        Open ``port`` and begin probation; success is decided by traffic.

        Neither the state transition nor the state restorers run here. A port
        that opens cleanly but never streams is indistinguishable from a
        working one at this point, and replaying parameters into a silent
        link leaves the firmware holding defaults while the GUI believes
        otherwise.
        """
        self._open_in_flight = False
        if self._manager.is_open:
            return
        if not self._manager.open_port(port):
            # Windows returns PermissionError both for a port held by another
            # application and for one whose driver is still binding.
            self._register_failure(port, "could not be opened")
            return

        self._probationary = port
        self._manager.clear_buffer()
        self._manager.write("CON\n")   # blinks the RGB LED: visible liveness cue
        self._handshake_timer.start(HANDSHAKE_TIMEOUT_MS)

    def _on_device_lost(self, reason: str) -> None:
        """Handle an unexpected loss and arm the reconnection sequence."""
        if self._state is ConnectionState.LOST:
            return
        self._handshake_timer.stop()
        self._probationary = None
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

    def _on_packet_received(self, _packet: list) -> None:
        """
        Promote a probationary port once the board has actually streamed.

        Bound to ``data_received``, which fires at the full sample rate, so
        the early return must remain the first statement.
        """
        if self._probationary is None:
            return

        port = self._probationary
        self._probationary = None
        self._handshake_timer.stop()

        self._pinned_serial_number = port.serial_number or self._pinned_serial_number
        self._awaiting_reenumeration = False
        self._candidate_cursor = 0
        self._consecutive_failures = 0
        self._hint_emitted = False
        self._failed_ports.discard(port.port_name)

        # Deferred to here so parameters are never pushed into a silent port.
        for restore in self._state_restorers:
            try:
                restore()
            except Exception as error:  # a broken restorer must not kill the link
                print(f"State restore failed: {error}")

        was_recovering = self._recovering
        self._recovering = False
        self._set_state(ConnectionState.CONNECTED)
        self.reconnected.emit(port) if was_recovering else self.connected.emit(port)

    def _on_handshake_timeout(self) -> None:
        """Reject a port that opened but produced no data."""
        port = self._probationary
        self._probationary = None
        if self._manager.is_open:
            self._manager.close()
        if port is not None:
            self._register_failure(port, "opened but sent no data")

    def _register_failure(self, port: SpikelingPort, reason: str) -> None:
        """
        Record a failed probe and advise the user after repeated failures.

        Parameters
        ----------
        port : SpikelingPort
            Candidate that failed.
        reason : str
            Short diagnostic, printed to the console.
        """
        print(f"[spikeling] {port.port_name} {reason}")
        self._failed_ports.add(port.port_name)
        self._consecutive_failures += 1

        if self._consecutive_failures >= FAILURES_BEFORE_HINT and not self._hint_emitted:
            self._hint_emitted = True
            self.manual_action_required.emit(
                "A Spikeling board was detected but no data arrived.\n\n"
                "Close any other program holding the serial port (Arduino IDE "
                "serial monitor, PuTTY), then press RESET on the board. "
                "Reconnection is automatic."
            )
