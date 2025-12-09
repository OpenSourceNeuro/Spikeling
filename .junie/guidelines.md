# Spikeling-V2 Development Guidelines

This document provides essential information for developers working on the Spikeling-V2 project.

## Build/Configuration Instructions

### Environment Setup

1. **Python Environment**: The project requires Python 3.8 or newer.

2. **Dependencies**: Install all required dependencies using:
   ```bash
   pip install -r GUI/PyQt/requirements.txt
   ```

   Key dependencies include:
   - PySide6 (Qt for Python)
   - numpy and pandas (data manipulation)
   - pyqtgraph (for plotting)
   - pyserial (for serial communication)
   - scipy (scientific computing)
   - pyinstaller (for creating standalone executables)

### Running the Application

To run the application in development mode:
```bash
cd GUI/PyQt
python Main.py
```

### Building Standalone Executables

The project includes PyInstaller spec files for different platforms:

- **Windows**:
  ```bash
  cd GUI/PyQt
  pyinstaller Spikeling-win.spec
  ```

- **macOS**:
  ```bash
  cd GUI/PyQt
  pyinstaller Spikeling-mac.spec
  ```

- **Linux**:
  ```bash
  cd GUI/PyQt
  pyinstaller Spikeling-linux.spec
  ```

The executable will be created in the `dist` directory.

## Testing Information

### Testing Framework

The project uses Python's built-in `unittest` framework for testing. Tests should be placed in files with names starting with `test_`.

### Running Tests

To run a specific test file:
```bash
python test_file.py
```

To run all tests in the project:
```bash
python -m unittest discover
```

### Creating New Tests

1. Create a new file with a name starting with `test_`.
2. Import the `unittest` module and the components you want to test.
3. Create a class that inherits from `unittest.TestCase`.
4. Add test methods that start with `test_`.
5. Use assertion methods like `assertEqual`, `assertTrue`, etc. to verify behavior.

### Example Test

Here's a simple test for the `SerialPortManager` class:

```python
import unittest
import sys
import os

# Add the GUI/PyQt directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'GUI', 'PyQt'))

# Import the serial manager
from serial_manager import SerialPortManager

class TestSerialPortManager(unittest.TestCase):
    """Test cases for the SerialPortManager class."""

    def setUp(self):
        """Set up the test environment."""
        # Get the singleton instance
        self.manager = SerialPortManager()
        # Clear any existing data
        self.manager.clear_data_buffer()

    def test_singleton_pattern(self):
        """Test that SerialPortManager implements the singleton pattern correctly."""
        # Create another instance and verify it's the same object
        another_manager = SerialPortManager()
        self.assertIs(self.manager, another_manager, 
                     "SerialPortManager should implement the singleton pattern")

    def test_is_valid_number(self):
        """Test the _is_valid_number method."""
        # Valid numbers
        self.assertTrue(self.manager._is_valid_number("123"))
        self.assertTrue(self.manager._is_valid_number("-123"))
        self.assertTrue(self.manager._is_valid_number("123.456"))
        self.assertTrue(self.manager._is_valid_number("-123.456"))
        
        # Invalid numbers
        self.assertFalse(self.manager._is_valid_number("-"))
        self.assertFalse(self.manager._is_valid_number("abc"))
        self.assertFalse(self.manager._is_valid_number(""))
        self.assertFalse(self.manager._is_valid_number("123abc"))

if __name__ == '__main__':
    unittest.main()
```

## Additional Development Information

### Project Structure

- **GUI/PyQt/**: Contains the main application code
  - **Main.py**: Entry point for the application
  - **Spikeling_UI.py**: Generated UI code from Qt Designer
  - **NavigationButtons.py**: Handles navigation and button functionality
  - **Spikeling_graph.py**: Manages data visualization
  - **serial_manager.py**: Handles serial communication with the device
  - **Page*.py**: Different pages/screens of the application

### Code Style Guidelines

The project follows these coding conventions:

1. **Docstrings**: Use triple quotes for comprehensive docstrings that describe:
   - Class/method purpose
   - Parameters with types
   - Return values with types
   - Exceptions raised

2. **Naming Conventions**:
   - Classes: CamelCase (e.g., `SerialPortManager`)
   - Methods/Functions: snake_case (e.g., `get_latest_data`)
   - Variables: snake_case (e.g., `serial_port`)
   - Constants: UPPER_CASE (e.g., `BAUD_RATE`)

3. **Error Handling**: Use try/except blocks for robust error handling, especially for I/O operations.

4. **Comments**: Add comments for complex logic or non-obvious behavior.

### Serial Communication

The application communicates with the Spikeling hardware via serial port. The `SerialPortManager` class handles this communication using a singleton pattern to ensure only one instance manages the serial port.

Key aspects:
- Data is received asynchronously using Qt's signal/slot mechanism
- Thread-safe data handling with QMutex
- Data validation and processing before use

### GUI Architecture

The application uses PySide6 (Qt for Python) for the GUI:
- UI files are created with Qt Designer (.ui files)
- UI files are converted to Python code using the PySide6 UI compiler
- The application follows a modular design with separate classes for different functionality
- Custom widgets and plots are implemented using pyqtgraph