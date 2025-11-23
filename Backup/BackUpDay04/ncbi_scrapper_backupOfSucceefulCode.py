import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple
import re
import os
from pathlib import Path
import time
from caddisfly_scraper import get_caddisfly_family_names 

# --- Configuration ---
NCBI_BASE_URL = "https://www.ncbi.nlm.nih.gov/protein/"
NCBI_EUTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
FIBROIN_TERM = "fibroin"
OUTPUT_ROOT_DIR = "ncbi_fibroin_sequences" # Root folder for all output

# --- Classification Constants ---
CHAIN_TYPES = {
    'heavy chain': ['heavy chain', 'fib-h', 'h-fibroin', 'h chain'],
    'light chain': ['light chain', 'fib-l', 'l-fibroin', 'l chain'],
    'others': [] # Default if no match is found
}
# Define the nested structure for results
EMPTY_CHAIN_STRUCTURE = {
    'heavy chain': [],
    'light chain': [],
    'others': []
}
# The final result structure will now be nested:
# {Family: {'full sequence': EMPTY_CHAIN_STRUCTURE, 'partial sequence': EMPTY_CHAIN_STRUCTURE}}


# --- Utility Functions ---

def safe_filename(name: str, max_len=50) -> str:
    """Generates a safe filename from a string."""
    safe_name = re.sub(r'[\\/:*?"<>|]', '', name).strip()
    safe_name = safe_name.replace(' ', '_')
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


# --- Core Scraper Functions (Updated) ---

def fetch_protein_sequence(accession_id: str) -> str:
    """
    Fetches the protein sequence using NCBI E-utilities (Efetch) for reliable FASTA output.
    (This function remains robust and unchanged from the previous version)
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
        print(f"    ERROR: Could not fetch sequence for {accession_id} using E-utilities: {e}")
        return ""
    except Exception as e:
        print(f"    ERROR: Unexpected error during E-utilities fetch for {accession_id}: {e}")
        return ""


def fetch_and_parse_search_results(query: str) -> List[Tuple[str, str]]:
    """
    Searches NCBI Protein database and extracts accession ID and name for each result.
    (This function remains robust and unchanged from the previous version)
    """
    search_url = f"{NCBI_BASE_URL}?term={query}"
    
    print(f"  Searching NCBI for: '{query}'...")
    try:
        response = requests.get(search_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        results = set()
        title_links = soup.select('a.pr-link, a.title, a[href^="/protein/"], a[data-entity-id]')

        for link in title_links:
            href = link.get('href')
            protein_name = link.get_text(strip=True)
            
            if href and protein_name:
                match = re.search(r'/protein/([A-Z]{1,3}\d+\.?\d*)', href)
                
                if match:
                    accession_id = match.group(1)
                    if protein_name.upper() != accession_id.upper() and accession_id not in protein_name:
                        results.add((accession_id, protein_name))
        
        return list(results)

    except requests.exceptions.RequestException as e:
        print(f"  ERROR: Could not fetch search results for '{query}': {e}")
        return []
    except Exception as e:
        print(f"  ERROR: An unexpected error occurred during search for '{query}': {e}")
        return []


def main_scraper() -> Dict[str, Dict[str, Dict[str, List[Dict[str, str]]]]]:
    """
    Executes the full scraping process with the new nested classification logic.
    """
    print("--- Starting NCBI Fibroin Scraper ---")
    print("Step 1: Fetching Caddisfly family names...")
    
    caddisfly_families = get_caddisfly_family_names()
    
    if not caddisfly_families:
        print("ERROR: Could not retrieve a list of Caddisfly families. Aborting.")
        return {}

    families_to_process = caddisfly_families
    
    print(f"Successfully retrieved {len(caddisfly_families)} families.")
    print("-" * 40)
    
    final_results = {}
    
    for family in families_to_process:
        print(f"Step 2: Processing Family: {family}")
        search_query = f"{family} {FIBROIN_TERM}"
        
        # Initialize storage with the new nested structure
        final_results[family] = {
            'full sequence': {k: [] for k in CHAIN_TYPES.keys()},
            'partial sequence': {k: [] for k in CHAIN_TYPES.keys()}
        }
        
        protein_records = fetch_and_parse_search_results(search_query)
        
        if not protein_records:
            print(f"  No protein records found for {family}.")
            print("-" * 40)
            continue
            
        print(f"  Found {len(protein_records)} records. Fetching sequences...")

        for record_id, record_name in protein_records:
            time.sleep(0.5) 
            
            sequence = fetch_protein_sequence(record_id)
            
            if not sequence:
                continue

            # 1. Determine sequence type (Full or Partial)
            is_partial = 'partial' in record_name.lower()
            seq_type = 'partial sequence' if is_partial else 'full sequence'
            
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
        
        print(f"  Finished {family}. Results: Full ({full_count}), Partial ({partial_count}).")
        print("-" * 40)
        
    return final_results

# --- Output Generation Functions (NEW/Updated) ---

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

The sequence below is displayed in FASTA format for easy reading and copy-pasting into alignment tools.

```fasta
>{data['id']} {data['name']}
{sequence_lines}
```
"""


