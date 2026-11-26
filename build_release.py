"""Build and package one Windows release variant."""

import argparse
import os
from pathlib import Path
import struct
import subprocess
import sys
from tempfile import TemporaryDirectory
import zipfile

from constants import APP_VERSION


PROJECT_ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(
        description="Build a Windows release package."
    )
    parser.add_argument(
        "target",
        choices=("windows", "win7", "win7-x86"),
        help="windows: Windows 10/11 x64; win7: Windows 7 x64; win7-x86: Windows 7 x86",
    )
    parser.add_argument(
        "--emis-internal", action="store_true",
        help="Build a private EMIS package with the engineer key. Never publish this package.",
    )
    args = parser.parse_args()

    if args.target in ("win7", "win7-x86"):
        required_python = (3, 8)
        spec_name = "Smart-Meter-Configurator-Windows-7.spec"
        dist_name = "dist-win7"
        work_name = "build-win7"
        suffix = "-Windows-7"
        if args.target == "win7-x86":
            dist_name += "-x86"
            work_name += "-x86"
            suffix += "-x86"
    else:
        required_python = (3, 14)
        spec_name = "Smart-Meter-Configurator.spec"
        dist_name = "dist"
        work_name = "build"
        suffix = ""

    if sys.version_info[:2] != required_python:
        parser.error(
            "This target requires Python "
            + ".".join(map(str, required_python))
        )

    required_bits = 32 if args.target == "win7-x86" else 64
    if struct.calcsize("P") * 8 != required_bits:
        parser.error(f"This target requires {required_bits}-bit Python")

    output_root = PROJECT_ROOT
    if args.emis_internal:
        output_root = Path(os.environ["LOCALAPPDATA"]) / "EMIS" / "Integrator" / "internal-builds"
        suffix += "-EMIS-Internal"
        dist_name += "-internal"

    build_name = f"Smart-Meter-Configurator-v{APP_VERSION}{suffix}"
    output_folder = output_root / dist_name / build_name
    archive_path = output_root / "releases" / f"{build_name}.zip"

    if archive_path.exists():
        parser.error(
            f"Archive already exists: {archive_path}\n"
            "Move it to a backup location before building again."
        )

    command = [
        sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm",
        "--distpath", str(output_root / dist_name),
    ]
    environment = os.environ.copy()
    environment.pop("EMIS_INTERNAL_KEY_MODULE_DIR", None)
    if args.emis_internal:
        from snapshot_windows_key import load_windows_key

        private_key = load_windows_key()
        with TemporaryDirectory(prefix="emis-internal-build-") as temp:
            work = Path(temp)
            (work / "_emis_internal_snapshot_key.py").write_text(
                f"PRIVATE_KEY = {bytes(private_key)!r}\n", encoding="ascii"
            )
            environment["EMIS_INTERNAL_KEY_MODULE_DIR"] = str(work)
            subprocess.run(
                [*command, "--workpath", str(work / "build"), spec_name],
                cwd=PROJECT_ROOT, env=environment, check=True,
            )
    else:
        subprocess.run(
            [*command, "--workpath", str(output_root / work_name), spec_name],
            cwd=PROJECT_ROOT, env=environment, check=True,
        )

    executable_path = output_folder / f"{build_name}.exe"
    if not executable_path.is_file():
        raise RuntimeError(
            f"Built executable not found: {executable_path}"
        )

    archive_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(
        archive_path,
        mode="x",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        for file_path in sorted(output_folder.rglob("*")):
            if file_path.is_file():
                archive.write(
                    file_path,
                    arcname=file_path.relative_to(
                        output_folder.parent
                    ).as_posix(),
                )

    with zipfile.ZipFile(archive_path, mode="r") as archive:
        damaged_file = archive.testzip()
        if damaged_file is not None:
            raise RuntimeError(
                f"Archive verification failed: {damaged_file}"
            )

    print(f"Release archive created: {archive_path}")

if __name__ == "__main__":
    main()