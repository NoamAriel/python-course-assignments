import json
import re
import time
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen


INPUT_PATH = "subjects.txt"
OUTPUT_JSON = "submissions.json"
OUTPUT_MD = "submissions.md"
DEADLINES_PATH = "deadlines.md"
USE_SCRAPED = True

API_URL = "https://api.github.com/repos/Code-Maven/wis-python-course-2025-10/issues"
USER_AGENT = "Mozilla/5.0 (compatible; CodexScraper/1.0)"
REQUEST_DELAY_SECONDS = 0.2
STATE = "all"
PER_PAGE = 100
SKIP_PROJECTS = {"Missing Day03 and Day08 Issues", "Day09"}


@dataclass
class IssueEntry:
    number: int
    title: str
    url: str
    opened_at: str | None


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_timestamp(text: str) -> str:
    cleaned = re.sub(r"[^0-9TZ:\-+]", "", text.strip())
    return cleaned


def extract_project_submitter(title: str) -> tuple[str, str]:
    title = normalize_whitespace(title)

    by_match = re.search(r"\bby\b", title, flags=re.IGNORECASE)
    if by_match:
        project = normalize_whitespace(title[: by_match.start()])
        submitter = normalize_whitespace(title[by_match.end() :])
        return project, submitter

    if "-" in title:
        left, right = title.rsplit("-", 1)
        if right.strip():
            project = normalize_whitespace(left)
            submitter = normalize_whitespace(right)
            return project, submitter

    day_match = re.match(r"^(Day\s*\d+|day\s*\d+)\s+(.+)$", title)
    if day_match:
        project = normalize_whitespace(day_match.group(1))
        submitter = normalize_whitespace(day_match.group(2))
        return project, submitter

    return title, ""


def normalize_submitter(name: str) -> str:
    cleaned = normalize_whitespace(name.replace("-", " "))
    if not cleaned:
        return ""
    return " ".join(part.capitalize() for part in cleaned.split())


def normalize_project(project: str) -> str:
    match = re.match(r"^day\s*0*(\d+)$", project.strip(), flags=re.IGNORECASE)
    if match:
        day_num = int(match.group(1))
        return f"Day{day_num:02d}"
    if re.match(r"^final\s+project\s+proposal$", project.strip(), flags=re.IGNORECASE):
        return "Final Project Proposal"
    if re.match(r"^proposal\s+for\s+final\s+project$", project.strip(), flags=re.IGNORECASE):
        return "Final Project Proposal"
    return project


def split_projects(project: str) -> list[str]:
    match = re.match(
        r"^day\s*0*(\d+)\s+and\s+(?:day\s*)?0*(\d+)$",
        project.strip(),
        flags=re.IGNORECASE,
    )
    if match:
        first = normalize_project(f"Day{match.group(1)}")
        second = normalize_project(f"Day{match.group(2)}")
        return [first, second]
    match = re.match(
        r"^day\s*0*(\d+)\s+and\s+proposal\s+for\s+final\s+project$",
        project.strip(),
        flags=re.IGNORECASE,
    )
    if match:
        day_part = normalize_project(f"Day{match.group(1)}")
        return [day_part, "Final Project Proposal"]
    return [normalize_project(project)]


def parse_deadlines(path: str) -> dict:
    deadlines = {}

    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = normalize_whitespace(raw_line)
            if not line:
                continue

            none_match = re.match(r"^(.+?)\s+None$", line, flags=re.IGNORECASE)
            if none_match:
                project = normalize_project(none_match.group(1))
                deadlines[project] = None
                continue

            date_match = re.match(
                r"^(.+?)\s+Dead-line:\s+(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2})$",
                line,
                flags=re.IGNORECASE,
            )
            if date_match:
                project = normalize_project(date_match.group(1))
                deadline_str = date_match.group(2)
                deadline_dt = datetime.strptime(deadline_str, "%Y.%m.%d %H:%M")
                deadlines[project] = deadline_dt.replace(tzinfo=timezone.utc)

    return deadlines


def parse_submission_datetime(submitted_at: str) -> datetime | None:
    if not submitted_at:
        return None
    try:
        return datetime.fromisoformat(submitted_at.replace("Z", "+00:00"))
    except ValueError:
        return None


def fetch_json(url: str) -> list[dict]:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request) as response:
        payload = response.read().decode("utf-8", errors="replace")
    return json.loads(payload)


def scrape_issues() -> list[IssueEntry]:
    issues: list[IssueEntry] = []
    page = 1

    while True:
        url = f"{API_URL}?state={STATE}&per_page={PER_PAGE}&page={page}"
        try:
            items = fetch_json(url)
        except HTTPError as exc:
            if exc.code == 403:
                raise SystemExit(
                    "GitHub API rate limit reached. Try again later or use a token."
                ) from exc
            raise

        if not items:
            break

        for item in items:
            if "pull_request" in item:
                continue
            issues.append(
                IssueEntry(
                    number=item.get("number"),
                    title=item.get("title") or "",
                    url=item.get("html_url") or "",
                    opened_at=item.get("created_at"),
                )
            )

        page += 1
        time.sleep(REQUEST_DELAY_SECONDS)

    return issues


