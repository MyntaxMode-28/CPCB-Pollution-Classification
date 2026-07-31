"""
CPCB Search Pipeline — implements Search_pipelines.md logic.
Deterministic matching: no LLM involved, so no hallucination risk.
"""
import re
import unicodedata
import pandas as pd
from rapidfuzz import fuzz
from seventeen_category import SEVENTEEN_CATEGORY

ABBREVIATIONS = {
    r"\bstp\b": "sewage treatment plant",
    r"\bcpp\b": "captive power plant",
    r"\bmsw\b": "municipal solid waste",
}

FILLER_WORDS = {"industry", "unit", "units", "other", "others", "miscellaneous", "general",
                 "facility", "plant", "and", "with", "using", "without", "having", "for", "captive"}

ALIASES = {
    "bakery": "bakery confectionery",
    "confectionary": "bakery confectionery",
    "confectionery": "bakery confectionery",
    "sweetshop": "bakery confectionery",
    "pastry": "bakery confectionery",
}


PRIORITY_TOKENS = {"internet", "cafe", "cyber", "cybercafe", "salon", "clinic", "shop",
                    "retail", "office", "studio", "kiosk", "bank", "atm", "center", "centre",
                    "bakery", "confectionery"}
HIGH_WEIGHT_TOKENS = {"pulp", "paper", "bleaching", "refinery", "pharmaceutical", "textile"}
LOW_WEIGHT_TOKENS = {"manufacturing", "processing", "production"}


def normalize(text: str) -> str:
    if not text:
        return ""
    text = str(text).lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    for pattern, repl in ABBREVIATIONS.items():
        text = re.sub(pattern, repl, text)
    text = re.sub(r"[^\w\s]", " ", text)
    tokens = [t for t in text.split() if t not in FILLER_WORDS]
    text = " ".join(tokens)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def canonicalize(user_input: str) -> str:
    """Return normalized input, boosted with alias tokens if matched — but never
    losing the original tokens (a full replace can break matching if the alias's
    own spelling/wording doesn't line up with the actual dataset entries)."""
    norm = normalize(user_input)
    input_tokens = set(norm.split())
    for alias_key, canonical in ALIASES.items():
        alias_tokens = set(alias_key.split())
        if alias_tokens and (alias_tokens.issubset(input_tokens) or norm == alias_key):
            canonical_norm = normalize(canonical)
            combined_tokens = input_tokens | set(canonical_norm.split())
            return " ".join(sorted(combined_tokens))
    return norm


def token_score(input_tokens: set, key_tokens: set) -> float:
    if not key_tokens:
        return 0.0
    overlap = input_tokens & key_tokens
    score = 0.0
    for t in overlap:
        if t in PRIORITY_TOKENS:
            score += 3.0
        elif t in HIGH_WEIGHT_TOKENS:
            score += 2.0
        elif t in LOW_WEIGHT_TOKENS:
            score += 0.5
        else:
            score += 1.0
    return score / max(len(key_tokens), 1)


