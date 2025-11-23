import re
from typing import Dict, Any
from pathlib import Path

# --- Configuration ---
OUTPUT_ROOT_DIR = "ncbi_fibroin_sequences" # Root folder for all output

# --- Utility Functions (Related to saving files) ---

def safe_filename(name: str, max_len=50) -> str:
    """Generates a safe filename/directory name from a string."""
    safe_name = re.sub(r'[\\/:*?"<>|]', '', name).strip()
    # Normalize spaces and hyphens to underscores, remove dots
    safe_name = safe_name.replace(' ', '_').replace('-', '_').replace('.', '_').lower()
    return safe_name[:max_len]


# --- Content Generation Functions ---

def generate_sequence_markdown(data: Dict[str, str], chain_type: str, seq_type: str) -> str:
    """Creates human-readable Markdown content for a single sequence file."""
    
    sequence_lines = '\n'.join([data['sequence'][i:i+60] for i in range(0, len(data['sequence']), 60)])
    
    return f"""# Fibroin Sequence Details

| Key | Value |
| :--- | :--- |
| **Accession ID** | `{data['id']}` |
| **Full Name** | `{data['name']}` |
| **Organism Name** | `{data['organism']}` |
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
        "The output files are now nested by Family, then by **Organism** for finer organization.",
        ""
    ]
    
    total_sequences = 0
    
    # Start the detailed table
    content.append("## Detailed Sequence Counts by Family and Type")
    content.append("| Family Name | Total Found | Full (Heavy) | Full (Light) | Full (Other) | Partial (Heavy) | Partial (Light) | Partial (Other) |")
    content.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

    for family, organisms_data in sorted(results.items()):
        
        # Initialize counts for the current family by summing across all organisms
        full_heavy, full_light, full_other, partial_heavy, partial_light, partial_other = 0, 0, 0, 0, 0, 0

        for organism_name, seq_types in organisms_data.items():
            full_heavy += len(seq_types['full sequence']['heavy chain'])
            full_light += len(seq_types['full sequence']['light chain'])
            full_other += len(seq_types['full sequence']['others'])
            
            partial_heavy += len(seq_types['partial sequence']['heavy chain'])
            partial_light += len(seq_types['partial sequence']['light chain'])
            partial_other += len(seq_types['partial sequence']['others'])
        
        family_total = sum([full_heavy, full_light, full_other, partial_heavy, partial_light, partial_other])
        total_sequences += family_total

        # Append row to the table
        row = f"| {family} | **{family_total}** | {full_heavy} | {full_light} | {full_other} | {partial_heavy} | {partial_light} | {partial_other} |"
        content.append(row)

    content.append("")
    content.append("---")
    content.append(f"## GRAND TOTAL SEQUENCES DOWNLOADED: **{total_sequences}**")
    content.append(f"\nAll sequences are saved in the `{root_dir}` folder, organized hierarchically by Suborder, Superfamily, Family, **Organism**, Sequence Type, and Chain Type.")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
        print(f"Successfully generated summary index: {output_path}")
    except Exception as e:
        print(f"ERROR: Could not write summary index file: {e}")


def save_results_to_files(results: Dict[str, Any], path_map: Dict[str, Any]):
    """
    Creates the complex nested folder structure and saves all sequences.
    """
    print("\n" + "="*80)
    print(f"Step 3: Creating nested directories and saving sequences to: '{OUTPUT_ROOT_DIR}'")
    print("New Structure: Suborder/Superfamily/Family/Organism/Sequence Type/Chain Type/")
    print("="*80)
    
    root_dir = Path(OUTPUT_ROOT_DIR)
    root_dir.mkdir(exist_ok=True)
    
    total_files_saved = 0
    
    for family, organisms_data in results.items():
        if not organisms_data:
            continue
            
        if family not in path_map:
            print(f"WARNING: Skipping {family} - path information missing.")
            continue
            
        # --- 1. Create Top Level Taxonomy directories (Suborder/Superfamily/Family) ---
        suborder_name = path_map[family]['suborder']
        superfamily_name = path_map[family]['superfamily']

        # Path: ROOT/Suborder/Superfamily
        superfamily_dir = root_dir / safe_filename(suborder_name) / safe_filename(superfamily_name)
        superfamily_dir.mkdir(parents=True, exist_ok=True)

        # Path: ROOT/Suborder/Superfamily/Family
        family_dir = superfamily_dir / safe_filename(family)
        family_dir.mkdir(exist_ok=True)
        print(f"  Organizing data for {family} in: {family_dir.relative_to(root_dir)}")
        
        # --- 2. Iterate through Organism, Sequence Type and Chain Type ---
        for organism_name, org_data in organisms_data.items():
            
            # Path: Family/Organism
            organism_dir = family_dir / safe_filename(organism_name, 60) 
            organism_dir.mkdir(exist_ok=True)
            # print(f"    -> Processing Organism: {organism_name}")

            for seq_type, chain_types in org_data.items():
                
                type_dir = organism_dir / safe_filename(seq_type)
                type_dir.mkdir(exist_ok=True)
                
                for chain_type, sequences in chain_types.items():
                    
                    chain_dir = type_dir / safe_filename(chain_type)
                    chain_dir.mkdir(exist_ok=True)
                    
                    if not sequences:
                        continue
                    
                    for data in sequences:
                        
                        # 1. Prepare FASTA Content
                        fasta_header = f">{data['id']} {data['name']}"
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
                            print(f"      ERROR: Could not write FASTA file {fasta_file_path.name}: {e}")

                        # Save Markdown file
                        markdown_file_path = chain_dir / f"{final_filename_base}.md"
                        try:
                            with open(markdown_file_path, 'w', encoding='utf-8') as f:
                                f.write(markdown_content)
                            total_files_saved += 1
                        except Exception as e:
                            print(f"      ERROR: Could not write Markdown file {markdown_file_path.name}: {e}")

    # Generate the Index after saving all files
    generate_summary_index(results, OUTPUT_ROOT_DIR)

    print("\n" + "="*80)
    print(f"--- SUCCESS: Operation Complete. Total {total_files_saved} individual files saved (FASTA and MD). ---")
    print(f"Find your structured data and index in the '{OUTPUT_ROOT_DIR}' folder.")
    print("="*80)