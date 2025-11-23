import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple, Any
import re
import os
from pathlib import Path
import time

# Use the new nested function for scraping the taxonomy
try:
    from caddisfly_scraper import get_trichoptera_taxonomy_structure
except ImportError:
    print("Error: Could not import get_trichoptera_taxonomy_structure.")
    print("Please ensure caddisfly_scraper.py is in the same directory.")
    exit()

# --- Configuration ---
NCBI_BASE_URL = "https://www.ncbi.nlm.nih.gov/protein/"
NCBI_EUTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
FIBROIN_TERM = "fibroin"
OUTPUT_ROOT_DIR = "ncbi_fibroin_sequences" # Root folder for all output
SLEEP_TIME = 0.5 # Pause between API calls to be polite

# --- Classification Constants ---
CHAIN_TYPES = {
    'heavy chain': ['heavy chain', 'fib-h', 'h-fibroin', 'h chain'],
    'light chain': ['light chain', 'fib-l', 'l-fibroin', 'l chain'],
    'others': [] # Default if no match is found
}
# The final result structure will now be keyed by Family, containing the nested classification:
# {Family: {'full sequence': {'heavy chain': [data...], ...}, 'partial sequence': {...}}}

# --- Utility Functions ---

def safe_filename(name: str, max_len=50) -> str:
    """Generates a safe filename/directory name from a string."""
    safe_name = re.sub(r'[\\/:*?"<>|]', '', name).strip()
    safe_name = safe_name.replace(' ', '_').replace('-', '_').replace('.', '').lower()
    return safe_name[:max_len]


def classify_protein_chain(name: str) -> str:
    """
    Classifies a protein based on its name into 'heavy chain', 'light chain', or 'others'.
    """
    name_lower = name.lower()
    for chain_type, keywords in CHAIN_TYPES.items():
        if chain_type == 'others':
            continue
        for keyword in keywords:
            if keyword in name_lower:
                return chain_type
    return 'others'


# --- Core Scraper Functions ---

def fetch_protein_sequence(accession_id: str) -> str:
    """
    Fetches the protein sequence using NCBI E-utilities (Efetch) for reliable FASTA output.
    """
    params = {
        'db': 'protein',
        'id': accession_id,
        'rettype': 'fasta',
        'retmode': 'text'
    }
    
    try:
        response = requests.get(NCBI_EUTILS_BASE_URL, headers=HEADERS, params=params, timeout=15)
        response.raise_for_status()
        content = response.text.strip()

        if not content.startswith('>'):
            return ""

        first_newline_index = content.find('\n')
        
        if first_newline_index == -1:
            return ""

        sequence_body = content[first_newline_index + 1:].upper()
        sequence = re.sub(r'[^A-Z*]', '', sequence_body)
            
        return sequence

    except requests.exceptions.RequestException as e:
        print(f"      ERROR: Could not fetch sequence for {accession_id} using E-utilities: {e}")
        return ""
    except Exception as e:
        print(f"      ERROR: Unexpected error during E-utilities fetch for {accession_id}: {e}")
        return ""


