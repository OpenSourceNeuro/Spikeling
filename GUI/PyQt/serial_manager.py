"""
Serial Port Manager Module

This module provides a singleton class for managing serial port connections
across different components of the application.
"""

from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo
from PySide6.QtCore import QObject, Signal, QByteArray, QMutex, QMutexLocker
from collections import deque

import Settings


class SerialPortManager(QObject):
    """
    Singleton class for managing serial port connections.

    This class ensures that only one serial port connection is active at a time
    and provides methods for opening, closing, and communicating with the port.
    It also handles asynchronous data acquisition using the readyRead signal.
    """

    # Signals
    error_occurred = Signal(str)
    connection_changed = Signal(bool)
    data_received = Signal(list)  # Signal emitted when valid data is received

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SerialPortManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        super().__init__()
        self._serial_port = QSerialPort()
        self._port_name = ""
        self._baud_rate = Settings.BaudRate
        self._buffer = ""
        self._data_buffer = deque(maxlen=1000)  # Buffer for storing processed data
        self._mutex = QMutex()  # Mutex for thread-safe access to the data buffer
        self._last_valid_data = None
        self._initialized = True

        # Connect the readyRead signal to the data handler
        self._serial_port.readyRead.connect(self._handle_ready_read)

    @property
    def is_open(self):
        """Check if the serial port is open."""
        return self._serial_port.isOpen()

    @property
    def port_name(self):
        """Get the current port name."""
        return self._port_name

    def configure_port(self, port_name):
        """
        Configure the serial port with the specified port name.

        Args:
            port_name (str): The name of the port to configure

        Returns:
            bool: True if configuration was successful, False otherwise
        """
        try:
            # Close the port if it's already open
            if self._serial_port.isOpen():
                self._serial_port.close()

            self._port_name = port_name

            # Configure the port
            self._serial_port.setPortName(self._port_name)
            self._serial_port.setBaudRate(self._baud_rate)
            self._serial_port.setDataBits(QSerialPort.Data8)
            self._serial_port.setParity(QSerialPort.NoParity)
            self._serial_port.setStopBits(QSerialPort.OneStop)
            self._serial_port.setFlowControl(QSerialPort.NoFlowControl)

            return True

        except Exception as e:
            self.error_occurred.emit(f"Error configuring port: {str(e)}")
            return False

    def open(self):
        """
        Open the serial port.

        Returns:
            bool: True if the port was successfully opened, False otherwise
        """
        if not self._port_name:
            self.error_occurred.emit("No port selected")
            return False

        try:
            # Open the port
            if not self._serial_port.open(QSerialPort.ReadWrite):
                error_msg = f"Failed to open port {self._port_name}: {self._serial_port.errorString()}"
                self.error_occurred.emit(error_msg)
                return False

            self.connection_changed.emit(True)
            return True

        except Exception as e:
            self.error_occurred.emit(f"Error opening port: {str(e)}")
            return False

    def close(self):
        """Close the serial port."""
        if self._serial_port.isOpen():
            self._serial_port.close()
            self.connection_changed.emit(False)

    def write(self, data):
        """
        Write data to the serial port.

        Args:
            data (str): The data to write to the port

        Returns:
            bool: True if the data was successfully written, False otherwise
        """
        if not self._serial_port.isOpen():
            return False

        try:
            # Convert string to bytes and write to port
            bytes_written = self._serial_port.write(data.encode('utf-8'))
            return bytes_written > 0

        except Exception as e:
            self.error_occurred.emit(f"Error writing to port: {str(e)}")
            return False

    def _is_valid_number(self, value):
        """
        Check if a string can be converted to a float.

        Args:
            value (str): The string to check

        Returns:
            bool: True if the string can be converted to a float, False otherwise
        """
        # Check if the string is just a minus sign
        if value == '-':
            return False

        try:
            float(value)
            return True
        except ValueError:
            return False


    def _handle_ready_read(self):
        try:
            # Read all available raw bytes
            rx = self._serial_port.readAll().data()

            # Decode safely (ignore junk bytes like 0xC0)
            rx_serial = rx.decode('utf-8', errors='ignore')

            # Append to buffer
            self._buffer += rx_serial

            # Process lines in buffer
            self.read_and_process_data()

        except Exception as e:
            self.error_occurred.emit(f"Error processing serial data: {str(e)}")


    def get_latest_data(self):
        """
        Get the latest valid data from the buffer.

        Returns:
            list: The latest valid data, or None if no valid data is available
        """
        # First try to read directly from the serial port
        direct_data = self.read_and_process_data()
        if direct_data:
            return direct_data

        # If direct read fails, return the last valid data from the buffer
        with QMutexLocker(self._mutex):
            if self._last_valid_data:
                return self._last_valid_data.copy()
            else:
                return None

    def read_and_process_data(self):
        """
        Process the buffered serial data.
        Keeps incomplete lines until the next chunk arrives.
        Emits only valid numeric packets (8 floats).
        """
        try:
            # Split buffer into lines
            lines = self._buffer.split("\n")
            # Keep the last line (might be incomplete)
            self._buffer = lines[-1]

            for line in lines[:-1]:
                line = line.strip()
                if not line:
                    continue

                # Split by comma
                values = line.split(",")

                # Expect exactly 8 values from Spikeling
                if len(values) == 8:
                    try:
                        # Convert to floats
                        floats = [float(v) for v in values]
                        # Emit as list
                        self.data_received.emit(floats)
                    except ValueError:
                        # Skip bad numeric conversion
                        continue

        except Exception as e:
            self.error_occurred.emit(f"Error processing buffered data: {str(e)}")

    def get_data_buffer(self):
        """
        Get a copy of the entire data buffer.

        Returns:
            list: A copy of the data buffer
        """
        with QMutexLocker(self._mutex):
            return list(self._data_buffer)

    def clear_data_buffer(self):
        """
        Clear the data buffer.
        """
        with QMutexLocker(self._mutex):
            self._data_buffer.clear()
            self._last_valid_data = None

    def clear_buffer(self):
        """
        Clear the input buffer.
        """
        self._buffer = ""
        self.clear_data_buffer()

    def read_all(self):
        """
        Read all available data from the serial port.

        This method is maintained for backward compatibility.
        It's recommended to use the asynchronous approach with the readyRead signal instead.

        Returns:
            bytes: The data read from the port, or None if an error occurred
        """
        if not self._serial_port.isOpen():
            return None

        try:
            return self._serial_port.readAll().data()

        except Exception as e:
            self.error_occurred.emit(f"Error reading from port: {str(e)}")
            return None

    def bytes_available(self):
        """
        Get the number of bytes available to read from the serial port.

        This method is maintained for backward compatibility.
        It's recommended to use the asynchronous approach with the readyRead signal instead.

        Returns:
            int: The number of bytes available, or 0 if the port is not open
        """
        if not self._serial_port.isOpen():
            return 0

        return self._serial_port.bytesAvailable()

    def get_serial_port(self):
        """
        Get the underlying QSerialPort object.

        Returns:
            QSerialPort: The serial port object
        """
        return self._serial_port


# Create a global instance of the serial port manager
serial_manager = SerialPortManager()