def format_timedelta(delta_seconds: int) -> str:
    sign = "-" if delta_seconds < 0 else "+"
    seconds = abs(delta_seconds)
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, sec = divmod(remainder, 60)
    if days:
        return f"{sign}{days}d {hours:02d}:{minutes:02d}:{sec:02d}"
    return f"{sign}{hours:02d}:{minutes:02d}:{sec:02d}"


def parse_issues(issues: list[IssueEntry], deadlines: dict) -> "OrderedDict[str, list[dict]]":
    data: "OrderedDict[str, list[dict]]" = OrderedDict()

    for issue in issues:
        title = issue.title.strip()
        submitted_at = issue.opened_at or ""
        project, submitter = extract_project_submitter(title)
        if normalize_project(project) in SKIP_PROJECTS:
            continue
        submitter = normalize_submitter(submitter)
        submitted_dt = parse_submission_datetime(submitted_at)

        entry = {
            "submitter": submitter or None,
            "submitted_at": submitted_at,
        }
        for normalized in split_projects(project):
            deadline_dt = deadlines.get(normalized)
            if submitted_dt and deadline_dt:
                delta_seconds = int((submitted_dt - deadline_dt).total_seconds())
                entry_with_deadline = {
                    **entry,
                    "on_time": delta_seconds <= 0,
                    "delta_seconds": delta_seconds,
                    "delta_human": format_timedelta(delta_seconds),
                }
            else:
                entry_with_deadline = {
                    **entry,
                    "on_time": None,
                    "delta_seconds": None,
                    "delta_human": None,
                }
            data.setdefault(normalized, []).append(entry_with_deadline)

    return data


def parse_subjects(path: str, deadlines: dict) -> "OrderedDict[str, list[dict]]":
    data: "OrderedDict[str, list[dict]]" = OrderedDict()

    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue

            parts = [p for p in line.split("\t") if p != ""]
            if len(parts) < 4:
                continue

            title = parts[2].strip()
            submitted_at = clean_timestamp(parts[-1])
            project, submitter = extract_project_submitter(title)
            if normalize_project(project) in SKIP_PROJECTS:
                continue
            submitter = normalize_submitter(submitter)
            submitted_dt = parse_submission_datetime(submitted_at)

            entry = {
                "submitter": submitter or None,
                "submitted_at": submitted_at,
            }
            for normalized in split_projects(project):
                deadline_dt = deadlines.get(normalized)
                if submitted_dt and deadline_dt:
                    delta_seconds = int((submitted_dt - deadline_dt).total_seconds())
                    entry_with_deadline = {
                        **entry,
                        "on_time": delta_seconds <= 0,
                        "delta_seconds": delta_seconds,
                        "delta_human": format_timedelta(delta_seconds),
                    }
                else:
                    entry_with_deadline = {
                        **entry,
                        "on_time": None,
                        "delta_seconds": None,
                        "delta_human": None,
                    }
                data.setdefault(normalized, []).append(entry_with_deadline)

    return data


def write_json(path: str, data: dict) -> None:
    ordered = OrderedDict(
        (project, sort_entries(entries))
        for project, entries in order_projects(data).items()
    )
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(ordered, handle, indent=2, ensure_ascii=True)


def write_md(path: str, data: dict) -> None:
    lines = ["# Submissions", ""]

    for project, entries in order_projects(data).items():
        lines.append(f"## {project}")
        lines.append("")
        lines.append("| Submitter | Submitted At | On Time | Delta |")
        lines.append("| --- | --- | --- | --- |")
        for entry in sort_entries(entries):
            submitter = entry["submitter"] or "Unknown"
            submitted_at = entry["submitted_at"]
            if entry["on_time"] is True:
                on_time = "Yes"
            elif entry["on_time"] is False:
                on_time = "No"
            else:
                on_time = "Unknown"
            delta = entry["delta_human"] or "Unknown"
            lines.append(f"| {submitter} | {submitted_at} | {on_time} | {delta} |")
        lines.append("")

    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def order_projects(data: dict) -> "OrderedDict[str, list[dict]]":
    ordered: "OrderedDict[str, list[dict]]" = OrderedDict()
    day_keys = []
    other_keys = []

    for key in data.keys():
        if re.match(r"^Day\d{2}$", key):
            day_keys.append(key)
        elif key == "Final Project Proposal":
            continue
        else:
            other_keys.append(key)

    for day in sorted(day_keys, key=lambda k: int(k[3:])):
        ordered[day] = data[day]

    if "Final Project Proposal" in data:
        ordered["Final Project Proposal"] = data["Final Project Proposal"]

    for key in other_keys:
        ordered[key] = data[key]

    return ordered


def sort_entries(entries: list[dict]) -> list[dict]:
    return sorted(
        entries,
        key=lambda entry: (entry["submitter"] or "Unknown").lower(),
    )


def get_submissions(deadlines: dict) -> "OrderedDict[str, list[dict]]":
    if USE_SCRAPED:
        issues = scrape_issues()
        return parse_issues(issues, deadlines)
    return parse_subjects(INPUT_PATH, deadlines)


def main() -> None:
    deadlines = parse_deadlines(DEADLINES_PATH)
    data = get_submissions(deadlines)
    write_json(OUTPUT_JSON, data)
    write_md(OUTPUT_MD, data)


if __name__ == "__main__":
    main()
