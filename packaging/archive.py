"""Archive a portable distribution and write its SHA-256 checksum."""
import argparse
import hashlib
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extract", action="store_true")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    if args.extract:
        shutil.unpack_archive(args.source, args.destination, filter="fully_trusted")
        return
    extension = ".zip" if args.destination.suffix == ".zip" else ".tar.gz"
    archive_format = "zip" if extension == ".zip" else "gztar"
    archive = Path(shutil.make_archive(str(args.destination).removesuffix(extension), archive_format, args.source))
    with archive.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    archive.with_name(archive.name + ".sha256").write_text(f"{digest}  {archive.name}\n", encoding="ascii")


if __name__ == "__main__":
    main()
