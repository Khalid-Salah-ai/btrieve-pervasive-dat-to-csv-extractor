# Legacy Btrieve / Pervasive `.DAT` & `.BTR` File Format Architecture & Offline CSV Extraction Guide

When migrating off legacy accounting, ERP, or DOS/Windows business systems (**Sage Timberline Office, Peachtree Accounting, DacEasy, ACCPAC Plus, Great Plains, or custom Btrieve 5.x / 6.x / Pervasive.SQL databases**), sysadmins and accountants often face a roadblock:
- The legacy 16-bit/32-bit **Btrieve / Pervasive.SQL / Actian Zen engine** is dead, unlicensed, or fails to install on modern 64-bit Windows 10/11/Server machines (`Error 2`, `Error 3012`, `MicroKernel Engine not running`).
- External data recovery firms demand **$1,500 – $5,000+** and require uploading confidential financial `.DAT` / `.BTR` files to third-party servers.

This repository documents the binary on-disk layout of **Btrieve File Control Records (FCR)** and **V1 Data Dictionary files (`FILE.DDF` & `FIELD.DDF`)**, and provides a free header inspection script alongside a **100% offline Windows GUI CSV Extractor**.

---

## 🚀 Instant Offline GUI Solution (Windows `.exe`)

If you don't want to write custom binary parsers and need to **preview or export your `.DAT` / `.BTR` tables to `.CSV` immediately on your local machine (100% Offline)**:

👉 **[Download Btrieve / Pervasive .DAT to CSV Extractor Pro (Windows Standalone .exe)](https://khalidtech8.gumroad.com/l/2026)**

* **Free 5-Row Local Preview Utility (`$0`):** Test your `.DAT` / `.BTR` files and `FILE.DDF` / `FIELD.DDF` dictionaries locally and inspect the first 5 extracted rows before paying a cent.
* **100% Offline & Zero Dependencies:** Runs as a standalone Windows executable (`BtrieveExtractorPro.exe`). No Pervasive engine, no ODBC drivers, and zero cloud uploads.
* **Native Accounting Type Decoder:** Automatically decodes Btrieve `DATE`, `TIME`, Packed BCD `DECIMAL`, `MONEY`, Zoned `NUMERIC`, `INTEGER`, `FLOAT`, and `STRING` (`CP1252`/`ASCII`) fields.
* **Automatic DDF Schema Mapping:** Point it to your folder containing `FILE.DDF` and `FIELD.DDF` to restore real table and column names automatically.

---

## 🔍 Free CLI Header Diagnostic Script (`btrieve_header_inspector.py`)

Included in this repository is `btrieve_header_inspector.py`, a zero-dependency Python 3 script that inspects the first 4 KB of any `.DAT` or `.BTR` file to verify whether it uses a pre-v6 (`v5-style`) or `v6.x` (`FC`) File Control Record.

```bash
python btrieve_header_inspector.py COMPANY.DAT
```

Sample output:
```text
================================================================
Btrieve / Pervasive FCR Diagnostic Report
================================================================
File Path           : INVOICE.DAT
File Size           : 1,048,576 bytes
Container Format    : Btrieve Pre-v6 ('v5-style' FCR, Version 4)
Page Length         : 1024 bytes
Logical Record Len  : 128 bytes
Physical Slot Len   : 130 bytes
Declared Live Rows  : 7,410 records
----------------------------------------------------------------
```

---

## 📐 Btrieve On-Disk Binary Layout Reference

### 1. Pre-v6 ("v5-Style") File Control Record (Page 0)
In Btrieve v3.x, v4.x, and v5.x files, Page 0 (`offset 0x0000`) is the File Control Record (FCR):

| Offset | Size | Type | Description |
| :--- | :--- | :--- | :--- |
| `0x0000` | 4 bytes | `uint32` | Magic signature (`00 00 00 00` for pre-v6 FCR) |
| `0x0006` | 2 bytes | `uint16 BE` | FCR version code (`3`, `4`, or `5`) |
| `0x0008` | 2 bytes | `uint16 LE` | Page size in bytes (multiple of 512: `512` .. `4096`) |
| `0x0010` | 4 bytes | `word-swapped u32` | Head pointer of the deleted/free record chain (`0xFFFFFFFF` if empty) |
| `0x0014` | 2 bytes | `uint16 LE` | Number of index keys (`key_count`) |
| `0x0016` | 2 bytes | `uint16 LE` | Logical record length (bytes per record payload) |
| `0x0018` | 2 bytes | `uint16 LE` | Physical slot length on disk |
| `0x001A` | 4 bytes | `word-swapped u32` | Total active (live) record count |
| `0x0106` | 2 bytes | `uint16 LE` | User flags (`0x0001` = variable-length, `0x0008` = compressed) |
| `0x0110` | `N * 30` | `KeyDef[]` | Array of 30-byte (`0x1E`) key segment definitions |

### 2. Btrieve v6.x (`FC` Signature) Dual-FCR Container
Btrieve 6.x introduced shadow paging and dual File Control Records:
- **Bytes `0x00..0x01`:** ASCII `"FC"` (`0x46 0x43`).
- **Page 0 and Page 1:** Both hold FCR structures. The active FCR is determined by comparing the signed 32-bit usage counter at `FCR + 0x04`.
- **Data Pages (`Page >= 2`):** Carry a 6-byte page header where `uint16` at `page_offset + 4` has high bit `0x8000` set for active data pages. Each record slot starts with a 2-byte status prefix (`0x0000` = deleted/free slot; non-zero = active record).

### 3. V1 Data Dictionary Layout (`FILE.DDF` & `FIELD.DDF`)
When `FILE.DDF` (97-byte records) and `FIELD.DDF` (32-byte records) are present:
- **`FILE.DDF` (`X$File`):**
  - `0..2`: `Xf$Id` (`uint16 LE` Table ID)
  - `2..22`: `Xf$Name` (20-byte space-padded ASCII table name)
  - `22..86`: `Xf$Loc` (64-byte relative path/filename of the `.DAT` file)
- **`FIELD.DDF` (`X$Field`):**
  - `0..2`: `Xe$Id` (`uint16 LE` Field ID)
  - `2..4`: `Xe$File` (`uint16 LE` Foreign key to `Xf$Id`)
  - `4..24`: `Xe$Name` (20-byte column name)
  - `24..25`: `Xe$DataType` (`uint8` Btrieve type code: `0`=String, `1`=Integer, `2`=Float, `3`=Date, `4`=Time, `5`=Decimal BCD, `6`=Money, `7`=Logical, `8`=Numeric, `10`=LString, `11`=ZString, `14`=Unsigned, `15`=AutoInc)
  - `25..27`: `Xe$Offset` (`uint16 LE` 0-based byte offset inside the record)
  - `27..29`: `Xe$Size` (`uint16 LE` column length in bytes)
  - `29..30`: `Xe$Dec` (`uint8` decimal scale / fractional digits)
  - `30..32`: `Xe$Flags` (`uint16 LE` bitflags, including bit 2 `0x0004` for nullable columns)

---

## 🛠️ Need Full Automated Recovery?
Download **[Btrieve / Pervasive .DAT to CSV Extractor Pro](https://khalidtech8.gumroad.com/l/2026)** to test your files with the free 5-row preview mode or unlock unlimited CSV exports.
