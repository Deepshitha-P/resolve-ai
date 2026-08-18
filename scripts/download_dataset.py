import os
import sys
import subprocess
from pathlib import Path

def check_kaggle_credentials():
    kaggle_dir = Path.home() / ".kaggle"
    kaggle_json = kaggle_dir / "kaggle.json"
    
    has_env = os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY")
    
    if not kaggle_json.exists() and not has_env:
        print("="*60)
        print("ERROR: Kaggle credentials not found!")
        print("To download the dataset, you need to authenticate with Kaggle.")
        print("1. Go to https://www.kaggle.com/<your-username>/account")
        print("2. Click 'Create New API Token' to download kaggle.json")
        print(f"3. Place it at {kaggle_json} or set env vars KAGGLE_USERNAME and KAGGLE_KEY")
        print("="*60)
        sys.exit(1)

def download_dataset():
    data_dir = Path("./data/raw")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    print("Downloading dataset 'thoughtvector/customer-support-on-twitter'...")
    try:
        subprocess.run(
            ["kaggle", "datasets", "download", "-d", "thoughtvector/customer-support-on-twitter", "-p", str(data_dir), "--unzip"],
            check=True
        )
    except subprocess.CalledProcessError:
        print("Error during download. Ensure Kaggle API is correctly configured.")
        sys.exit(1)
        
    csv_file = data_dir / "twcs.csv"
    if not csv_file.exists():
        print(f"Error: Expected {csv_file} not found after download.")
        sys.exit(1)
        
    size_mb = csv_file.stat().st_size / (1024 * 1024)
    
    print("Counting rows (this may take a moment)...")
    # Simple row count
    row_count = 0
    with open(csv_file, 'rb') as f:
        for _ in f:
            row_count += 1
            
    # Subtract header
    row_count -= 1 
            
    print("="*60)
    print("DOWNLOAD COMPLETE")
    print(f"File: {csv_file}")
    print(f"Size: {size_mb:.2f} MB")
    print(f"Rows: {row_count:,}")
    print("="*60)

if __name__ == "__main__":
    check_kaggle_credentials()
    download_dataset()
