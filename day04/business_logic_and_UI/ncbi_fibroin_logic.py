import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple, Any
import re
import time
from caddisfly_scraper import get_trichoptera_taxonomy_structure

# --- Configuration & Constants ---
NCBI_BASE_URL = "https://www.ncbi.nlm.nih.gov/protein/"
NCBI_EUTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
FIBROIN_TERM = "fibroin"
SLEEP_TIME = 0.5 # Pause between API calls to be polite

# Classification mapping for protein chains
CHAIN_TYPES = {
    'heavy chain': ['heavy chain', 'fib-h', 'h-fibroin', 'h chain'],
    'light chain': ['light chain', 'fib-l', 'l-fibroin', 'l chain'],
    'others': [] # Default if no match is found
}


# --- Utility Functions (Part of the logic to classify data) ---

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

def extract_organism_name(protein_name: str) -> str:
    """
    Extracts the organism name typically enclosed in square brackets in the NCBI title.
    """
    # Regex to find content inside the last pair of square brackets
    match = re.search(r'\[(.*?)\]$', protein_name.strip())
    if match:
        organism = match.group(1).strip()
        if len(organism) > 3:
            return organism
    return "Unknown Organism"


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
        # Remove any non-standard amino acid characters 
        sequence = re.sub(r'[^A-Z*]', '', sequence_body) 
            
        return sequence

    except requests.exceptions.RequestException as e:
        print(f"      ERROR: Could not fetch sequence for {accession_id} using E-utilities: {e}")
        return ""
    except Exception as e:
        print(f"      ERROR: Unexpected error during E-utilities fetch for {accession_id}: {e}")
        return ""


def fetch_and_parse_search_results(query: str) -> List[Tuple[str, str]]:
    """
    Searches NCBI Protein database and extracts accession ID and name for each result.
    """
    search_url = f"{NCBI_BASE_URL}?term={query}"
    
    # print(f"    Searching NCBI for: '{query}'...")
    try:
        response = requests.get(search_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        # Explicitly check for NCBI's "Term not found" message
        if "The following term was not found in Protein:" in response.text:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        results = set()
        title_links = soup.select('a.pr-link, a.title, a[href^="/protein/"], a[data-entity-id]')

        for link in title_links:
            href = link.get('href')
            protein_name = link.get_text(strip=True)
            
            if href and protein_name:
                # Regex to extract accession ID (e.g., AAN02787.1)
                match = re.search(r'/protein/([A-Z]{1,3}\d+\.?\d*)', href)
                
                if match:
                    accession_id = match.group(1)
                    if accession_id not in protein_name:
                        results.add((accession_id, protein_name))
        
        return list(results)

    except requests.exceptions.RequestException as e:
        print(f"    ERROR: Could not fetch search results for '{query}': {e}")
        return []
    except Exception as e:
        print(f"    ERROR: An unexpected error occurred during search for '{query}': {e}")
        return []


def run_ncbi_search_and_classification() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Orchestrates the taxonomy fetch, NCBI search, sequence fetch, and classification.
    Returns the classified data and the taxonomy path map.
    """
    print("Step 1: Fetching Caddisfly nested taxonomy structure...")
    
    # Get the structure: {Suborder: {Superfamily: [Family, ...]}}
    nested_taxonomy = get_trichoptera_taxonomy_structure()
    
    if not nested_taxonomy:
        print("ERROR: Could not retrieve a list of Caddisfly families. Aborting.")
        return {}, {}
    
    # Extract a flat list of all families for iteration
    families_to_process = [
        family 
        for suborders in nested_taxonomy.values() 
        for superfamilies in suborders.values() 
        for family in superfamilies
    ]

    print(f"Successfully retrieved {len(families_to_process)} extant families for processing.")
    print("-" * 40)
    
    # This dictionary will store the final, classified results, keyed by Family -> Organism
    final_results: Dict[str, Dict[str, Any]] = {} 
    
    # Map Family Name back to its Suborder and Superfamily for file saving later
    family_to_path = {}
    for suborder, superfamilies in nested_taxonomy.items():
        for superfamily, families in superfamilies.items():
            for family in families:
                family_to_path[family] = {'suborder': suborder, 'superfamily': superfamily}
                
    
    for family in families_to_process:
        print(f"Step 2: Processing Family: {family}")
        search_query = f"{family} {FIBROIN_TERM}"
        
        # Initialize storage for the current family, keyed by organism name
        final_results[family] = {}
        
        protein_records = fetch_and_parse_search_results(search_query)
        
        if not protein_records:
            print(f"    No protein records found for {family}. Skipping download.")
            print("-" * 40)
            continue
            
        print(f"    Found {len(protein_records)} records. Fetching sequences...")

        for record_id, record_name in protein_records:
            time.sleep(SLEEP_TIME) 
            
            sequence = fetch_protein_sequence(record_id)
            
            if not sequence:
                continue

            # 0. Extract Organism Name
            organism_name = extract_organism_name(record_name)
            
            # Initialize organism storage if new
            if organism_name not in final_results[family]:
                final_results[family][organism_name] = {
                    'full sequence': {k: [] for k in CHAIN_TYPES.keys()},
                    'partial sequence': {k: [] for k in CHAIN_TYPES.keys()}
                }

            # 1. Determine sequence type (Full or Partial)
            is_partial = 'partial' in record_name.lower()
            seq_type = 'partial sequence' if is_partial or '*' in sequence else 'full sequence'
            
            # 2. Determine chain type (Heavy, Light, Other)
            chain_type = classify_protein_chain(record_name)
            
            sequence_data = {
                'id': record_id,
                'name': record_name,
                'organism': organism_name,
                'sequence': sequence
            }
            
            # Save data into the correct nested list: family -> organism -> seq_type -> chain_type
            final_results[family][organism_name][seq_type][chain_type].append(sequence_data)
        
        # Calculate counts for printing status
        full_count = sum(
            len(v) 
            for org_data in final_results[family].values() 
            for v in org_data['full sequence'].values()
        )
        partial_count = sum(
            len(v) 
            for org_data in final_results[family].values() 
            for v in org_data['partial sequence'].values()
        )
        
        print(f"    Finished {family}. Results: Total found ({full_count + partial_count}), Full ({full_count}), Partial ({partial_count}).")
        print("-" * 40)
            
    # Return the classified data and the taxonomy path map
    return final_results, family_to_path