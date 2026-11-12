# Building Windows packages

## Build variants

The project provides two separate 64-bit Windows builds:

| Target system | Python | Dependencies | Build recipe |
|---|---|---|---|
| Windows 10/11 | 3.14 | `requirements.txt` | `Smart-Meter-Configurator.spec` |
| Windows 7 | 3.8.10 | `requirements-win7.txt` | `Smart-Meter-Configurator-Windows-7.spec` |

Run all commands below in PowerShell from the repository root.

The Windows 7 package can be built on Windows 10/11 using
Python 3.8.10. Compatibility must also be checked on Windows 7.

Keep the two Python environments separate.

## Prepare the Windows 10/11 environment

Install 64-bit Python 3.14, then run:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install PyInstaller==6.21.0
```

## Prepare the Windows 7 environment

Install 64-bit Python 3.8.10, then run:

```powershell
py -3.8 -m venv .venv-win7
.\.venv-win7\Scripts\python.exe -m pip install -r requirements-win7.txt
```

The Windows 7 requirements include the pinned PyInstaller
and hook versions used for that build.

Environment activation is not required: each command uses
the appropriate environment's Python executable directly.

## Run tests

Check both environments before building:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests
.\.venv-win7\Scripts\python.exe -B -m unittest discover -s tests
```

Automated tests do not replace communication checks
with a real meter.

## Build and package Windows 10/11

```powershell
.\.venv\Scripts\python.exe build_release.py windows
```

## Build and package Windows 7

```powershell
.\.venv-win7\Scripts\python.exe build_release.py win7
```

The script reads `APP_VERSION` from `constants.py`,
runs PyInstaller, creates a ZIP archive, and checks its integrity.

Build folders are created in `dist/` or `dist-win7/`.
Release archives are created in `releases/`.

Output names include the application version automatically.
The Windows 7 x64 variant uses the `-Windows-7` suffix.
For Windows 7 x86, create a separate virtual environment with 32-bit Python
3.8.10, install `requirements-win7.txt` there, then run
`build_release.py win7-x86` with that interpreter. The ZIP uses the
`-Windows-7-x86` suffix.

Existing release archives are not overwritten.
Before rebuilding the same version, move the previous archive
to a backup location.

## Verify the packages

Run the executable from each output folder and check:

- the displayed application version;
- connection to a supported meter;
- reading of device information and measurements;
- disconnection and release of the COM port;
- reconnection after another application has used the port.

Check the Windows 7 package on an actual Windows 7 system.
Running it on Windows 10/11 alone does not verify Windows 7 compatibility.

Keep all accompanying files together. The Windows 10/11
package requires its `_internal` directory.

## Prepare a new release

1. Update `APP_VERSION` in `constants.py`.
2. Add a changelog entry describing the changes.
3. Run tests in both Python environments.
4. Run `build_release.py` for all three Windows targets.
5. Extract both generated ZIP archives into separate test folders.
6. Verify application startup, icons, and communication with a meter.
7. Check the Windows 7 package on Windows 7.
8. Commit and push the source and documentation changes.
9. Create a GitHub Release from the intended commit.
   Use `v` followed by `APP_VERSION` as the tag.
10. Attach both generated ZIP archives from `releases/`.
11. Publish a regular release and mark it as the latest release.
12. Verify both downloads and update detection
    from the previous application version.

The build recipes have permanent filenames.
Executable, folder, and archive names are generated from
`APP_VERSION`; do not edit them manually for each release.

Build folders, Python environments, and release ZIP archives
must remain outside version control.
Commit the `.spec` build recipes and `build_release.py`.

The application checks the latest published GitHub Release.
It opens the release page for manual downloading;
it does not install updates automatically.