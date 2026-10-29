# Smart Meter Configurator

[![Python tests](https://github.com/Sugo174/Smart-electric-meter-configurator/actions/workflows/tests.yml/badge.svg)](https://github.com/Sugo174/Smart-electric-meter-configurator/actions/workflows/tests.yml)
 
Desktop application for configuration, diagnostics, and commissioning of smart electricity meters.

## Table of Contents

- [Overview](#overview)
- [Download and Run](#download-and-run)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Project Goals](#project-goals)
- [Current Status](#current-status)
- [Media](#media)
- [License](#license)

## Overview
 
Smart Meter Configurator is a Python-based desktop application designed for field engineers to simplify smart meter setup, diagnostics, and maintenance.
It provides automatic communication parameter detection, real-time monitoring, device configuration, and multilingual support through a streamlined interface optimized for industrial environments.

## Download and Run

### Ready-to-Use Windows Versions

Choose the build for your operating system:

- **Windows 10/11:** [Smart-Meter-Configurator-v1.11.zip](https://github.com/Sugo174/Smart-electric-meter-configurator/releases/download/v1.11/Smart-Meter-Configurator-v1.11.zip)
- **Windows 7 (64-bit):** [Smart-Meter-Configurator-v1.11-Windows-7.zip](https://github.com/Sugo174/Smart-electric-meter-configurator/releases/download/v1.11/Smart-Meter-Configurator-v1.11-Windows-7.zip)

1. Download and extract the entire archive.
2. Connect the smart meter through an RS-485 adapter.
3. Run the executable from the extracted folder.

Keep all extracted files and folders together. The Windows 10/11 build
requires the `_internal` folder. Python installation is not required
for either packaged build.

See the [latest release](https://github.com/Sugo174/Smart-electric-meter-configurator/releases/latest)
for release notes and downloads.


### Running from Source

Requirements:

- Windows
- Python 3.10+
- RS-485 adapter
- Supported smart electricity meter

Clone the repository and install the dependencies:

```bash
git clone https://github.com/Sugo174/Smart-electric-meter-configurator.git
cd Smart-electric-meter-configurator
pip install -r requirements.txt
```

Start the application:

```bash
python gui.py
```

 
## Key Features
 
### Automatic Communication Parameter Discovery
 
The application can automatically detect:
- Device address
- Baud rate
- Parity settings
 
This allows engineers to establish communication with a meter without prior knowledge of its current communication parameters, significantly reducing commissioning time and setup complexity.
 
### Meter Configuration
 
- Support for single-channel meters
- Support for dual-channel meters
- Modbus communication parameter configuration
- Device address configuration
- Sensitivity adjustment
- Threshold configuration

### Pulse Output Constant

- Select the pulse output constant from the supported values:
  1000, 500, 200, 100, 50, 25, 20, 10 or 5 imp/kWh.
- A single-channel meter uses channel A. A dual-channel meter has
  independent settings for channels A and B.
- Selecting a value writes it to the meter and checks it by reading it back.

### Device Information and Barcode Auto-fill

The Device Information tab lets users edit the serial number,
manufacturer, meter type, metrological software version and date.
A manually entered serial number must contain exactly 12 digits.

Auto-fill accepts a scanned or manually entered serial number in the
`977 C P YY MM SSS` format. Press Enter or select **Apply** to start.
The application synchronizes the meter clock with the PC and fills in:

- The entered serial number.
- Manufacturer: `EMIS`.
- Meter type: `EE977`.
- Metrological software version: `EE977 v.1.01.00`.
- Date: the date the serial number was entered or scanned.

The fields are written and checked one at a time. If an error occurs,
some fields may already have been written.

### Time Management
 
- Manual date and time configuration
- Synchronization with PC system time

### Serial Number Decoding

The Device Information tab decodes valid 12-digit serial numbers for EMIS-ELECTRA 977 meters.

- Meter series
- Single-channel or dual-channel configuration
- DC or AC power supply
- Manufacturing month and year
- Number in series

### Tariff Schedule Configuration

The application can read, edit, validate, and write daily tariff schedules directly to the meter.

- Supports from 1 to 14 tariff periods
- Supports tariff numbers from 1 to 4
- Requires the first period to start at `00:00`
- Validates strictly increasing start times before writing
- Reads the schedule back from the meter after a successful write

The meter stores 14 schedule records. When fewer periods are configured, the application automatically repeats the final period to fill the required register block.

### Update Checks

The application checks the latest published GitHub Release after startup.

- Shows an update dialog only when a newer version is available
- Opens the corresponding GitHub Release page for downloading
- Provides a manual update check through the Program Settings menu
- Does not interrupt startup when the internet connection or GitHub is unavailable
 
### Real-Time Monitoring
 
- Voltage monitoring
- Current monitoring
- Power monitoring
- Frequency monitoring
- Energy consumption monitoring
 
### Protected Operations
 
- Energy reset functionality
- Confirmation code required before clearing stored energy values
- Warning prompt before the reset operation
 
### Supported Devices

The application is designed and tested for EMIS-ELECTRA 977 DC smart electricity meters:

- Single-channel configuration
- Dual-channel configuration
- Modbus RTU communication over RS-485
- Automatic detection of device address, baud rate, and parity

The automatic scan checks Modbus addresses from `1` to `10` and the following baud rates:

- 1200
- 2400
- 4800
- 9600
- 19200

Support for other meter models is not guaranteed. Additional devices require compatible register maps and corresponding changes to the communication logic.

### Operational Safety

The application can write configuration parameters directly to the connected meter.

- Verify the selected meter type before changing any settings.
- Follow the meter manufacturer's wiring and operating instructions.
- Do not disconnect the meter or RS-485 adapter while parameters are being written.
- Energy reset permanently clears stored energy values and requires confirmation.
 
### Multilingual Interface
 
- English
- Russian
- Simplified Chinese
 
Designed for easy extension with additional languages.
 
### User Experience
 
- Modern desktop UI
- Visual meter type selection
- Optimized commissioning workflow
- Simplified navigation for field use
 
## Technology Stack
 
- Python
- Tkinter
- sv_ttk
- Modbus RTU
- RS-485 Communication

## Project Structure

- `gui.py` — Application entry point and graphical user interface.
- `device.py` — Modbus RTU communication and meter operations.
- `constants.py` — Register addresses, communication parameters, and shared constants.
- `requirements.txt` — Python dependencies required to run the source code.
- `CHANGELOG.md` — Version history and notable changes.
- `icons/` — Interface icons.
- `images/` — Smart meter images used by the application.
- `assets/screenshots/` — Screenshots displayed in this README.
- `assets/video/` — Demonstration video.
- `LICENSE` — MIT License terms.
 
## Project Goals

Reduce commissioning time and eliminate manual communication setup by introducing automatic parameter detection and a structured configuration environment for smart meters.
 
## Current Status
 
✔ Fully Functional
 
✔ Tested on Real Devices
 
✔ Multilingual Interface
 
✔ Ready for Field Use

## Media

### Screenshots

#### Connection

![Automatic meter connection and parameter detection](assets/screenshots/Connection.PNG)

#### Device Information

![Connected smart meter information](assets/screenshots/Device_Info.PNG)

#### Date and Time

![Smart meter date and time configuration](assets/screenshots/Date&Time.PNG)

#### Current Values

![Real-time electrical measurements](assets/screenshots/Current_Values.PNG)

#### Device Settings

![Smart meter configuration settings](assets/screenshots/Device_Settings.PNG)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
