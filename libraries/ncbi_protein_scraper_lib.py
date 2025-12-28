import json
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, TypeVar

import requests

# Basic headers; override or extend if needed
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

NCBI_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
NCBI_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
NCBI_TAXONOMY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
RANK_META_KEY = "__rank__"


def safe_filename(name: str, max_len: int = 80) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]', "", name)
    cleaned = re.sub(r"\s+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned[:max_len].lower()


def safe_join(base: Path, parts: List[str], max_length: int = 240) -> Path:
    """
    Join path parts under base, abbreviating with short hashes if the full path
    would exceed max_length (helps on Windows path length limits).
    """
    path = base
    for part in parts:
        candidate = path / part
        if len(str(candidate)) >= max_length:
            short = (part[:16] + "_" + hex(abs(hash(part)) & 0xFFFF)[2:]).strip("_")
            candidate = path / short
        path = candidate
    return path


T = TypeVar("T")


def chunked(iterable: Sequence[T], size: int) -> List[List[T]]:
    return [list(iterable[i:i + size]) for i in range(0, len(iterable), size)]


def extract_taxonomy_and_sequence(genbank_text: str) -> Tuple[str, List[str], str]:
    organism = "Unknown organism"
    taxonomy: List[str] = []
    sequence = ""
    lines = genbank_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("  ORGANISM"):
            organism = line[len("  ORGANISM"):].strip() or organism
            i += 1
            tax_lines: List[str] = []
            while i < len(lines) and lines[i].startswith(" " * 12):
                tax_lines.append(lines[i].strip())
                i += 1
            taxonomy_text = " ".join(tax_lines)
            taxonomy = [p.strip().strip(".") for p in taxonomy_text.split(";") if p.strip()]
        if line.startswith("ORIGIN"):
            i += 1
            seq_parts: List[str] = []
            while i < len(lines) and not lines[i].startswith("//"):
                seq_parts.append(re.sub(r"[^A-Za-z*]", "", lines[i]))
                i += 1
            sequence = "".join(seq_parts).upper()
            break
        i += 1
    return organism, taxonomy, sequence


def fetch_ids(term: str, api_key: Optional[str]) -> List[str]:
    params = {
        "db": "protein",
        "term": term,
        "retmax": 200,
        "retmode": "xml",
        "idtype": "acc",
    }
    if api_key:
        params["api_key"] = api_key
    resp = SESSION.get(NCBI_ESEARCH_URL, params=params, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    not_found = root.find(".//ErrorList/PhraseNotFound")
    if not_found is not None and (not_found.text or "").strip():
        return []
    return [el.text.strip() for el in root.findall(".//IdList/Id") if el.text]


def fetch_ids_all(
    term: str,
    api_key: Optional[str],
    batch: int = 50000,
    max_records: Optional[int] = None, # limit total records fetched
) -> List[str]:
    """
    Pull the full ID list by paging retstart/retmax.
    NCBI caps retmax at 100000; 50000 is a safe default.
    """
    retstart = 0
    ids: List[str] = []
    total = None

    while True:
        params = {
            "db": "protein",
            "term": term,
            "retstart": retstart,
            "retmax": batch,
            "retmode": "xml",
            "idtype": "acc",
        }
        if api_key:
            params["api_key"] = api_key
        resp = SESSION.get(NCBI_ESEARCH_URL, params=params, timeout=30)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)

        if total is None:
            total = int(root.findtext(".//Count") or "0")
            print(f"[INFO] ESearch found {total} IDs for '{term}'")

        not_found = root.find(".//ErrorList/PhraseNotFound")
        if not_found is not None and (not_found.text or "").strip():
            break

        ids.extend([el.text.strip() for el in root.findall(".//IdList/Id") if el.text])
        retstart += batch

        if max_records and len(ids) >= max_records:
            ids = ids[:max_records]
            break
        if retstart >= total:
            break

        # brief pause to avoid hammering ESearch if loops are large
        time.sleep(0.05)

    return ids


def fetch_summaries(
    ids: List[str],
    api_key: Optional[str],
    chunk_size: int = 150,
    max_retries: int = 3,
) -> List[Tuple[str, str, Optional[str]]]:
    results: List[Tuple[str, str, Optional[str]]] = []
    for chunk in chunked(ids, chunk_size):
        params = {"db": "protein", "id": ",".join(chunk), "retmode": "xml"}
        if api_key:
            params["api_key"] = api_key

        resp_text: Optional[str] = None
        for attempt in range(max_retries):
            try:
                resp = SESSION.get(NCBI_ESUMMARY_URL, params=params, timeout=30)
                # Treat 429/5xx as transient
                if resp.status_code == 429 or resp.status_code >= 500:
                    raise requests.HTTPError(f"Status {resp.status_code}", response=resp)
                resp.raise_for_status()
                resp_text = resp.text
                break
            except Exception as exc:
                if attempt == max_retries - 1:
                    print(
                        f"[WARN] ESummary failed for chunk size {len(chunk)} "
                        f"after {max_retries} attempts: {exc}"
                    )
                    resp_text = None
                else:
                    delay = min(2 ** attempt, 8)
                    print(
                        f"[WARN] ESummary error (attempt {attempt + 1}/{max_retries}) "
                        f"for chunk size {len(chunk)}: {exc}. Retrying in {delay}s..."
                    )
                    time.sleep(delay)
        if not resp_text:
            continue

        root = ET.fromstring(resp_text)
        for docsum in root.findall(".//DocSum"):
            accession = None
            title = None
            taxid = None
            for item in docsum.findall("Item"):
                name = item.attrib.get("Name")
                if name == "Title":
                    title = (item.text or "").strip()
                elif name in ("AccessionVersion", "Caption"):
                    accession = accession or (item.text or "").strip()
                elif name == "TaxId":
                    taxid = (item.text or "").strip()
            if accession and title:
                results.append((accession, title, taxid))
    return results


def fetch_genbank(accession: str, api_key: Optional[str]) -> Tuple[str, List[str], str]:
    params = {"db": "protein", "id": accession, "rettype": "gp", "retmode": "text"}
    if api_key:
        params["api_key"] = api_key
    resp = SESSION.get(NCBI_EFETCH_URL, params=params, timeout=30)
    resp.raise_for_status()
    return extract_taxonomy_and_sequence(resp.text)

def fetch_genbank_batch(
    accessions: List[str],
    api_key: Optional[str],
    max_retries: int = 3,
) -> Dict[str, Tuple[str, List[str], str]]:
    """
    Fetch multiple GenBank (GenPept) records in one EFetch call.
    Returns a dict: accession -> (organism, taxonomy, sequence).
    """
    if not accessions:
        return {}

    params = {
        "db": "protein",
        "id": ",".join(accessions),
        "rettype": "gp",
        "retmode": "text",
    }
    if api_key:
        params["api_key"] = api_key

    # Simple retry/backoff for 429s etc.
    for attempt in range(max_retries):
        resp = SESSION.get(NCBI_EFETCH_URL, params=params, timeout=60)
        if resp.status_code == 429:
            # too many requests; exponential backoff
            delay = 2 ** attempt
            print(
                f"[WARN] 429 from NCBI EFetch (batch of {len(accessions)}). "
                f"Sleeping {delay}s and retrying..."
            )
            time.sleep(delay)
            continue
        resp.raise_for_status()
        break
    else:
        # exhausted retries
        resp.raise_for_status()

    text = resp.text.replace("\r\n", "\n").strip()
    raw_records = [rec for rec in text.split("\n//") if rec.strip()]

    if len(raw_records) != len(accessions):
        print(
            f"[WARN] Expected {len(accessions)} GenBank records, "
            f"got {len(raw_records)}. Proceeding with min(len(ids), len(records))."
        )

    results: Dict[str, Tuple[str, List[str], str]] = {}
    for acc, rec_text in zip(accessions, raw_records):
        organism, taxonomy, seq = extract_taxonomy_and_sequence(rec_text)
        results[acc] = (organism, taxonomy, seq)
    return results


def fetch_taxonomy_lineage(taxid: str, api_key: Optional[str]) -> List[Tuple[str, str]]:
    """
    Fetch ranked lineage from NCBI Taxonomy for a given TaxID.
    Returns a list of (rank, scientific_name) tuples.
    """
    params = {"db": "taxonomy", "id": taxid, "retmode": "xml"}
    if api_key:
        params["api_key"] = api_key
    resp = SESSION.get(NCBI_TAXONOMY_URL, params=params, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    lineage: List[Tuple[str, str]] = []
    for taxon in root.findall(".//LineageEx/Taxon"):
        rank = (taxon.findtext("Rank") or "").strip()
        name = (taxon.findtext("ScientificName") or "").strip()
        if rank and name:
            lineage.append((rank, name))
    # include the queried taxon itself
    this_rank = (root.findtext(".//Taxon/Rank") or "").strip()
    this_name = (root.findtext(".//Taxon/ScientificName") or "").strip()
    if this_rank and this_name:
        lineage.append((this_rank, this_name))
    return lineage


def _set_rank_meta(node: Dict[str, Any], rank: Optional[str]) -> None:
    if rank and RANK_META_KEY not in node:
        node[RANK_META_KEY] = rank


def classify_type(title: str, expected_types: List[str]) -> str:
    """
    Classify a title to a canonical type.
    expected_types can be:
      - List[str]: simple priority-ordered substrings (legacy).
      - Dict[str, List[str]]: mapping canonical type -> list of substrings/aliases.
    Returns the canonical type on match, else "Unknown_type".
    """
    tl = title.lower()

    # Mapping form
    if isinstance(expected_types, dict):  # type: ignore[arg-type]
        for canonical, aliases in expected_types.items():  # type: ignore[union-attr]
            for alias in aliases:
                if alias.lower() in tl:
                    return canonical
        return "Unknown_type"

    # List form (legacy)
    for t in expected_types:
        if t.lower() in tl:
            return t
    return "Unknown_type"


def run_ncbi_protein_scraper(
    order_name: str,
    family_names: Optional[List[str]] = None,
    protein_terms: Optional[List[str]] = None,
    expected_types: Optional[List[str]] = None,
    api_key: Optional[str] = None,
    output_root: str = "ncbi_sequences",
    sleep_time: float = 0.20,
) -> None:
    """
    Generic scraper: searches NCBI Protein for <order> <protein_term>, downloads GenBank,
    and saves JSON/Markdown under a nested tree:
    order / ...taxonomy... / species / partial|full / type / files
    """
    protein_terms = protein_terms or ["fibroin"]
    expected_types = expected_types or ["Heavy Chain", "Light Chain"]
    family_names = family_names or []
    root_dir = Path(output_root)
    root_dir.mkdir(exist_ok=True)
    phylo_tree: Dict[str, Any] = {}
    total_saved = 0
    tax_cache: Dict[str, List[Tuple[str, str]]] = {}  # <-- here, once per run
    target_ranks = ["order", "suborder", "infraorder", "superfamily",
                    "family", "subfamily", "tribe", "genus"]
    target_ranks_set = {r.lower() for r in target_ranks}
    order_lower = order_name.lower()

    scopes = [order_name] + family_names  # try order-wide, then family-specific

    for scope in scopes:
        for protein_term in protein_terms:
            # Prefer an organism-scoped query to keep results within the clade.
            org_query = f"\"{scope}\"[Organism] AND {protein_term}"
            fallback_query = f"{scope} {protein_term}"

            primary_ids: List[str] = []
            try:
                primary_ids = fetch_ids_all(org_query, api_key)
            except Exception as exc:
                print(f"[INFO] ESearch failed for '{org_query}': {exc}")

            fallback_ids: List[str] = []
            if not primary_ids:
                try:
                    fallback_ids = fetch_ids_all(fallback_query, api_key)
                except Exception as exc:
                    print(f"[INFO] ESearch failed for '{fallback_query}': {exc}")

            combined_ids: List[str] = []
            seen_ids: set[str] = set()

            for _id in primary_ids + fallback_ids:
                if _id not in seen_ids:
                    seen_ids.add(_id)
                    combined_ids.append(_id)

            if not combined_ids:
                print(f"[INFO] No results for '{org_query}' or '{fallback_query}'")
                continue

            try:
                summaries = fetch_summaries(combined_ids, api_key)
            except Exception as exc:
                print(f"[INFO] No results for '{org_query}' (ESummary failed: {exc})")
                continue

            print(f"[INFO] {org_query} (+fallback): {len(summaries)} candidate proteins")

            BATCH_FETCH = 150  # tune 100-200 based on throttle/response size

            for summaries_chunk in chunked(summaries, BATCH_FETCH):
                accession_chunk = [acc for acc, _, _ in summaries_chunk]

                if sleep_time > 0:
                    time.sleep(sleep_time)

                try:
                    gb_map = fetch_genbank_batch(accession_chunk, api_key)
                except Exception as exc:
                    print(f"[WARN] EFetch batch failed for {len(accession_chunk)} accessions: {exc}")
                    continue

                for accession, title, taxid in summaries_chunk:
                    if accession not in gb_map:
                        print(f"[WARN] No GenBank data for {accession}")
                        continue

                    organism, taxonomy_full, origin_seq = gb_map[accession]
                    if not origin_seq:
                        continue
                    taxonomy_anchor = order_lower

                    lineage = []
                    rank_by_name: Dict[str, str] = {}
                    if taxid:
                        if taxid in tax_cache:
                            ranked = tax_cache[taxid]
                        else:
                            try:
                                ranked = fetch_taxonomy_lineage(taxid, api_key)
                            except Exception:
                                ranked = []
                            tax_cache[taxid] = ranked
                        if ranked:
                            for rk, nm in ranked:
                                if rk and nm:
                                    rank_by_name[nm] = rk
                            if ranked:
                                this_rank, this_name = ranked[-1]
                                if this_rank and this_name and organism != this_name and this_name in organism:
                                    rank_by_name[organism] = this_rank
                            filtered = [(rk, nm) for rk, nm in ranked if (rk or "").lower() in target_ranks_set]
                            started = False
                            lineage_names: List[str] = []
                            for rk, nm in filtered:
                                if nm.lower() == taxonomy_anchor or (rk.lower() == "order" and nm.lower() == taxonomy_anchor):
                                    started = True
                                if started:
                                    lineage_names.append(nm)
                            lineage = lineage_names

                    if not lineage:
                        for idx, name in enumerate(taxonomy_full):
                            if name.lower() == taxonomy_anchor:
                                lineage = taxonomy_full[idx:]
                                break
                        if not lineage:
                            continue
                        anchor_idx = 0
                        for i, name in enumerate(lineage):
                            if name.lower() == taxonomy_anchor:
                                anchor_idx = i
                                break
                        lineage = lineage[anchor_idx : anchor_idx + 8]
                        if taxonomy_anchor and taxonomy_anchor not in rank_by_name:
                            rank_by_name[taxonomy_anchor] = "order"
                        if organism and organism not in rank_by_name and " " in organism:
                            rank_by_name[organism] = "species"

                    is_partial = "partial" in title.lower()
                    seq_band = "partial" if is_partial else "full"
                    prot_type = classify_type(title, expected_types)
                    species = organism
                    path_nodes = lineage + [species, seq_band, prot_type]

                    safe_parts = [safe_filename(node) for node in path_nodes]
                    target = safe_join(root_dir, safe_parts)
                    target.mkdir(parents=True, exist_ok=True)
                    md_path = target / f"{accession}.md"
                    json_path = target / f"{accession}.json"

                    record = {
                        "accession": accession,
                        "title": title,
                        "family_query": scope,
                        "protein_term": protein_term,
                        "organism_name": organism,
                        "taxonomy_full": taxonomy_full,
                        "taxonomy_from_order": lineage,
                        "sequence_length": len(origin_seq),
                        "origin_sequence": origin_seq,
                        "partial_full": seq_band,
                        "type": prot_type,
                        "ncbi_url": f"https://www.ncbi.nlm.nih.gov/protein/{accession}",
                    }
                    json_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

                    md_content = f"""# Protein Record

- Accession: `{accession}`
- Title: `{title}`
- Query: `{scope} {protein_term}`
- Organism: `{organism}`
- Sequence length: `{len(origin_seq)}`
- Partial/Full: `{seq_band}`
- Type: `{prot_type}`
- NCBI URL: {record['ncbi_url']}

## Taxonomy (from {order_name})
{" > ".join(lineage)}

## ORIGIN
```text
{origin_seq}
```
"""
                    md_path.write_text(md_content, encoding="utf-8")

                    node = phylo_tree
                    for key in path_nodes[:-1]:
                        child = node.get(key)
                        if not isinstance(child, dict):
                            child = {}
                            node[key] = child
                        _set_rank_meta(child, rank_by_name.get(key))
                        node = child
                    node.setdefault(path_nodes[-1], []).append(
                        {"accession": accession, "title": title, "ncbi_url": record["ncbi_url"]}
                    )

                    total_saved += 1

    # save tree
    tree_path = root_dir / "phylo_tree.json"
    tree_path.write_text(json.dumps(phylo_tree, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[DONE] Saved {total_saved} records. Tree: {tree_path}")

    # also write a compact markdown view
    def _count_records(node: Any) -> int:
        if isinstance(node, list):
            return len(node)
        if isinstance(node, dict):
            return sum(_count_records(child) for child in node.values())
        return 0

    def _emit_md(lines: List[str], node: Any, depth: int = 0, max_depth: int = 8) -> None:
        if not isinstance(node, dict) or depth >= max_depth:
            return
        for key in sorted(node.keys()):
            if str(key).startswith("__"):
                continue
            child = node[key]
            cnt = _count_records(child)
            rank_tag = ""
            if isinstance(child, dict):
                rank = child.get(RANK_META_KEY)
                if isinstance(rank, str) and rank.strip():
                    rank_disp = rank.replace("_", " ").title()
                    rank_tag = f" [{rank_disp}]"
            lines.append(f"{'  '*depth}- {key}{rank_tag} ({cnt})")
            if isinstance(child, dict):
                _emit_md(lines, child, depth + 1, max_depth)

    tree_md_path = root_dir / "phylo_tree.md"
    md_lines: List[str] = [
        "# Phylogenetic Tree",
        "",
        f"- JSON file: `{tree_path.name}`",
        f"- Records saved: {total_saved}",
        f"- Root order: {order_name}",
        "",
        "## Tree (node name with record counts and ranks)",
    ]
    _emit_md(md_lines, phylo_tree, depth=0, max_depth=8)
    tree_md_path.write_text("\n".join(md_lines), encoding="utf-8")
