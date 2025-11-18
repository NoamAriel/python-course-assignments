import os
import shutil
import glob

def clean_project_artifacts():
    """
    Recursively finds and deletes common Python and testing artifacts 
    like __pycache__, .pyc files, and pytest cache folders.
    """
    # List of files and folders to target for deletion
    # '**/' means search recursively in all subdirectories
    cleanup_patterns = [
        '**/__pycache__',        # The notorious Python cache directory
        '**/*.pyc',              # Bytecode files that may exist outside the cache
        '**/.pytest_cache',      # Pytest's internal cache directory
        '**/.coverage',          # Code coverage output file
        '**/htmlcov',            # Code coverage report directory
        '**/.mypy_cache',        # MyPy type checker cache
    ]

    print("Starting project cleanup...")
    deleted_count = 0

    for pattern in cleanup_patterns:
        # Use glob.glob to find all matching paths recursively
        for path in glob.glob(pattern, recursive=True):
            try:
                if os.path.isdir(path):
                    # For directories, use shutil.rmtree for safe recursive deletion
                    shutil.rmtree(path)
                    print(f"🧹 Removed directory: {path}")
                    deleted_count += 1
                elif os.path.isfile(path):
                    # For individual files
                    os.remove(path)
                    print(f"🗑️ Removed file: {path}")
                    deleted_count += 1
            except OSError as e:
                # Handle cases where deletion fails (e.g., file is in use)
                print(f"🚨 Error removing {path}: {e}")

    if deleted_count == 0:
        print("✅ Cleanup complete. No cache artifacts found.")
    else:
        print(f"\n✨ Cleanup finished. Total {deleted_count} artifacts removed.")

if __name__ == "__main__":
    clean_project_artifacts()