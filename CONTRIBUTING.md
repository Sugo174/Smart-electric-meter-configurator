# Contributing

## Reporting a problem

Before opening an issue, check
[Running on Windows](docs/RUN_WINDOWS.md)
or the [Russian instructions](docs/RUN_WINDOWS_RU.md).

Include:

- application version and Windows build;
- Windows version;
- meter model and single-channel or dual-channel configuration;
- steps to reproduce the problem;
- expected and actual behaviour;
- sanitized error text or screenshots.

Do not publish customer information, confidential device data,
or internal network details.

## Development setup

Follow the source setup instructions in
[README.ru.md](README.ru.md#запуск-из-исходников).

Keep the main Python environment separate from the
Python 3.8 environment used for Windows 7.

Build instructions are available in
[docs/BUILD_WINDOWS.md](docs/BUILD_WINDOWS.md).

## Code changes

- Keep changes focused on one problem or feature.
- Preserve compatibility with Python 3.8 for shared application code.
- Update Russian, English, and Chinese interface text when applicable.
- Check register addresses, data types, scaling, and access permissions
  against the documentation for the supported meter.
- Preserve confirmation and read-back checks for write operations.
- Keep Tkinter widget updates in the main interface thread.
- Update documentation when behaviour changes.
- Add or update automated tests when they help verify the change.

## Validation

Run the tests in both prepared environments:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests
.\.venv-win7\Scripts\python.exe -B -m unittest discover -s tests
```

Changes affecting meter communication also require checks
with a real supported device. Describe which checks were performed
and which remain unverified.

## Commits and pull requests

Use clear English commit messages.

Explain the problem, the resulting behaviour,
and how the change was checked.

Do not commit Python environments, local configuration,
build output, or release archives.
Commit the `.spec` build recipes when they change.