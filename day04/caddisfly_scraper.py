import requests
from bs4 import BeautifulSoup, Tag
from typing import Dict, List, Any
import re

# --- Configuration ---
WIKI_URL = "https://en.wikipedia.org/wiki/Caddisfly"
# This is the target section header text.
TAXONOMY_SECTION_ID = "TAXONOMY" 

# IMPORTANT FIX: Include a User-Agent header to avoid 403 Forbidden errors.
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# --- Web Scraping Function (No changes needed, extraction is confirmed working) ---

def fetch_taxonomy_data(url: str) -> str:
    """
    Fetches the content of the specified URL and isolates the Taxonomy section's content.
    
    This function uses a targeted search for list elements (ul, ol, dl) following the h2 header
    that contain the expected taxonomy markers, making it highly robust against Wikipedia's HTML changes.
    """
    print(f"Fetching data from: {url}")
    try:
        # 1. Fetch the HTML content
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        
        # 2. Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 3. Find the Taxonomy section header (h2)
        start_element = None
        
        # Find the <span> element for the ID (case-insensitive search)
        taxonomy_heading_span = soup.find('span', {'id': re.compile(TAXONOMY_SECTION_ID, re.IGNORECASE)})
        
        if taxonomy_heading_span:
            # Get the parent <h2> tag
            start_element = taxonomy_heading_span.find_parent('h2')
        
        if not start_element:
            # Fallback—Find any <h2> element that contains the text "Taxonomy"
            start_element = soup.find('h2', string=lambda t: t and TAXONOMY_SECTION_ID.lower() in t.lower())
        
        if not start_element:
            raise ValueError(f"Could not find the section '{TAXONOMY_SECTION_ID}' on the page.")

        # 4. CRITICAL FIX: Find the first content container after the h2 that looks like a list.
        def is_taxonomy_list(tag):
            if tag.name in ['dl', 'ul', 'ol', 'div']: # Check common list/container tags
                # Ensure the list contains content relevant to the taxonomy (e.g., "Superfamily")
                text = tag.get_text()
                if "Superfamily" in text or "Annulipalpia" in text:
                    return True
            return False

        # Search for the most relevant container
        content_container = start_element.find_next(is_taxonomy_list)

        if not content_container:
            # Fallback to a wider search if the specific tags are missed
            content_container = start_element.find_next('div', class_='mw-parser-output')
            if content_container:
                # Limit the search within the mw-parser-output to elements immediately following the h2
                next_element = start_element.find_next_sibling()
                
                raw_text_data = ""
                # Iterate through siblings until the next major header
                while next_element and next_element.name not in ['h2', 'h3']:
                    if isinstance(next_element, Tag):
                        # Extract text with newlines to preserve the vertical structure
                        raw_text_data += next_element.get_text(separator='\n', strip=True) + "\n"
                    next_element = next_element.find_next_sibling()
            
                # If the iteration found content, use it
                if raw_text_data:
                    # Use a broad, aggressive approach to clean and return the raw data
                    # This ensures the parser receives the "vertical" list structure
                    processed_data = '\n'.join([line.strip() for line in raw_text_data.split('\n') if line.strip()])
                    return processed_data
                else:
                    raise ValueError("Could not extract any content block after the header.")
        
        if not content_container:
            raise ValueError("Could not find the expected list container (dl, ul, ol, or div) after the header.")
        
        # 5. Extract all text from the found container element
        # Use a separator to ensure the vertical structure (Suborder\nAnnulipalpia) is preserved
        raw_text_data = content_container.get_text(separator='\n', strip=True)
        
        # Filter out empty lines and noise
        processed_data = '\n'.join([line.strip() for line in raw_text_data.split('\n') if line.strip()])
        
        # Validation check: Ensure the extracted text contains the expected content pattern
        if "Superfamily" not in processed_data and "Annulipalpia" not in processed_data:
             print(f"WARNING: Found a container, but it lacked taxonomy markers. Content length: {len(processed_data)}")
             print(f"WARNING: Content preview: {processed_data[:200]}...")
             raise ValueError("Extracted content is too short or lacks expected taxonomy markers (Superfamily/Suborder).")

        return processed_data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the page: {e}")
        return ""
    except ValueError as e:
        print(f"Error parsing page structure: {e}")
        return ""
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return ""

# --- Data Parsing Function (FINAL FIX: Consistent handling of inline vs. two-line names) ---

