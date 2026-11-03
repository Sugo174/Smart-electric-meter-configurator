# Building Windows packages

## Build variants

The project provides two separate 64-bit Windows builds:

| Target system | Python | Dependencies | Build recipe |
|---|---|---|---|
| Windows 10/11 | 3.14 | `requirements.txt` | `Smart-Meter-Configurator-v1.11.1.spec` |
| Windows 7 | 3.8.10 | `requirements-win7.txt` | `Smart-Meter-Configurator-v1.11.1-Windows-7.spec` |

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

## Build the Windows 10/11 package

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm --distpath dist --workpath build Smart-Meter-Configurator-v1.11.1.spec
```

Output:

```text
dist/Smart-Meter-Configurator-v1.11.1/
```

## Build the Windows 7 package

```powershell
.\.venv-win7\Scripts\python.exe -m PyInstaller --clean --noconfirm --distpath dist-win7 --workpath build-win7 Smart-Meter-Configurator-v1.11.1-Windows-7.spec
```

Output:

```text
dist-win7/Smart-Meter-Configurator-v1.11.1-Windows-7/
```

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

## Create release archives

Create ZIP archives containing the complete build folders:

```powershell
New-Item -ItemType Directory -Path .\releases -Force | Out-Null

Compress-Archive -LiteralPath .\dist\Smart-Meter-Configurator-v1.11.1 -DestinationPath .\releases\Smart-Meter-Configurator-v1.11.1.zip

Compress-Archive -LiteralPath .\dist-win7\Smart-Meter-Configurator-v1.11.1-Windows-7 -DestinationPath .\releases\Smart-Meter-Configurator-v1.11.1-Windows-7.zip
```

If an archive with the same name already exists, move it
to a backup location or remove it before running the command.

Extract each archive to a separate test folder and verify
that the application starts from the extracted package.

Do not include local configuration files, temporary files,
or unrelated build artifacts in public release archives.

## Prepare a new release

The commands above describe version 1.11.1.
For a future release:

1. Update `APP_VERSION` in `constants.py`.
2. Rename both `.spec` files for the new version.
3. Update both `name` values inside each `.spec` file:
   the executable name and the output folder name.
4. Update the changelog, download links in both README files,
   and the version-specific examples in this build guide.
5. Run tests, build both packages, and verify them.
6. Create and check both ZIP archives.
7. Commit and push the source and documentation changes.
8. Create a GitHub Release from the intended commit,
   using a matching version tag such as `v1.11.1`.
9. Attach both ZIP archives and check their names carefully.
10. Publish a regular release and mark it as the latest release.
11. Verify both download links and update detection
    from the previous application version.

Build folders, Python environments, and release ZIP archives
must remain outside version control. The `.spec` build recipes
must be committed.

The application checks the latest published GitHub Release.
It opens the release page for manual downloading;
it does not install updates automatically.