import zipfile
from pathlib import Path

input_dir = Path("input")
zip_files = list(input_dir.glob("*.zip"))

if not zip_files:
    print("No zip files found in the input directory.")
else:
    archive_path = zip_files[0] # Get the first zip file
    print(f"Attempting to read: {archive_path}")
    try:
        with zipfile.ZipFile(archive_path, 'r') as zf:
            print(f"Contents of {archive_path.name}:")
            for name in zf.namelist():
                print(name)
    except zipfile.BadZipFile:
        print(f"Error: {archive_path.name} is not a valid ZIP file or is corrupted.")
    except FileNotFoundError:
        print(f"Error: {archive_path.name} not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")