def parse_trichoptera_data(raw_text: str) -> Dict[str, Dict[str, List[str]]]:
    """
    Parses the raw text extracted from the webpage into a structured dictionary.
    
    The structure is: {Suborder: {Superfamily: [Family Names]}}
    This version correctly handles the line-separated (vertical) format, including '†' markers,
    and resolves the inconsistent two-line vs. one-line name placement.
    """
    TRICHOPTERA_FAMILIES = {}
    current_suborder = None
    current_superfamily = None
    
    # 1. Clean up references and non-breaking spaces
    cleaned_text = re.sub(r'\[.*?\]|\xa0|·|\s*edit\s*', '', raw_text, flags=re.IGNORECASE)
    lines = cleaned_text.split('\n')
    
    # 2. Process data line by line to build the hierarchical structure
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1 # Advance iterator, then handle potential skips later
        if not line:
            continue
            
        line_lower = line.lower()
        
        # 2a. Handle Suborder
        if line_lower.startswith("suborder"):
            current_suborder = None
            
            # Check for inline name (unlikely, but safe: "Suborder Annulipalpia")
            if len(line.split()) > 1:
                current_suborder = line.split(maxsplit=1)[1].strip()
            # Assume two-line format: Suborder\nAnnulipalpia (Check previous line structure)
            elif i < len(lines):
                current_suborder = lines[i].strip()
                i += 1 # Consume the next line (the suborder name)
            
            if current_suborder and current_suborder not in TRICHOPTERA_FAMILIES:
                TRICHOPTERA_FAMILIES[current_suborder] = {}
            current_superfamily = None # Reset Superfamily
            
        # 2b. Handle Superfamily
        elif line_lower.startswith("superfamily"):
            current_superfamily = None
            is_fossil_rank = '†' in line
            
            # Check for inline name (e.g., "Superfamily Psychomyioidea")
            if len(line.split()) > 1 and line_lower != "superfamily" and line_lower != "superfamily †":
                # Split off the rank word(s) and take the rest as the name
                superfamily_name = line.split(maxsplit=1)[1].strip()
                current_superfamily = superfamily_name
                     
            # Assume two-line format (e.g., "Superfamily" \n "Hydropsychoidea")
            elif i < len(lines):
                superfamily_base_name = lines[i].strip()
                current_superfamily = superfamily_base_name
                i += 1 # Consume the next line (the superfamily name)

            # Apply fossil marker logic consistently
            if current_superfamily and is_fossil_rank and '†' not in current_superfamily:
                 current_superfamily += '†'
            
            # Initialize the Superfamily structure
            if current_superfamily and current_suborder:
                if current_superfamily not in TRICHOPTERA_FAMILIES[current_suborder]:
                    TRICHOPTERA_FAMILIES[current_suborder][current_superfamily] = []
        
        # 2c. Handle Family
        elif line_lower.startswith("family"):
            if i < len(lines) and current_suborder and current_superfamily:
                family_base_name = lines[i].strip()
                family_name = family_base_name
                is_fossil_rank = '†' in line
                
                # Check if the rank line contains the fossil marker (e.g., "Family †")
                if is_fossil_rank and '†' not in family_name:
                    family_name = family_base_name + '†'
                
                # Add the family name (with or without †)
                if family_name not in TRICHOPTERA_FAMILIES[current_suborder][current_superfamily]:
                    TRICHOPTERA_FAMILIES[current_suborder][current_superfamily].append(family_name)
                    
                i += 1 # Consume the next line (the family name)
        
        # If the line was neither a rank nor consumed by the two-line logic, the main iterator advances it.

    return TRICHOPTERA_FAMILIES

# --- Utility Functions (No changes needed here) ---

def get_all_trichoptera_families(structured_data: Dict[str, Any]) -> List[str]:
    """
    Extracts all family names from the nested dictionary structure and returns them as a single,
    flat list.
    """
    all_families = []
    for suborder, superfamilies in structured_data.items():
        for superfamily, families in superfamilies.items():
            all_families.extend(families)
    # Return unique families, as the new parsing logic might result in some duplicates
    return sorted(list(set(all_families))) 

def print_families_by_suborder(structured_data: Dict[str, Any]):
    """
    Prints the families organized by their suborder and superfamily for clarity.
    """
    print("\n" + "="*70)
    print("--- EXTRACTED FAMILIES OF THE ORDER TRICHOPTERA (Caddisflies) ---")
    print("="*70)
    
    all_families = get_all_trichoptera_families(structured_data)
    total_families = len(all_families)
    print(f"\nTotal families extracted: {total_families}\n")

    for suborder, superfamilies in structured_data.items():
        print(f"[{suborder.upper()}]")
        for superfamily, families in superfamilies.items():
            # Check for the fossil marker '†'
            extant_families = [f for f in families if '†' not in f]
            fossil_families = [f for f in families if '†' in f]
            
            # Display Superfamily name, removing the † if present for the title, but not for the logic
            display_superfamily = superfamily.rstrip('†').strip()
            
            print(f"  Superfamily: {display_superfamily} (Total: {len(families)})")
            
            if extant_families:
                print(f"    Extant Families: {', '.join(extant_families)}")
            
            if fossil_families:
                # Remove the trailing '†' for cleaner display
                cleaned_fossils = [f.rstrip('†').strip() for f in fossil_families]
                print(f"    Fossil Families: {', '.join(cleaned_fossils)}")
        print("-" * 70)
        
    print("\n--- Flat List (In Order of Appearance) ---")
    print(all_families)


# --- MAIN EXECUTION ---

if __name__ == "__main__":
    # Check if requests and BeautifulSoup are installed (optional but helpful)
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("Required libraries 'requests' and 'beautifulsoup4' are not installed.")
        print("Please install them using: uv pip install requests beautifulsoup4")
        exit()

    # 1. Fetch the data from the website
    raw_content = fetch_taxonomy_data(WIKI_URL)
    
    if raw_content:
        # **DEBUGGING STEP: Print the raw content being parsed**
        print("\n--- DEBUG: RAW CONTENT EXTRACTED (Inspect this if parsing fails) ---")
        print(raw_content)
        print("------------------------------------------------------------------\n")
        
        print("\nStep 2: Parsing extracted content...")
        
        # 2. Parse the Raw Content into a structured dictionary
        trichoptera_families = parse_trichoptera_data(raw_content)
        
        if trichoptera_families:
            print("Step 3: Parsing complete. Displaying results.")
            
            # 3. Print the organized list of families
            print_families_by_suborder(trichoptera_families)
        else:
            print("\nError: Failed to parse any families from the extracted content.")
            
    else:
        print(f"\nCould not retrieve content from {WIKI_URL} due to extraction or network issues.")