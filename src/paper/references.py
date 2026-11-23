"""References of the paper: fetched from Crossref or arXiv, never typed from memory.

paper/references.yaml declares each reference by an identifier (a DOI or an arXiv number)
and by a fragment of the title that is expected. `fetch` asks the public service for the
record of this identifier and refuses it when the title does not hold the fragment, which
guards against a wrong identifier. Title, authors, venue, year and pages of the reference
list are those of the fetched record (paper/references.json); nothing else is added.

The list printed in the paper follows the Vancouver style of the journal, numbered in the
order of first citation, as in the template (IJASCA).
"""

import html
import re
import xml.etree.ElementTree as ET

import requests

CROSSREF = "https://api.crossref.org/works/{}"
ARXIV = "https://export.arxiv.org/api/query"
USER_AGENT = "reference-check/1.0 (python-requests)"   # no personal contact in the requests
ATOM = {"a": "http://www.w3.org/2005/Atom"}
MAX_AUTHORS = 6   # Vancouver: the first six authors, then "et al"


def clean(text: str) -> str:
    """Text of a field without markup, entities or line breaks."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", text or ""))).strip()


def normalise(text: str) -> str:
    """Lower-case letters and digits only: what two spellings of one title have in common."""
    return re.sub(r"[^a-z0-9]+", " ", clean(text).lower()).strip()


def session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    return s


def from_crossref(doi: str, s: requests.Session) -> dict:
    answer = s.get(CROSSREF.format(doi), timeout=60)
    answer.raise_for_status()
    m = answer.json()["message"]
    containers = [clean(name) for name in m.get("container-title") or []]
    record = {
        "source": "crossref", "doi": m["DOI"].lower(), "type": m["type"],
        "title": clean((m.get("title") or [""])[0]),
        "authors": [{"family": clean(a.get("family") or a.get("name") or ""), "given": clean(a.get("given") or "")}
                    for a in m.get("author") or []],
        # The year of the printed issue when there is one (it goes with the volume), else the first date.
        "year": ((m.get("published-print") or m.get("issued") or {}).get("date-parts") or [[None]])[0][0],
        # A chapter of a book series names the series first and the book last.
        "venue": containers[-1] if containers else "",
        "series": containers[0] if len(containers) > 1 else "",
        "volume": m.get("volume", ""), "issue": m.get("issue", ""),
        "pages": (m.get("page") or m.get("article-number") or "").replace("--", "-"),
        "publisher": clean(m.get("publisher") or ""),
    }
    subtitle = clean((m.get("subtitle") or [""])[0])
    if subtitle and normalise(subtitle) not in normalise(record["title"]):
        record["title"] = f"{record['title']}: {subtitle}"
    return record


def from_arxiv(number: str, s: requests.Session) -> dict:
    answer = s.get(ARXIV, params={"id_list": number}, timeout=60)
    answer.raise_for_status()
    entry = ET.fromstring(answer.text).find("a:entry", ATOM)
    if entry is None or entry.find("a:title", ATOM) is None:
        raise ValueError(f"arXiv has no record {number}")
    authors = []
    for author in entry.findall("a:author", ATOM):
        # arXiv gives one string per author: the last word is taken as the family name.
        *given, family = clean(author.find("a:name", ATOM).text).split()
        authors.append({"family": family, "given": " ".join(given)})
    return {"source": "arxiv", "arxiv": number, "doi": f"10.48550/arxiv.{number}", "type": "preprint",
            "title": clean(entry.find("a:title", ATOM).text), "authors": authors,
            "year": int(entry.find("a:published", ATOM).text[:4]),
            "venue": "", "series": "", "volume": "", "issue": "", "pages": "", "publisher": ""}


def fetch(key: str, declared: dict, s: requests.Session) -> dict:
    """Record of one declared reference; an error if the service does not give the expected title."""
    if ("doi" in declared) == ("arxiv" in declared):
        raise ValueError(f"{key}: declare either a doi or an arxiv number")
    record = from_crossref(declared["doi"], s) if "doi" in declared else from_arxiv(str(declared["arxiv"]), s)
    check(key, declared, record)
    record["expected_title"] = declared["title"]
    return record


def check(key: str, declared: dict, record: dict) -> None:
    """The record is the declared one: same identifier, expected title, authors and a year."""
    identifier = str(declared.get("doi") or declared.get("arxiv")).lower()
    if identifier not in (record.get("doi", ""), str(record.get("arxiv", "")).lower()):
        raise ValueError(f"{key}: the record is not the one of {identifier}")
    if normalise(declared["title"]) not in normalise(record["title"]):
        raise ValueError(f"{key}: expected a title with {declared['title']!r}, the record says {record['title']!r}")
    if not record["authors"] or not record["year"]:
        raise ValueError(f"{key}: the record has no author or no year")


# ---------------------------------------------------------------- printing


def tex(text: str) -> str:
    """Text of a record made safe for LaTeX."""
    text = text.replace("\\", " ")
    for char in "&%#_$":
        text = text.replace(char, "\\" + char)
    for char, written in {"{": "", "}": "", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}", "\u00a0": " ",
                          "\u2010": "-", "\u2011": "-", "\u2212": "-", "\u2009": " ", "\u202f": " "}.items():
        text = text.replace(char, written)
    return text


def initials(given: str) -> str:
    return "".join(part[0].upper() for part in re.split(r"[\s.\-]+", given) if part)


def person(author: dict) -> str:
    return f"{author['family']} {initials(author['given'])}".strip()


def vancouver(record: dict) -> str:
    """One entry of the reference list, in LaTeX."""
    names = [person(author) for author in record["authors"]]
    names = [*names[:MAX_AUTHORS], "et al"] if len(names) > MAX_AUTHORS else names
    title = record["title"] + ("" if record["title"][-1] in ".?!" else ".")
    year, pages = record["year"], record["pages"]
    if record["source"] == "arxiv":
        where = f"arXiv:{record['arxiv']} [Preprint]. {year}."
    elif record["type"] == "journal-article":
        where = f"{record['venue']}. {year}"
        if record["volume"]:
            where += f";{record['volume']}" + (f"({record['issue']})" if record["issue"] else "")
        where += (f":{pages}" if pages else "") + "."
    elif record["type"] in ("book", "monograph"):
        where = f"{record['publisher']}; {year}."
    else:   # paper of a proceedings volume or chapter of a book
        where = f"In: {record['venue']}" + (f". {record['series']}" if record["series"] else "") + f"; {year}."
        where += f" p. {pages}." if pages else ""
    doi = record["doi"]
    return (f"{tex(', '.join(names))}. {tex(title)} {tex(where)} "
            rf"doi: \href{{https://doi.org/{doi}}}{{\nolinkurl{{{doi}}}}}")


def cited_keys(texts: list[str]) -> list[str]:
    """Keys of the \\cite commands of the texts, in the order of their first use."""
    keys = []
    for text in texts:
        text = re.sub(r"(?<!\\)%.*", "", text)
        for group in re.findall(r"\\cite\{([^}]+)\}", text):
            keys += [key.strip() for key in group.split(",")]
    return list(dict.fromkeys(keys))


def thebibliography(keys: list[str], records: dict) -> str:
    """Reference list of the paper: the cited keys only, in the order given."""
    unknown = [key for key in keys if key not in records]
    if unknown:
        raise ValueError(f"cited but not verified (paper/references.json): {unknown}")
    lines = ["% Generated by scripts/11_paper.py from paper/references.json (records fetched from Crossref or arXiv",
             "% by scripts/11c_references.py). Do not edit: change paper/references.yaml and run both scripts.",
             rf"{{\small\begin{{thebibliography}}{{{max(len(keys), 1)}}}\setlength{{\itemsep}}{{1pt}}"]
    lines += [rf"\bibitem{{{key}}} {vancouver(records[key])}" for key in keys]
    return "\n".join([*lines, r"\end{thebibliography}}", ""])


BIB_TYPES = {"journal-article": "article", "proceedings-article": "inproceedings", "book-chapter": "incollection",
             "book": "book", "monograph": "book", "preprint": "misc"}


def bibtex(records: dict) -> str:
    """The same records as a BibTeX file, for whoever reuses the references."""
    entries = ["% Generated by scripts/11c_references.py from the records of Crossref and arXiv. Do not edit.\n"]
    for key, r in records.items():
        kind = BIB_TYPES.get(r["type"], "misc")
        venue = {"article": "journal", "inproceedings": "booktitle", "incollection": "booktitle"}.get(kind)
        fields = {"author": " and ".join(f"{a['family']}, {a['given']}".rstrip(", ") for a in r["authors"]),
                  "title": "{" + r["title"] + "}", "year": str(r["year"])}
        if venue and r["venue"]:
            fields[venue] = r["venue"]
        fields |= {name: r[name] for name in ("series", "volume", "pages", "publisher") if r[name]}
        if r["issue"]:
            fields["number"] = r["issue"]
        if r["source"] == "arxiv":
            fields |= {"eprint": r["arxiv"], "archiveprefix": "arXiv"}
        fields["doi"] = r["doi"]
        body = ",\n".join(f"  {name} = {{{value}}}" for name, value in fields.items())
        entries.append(f"@{kind}{{{key},\n{body}\n}}\n")
    return "\n".join(entries)
