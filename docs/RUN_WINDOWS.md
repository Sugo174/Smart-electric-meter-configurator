# Running Smart Meter Configurator on Windows

[Русская версия](RUN_WINDOWS_RU.md) · [Project overview](../README.md)

## Before you start

The application requires:

- Windows 10/11 or 64-bit Windows 7;
- the application build for your Windows version;
- a supported EMIS-ELECTRA 977 DC electricity meter;
- an RS-485 adapter with its driver installed;
- meter wiring that follows the manufacturer's operating instructions.

Python installation is not required for packaged builds.

## First launch

1. Download the appropriate ZIP archive from
   [Releases](https://github.com/Sugo174/Smart-electric-meter-configurator/releases).
2. Extract the entire archive to a permanent folder
   where your Windows account has write access.
3. Keep all build files together.
   The Windows 10/11 build requires the `_internal` folder.
4. Connect the RS-485 adapter to the computer and the meter.
5. Run the application executable.
6. Select the meter configuration: single-channel or dual-channel.
7. Select the adapter's COM port and click Connect.
8. After connecting, check the device information and readings.

Before connecting, release the selected COM port in other applications.
Detected ports remain visible in the list even when they are busy.

## Disconnecting from the meter

Click Disconnect and wait for disconnection to complete.

If the application reports that polling is still stopping,
wait a moment and disconnect again.

After successful disconnection, the COM port can be used
by another application.

## Updating the application

The application checks GitHub for new releases at startup.
A manual check is available in the Program Settings menu.

Updates are installed manually:

1. Finish any meter operations and close the application.
2. Download the new version for your Windows version.
3. Extract it to a separate folder.
4. Start the new version and check the meter connection.

Do not mix files from different application versions
or builds for different operating systems.

## Troubleshooting

### The COM port is missing from the list

- Check the adapter's connection to the computer.
- Check the adapter and its port number in Windows Device Manager.
- Install the adapter driver if Windows has not recognized it.
- Click Refresh in the application.

### The COM port is listed, but the connection fails

- Disconnect other applications from the selected port.
- Check the meter's power supply and RS-485 wiring.
- Check the selected meter configuration.
- Verify the device address, baud rate, and parity.

A listed COM port means that Windows has detected the device.
It does not confirm that the port is available or that the meter responds.

### The application does not start

- Check that the build matches your Windows version.
- Extract the entire ZIP archive before running the application.
- Keep the executable together with all accompanying build files.
- For Windows 10/11, check that the `_internal` folder is present.
- If an error appears, save its full text.

### A newer version is not detected

Check your internet connection and access to GitHub.
If necessary, open the Releases page manually.

An update check failure does not prevent communication with the meter.

## Requesting help

Include:

- the application version and build;
- the Windows version;
- the meter configuration;
- the steps leading to the problem;
- the expected and actual behaviour;
- the full error text, if available.

If useful, include a screenshot or a short video.
Remove confidential information before sharing any materials.