class Database:
    def __init__(self, xlsx_path: str):
        self.cpcb = pd.read_excel(xlsx_path, sheet_name="CPCB list")
        self.white = pd.read_excel(xlsx_path, sheet_name="White sub sectors")
        self.not_in_ambit = pd.read_excel(xlsx_path, sheet_name="Not in ambit")
        self._prepare()

    def _prepare(self):
        # CPCB list: exclude header rows (blank/non-numeric PI)
        self.cpcb["search_key"] = self.cpcb["Sector/Activity Name"].apply(normalize)
        self.cpcb["_pi_numeric"] = pd.to_numeric(self.cpcb["Pollution Index (PI)"], errors="coerce")
        self.cpcb["_searchable"] = self.cpcb["_pi_numeric"].notna() & (self.cpcb["search_key"] != "")

        # White sub sectors: PI is always numeric here (inherits nothing missing in this sheet version)
        self.white["search_key"] = self.white["Sector/Activity Name"].apply(normalize)
        self.white["_pi_numeric"] = pd.to_numeric(self.white["Pollution Index"], errors="coerce")
        self.white["_searchable"] = self.white["search_key"] != ""

        self.not_in_ambit["search_key"] = self.not_in_ambit["Sector/Activity Name"].apply(normalize)
        self.not_in_ambit["_searchable"] = self.not_in_ambit["search_key"] != ""

    def search_17_category(self, user_input: str):
        """Search the corrected 17-category authoritative list. Returns list of matches."""
        query = canonicalize(user_input)
        query_tokens = set(query.split())
        matches = []
        for entry in SEVENTEEN_CATEGORY:
            key = normalize(entry["name"])
            key_tokens = set(key.split())
            if not key_tokens:
                continue
            if query == key or query in key or key in query:
                matches.append(entry)
                continue
            sim = fuzz.token_sort_ratio(query, key) / 100.0
            overlap = query_tokens & key_tokens
            overlap_ratio_of_query = len(overlap) / max(len(query_tokens), 1)
            # require the match to be strong from the QUERY's side (most of what the
            # user typed is actually present in the candidate name), not just any overlap
            if sim >= 0.78 or (overlap_ratio_of_query >= 0.8 and sim >= 0.55):
                matches.append(entry)
        return matches

    def search(self, user_input: str, top_n: int = 10):
        query = canonicalize(user_input)
        query_tokens = set(query.split())
        candidates = []

        seventeen_matches = self.search_17_category(user_input)
        if seventeen_matches:
            out = []
            for m in seventeen_matches:
                out.append({
                    "sector": m["name"], "category": m["category"], "pi": m["pi"],
                    "source": "17-Category Industries", "notes": "",
                    "seventeen_category": True,
                    "inspection_frequency": "Quarterly (17-Category Override)",
                })
            status = "exact" if len(out) == 1 else "multiple"
            return out, status

        sheets = [
            ("CPCB list", self.cpcb, "Category"),
            ("White sub sectors", self.white, None),
            ("Not in ambit", self.not_in_ambit, None),
        ]

        # STAGE 1: exact match — return immediately if found
        for sheet_name, df, cat_col in sheets:
            rows = df[df["_searchable"] & (df["search_key"] == query)]
            if len(rows):
                return self._format_results(rows, sheet_name), "exact"

        # STAGE 2 + 3: substring + weighted token overlap
        for sheet_name, df, cat_col in sheets:
            sub = df[df["_searchable"]]
            for idx, row in sub.iterrows():
                key = row["search_key"]
                key_tokens = set(key.split())
                score = 0.0
                if query in key or key in query:
                    score += 5.0
                score += token_score(query_tokens, key_tokens) * 3
                if score > 0:
                    candidates.append((score, sheet_name, idx))

        candidates.sort(key=lambda c: c[0], reverse=True)
        top_candidates = candidates[:15]

        # STAGE 4: fuzzy match refine
        scored = []
        for score, sheet_name, idx in top_candidates:
            df = {"CPCB list": self.cpcb, "White sub sectors": self.white,
                  "Not in ambit": self.not_in_ambit}[sheet_name]
            key = df.loc[idx, "search_key"]
            sim = fuzz.token_sort_ratio(query, key) / 100.0
            threshold = 0.55 if sheet_name == "White sub sectors" else 0.65
            if sim >= threshold or score >= 3.0:
                scored.append((score + sim * 5, sheet_name, idx))

        scored.sort(key=lambda c: c[0], reverse=True)
        results_by_sheet = {}
        for score, sheet_name, idx in scored[:top_n]:
            results_by_sheet.setdefault(sheet_name, []).append(idx)

        all_rows = []
        for sheet_name, idxs in results_by_sheet.items():
            df = {"CPCB list": self.cpcb, "White sub sectors": self.white,
                  "Not in ambit": self.not_in_ambit}[sheet_name]
            all_rows.extend(self._format_results(df.loc[idxs], sheet_name))

        if not all_rows:
            return [], "none"
        if len(all_rows) == 1:
            return all_rows, "exact"
        return all_rows[:top_n], "multiple"

    def _clean(self, val):
        """Convert pandas NaN/NaT to None or empty string so it's valid JSON."""
        if pd.isna(val):
            return None
        return val

    def _format_results(self, rows, sheet_name):
        out = []
        for _, row in rows.iterrows():
            if sheet_name == "CPCB list":
                out.append({
                    "sector": self._clean(row["Sector/Activity Name"]) or "",
                    "category": self._clean(row.get("Category", "")) or "",
                    "pi": self._clean(row.get("Pollution Index (PI)", None)),
                    "source": sheet_name,
                    "notes": self._clean(row.get("Remarks", "")) or "",
                })
            elif sheet_name == "White sub sectors":
                out.append({
                    "sector": self._clean(row["Sector/Activity Name"]) or "",
                    "category": "White",
                    "pi": self._clean(row.get("Pollution Index", None)),
                    "source": sheet_name,
                    "notes": f"Main sector: {self._clean(row.get('Main Sector', '')) or ''}",
                    "main_sector": self._clean(row.get("Main Sector", "")) or "",
                })
            else:
                out.append({
                    "sector": self._clean(row["Sector/Activity Name"]) or "",
                    "category": "Not in ambit",
                    "pi": None,
                    "source": sheet_name,
                    "notes": "",
                })
        return out
