import requests
from bs4 import BeautifulSoup, Tag
from typing import Dict, List, Any
import re

# --- Configuration ---
WIKI_URL = "https://en.wikipedia.org/wiki/Caddisfly"
TAXONOMY_SECTION_ID = "TAXONOMY" 
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# --- Web Scraping Function (Confirmed Working) ---

def fetch_taxonomy_data(url: str) -> str:
    """
    Fetches the content of the specified URL and isolates the Taxonomy section's content.
    """
    # print(f"Fetching data from: {url}") # Suppressing chatty output for import
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status() 
        soup = BeautifulSoup(response.content, 'html.parser')
        
        start_element = None
        taxonomy_heading_span = soup.find('span', {'id': re.compile(TAXONOMY_SECTION_ID, re.IGNORECASE)})
        
        if taxonomy_heading_span:
            start_element = taxonomy_heading_span.find_parent('h2')
        
        if not start_element:
            start_element = soup.find('h2', string=lambda t: t and TAXONOMY_SECTION_ID.lower() in t.lower())
        
        if not start_element:
            raise ValueError(f"Could not find the section '{TAXONOMY_SECTION_ID}' on the page.")

        def is_taxonomy_list(tag):
            if tag.name in ['dl', 'ul', 'ol', 'div']:
                text = tag.get_text()
                if "Superfamily" in text or "Annulipalpia" in text:
                    return True
            return False

        content_container = start_element.find_next(is_taxonomy_list)

        if not content_container:
            # Fallback (The logic that worked for us previously)
            next_element = start_element.find_next_sibling()
            raw_text_data = ""
            while next_element and next_element.name not in ['h2', 'h3']:
                if isinstance(next_element, Tag):
                    raw_text_data += next_element.get_text(separator='\n', strip=True) + "\n"
                next_element = next_element.find_next_sibling()
            
            if raw_text_data:
                processed_data = '\n'.join([line.strip() for line in raw_text_data.split('\n') if line.strip()])
                return processed_data
            else:
                raise ValueError("Could not extract any content block after the header.")
        
        raw_text_data = content_container.get_text(separator='\n', strip=True)
        processed_data = '\n'.join([line.strip() for line in raw_text_data.split('\n') if line.strip()])
        
        if "Superfamily" not in processed_data and "Annulipalpia" not in processed_data:
             raise ValueError("Extracted content is too short or lacks expected taxonomy markers.")

        return processed_data

    except Exception as e:
        # print(f"An error occurred during taxonomy data fetching: {e}")
        return ""

# --- Data Parsing Function (Final Working Version) ---

def parse_trichoptera_data(raw_text: str) -> Dict[str, Dict[str, List[str]]]:
    """
    Parses the raw text extracted from the webpage into a structured dictionary.
    """
    TRICHOPTERA_FAMILIES = {}
    current_suborder = None
    current_superfamily = None
    
    cleaned_text = re.sub(r'\[.*?\]|\xa0|·|\s*edit\s*', '', raw_text, flags=re.IGNORECASE)
    lines = cleaned_text.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1 
        if not line:
            continue
            
        line_lower = line.lower()
        
        if line_lower.startswith("suborder"):
            current_suborder = None
            if len(line.split()) > 1:
                current_suborder = line.split(maxsplit=1)[1].strip()
            elif i < len(lines):
                current_suborder = lines[i].strip()
                i += 1 
            
            if current_suborder and current_suborder not in TRICHOPTERA_FAMILIES:
                TRICHOPTERA_FAMILIES[current_suborder] = {}
            current_superfamily = None
            
        elif line_lower.startswith("superfamily"):
            current_superfamily = None
            is_fossil_rank = '†' in line
            
            if len(line.split()) > 1 and line_lower != "superfamily" and line_lower != "superfamily †":
                superfamily_name = line.split(maxsplit=1)[1].strip()
                current_superfamily = superfamily_name
                     
            elif i < len(lines):
                superfamily_base_name = lines[i].strip()
                current_superfamily = superfamily_base_name
                i += 1 

            if current_superfamily and is_fossil_rank and '†' not in current_superfamily:
                 current_superfamily += '†'
            
            if current_superfamily and current_suborder:
                if current_superfamily not in TRICHOPTERA_FAMILIES[current_suborder]:
                    TRICHOPTERA_FAMILIES[current_suborder][current_superfamily] = []
        
        elif line_lower.startswith("family"):
            if i < len(lines) and current_suborder and current_superfamily:
                family_base_name = lines[i].strip()
                family_name = family_base_name
                is_fossil_rank = '†' in line
                
                if is_fossil_rank and '†' not in family_name:
                    family_name = family_base_name + '†'
                
                if family_name not in TRICHOPTERA_FAMILIES[current_suborder][current_superfamily]:
                    TRICHOPTERA_FAMILIES[current_suborder][current_superfamily].append(family_name)
                    
                i += 1
    return TRICHOPTERA_FAMILIES

# --- EXPORT FUNCTION ---

def get_caddisfly_family_names() -> List[str]:
    """
    Public function to fetch and return a flat list of all extant family names.
    Fossil names are excluded for a more relevant NCBI search.
    """
    raw_content = fetch_taxonomy_data(WIKI_URL)
    if not raw_content:
        # Fallback list if fetching fails
        print("WARNING: Using hardcoded family list as scraper failed to fetch new data.")
        return ['Hydropsychidae', 'Limnephilidae', 'Hydroptilidae', 'Leptoceridae']

    structured_data = parse_trichoptera_data(raw_content)
    
    # Extract only extant families (those without the '†' marker)
    extant_families = []
    for suborders in structured_data.values():
        for families in suborders.values():
            extant_families.extend([f for f in families if '†' not in f])
            
    # Return unique extant names
    return sorted(list(set(extant_families)))

# If run directly, still print the results (optional for convenience)
if __name__ == "__main__":
    raw_content = fetch_taxonomy_data(WIKI_URL)
    if raw_content:
        print("\n--- DEBUG: RAW CONTENT EXTRACTED ---")
        print(raw_content)
        print("------------------------------------\n")
        
        structured_data = parse_trichoptera_data(raw_content)
        
        # Helper function for printing (copied from previous iterations)
        def print_families_by_suborder(structured_data: Dict[str, Any]):
            print("\n" + "="*70)
            print("--- EXTRACTED FAMILIES OF THE ORDER TRICHOPTERA (Caddisflies) ---")
            print("="*70)
            all_families = sorted(list(set(f for suborders in structured_data.values() for families in suborders.values() for f in families)))
            total_families = len(all_families)
            print(f"\nTotal families extracted: {total_families}\n")
            
            for suborder, superfamilies in structured_data.items():
                print(f"[{suborder.upper()}]")
                for superfamily, families in superfamilies.items():
                    extant_families = [f for f in families if '†' not in f]
                    fossil_families = [f for f in families if '†' in f]
                    display_superfamily = superfamily.rstrip('†').strip()
                    print(f"  Superfamily: {display_superfamily} (Total: {len(families)})")
                    if extant_families:
                        print(f"    Extant Families: {', '.join(extant_families)}")
                    if fossil_families:
                        cleaned_fossils = [f.rstrip('†').strip() for f in fossil_families]
                        print(f"    Fossil Families: {', '.join(cleaned_fossils)}")
                print("-" * 70)
                
            print("\n--- Flat List of All Families ---")
            print(all_families)

        print_families_by_suborder(structured_data)
    else:
        print(f"\nCould not retrieve taxonomy content from {WIKI_URL}.")