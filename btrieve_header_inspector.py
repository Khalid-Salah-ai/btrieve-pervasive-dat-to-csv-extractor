#!/usr/bin/env python3
"""
btrieve_header_inspector.py -- Free Open-Source CLI Inspector for Legacy Btrieve / Pervasive (.DAT / .BTR) File Headers.

Inspects File Control Record (FCR) metadata (version, page size, logical/physical record length,
declared record count, and key definitions) without requiring the Pervasive/Actian database engine.

Need to extract all data records, decode Packed Decimal/Money/Date fields, and map FILE.DDF / FIELD.DDF
dictionaries into clean CSVs offline?
Download the standalone Windows GUI Extractor (BtrieveExtractorPro):
https://khalidtech8.gumroad.com/l/2026
"""

import struct
import sys
import os


def inspect_btrieve_header(filepath: str) -> None:
    if not os.path.isfile(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    with open(filepath, "rb") as f:
        header = f.read(4096)

    file_size = os.path.getsize(filepath)
    print("=" * 64)
    print(f"Btrieve / Pervasive FCR Diagnostic Report")
    print("=" * 64)
    print(f"File Path           : {filepath}")
    print(f"File Size           : {file_size:,} bytes")

    if len(header) < 274:
        print("Status              : INVALID (File too small to contain an FCR header)")
        sys.exit(1)

    if header[:2] == b"FC":
        container = "Btrieve v6.x / Pervasive ('FC' Dual-FCR Container)"
        page_len = struct.unpack_from("<H", header, 0x08)[0]
        rec_len = struct.unpack_from("<H", header, 0x16)[0]
        phys_len = struct.unpack_from("<H", header, 0x18)[0]
        rec_count = (struct.unpack_from("<H", header, 0x1A)[0] << 16) | struct.unpack_from("<H", header, 0x1C)[0]
    elif header[:4] == b"\x00\x00\x00\x00":
        ver = (header[6] << 16) | header[7]
        container = f"Btrieve Pre-v6 ('v5-style' FCR, Version {ver})"
        page_len = struct.unpack_from("<H", header, 0x08)[0]
        rec_len = struct.unpack_from("<H", header, 0x16)[0]
        phys_len = struct.unpack_from("<H", header, 0x18)[0]
        rec_count = (struct.unpack_from("<H", header, 0x1A)[0] << 16) | struct.unpack_from("<H", header, 0x1C)[0]
    else:
        print(f"Status              : UNKNOWN SIGNATURE ({header[:4].hex()})")
        sys.exit(1)

    print(f"Container Format    : {container}")
    print(f"Page Length         : {page_len} bytes")
    print(f"Logical Record Len  : {rec_len} bytes")
    print(f"Physical Slot Len   : {phys_len} bytes")
    print(f"Declared Live Rows  : {rec_count:,} records")
    print("-" * 64)
    print("To extract all records to CSV offline (with FILE.DDF / FIELD.DDF column mapping):")
    print("-> Download BtrieveExtractorPro (Windows GUI): https://khalidtech8.gumroad.com/l/2026")
    print("=" * 64)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python btrieve_header_inspector.py <path_to_file.DAT>")
        sys.exit(1)
    inspect_btrieve_header(sys.argv[1])
