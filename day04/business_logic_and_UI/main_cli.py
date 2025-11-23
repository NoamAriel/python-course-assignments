import sys
import os

# Check for necessary logic files before running
try:
    # Logic imports
    from ncbi_fibroin_logic import run_ncbi_search_and_classification
    # Persistence/Output imports
    from output_handler import save_results_to_files
except ImportError as e:
    print("\n[FATAL ERROR] Required logic or output files are missing.")
    print(f"Ensure that 'caddisfly_scraper.py', 'ncbi_fibroin_logic.py', and 'output_handler.py' are present.")
    print(f"Missing import: {e.name}")
    sys.exit(1)

def run_scraper_cli():
    """
    Main execution function that runs the scraper logic and saves the results.
    """
    print("--- Starting NCBI Fibroin Scraper CLI ---")

    try:
        # Step A: Run the core logic (Data fetch, classification, structure mapping)
        results, path_map = run_ncbi_search_and_classification()
        
        if not results:
            print("\nWARNING: Scraper returned no data. No files will be saved.")
            return

        # Step B: Save the results to the file system (Persistence/Output)
        save_results_to_files(results, path_map)
        
    except Exception as e:
        print(f"\nFATAL ERROR during CLI execution: {e}")
        
    print("--- CLI Execution Finished ---")


if __name__ == "__main__":
    # Check for the existence of the three required files before execution
    if not all(os.path.exists(f) for f in ['caddisfly_scraper.py', 'ncbi_fibroin_logic.py', 'output_handler.py']):
         print("\n[FATAL ERROR] Cannot run. One or more required Python files are missing.")
         print("Ensure 'caddisfly_scraper.py', 'ncbi_fibroin_logic.py', and 'output_handler.py' are available.")
         sys.exit(1)
         
    run_scraper_cli()