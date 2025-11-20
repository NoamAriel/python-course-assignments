import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple
import re
from caddisfly_scraper import get_caddisfly_family_names # Import the family list

# --- Configuration ---
NCBI_BASE_URL = "https://www.ncbi.nlm.nih.gov/protein/" # Used for search
NCBI_EUTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi" # Used for reliable sequence fetch
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
FIBROIN_TERM = "fibroin"

# --- Data Structure for Results ---
# The final result structure will be organized by family and then by sequence type
# {FamilyName: {'full sequence': [Sequence_Data], 'partial sequence': [Sequence_Data]}}
# Sequence_Data = {'id': str, 'name': str, 'sequence': str}


def fetch_and_parse_search_results(query: str) -> List[Tuple[str, str]]:
    """
    Searches NCBI Protein database and extracts accession ID and name for each result.
    
    This version extracts Accession IDs from the protein link URLs.
    """
    search_url = f"{NCBI_BASE_URL}?term={query}"
    
    print(f"  Searching NCBI for: '{query}'...")
    try:
        response = requests.get(search_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        results = set() # Use a set to store unique results (ID, Name)
        
        # Target links that point to a protein record
        title_links = soup.select('a.pr-link, a.title, a[href^="/protein/"]')

        for link in title_links:
            href = link.get('href')
            protein_name = link.get_text(strip=True)
            
            if href and protein_name:
                # Regex to extract the Accession ID (e.g., AAB12345.1) from the href
                match = re.search(r'/protein/([A-Z]{1,3}\d+\.?\d*)', href)
                
                if match:
                    accession_id = match.group(1)
                    # Filter out cases where the link text is just the accession ID itself
                    if protein_name.upper() != accession_id.upper():
                        results.add((accession_id, protein_name))
        
        # Convert set of results back to a list
        return list(results)

    except requests.exceptions.RequestException as e:
        print(f"  ERROR: Could not fetch search results for '{query}': {e}")
        return []
    except Exception as e:
        print(f"  ERROR: An unexpected error occurred during search for '{query}': {e}")
        return []


def fetch_protein_sequence(accession_id: str) -> str:
    """
    Fetches the protein sequence using NCBI E-utilities (Efetch) for reliable FASTA output.
    
    This method is highly reliable as it uses the API endpoint designed for bulk data retrieval.
    """
    # Use Efetch with db=protein, rettype=fasta, retmode=text
    params = {
        'db': 'protein',
        'id': accession_id,
        'rettype': 'fasta',
        'retmode': 'text'
    }
    
    try:
        # Use E-utilities URL instead of the regular NCBI protein page URL
        response = requests.get(NCBI_EUTILS_BASE_URL, headers=HEADERS, params=params, timeout=15)
        response.raise_for_status()
        content = response.text.strip()

        # 1. Check if content is valid FASTA
        if not content.startswith('>'):
            return ""

        # 2. Separate header (first line) from the sequence body
        first_newline_index = content.find('\n')
        
        if first_newline_index == -1:
            return "" # No sequence data

        # Get the body starting immediately after the first newline
        sequence_body = content[first_newline_index + 1:].upper()
        
        if not sequence_body:
            return ""
            
        # 3. Robust cleaning: Remove ALL characters that are NOT uppercase English letters (A-Z) or a stop codon (*)
        sequence = re.sub(r'[^A-Z*]', '', sequence_body)
            
        return sequence

    except requests.exceptions.RequestException as e:
        print(f"    ERROR: Could not fetch sequence for {accession_id} using E-utilities: {e}")
        return ""
    except Exception as e:
        print(f"    ERROR: Unexpected error during E-utilities fetch for {accession_id}: {e}")
        return ""


def main_scraper() -> Dict[str, Dict[str, List[Dict[str, str]]]]:
    """
    Executes the full scraping process: get families, search NCBI, fetch sequences, and organize.
    """
    print("--- Starting NCBI Fibroin Scraper ---")
    print("Step 1: Fetching Caddisfly family names...")
    
    # Get extant families (excluding fossils)
    caddisfly_families = get_caddisfly_family_names()
    
    if not caddisfly_families:
        print("ERROR: Could not retrieve a list of Caddisfly families. Aborting.")
        return {}

    families_to_process = caddisfly_families
    
    print(f"Successfully retrieved {len(caddisfly_families)} families.")
    print(f"Processing all {len(families_to_process)} families.")
    print("-" * 40)
    
    final_results = {}
    
    for family in families_to_process:
        print(f"Step 2: Processing Family: {family}")
        
        search_query = f"{family} {FIBROIN_TERM}"
        
        # Initialize storage for this family
        final_results[family] = {
            'full sequence': [],
            'partial sequence': []
        }
        
        # A. Get search results for the family + fibroin
        protein_records = fetch_and_parse_search_results(search_query)
        
        if not protein_records:
            print(f"  No protein records found for {family}.")
            print("-" * 40)
            continue
            
        print(f"  Found {len(protein_records)} records. Fetching sequences...")

        # B. Fetch the sequence for each record
        for record_id, record_name in protein_records:
            sequence = fetch_protein_sequence(record_id)
            
            if not sequence:
                continue

            # C. Determine sequence type (Full or Partial)
            is_partial = 'partial' in record_name.lower()
            seq_type = 'partial sequence' if is_partial else 'full sequence'
            
            sequence_data = {
                'id': record_id,
                'name': record_name,
                'sequence': sequence
            }
            
            final_results[family][seq_type].append(sequence_data)
        
        full_count = len(final_results[family]['full sequence'])
        partial_count = len(final_results[family]['partial sequence'])
        
        print(f"  Finished {family}. Results: Full ({full_count}), Partial ({partial_count}).")
        print("-" * 40)
        
    return final_results


def print_final_results(results: Dict[str, Dict[str, List[Dict[str, str]]]]):
    """
    Prints the final structured results in a human-readable, copy-paste friendly format.
    """
    print("\n" + "="*80)
    print("                 FINAL ORGANIZED PROTEIN SEQUENCE RESULTS")
    print("="*80)
    
    found_any_sequence = False
    families_printed = set()
    
    # First Pass: Print families that found sequences
    for family, seq_types in results.items():
        total_found = sum(len(seqs) for seqs in seq_types.values())
        
        if total_found > 0:
            found_any_sequence = True
            families_printed.add(family)
            print(f"\n################ FAMILY: {family.upper()} ################")
            
            for seq_type, sequences in seq_types.items():
                
                print(f"\n--- {seq_type.upper()} ({len(sequences)} SEQUENCES) ---")
                
                if not sequences:
                    print("  [No sequences found in this category.]")
                    continue
                    
                for data in sequences:
                    print("\n--------------------------------------------------")
                    # Generate a safe file name
                    safe_name = re.sub(r'[^a-zA-Z0-9_ -]', '', data['name'][:50]).replace(' ', '_').strip()
                    # Truncate to a reasonable length for a file name
                    final_filename = f"{data['id']}_{safe_name[:30]}.fasta" 
                    print(f"SUGGESTED FILENAME: {final_filename}")
                    print(f"Accession ID: {data['id']}")
                    print(f"Protein Name: {data['name']}")
                    print(f"Sequence Length: {len(data['sequence'])}")
                    print("--------------------------------------------------")
                    
                    # Print sequence in FASTA format
                    fasta_header = f">{data['id']} {data['name']}"
                    fasta_sequence = '\n'.join([data['sequence'][i:i+60] for i in range(0, len(data['sequence']), 60)])
                    print(f"{fasta_header}\n{fasta_sequence}")
    
    # Second Pass: Print families that found zero sequences (for completeness)
    if not found_any_sequence or len(families_printed) < len(results):
        for family in sorted(results.keys()):
            if family not in families_printed:
                print(f"\n################ FAMILY: {family.upper()} ################")
                print("\n--- FULL SEQUENCE (0 SEQUENCES) ---")
                print("  [No sequences found in this category.]")
                print("\n--- PARTIAL SEQUENCE (0 SEQUENCES) ---")
                print("  [No sequences found in this category.]")

    
    print("\n" + "="*80)
    print("--- END OF REPORT ---")
    print("NOTE: You can now copy the output above to create your local files/folders.")
    
    # Optional: Suggest an action to the user
    print("\n[ACTION SUGGESTION]:")
    print("The scraper is now using the robust NCBI E-utilities API. If sequences were found, copy the full FASTA block (starting with '>') and save it as the 'SUGGESTED FILENAME' provided in the output.")


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # Check for dependencies
    try:
        import requests
        from bs4 import BeautifulSoup
        # Ensure caddisfly_scraper is available
        from caddisfly_scraper import get_caddisfly_family_names
        _ = get_caddisfly_family_names()
    except ImportError as e:
        print(f"Required libraries are missing. Please install them: uv pip install requests beautifulsoup4")
        print(f"Missing dependency: {e.name}")
        exit()

    try:
        results = main_scraper()
        print_final_results(results)
    except Exception as e:
        print(f"\nFATAL ERROR in main execution: {e}")