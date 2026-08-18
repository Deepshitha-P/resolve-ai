import os
import glob
import time

files_to_check = [
    "frontend/index.html",
    "frontend/script.js",
    "frontend/style.css",
    "pipeline/stage18_analytics_v2.py"
]

# Find parquet files recursively in data/
parquet_files = glob.glob("data/**/*.parquet", recursive=True)
files_to_check.extend(parquet_files)

for f in files_to_check:
    if os.path.exists(f):
        sz = os.path.getsize(f)
        mt = os.path.getmtime(f)
        print(f"File: {f} | Size: {sz:,} bytes | Modified: {time.ctime(mt)}")
    else:
        print(f"File: {f} | Does not exist!")
