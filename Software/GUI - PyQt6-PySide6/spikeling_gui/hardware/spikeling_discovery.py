"""
Cross-platform discovery of Spikeling boards on the host USB bus.

Identification relies solely on the USB descriptors already emitted by the
firmware (``build_opt.h``), so no device-side change is required:

* Espressif vendor id ``0x303A`` for the ESP32-S3 native USB CDC peripheral.
* Product string ``Spikeling`` / manufacturer string ``Open Source Neuro``.
* ``USB_SERIAL=__MAC__`` yields a unique, reboot-stable serial number used to
  re-attach to the *same* physical board after a hot-plug.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from PySide6.QtSerialPort import QSerialPortInfo

ESPRESSIF_VENDOR_ID = 0x303A
SPIKELING_DESCRIPTOR_KEYWORDS = ("spikeling", "open source neuro")
GENERIC_USB_UART_VENDOR_IDS = (0x10C4, 0x1A86, 0x0403, 0x067B)  # CP210x, CH34x, FTDI, PL2303


@dataclass(frozen=True)
class SpikelingPort:
    """
    A serial port that is a plausible Spikeling board.

    Attributes
    ----------
    port_name : str
        Platform port name handed to :meth:`QSerialPort.setPortName`
        (``COM5``, ``ttyACM0``, ``cu.usbmodem14201``).
    system_location : str
        Absolute device node, useful for logging and udev diagnostics.
    description : str
        USB product string.
    manufacturer : str
        USB manufacturer string.
    serial_number : str
        USB serial string; the board's MAC address for Spikeling firmware.
    vendor_id : int or None
        USB vendor identifier, ``None`` when the OS does not expose it.
    product_id : int or None
        USB product identifier, ``None`` when the OS does not expose it.
    confidence : int
        Higher is better: ``2`` descriptor match, ``1`` vendor-id match,
        ``0`` generic USB-UART bridge.
    """

    port_name: str
    system_location: str
    description: str
    manufacturer: str
    serial_number: str
    vendor_id: Optional[int]
    product_id: Optional[int]
    confidence: int

    @property
    def label(self) -> str:
        """Human-readable one-line identifier for UI widgets and popups."""
        suffix = f" [{self.serial_number}]" if self.serial_number else ""
        return f"{self.port_name} - {self.description or 'Serial device'}{suffix}"


def _score_port(info: QSerialPortInfo) -> Optional[int]:
    """
    Rate how likely a port is a Spikeling board.

    Returns
    -------
    int or None
        Confidence score, or ``None`` when the port should be ignored.
    """
    haystack = f"{info.description()} {info.manufacturer()}".lower()
    if any(keyword in haystack for keyword in SPIKELING_DESCRIPTOR_KEYWORDS):
        return 2
    if info.hasVendorIdentifier() and info.vendorIdentifier() == ESPRESSIF_VENDOR_ID:
        return 1
    if info.hasVendorIdentifier() and info.vendorIdentifier() in GENERIC_USB_UART_VENDOR_IDS:
        return 0
    return None


def _to_spikeling_port(info: QSerialPortInfo, confidence: int) -> SpikelingPort:
    """Convert a :class:`QSerialPortInfo` into an immutable :class:`SpikelingPort`."""
    return SpikelingPort(
        port_name=info.portName(),
        system_location=info.systemLocation(),
        description=info.description(),
        manufacturer=info.manufacturer(),
        serial_number=info.serialNumber(),
        vendor_id=info.vendorIdentifier() if info.hasVendorIdentifier() else None,
        product_id=info.productIdentifier() if info.hasProductIdentifier() else None,
        confidence=confidence,
    )


def discover_spikeling_ports(preferred_serial_number: str = "",
                             accept_generic_bridges: bool = True) -> list[SpikelingPort]:
    """
    Enumerate candidate Spikeling ports, best match first.

    Parameters
    ----------
    preferred_serial_number : str, optional
        Serial number of a previously connected board; it is ranked first so a
        hot-plug always re-attaches to the same hardware when several boards
        share the bus.
    accept_generic_bridges : bool, optional
        Also return CP210x/CH34x/FTDI/PL2303 adapters, needed for Spikeling
        revisions that use an external USB-UART bridge instead of native CDC.

    Returns
    -------
    list of SpikelingPort
        Sorted by pinned-serial match, then descriptor confidence, then name.

    Notes
    -----
    On macOS ``QSerialPortInfo`` reports the ``cu.*`` callout nodes, which are
    the correct ones for a non-modem device. On Linux the user must belong to
    the ``dialout`` group (Debian/Ubuntu) for the port to be openable.
    """
    candidates: list[SpikelingPort] = []
    for info in QSerialPortInfo.availablePorts():
        if info.isNull():
            continue
        confidence = _score_port(info)
        if confidence is None:
            continue
        if confidence == 0 and not accept_generic_bridges:
            continue
        candidates.append(_to_spikeling_port(info, confidence))

    def sort_key(port: SpikelingPort):
        pinned = bool(preferred_serial_number) and port.serial_number == preferred_serial_number
        return (not pinned, -port.confidence, port.port_name)

    return sorted(candidates, key=sort_key)


def find_port_by_serial_number(serial_number: str) -> Optional[SpikelingPort]:
    """Return the currently enumerated port carrying ``serial_number``, if any."""
    if not serial_number:
        return None
    for port in discover_spikeling_ports(preferred_serial_number=serial_number):
        if port.serial_number == serial_number:
            return port
    return None


def format_port_list(ports: Iterable[SpikelingPort]) -> str:
    """Render a port collection as a newline-separated diagnostic string."""
    return "\n".join(port.label for port in ports) or "No Spikeling board detected."
