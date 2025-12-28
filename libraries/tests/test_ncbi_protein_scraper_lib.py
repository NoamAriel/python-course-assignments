from spiders.ncbi_protein_scraper_lib import run_ncbi_protein_scraper

run_ncbi_protein_scraper(
    order_name="Trichoptera",
    family_names=["Limnephilidae", "Hydropsychidae"],
    protein_terms=["fibroin"],
    expected_types=["Heavy Chain", "Light Chain"],
    output_root="ncbi_fibroin_sequences"
)