def generate_summary_index(results: Dict, root_dir: str):
    """
    Generates a comprehensive Markdown index file summarizing all download statistics.
    """
    output_path = Path(root_dir) / "Summary_Index.md"
    content = [
        "# NCBI Caddisfly Fibroin Scraper Index",
        "",
        "This file summarizes the results from the NCBI protein database search for 'Fibroin' across all identified Caddisfly families.",
        ""
    ]
    
    total_sequences = 0
    
    # Start the detailed table
    content.append("## Detailed Sequence Counts by Family and Type")
    content.append("| Family Name | Total Found | Full Chain (Heavy) | Full Chain (Light) | Full Chain (Other) | Partial Chain (Heavy) | Partial Chain (Light) | Partial Chain (Other) |")
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
    content.append(f"\nAll sequences are saved in the `{root_dir}` folder, organized by family, sequence type, and chain type.")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
        print(f"Successfully generated summary index: {output_path}")
    except Exception as e:
        print(f"ERROR: Could not write summary index file: {e}")


def save_results_to_files(results: Dict[str, Dict[str, Dict[str, List[Dict[str, str]]]]]):
    """
    Creates the nested folder structure and saves all sequences into both FASTA and Markdown files.
    """
    print("\n" + "="*80)
    print(f"Step 3: Creating nested directories and saving sequences to: '{OUTPUT_ROOT_DIR}'")
    print("Files will be saved in dual format: .fasta (for tools) and .md (for reading).")
    print("="*80)
    
    root_dir = Path(OUTPUT_ROOT_DIR)
    root_dir.mkdir(exist_ok=True)
    
    total_files_saved = 0
    
    for family, seq_types in results.items():
        family_dir = root_dir / safe_filename(family)
        family_dir.mkdir(exist_ok=True)
        print(f"Created family directory: {family_dir}")

        for seq_type, chain_types in seq_types.items():
            # seq_type is 'full sequence' or 'partial sequence'
            type_dir = family_dir / safe_filename(seq_type)
            type_dir.mkdir(exist_ok=True)
            
            for chain_type, sequences in chain_types.items():
                # chain_type is 'heavy chain', 'light chain', or 'others'
                chain_dir = type_dir / safe_filename(chain_type)
                chain_dir.mkdir(exist_ok=True)
                
                print(f"  Created structure: {chain_dir}")
                
                if not sequences:
                    # print(f"  No sequences in '{chain_type}' for '{seq_type}' in {family}.")
                    continue
                
                for data in sequences:
                    # 1. Prepare FASTA Content
                    fasta_header = f">{data['id']} {data['name']}"
                    # Sequence split into lines of 60 characters
                    fasta_sequence = '\n'.join([data['sequence'][i:i+60] for i in range(0, len(data['sequence']), 60)])
                    fasta_content = f"{fasta_header}\n{fasta_sequence}\n"
                    
                    # 2. Prepare Markdown Content (Word substitute)
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
                        print(f"    ERROR: Could not write FASTA file {fasta_file_path.name}: {e}")

                    # Save Markdown file
                    markdown_file_path = chain_dir / f"{final_filename_base}.md"
                    try:
                        with open(markdown_file_path, 'w', encoding='utf-8') as f:
                            f.write(markdown_content)
                        total_files_saved += 1
                    except Exception as e:
                        print(f"    ERROR: Could not write Markdown file {markdown_file_path.name}: {e}")

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
        from caddisfly_scraper import get_caddisfly_family_names
        _ = get_caddisfly_family_names()
    except ImportError as e:
        print(f"Required libraries are missing. Please install them: uv pip install requests beautifulsoup4")
        print(f"Missing dependency: {e.name}")
        exit()

    try:
        # Run the scraper to get structured data
        results = main_scraper()
        
        # Save the results to the local file system
        save_results_to_files(results)
        
    except Exception as e:
        print(f"\nFATAL ERROR in main execution: {e}")
        