def fetch_and_parse_search_results(query: str) -> List[Tuple[str, str]]:
    """
    Searches NCBI Protein database and extracts accession ID and name for each result.
    """
    search_url = f"{NCBI_BASE_URL}?term={query}"
    
    print(f"    Searching NCBI for: '{query}'...")
    try:
        response = requests.get(search_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        results = set()
        # Look for various common result link classes and structures
        title_links = soup.select('a.pr-link, a.title, a[href^="/protein/"], a[data-entity-id]')

        for link in title_links:
            href = link.get('href')
            protein_name = link.get_text(strip=True)
            
            if href and protein_name:
                # Regex to extract accession ID (e.g., AAN02787.1)
                match = re.search(r'/protein/([A-Z]{1,3}\d+\.?\d*)', href)
                
                if match:
                    accession_id = match.group(1)
                    # Simple check to avoid noise where name is just the ID
                    if protein_name.upper() != accession_id.upper() and accession_id not in protein_name:
                        results.add((accession_id, protein_name))
        
        return list(results)

    except requests.exceptions.RequestException as e:
        print(f"    ERROR: Could not fetch search results for '{query}': {e}")
        return []
    except Exception as e:
        print(f"    ERROR: An unexpected error occurred during search for '{query}': {e}")
        return []


def main_scraper() -> Dict[str, Dict[str, Dict[str, List[Dict[str, str]]]]]:
    """
    Executes the full scraping process based on the nested taxonomy structure.
    Returns a flat dictionary keyed by Family Name for easy data lookup.
    """
    print("--- Starting NCBI Fibroin Scraper ---")
    print("Step 1: Fetching Caddisfly nested taxonomy structure...")
    
    # Get the structure: {Suborder: {Superfamily: [Family, ...]}}
    nested_taxonomy = get_trichoptera_taxonomy_structure()
    
    if not nested_taxonomy:
        print("ERROR: Could not retrieve a list of Caddisfly families. Aborting.")
        return {}
    
    # Extract a flat list of all families for iteration
    families_to_process = [
        family 
        for suborders in nested_taxonomy.values() 
        for superfamilies in suborders.values() 
        for family in superfamilies
    ]

    print(f"Successfully retrieved {len(families_to_process)} extant families for processing.")
    print("-" * 40)
    
    # This dictionary will store the final, classified results, keyed by Family name
    final_results = {}
    
    # Map Family Name back to its Suborder and Superfamily for file saving later
    family_to_path = {}
    for suborder, superfamilies in nested_taxonomy.items():
        for superfamily, families in superfamilies.items():
            for family in families:
                family_to_path[family] = {'suborder': suborder, 'superfamily': superfamily}
                
    
    for family in families_to_process:
        print(f"Step 2: Processing Family: {family}")
        search_query = f"{family} {FIBROIN_TERM}"
        
        # Initialize storage with the new nested classification structure
        final_results[family] = {
            'full sequence': {k: [] for k in CHAIN_TYPES.keys()},
            'partial sequence': {k: [] for k in CHAIN_TYPES.keys()}
        }
        
        protein_records = fetch_and_parse_search_results(search_query)
        
        if not protein_records:
            print(f"    No protein records found for {family}.")
            print("-" * 40)
            continue
            
        print(f"    Found {len(protein_records)} records. Fetching sequences...")

        for record_id, record_name in protein_records:
            time.sleep(SLEEP_TIME) 
            
            sequence = fetch_protein_sequence(record_id)
            
            if not sequence:
                continue

            # 1. Determine sequence type (Full or Partial)
            is_partial = 'partial' in record_name.lower()
            seq_type = 'partial sequence' if is_partial or '*' in sequence else 'full sequence'
            
            # 2. Determine chain type (Heavy, Light, Other)
            chain_type = classify_protein_chain(record_name)
            
            sequence_data = {
                'id': record_id,
                'name': record_name,
                'sequence': sequence
            }
            
            # Save data into the correct nested list
            final_results[family][seq_type][chain_type].append(sequence_data)
        
        full_count = sum(len(v) for v in final_results[family]['full sequence'].values())
        partial_count = sum(len(v) for v in final_results[family]['partial sequence'].values())
        
        print(f"    Finished {family}. Results: Full ({full_count}), Partial ({partial_count}).")
        print("-" * 40)
            
    # Return the classified data and the taxonomy path map
    return final_results, family_to_path


# --- Output Generation Functions ---

def generate_sequence_markdown(data: Dict[str, str], chain_type: str, seq_type: str) -> str:
    """Creates human-readable Markdown content for a single sequence file."""
    
    sequence_lines = '\n'.join([data['sequence'][i:i+60] for i in range(0, len(data['sequence']), 60)])
    
    return f"""# Fibroin Sequence Details

| Key | Value |
| :--- | :--- |
| **Accession ID** | `{data['id']}` |
| **Full Name** | `{data['name']}` |
| **Sequence Type** | `{seq_type.title()}` |
| **Chain Classification** | `{chain_type.title()}` |
| **Length (Residues)** | `{len(data['sequence'])}` |

---

## Protein Sequence (FASTA Format)

The sequence below is displayed in standard FASTA format for easy reading and copy-pasting into alignment tools.

```fasta
>{data['id']} {data['name']}
{sequence_lines}
```
"""


def generate_summary_index(results: Dict[str, Any], root_dir: str):
    """
    Generates a comprehensive Markdown index file summarizing all download statistics.
    """
    output_path = Path(root_dir) / "Summary_Index.md"
    content = [
        "# NCBI Caddisfly Fibroin Scraper Index",
        "",
        "This file summarizes the results from the NCBI protein database search for 'Fibroin' across all identified extant Caddisfly families.",
        ""
    ]
    
    total_sequences = 0
    
    # Start the detailed table
    content.append("## Detailed Sequence Counts by Family and Type")
    content.append("| Family Name | Total Found | Full (Heavy) | Full (Light) | Full (Other) | Partial (Heavy) | Partial (Light) | Partial (Other) |")
    content.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

    for family, seq_types in sorted(results.items()):
        
        # Get counts for all six sub-categories
        full_heavy = len(seq_types['full sequence']['heavy chain'])
        full_light = len(seq_types['full sequence']['light chain'])
        full_other = len(seq_types['full sequence']['others'])
        
        partial_heavy = len(seq_types['partial sequence']['heavy chain'])
        partial_light = len(seq_types['partial sequence']['light chain'])
        partial_other = len(seq_types['partial sequence']['others'])
        
        family_total = sum([full_heavy, full_light, full_other, partial_heavy, partial_light, partial_other])
        total_sequences += family_total

        # Append row to the table
        row = f"| {family} | **{family_total}** | {full_heavy} | {full_light} | {full_other} | {partial_heavy} | {partial_light} | {partial_other} |"
        content.append(row)

    content.append("")
    content.append("---")
    content.append(f"## GRAND TOTAL SEQUENCES DOWNLOADED: **{total_sequences}**")
    content.append(f"\nAll sequences are saved in the `{root_dir}` folder, organized hierarchically by Suborder, Superfamily, Sequence Type, and Chain Type.")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
        print(f"Successfully generated summary index: {output_path}")
    except Exception as e:
        print(f"ERROR: Could not write summary index file: {e}")


def save_results_to_files(results: Dict[str, Any], path_map: Dict[str, Any]):
    """
    Creates the complex nested folder structure (Suborder/Superfamily/Family/SeqType/ChainType) 
    and saves all sequences into both FASTA and Markdown files.
    """
    print("\n" + "="*80)
    print(f"Step 3: Creating nested directories and saving sequences to: '{OUTPUT_ROOT_DIR}'")
    print("Structure: Suborder/Superfamily/Family/Sequence Type/Chain Type/")
    print("="*80)
    
    root_dir = Path(OUTPUT_ROOT_DIR)
    root_dir.mkdir(exist_ok=True)
    
    total_files_saved = 0
    
    for family, seq_types in results.items():
        if family not in path_map:
            print(f"WARNING: Skipping {family} - path information missing.")
            continue
            
        # --- 1. Create Suborder and Superfamily directories (Top Level Taxonomy) ---
        suborder_name = path_map[family]['suborder']
        superfamily_name = path_map[family]['superfamily']

        # Path: ROOT/Suborder/Superfamily
        superfamily_dir = root_dir / safe_filename(suborder_name) / safe_filename(superfamily_name)
        superfamily_dir.mkdir(parents=True, exist_ok=True)

        # Path: ROOT/Suborder/Superfamily/Family (Third Level Taxonomy)
        family_dir = superfamily_dir / safe_filename(family)
        family_dir.mkdir(exist_ok=True)
        print(f"  Organizing data for {family} in: {family_dir.relative_to(root_dir)}")
        
        # --- 2. Iterate through Sequence Type and Chain Type (Classification) ---
        for seq_type, chain_types in seq_types.items():
            # seq_type is 'full sequence' or 'partial sequence'
            type_dir = family_dir / safe_filename(seq_type)
            type_dir.mkdir(exist_ok=True)
            
            for chain_type, sequences in chain_types.items():
                # chain_type is 'heavy chain', 'light chain', or 'others'
                chain_dir = type_dir / safe_filename(chain_type)
                chain_dir.mkdir(exist_ok=True)
                
                if not sequences:
                    continue
                
                for data in sequences:
                    # 1. Prepare FASTA Content
                    fasta_header = f">{data['id']} {data['name']}"
                    # Sequence split into lines of 60 characters
                    fasta_sequence = '\n'.join([data['sequence'][i:i+60] for i in range(0, len(data['sequence']), 60)])
                    fasta_content = f"{fasta_header}\n{fasta_sequence}\n"
                    
                    # 2. Prepare Markdown Content
                    markdown_content = generate_sequence_markdown(data, chain_type, seq_type)
                    
                    # Generate a unique, safe filename using Accession ID
                    final_filename_base = f"{data['id']}_{safe_filename(data['name'], 30)}"
                    
                    # Save FASTA file
                    fasta_file_path = chain_dir / f"{final_filename_base}.fasta"
                    try:
                        with open(fasta_file_path, 'w', encoding='utf-8') as f:
                            f.write(fasta_content)
                        total_files_saved += 1
                    except Exception as e:
                        print(f"      ERROR: Could not write FASTA file {fasta_file_path.name}: {e}")

                    # Save Markdown file
                    markdown_file_path = chain_dir / f"{final_filename_base}.md"
                    try:
                        with open(markdown_file_path, 'w', encoding='utf-8') as f:
                            f.write(markdown_content)
                        total_files_saved += 1
                    except Exception as e:
                        print(f"      ERROR: Could not write Markdown file {markdown_file_path.name}: {e}")

    # Generate the Index after saving all files
    generate_summary_index(results, OUTPUT_ROOT_DIR)

    print("\n" + "="*80)
    print(f"--- SUCCESS: Operation Complete. Total {total_files_saved} individual files saved (FASTA and MD). ---")
    print(f"Find your structured data and index in the '{OUTPUT_ROOT_DIR}' folder.")
    print("="*80)


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # Check for dependencies
    try:
        import requests
        from bs4 import BeautifulSoup
        import os
        from pathlib import Path
        from caddisfly_scraper import get_trichoptera_taxonomy_structure
        _ = get_trichoptera_taxonomy_structure() # Test import
    except ImportError as e:
        print(f"Required libraries are missing or caddisfly_scraper.py is not available.")
        print(f"Missing dependency: {e.name}")
        exit()

    try:
        # Run the scraper to get classified data and the path map
        results, path_map = main_scraper()
        
        # Save the results to the local file system with nested directories
        save_results_to_files(results, path_map)
        
    except Exception as e:
        print(f"\nFATAL ERROR in main execution: {e}")