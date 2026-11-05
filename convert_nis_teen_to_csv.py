"""Convert the NIS-Teen public-use .DAT files (fixed-width text) to CSV.

Each year's folder ships a SAS script whose INPUT block lists every column
as `@<start position> <NAME> <$><width>.<decimals>`. This reads that layout,
slices each line of the .DAT file at those positions, and writes one CSV per
year. Missing values ("." or blank) become empty cells, which pandas reads
as NaN.

Usage (from the SI-670-class-project folder):
    python3 convert_nis_teen_to_csv.py              # every year
    python3 convert_nis_teen_to_csv.py 2023 2024    # just these years

Output: csv/nisteen_<year>.csv next to this script.
"""

import csv
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "248453-V2")
OUT_DIR = os.path.join(HERE, "csv")

COLUMN = re.compile(r"@\s*(\d+)\s+([A-Za-z_]\w*)\s+\$?\s*(\d+)\.\d*")


def read_layout(sas_path):
    """[(name, start, end)] from the SAS INPUT block, 0-based and end-exclusive."""
    with open(sas_path, encoding="latin-1") as f:
        text = f.read()
    block = re.search(r"\bINPUT\b(.*?);", text, re.S | re.I)
    if not block:
        raise ValueError(f"No INPUT block in {sas_path}")
    return [(name, int(pos) - 1, int(pos) - 1 + int(width)) for pos, name, width in COLUMN.findall(block.group(1))]


def convert_year(year_dir):
    year = os.path.basename(year_dir)
    sas_path = glob.glob(os.path.join(year_dir, "*.[sS][aA][sS]"))[0]
    dat_path = glob.glob(os.path.join(year_dir, "*.[dD][aA][tT]"))[0]
    layout = read_layout(sas_path)
    out_path = os.path.join(OUT_DIR, f"nisteen_{year}.csv")

    rows = 0
    with open(dat_path, encoding="latin-1", newline="") as src, open(out_path, "w", newline="") as dst:
        writer = csv.writer(dst)
        writer.writerow([name for name, _, _ in layout])
        for line in src:
            line = line.rstrip("\r\n")
            if not line.strip():
                continue
            values = []
            for _, start, end in layout:
                value = line[start:end].strip()
                values.append("" if value == "." else value)
            writer.writerow(values)
            rows += 1
    print(f"{year}: {rows:,} rows x {len(layout)} columns -> {os.path.relpath(out_path, HERE)}")


def main():
    wanted = set(sys.argv[1:])
    year_dirs = sorted(glob.glob(os.path.join(DATA_DIR, "*", "[0-9][0-9][0-9][0-9]")))
    if wanted:
        year_dirs = [d for d in year_dirs if os.path.basename(d) in wanted]
    if not year_dirs:
        sys.exit(f"No matching year folders under {DATA_DIR}")
    os.makedirs(OUT_DIR, exist_ok=True)
    for year_dir in year_dirs:
        convert_year(year_dir)


if __name__ == "__main__":
    main()
