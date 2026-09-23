from __future__ import annotations

import json
import math
import re
import time
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Callable, Iterable

import pymupdf
from docx import Document

from services.analyzer_knowledge import (
    BUSINESS_CONCEPTS,
    DEGREE_LABELS,
    DEGREE_PATTERNS,
    EDUCATION_FIELDS,
    EDUCATION_FIELD_RELATIONS,
    LANGUAGES,
    LANGUAGE_LEVELS,
    NEGATIVE_REQUIREMENT_MARKERS,
    PREFERRED_MARKERS,
    PROFESSIONAL_SIGNAL_WORDS,
    RELATED_ROLE_FAMILIES,
    REQUIRED_MARKERS,
    RESPONSIBILITY_MARKERS,
    ROLE_FAMILIES,
    ROLE_DOMAIN_SIGNALS,
    SENIORITY_PATTERNS,
    SKILLS,
    STOPWORDS,
    TITLE_STOPWORDS,
)
from services.settings_service import SettingsService
from services.semantic_match_service import SemanticMatchService

ProgressCallback = Callable[[str, int], None]


@dataclass(frozen=True)
class Mention:
    name: str
    importance: str
    evidence: str
    category: str = ""


@dataclass(frozen=True)
class Dimension:
    name: str
    weight: float
    applicable: bool
    ratio: float
    note: str


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def normalize(text: str) -> str:
    text = strip_accents(text).lower()
    text = text.replace("’", "'").replace("`", "'")
    text = re.sub(r"[\t\r]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenise(text: str) -> list[str]:
    clean = normalize(text)
    return re.findall(r"[a-z0-9][a-z0-9+#./-]*", clean)


def meaningful_tokens(text: str, *, title: bool = False) -> list[str]:
    stop = TITLE_STOPWORDS if title else STOPWORDS
    tokens = []
    for token in tokenise(text):
        token = token.strip("./-")
        if not token or token in stop:
            continue
        if len(token) < 3 and token not in {"sql", "aws", "gcp", "dax", "etl", "elt", "uat", "uml"}:
            continue
        if token.isdigit():
            continue
        tokens.append(token)
    return tokens


def flatten_json_strings(value) -> str:
    chunks: list[str] = []
    if isinstance(value, dict):
        for item in value.values():
            chunks.append(flatten_json_strings(item))
    elif isinstance(value, list):
        for item in value:
            chunks.append(flatten_json_strings(item))
    elif isinstance(value, (str, int, float)):
        chunks.append(str(value))
    return "\n".join(chunk for chunk in chunks if chunk)


def phrase_regex(phrase: str) -> re.Pattern[str]:
    phrase = normalize(phrase)
    escaped = re.escape(phrase)
    # Spaces in aliases can tolerate punctuation or repeated whitespace.
    escaped = escaped.replace(r"\ ", r"[\s\-_/.]+")
    return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", re.IGNORECASE)


def contains_phrase(text: str, phrase: str) -> bool:
    return bool(phrase_regex(phrase).search(normalize(text)))


def context_importance(text: str) -> str:
    n = normalize(text)
    if any(normalize(marker) in n for marker in NEGATIVE_REQUIREMENT_MARKERS):
        return "optional"
    if any(normalize(marker) in n for marker in REQUIRED_MARKERS):
        return "required"
    if any(normalize(marker) in n for marker in PREFERRED_MARKERS):
        return "preferred"
    return "neutral"


def split_evidence_units(text: str) -> list[str]:
    # Preserve list/bullet structure and also split very long paragraphs.
    raw_lines = [line.strip(" \t•*-–—") for line in (text or "").splitlines()]
    units: list[str] = []
    for line in raw_lines:
        if not line:
            continue
        parts = re.split(r"(?<=[.!?;])\s+", line)
        units.extend(part.strip() for part in parts if part.strip())
    return units


def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return max(0.0, min(1.0, numerator / denominator))


def weighted_average(pairs: Iterable[tuple[float, float]]) -> float:
    pairs = list(pairs)
    denominator = sum(weight for _, weight in pairs if weight > 0)
    if denominator <= 0:
        return 0.0
    return sum(value * weight for value, weight in pairs if weight > 0) / denominator


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------


class AnalyzerService:
    """
    JAM Match Engine v4.

    Local, deterministic and evidence-based. It is intentionally conservative:
    missing criteria never earn free points, and weak/garbage job descriptions
    return no score instead of an inflated number.
    """

    ENGINE_VERSION = "4.1"

    def __init__(self) -> None:
        self.settings = SettingsService()
        self.semantic = SemanticMatchService()
        self._skill_patterns = {
            canonical: [phrase_regex(alias) for alias in spec["aliases"]]
            for canonical, spec in SKILLS.items()
        }
        self._concept_patterns = {
            canonical: [phrase_regex(alias) for alias in aliases]
            for canonical, aliases in BUSINESS_CONCEPTS.items()
        }
        self._role_patterns = {
            canonical: [phrase_regex(alias) for alias in aliases]
            for canonical, aliases in ROLE_FAMILIES.items()
        }
        self._language_patterns = {
            canonical: [phrase_regex(alias) for alias in aliases]
            for canonical, aliases in LANGUAGES.items()
        }

    # ------------------------------------------------------------------
    # Progress
    # ------------------------------------------------------------------

    @staticmethod
    def _emit(callback: ProgressCallback | None, label: str, percent: int) -> None:
        if callback is None:
            return
        try:
            callback(label, int(max(0, min(100, percent))))
        except Exception:
            # UI callbacks must never break analysis.
            pass

    # ------------------------------------------------------------------
    # CV extraction
    # ------------------------------------------------------------------

    def extract_cv_text(self, path_value: str) -> str:
        path = Path(path_value)
        if not path.exists():
            raise FileNotFoundError("The selected CV file no longer exists.")

        suffix = path.suffix.lower()

        if suffix == ".pdf":
            with pymupdf.open(path) as doc:
                pages = [page.get_text("text") for page in doc]
            return "\n".join(pages).strip()

        if suffix == ".docx":
            document = Document(path)
            chunks = [p.text for p in document.paragraphs]
            # Tables often contain skills/education in CV templates.
            for table in document.tables:
                for row in table.rows:
                    chunks.extend(cell.text for cell in row.cells)
            return "\n".join(chunks).strip()

        if suffix in {".txt", ".md"}:
            return path.read_text(encoding="utf-8", errors="ignore").strip()

        if suffix == ".cvm":
            raw = path.read_text(encoding="utf-8", errors="ignore")
            try:
                return flatten_json_strings(json.loads(raw)).strip()
            except json.JSONDecodeError:
                return raw.strip()

        raise ValueError(
            "Supported CV formats: PDF, DOCX, TXT, MD and readable .cvm files."
        )

    # ------------------------------------------------------------------
    # Generic extraction
    # ------------------------------------------------------------------

    def extract_mentions(
        self,
        text: str,
        *,
        patterns: dict[str, list[re.Pattern[str]]],
        categories: dict[str, str] | None = None,
        classify_job_requirement: bool = False,
    ) -> list[Mention]:
        units = split_evidence_units(text)
        mentions: dict[str, Mention] = {}

        # If the input has no line breaks, still inspect the whole string.
        if not units and text.strip():
            units = [text.strip()]

        carried_importance: str | None = None
        carry_remaining = 0

        for unit in units:
            normalized_unit = normalize(unit)

            explicit_importance = context_importance(unit) if classify_job_requirement else "present"

            if classify_job_requirement:
                # Requirement lists are commonly formatted as:
                #   Required:
                #   - Databricks
                #   - Spark
                # or a sentence ending with "Required:" followed by wrapped
                # lines. Carry the section importance across a few following
                # units until a new responsibility/preference context appears.
                if explicit_importance in {"required", "preferred", "optional"}:
                    carried_importance = explicit_importance
                    carry_remaining = 4
                elif any(normalize(marker) in normalized_unit for marker in RESPONSIBILITY_MARKERS):
                    carried_importance = None
                    carry_remaining = 0
                elif carried_importance and carry_remaining > 0:
                    explicit_importance = carried_importance
                    carry_remaining -= 1
                else:
                    carried_importance = None
                    carry_remaining = 0

            for canonical, regexes in patterns.items():
                if not any(pattern.search(normalized_unit) for pattern in regexes):
                    continue

                importance = explicit_importance
                category = (categories or {}).get(canonical, "")

                previous = mentions.get(canonical)
                if previous is None:
                    mentions[canonical] = Mention(
                        canonical,
                        importance,
                        unit[:240],
                        category,
                    )
                elif classify_job_requirement:
                    priority = {"required": 4, "neutral": 3, "preferred": 2, "optional": 1}
                    if priority.get(importance, 0) > priority.get(previous.importance, 0):
                        mentions[canonical] = Mention(
                            canonical,
                            importance,
                            unit[:240],
                            category,
                        )

        return sorted(mentions.values(), key=lambda item: item.name.lower())

    def extract_skills(self, text: str, *, job: bool = False) -> list[Mention]:
        categories = {
            canonical: spec["category"]
            for canonical, spec in SKILLS.items()
        }
        return self.extract_mentions(
            text,
            patterns=self._skill_patterns,
            categories=categories,
            classify_job_requirement=job,
        )

    def extract_concepts(self, text: str, *, job: bool = False) -> list[Mention]:
        return self.extract_mentions(
            text,
            patterns=self._concept_patterns,
            classify_job_requirement=job,
        )

    def extract_role_families(self, text: str) -> list[str]:
        n = normalize(text)
        found = []
        for family, patterns in self._role_patterns.items():
            if any(pattern.search(n) for pattern in patterns):
                found.append(family)
        return found

    def extract_seniority(self, text: str) -> str | None:
        n = normalize(text)
        for label, aliases in SENIORITY_PATTERNS.items():
            if any(contains_phrase(n, alias) for alias in aliases):
                return label
        return None

    # ------------------------------------------------------------------
    # Experience
    # ------------------------------------------------------------------

    def extract_required_years(self, text: str) -> dict | None:
        n = normalize(text)
        patterns = [
            # English ranges / minimums
            r"\b(\d{1,2})\s*(?:-|–|—|to)\s*(\d{1,2})\s*\+?\s*(?:years?|yrs?)\b",
            r"\b(?:minimum|min\.?|at least)\s*(\d{1,2})\s*\+?\s*(?:years?|yrs?)\b",
            r"\b(\d{1,2})\s*\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:relevant\s+)?experience\b",
            r"\b(\d{1,2})\s*\+?\s*(?:years?|yrs?)\s+(?:minimum|required)\b",
            # French
            r"\b(\d{1,2})\s*(?:-|–|—|a|à)\s*(\d{1,2})\s*ans?\s+d[' ]?experience\b",
            r"\b(?:minimum|au moins)\s*(\d{1,2})\s*ans?\b",
            r"\b(\d{1,2})\s*ans?\s+d[' ]?experience\b",
            r"\bexperience\s+(?:de|d[' ])\s*(\d{1,2})\s*ans?\b",
        ]

        candidates: list[tuple[int, int | None, str]] = []
        for pattern in patterns:
            for match in re.finditer(pattern, n, flags=re.IGNORECASE):
                groups = match.groups()
                minimum = int(groups[0])
                maximum = int(groups[1]) if len(groups) > 1 and groups[1] else None
                if minimum > 20 or (maximum and maximum > 25):
                    continue
                candidates.append((minimum, maximum, match.group(0)))

        if not candidates:
            return None

        # Prefer the highest explicit minimum because it is the safest
        # interpretation when an ad contains multiple seniority examples.
        minimum, maximum, raw = max(candidates, key=lambda item: item[0])
        return {"min": minimum, "max": maximum, "raw": raw}

    @staticmethod
    def _month_number(value: str) -> int | None:
        value = normalize(value).strip(". ")
        months = {
            "jan": 1, "january": 1, "janvier": 1,
            "feb": 2, "february": 2, "fev": 2, "fevr": 2, "fevrier": 2,
            "mar": 3, "march": 3, "mars": 3,
            "apr": 4, "april": 4, "avr": 4, "avril": 4,
            "may": 5, "mai": 5,
            "jun": 6, "june": 6, "juin": 6,
            "jul": 7, "july": 7, "juil": 7, "juillet": 7,
            "aug": 8, "august": 8, "aout": 8,
            "sep": 9, "sept": 9, "september": 9, "septembre": 9,
            "oct": 10, "october": 10, "octobre": 10,
            "nov": 11, "november": 11, "novembre": 11,
            "dec": 12, "december": 12, "decembre": 12,
        }
        return months.get(value)

    def estimate_cv_years(self, text: str) -> dict:
        n = normalize(text)

        explicit = [
            float(value)
            for value in re.findall(
                r"\b(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?|ans?)\s+(?:of\s+|d[' ]?)?(?:professional\s+)?experience\b",
                n,
            )
            if float(value) <= 30
        ]

        now = datetime.now()
        intervals: list[tuple[int, int]] = []

        # Month name + year -> month name/year or present.
        month_names = (
            r"jan(?:uary|vier)?|feb(?:ruary)?|fev(?:rier)?|mar(?:ch|s)?|apr(?:il)?|avr(?:il)?|"
            r"may|mai|jun(?:e)?|juin|jul(?:y)?|juil(?:let)?|aug(?:ust)?|aout|"
            r"sep(?:t(?:ember|embre)?)?|oct(?:ober|obre)?|nov(?:ember|embre)?|dec(?:ember|embre)?"
        )
        pattern_month = re.compile(
            rf"\b({month_names})\.?\s+(20\d{{2}})\s*(?:-|–|—|to|a|à)\s*"
            rf"(?:(?P<endmonth>{month_names})\.?\s+)?(?P<endyear>20\d{{2}}|present|current|now|today|aujourd'hui|actuel|actuelle)\b",
            re.IGNORECASE,
        )
        for match in pattern_month.finditer(n):
            start_month = self._month_number(match.group(1)) or 1
            start_year = int(match.group(2))
            end_raw = match.group("endyear")
            if end_raw and end_raw.isdigit():
                end_year = int(end_raw)
                end_month = self._month_number(match.group("endmonth") or "") or 12
            else:
                end_year = now.year
                end_month = now.month
            start_idx = start_year * 12 + start_month - 1
            end_idx = end_year * 12 + end_month - 1
            if 0 <= end_idx - start_idx <= 360:
                intervals.append((start_idx, end_idx))

        # MM/YYYY ranges.
        pattern_numeric = re.compile(
            r"\b(0?[1-9]|1[0-2])[/.-](20\d{2})\s*(?:-|–|—|to|a|à)\s*"
            r"(?:(0?[1-9]|1[0-2])[/.-])?(20\d{2}|present|current|now|today|actuel|actuelle)\b",
            re.IGNORECASE,
        )
        for match in pattern_numeric.finditer(n):
            start_month = int(match.group(1))
            start_year = int(match.group(2))
            end_raw = match.group(4)
            if end_raw.isdigit():
                end_year = int(end_raw)
                end_month = int(match.group(3) or 12)
            else:
                end_year = now.year
                end_month = now.month
            start_idx = start_year * 12 + start_month - 1
            end_idx = end_year * 12 + end_month - 1
            if 0 <= end_idx - start_idx <= 360:
                intervals.append((start_idx, end_idx))

        # Year-only ranges, but only when not already covered by a month range.
        for match in re.finditer(
            r"\b(20\d{2})\s*(?:-|–|—|to|a|à)\s*(20\d{2}|present|current|now|today|actuel|actuelle)\b",
            n,
            flags=re.IGNORECASE,
        ):
            start_year = int(match.group(1))
            end_raw = match.group(2)
            end_year = int(end_raw) if end_raw.isdigit() else now.year
            start_idx = start_year * 12
            end_idx = end_year * 12 + (11 if end_raw.isdigit() else now.month - 1)
            if 0 <= end_idx - start_idx <= 360:
                intervals.append((start_idx, end_idx))

        # Merge overlapping month intervals.
        merged: list[list[int]] = []
        for start, end in sorted(set(intervals)):
            if not merged or start > merged[-1][1] + 1:
                merged.append([start, end])
            else:
                merged[-1][1] = max(merged[-1][1], end)

        months = sum(end - start + 1 for start, end in merged)
        range_years = round(months / 12.0, 1) if months else None
        explicit_years = max(explicit) if explicit else None

        candidates = [value for value in (explicit_years, range_years) if value is not None]
        years = max(candidates) if candidates else None

        return {
            "years": years,
            "explicit_years": explicit_years,
            "timeline_years": range_years,
            "interval_count": len(merged),
        }

    # ------------------------------------------------------------------
    # Education / languages / salary
    # ------------------------------------------------------------------

    def extract_degree_level(self, text: str) -> dict:
        n = normalize(text)
        detected = 0
        evidence = ""
        for pattern, level in DEGREE_PATTERNS:
            match = re.search(pattern, n, flags=re.IGNORECASE)
            if match and level > detected:
                detected = level
                evidence = match.group(0)
        return {
            "level": detected,
            "label": DEGREE_LABELS.get(detected, "Unknown"),
            "evidence": evidence,
        }

    def extract_education_profile(self, text: str, *, job: bool = False) -> dict:
        """Extract degree level plus field-of-study evidence.

        For job descriptions we only trust field names that appear in an
        education-looking unit (Master, Bac+3, BTS, formation, degree, etc.).
        This prevents a finance/accounting responsibility elsewhere in the ad
        from being mistaken for the requested diploma field.
        """
        units = split_evidence_units(text)
        education_markers = (
            "master", "bachelor", "licence", "bts", "dut", "dcg", "dscg",
            "bac+", "bac +", "degree", "diploma", "diplome", "diplôme",
            "formation", "education", "études", "etudes", "phd", "doctorat",
            "engineering degree", "diplome d'ingenieur", "diplôme d'ingénieur",
        )

        evidence_units = []
        for unit in units:
            nu = normalize(unit)
            if any(normalize(marker) in nu for marker in education_markers):
                evidence_units.append(unit)

        # A CV sometimes puts the degree title on the line immediately after an
        # EDUCATION heading. Include nearby short lines conservatively.
        if not job:
            lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
            for index, line in enumerate(lines):
                nl = normalize(line)
                if nl in {"education", "formation", "formations", "etudes", "études"}:
                    evidence_units.extend(lines[index + 1:index + 4])

        if not evidence_units:
            evidence_units = units if not job else []

        detected_levels: list[tuple[int, str]] = []
        for unit in evidence_units or [text]:
            nu = normalize(unit)
            for pattern, level in DEGREE_PATTERNS:
                match = re.search(pattern, nu, flags=re.IGNORECASE)
                if match:
                    detected_levels.append((level, unit[:260]))

        if detected_levels:
            # A job saying "Bac+2 ou Bac+3" asks for at least Bac+2; a CV
            # should advertise its highest evidenced level.
            level = min(item[0] for item in detected_levels) if job else max(item[0] for item in detected_levels)
            level_evidence = next(item[1] for item in detected_levels if item[0] == level)
        else:
            level = 0
            level_evidence = ""

        fields: list[str] = []
        field_evidence: dict[str, str] = {}
        search_units = evidence_units if evidence_units else ([] if job else units)

        for unit in search_units:
            unit_normalized = normalize(unit)

            # "Business School, Engineering School, or University" describes
            # acceptable institution TYPES, not a required Engineering field.
            # Likewise "engineering school" alone is not equivalent to
            # "engineering degree" / "degree in engineering".
            generic_institution_choice = bool(
                job
                and re.search(
                    r"\b(?:business\s+school|engineering\s+school|university)\b",
                    unit_normalized,
                )
                and not re.search(
                    r"\b(?:degree|master|bachelor|licence|diploma|diplome|diplôme)\s+(?:in|of|en)\s+engineering\b",
                    unit_normalized,
                )
            )

            if generic_institution_choice:
                # Degree level still counts, but no field restriction is
                # inferred from the institution wording.
                continue
            for field, aliases in EDUCATION_FIELDS.items():
                if field in fields:
                    continue
                if any(contains_phrase(unit, alias) for alias in aliases):
                    fields.append(field)
                    field_evidence[field] = unit[:260]

        return {
            "level": level,
            "label": DEGREE_LABELS.get(level, "Unknown"),
            "evidence": level_evidence,
            "fields": fields,
            "field_evidence": field_evidence,
        }

    @staticmethod
    def _education_field_similarity(required_field: str, cv_field: str) -> float:
        if required_field == cv_field:
            return 1.0
        if cv_field in EDUCATION_FIELD_RELATIONS.get(required_field, set()):
            return 0.70
        if required_field in EDUCATION_FIELD_RELATIONS.get(cv_field, set()):
            return 0.70
        return 0.0

    def extract_reference(self, text: str) -> dict | None:
        raw = text or ""
        patterns = [
            # Require a real separator/end boundary after short forms such as
            # "Ref" / "Réf" so words like "réflexions" cannot become fake
            # references (for example "lexions").
            (
                "Reference",
                r"(?im)(?:\b(?:reference|référence)\b|\b(?:ref|réf)\.?(?=\s|[:#-]))\s*(?:n[°o]\s*)?[:#-]?\s*([A-Z0-9][A-Z0-9._/-]{2,})\b",
            ),
            (
                "Job ID",
                r"(?im)\b(?:job\s*id|job\s*#|job\s*number)\b\s*[:#-]?\s*([A-Z0-9][A-Z0-9._/-]{2,})\b",
            ),
            (
                "Requisition",
                r"(?im)\b(?:requisition(?:\s*(?:id|number))?|req\.?\s*id)\b\s*[:#-]?\s*([A-Z0-9][A-Z0-9._/-]{2,})\b",
            ),
            (
                "Offer number",
                r"(?im)\b(?:offre\s*n[°o]|numero\s+d['’]offre|numéro\s+d['’]offre|n[°o]\s+de\s+poste)\s*[:#-]?\s*([A-Z0-9][A-Z0-9._/-]{2,})\b",
            ),
        ]

        for label, pattern in patterns:
            match = re.search(pattern, raw)
            if match:
                value = match.group(1).strip().rstrip(".,;)")
                if len(value) >= 3:
                    return {"label": label, "value": value, "evidence": match.group(0)[:220]}

        linkedin = re.search(r"linkedin\.com/jobs/view/(\d{6,})", raw, flags=re.IGNORECASE)
        if linkedin:
            return {"label": "LinkedIn Job ID", "value": linkedin.group(1), "evidence": linkedin.group(0)}

        return None

    def extract_languages(self, text: str, *, job: bool = False) -> list[dict]:
        units = split_evidence_units(text)
        found: dict[str, dict] = {}

        for unit in units:
            nu = normalize(unit)
            for language, patterns in self._language_patterns.items():
                if not any(pattern.search(nu) for pattern in patterns):
                    continue

                level = 0
                level_label = "Not specified"
                for label, numeric in LANGUAGE_LEVELS.items():
                    if contains_phrase(nu, label) and numeric > level:
                        level = numeric
                        level_label = label

                importance = context_importance(unit) if job else "present"
                previous = found.get(language)
                if previous is None or level > previous["level"]:
                    found[language] = {
                        "language": language,
                        "level": level,
                        "level_label": level_label,
                        "importance": importance,
                        "evidence": unit[:220],
                    }

        return sorted(found.values(), key=lambda item: item["language"])

    def extract_salary(self, text: str) -> dict | None:
        raw = (text or "").replace("\u202f", " ").replace("\xa0", " ")
        n = normalize(raw)

        currency = None
        if re.search(r"€|\beur\b|euros?", raw, flags=re.IGNORECASE):
            currency = "EUR"
        elif re.search(r"\btnd\b|\bdt\b|dinar", n):
            currency = "TND"
        elif re.search(r"\$|\busd\b", raw, flags=re.IGNORECASE):
            currency = "USD"
        elif re.search(r"£|\bgbp\b", raw, flags=re.IGNORECASE):
            currency = "GBP"

        def salary_period(start: int, end: int, *, default: str = "annual") -> str:
            context = n[max(0, start - 90): min(len(n), end + 90)]
            if re.search(r"\b(?:month|monthly|per month|mois|par mois|mensuel|mensuelle)\b", context):
                return "monthly"
            if re.search(r"\b(?:day|daily|per day|jour|par jour|journalier|journaliere)\b", context):
                return "daily"
            if re.search(r"\b(?:year|annual|annually|per year|an|annee|année|annuel|annuelle|par an)\b", context):
                return "annual"
            return default

        patterns = [
            r"(?:€|\$|£|eur|usd|gbp|tnd|dt)?\s*(\d{1,3}(?:[.,]\d+)?)\s*k\s*(?:-|–|—|to|a|à)\s*(?:€|\$|£|eur|usd|gbp|tnd|dt)?\s*(\d{1,3}(?:[.,]\d+)?)\s*k",
            r"(\d{2,3})\s*000\s*(?:€|\$|£|eur|usd|gbp|tnd|dt)?\s*(?:-|–|—|to|a|à)\s*(\d{2,3})\s*000",
        ]
        for pattern in patterns:
            match = re.search(pattern, n, flags=re.IGNORECASE)
            if match:
                a = float(match.group(1).replace(",", "."))
                b = float(match.group(2).replace(",", "."))
                if "k" in match.group(0):
                    a *= 1000
                    b *= 1000
                else:
                    a *= 1000
                    b *= 1000
                return {
                    "min": int(min(a, b)),
                    "max": int(max(a, b)),
                    "currency": currency,
                    "period": salary_period(match.start(), match.end(), default="annual"),
                    "raw": match.group(0),
                }

        single_k = re.search(
            r"(?:€|\$|£|eur|usd|gbp|tnd|dt)?\s*(\d{1,3}(?:[.,]\d+)?)\s*k\b",
            n,
            flags=re.IGNORECASE,
        )
        if single_k:
            value = int(float(single_k.group(1).replace(",", ".")) * 1000)
            return {
                "min": value,
                "max": value,
                "currency": currency,
                "period": salary_period(single_k.start(), single_k.end(), default="annual"),
                "raw": single_k.group(0),
            }

        # Tunisia ads often state "2000 DT" / "2500 TND" monthly.
        plain = re.search(
            r"\b(\d{3,6})\s*(tnd|dt|eur|€|usd|\$|gbp|£)\b",
            n,
            flags=re.IGNORECASE,
        )
        if plain:
            value = int(plain.group(1))
            plain_default = "monthly" if currency == "TND" else "annual"
            return {
                "min": value,
                "max": value,
                "currency": currency,
                "period": salary_period(plain.start(), plain.end(), default=plain_default),
                "raw": plain.group(0),
            }

        return None

    # ------------------------------------------------------------------
    # Lexical / role matching
    # ------------------------------------------------------------------

    def extract_cv_role_families(self, cv_text: str) -> list[str]:
        """Extract role families from role-title-like CV lines only.

        Scanning the whole CV for role words is too permissive. A course, tool,
        project, or banking internship can mention a domain without proving the
        candidate actually held that profession.
        """
        families: set[str] = set()
        lines = [line.strip(" \t•*-–—") for line in (cv_text or "").splitlines()]

        education_markers = {
            "master", "bachelor", "licence", "degree", "diploma", "diplome",
            "diplôme", "university", "universite", "université", "school",
            "ecole", "école", "certification", "course", "cours",
        }
        skill_markers = {
            "skills", "competences", "compétences", "tools", "outils",
            "technologies", "technical", "techniques",
        }

        for raw in lines:
            if not raw or len(raw) > 125:
                continue

            n = normalize(raw)
            tokens = meaningful_tokens(raw, title=True)
            if not tokens:
                continue

            if any(marker in n for marker in education_markers):
                continue
            if any(marker in n for marker in skill_markers):
                continue

            # Job-title lines are normally concise. Permit a little context for
            # lines such as "Data Analyst Intern | Company".
            if len(tokens) > 12:
                continue

            for family, regexes in self._role_patterns.items():
                if any(pattern.search(n) for pattern in regexes):
                    families.add(family)

        return sorted(families)

    def match_critical_domain(
        self,
        job_title: str,
        description: str,
        cv_text: str,
        role: dict,
    ) -> dict:
        """Compare profession-specific evidence from the JD with the CV.

        This prevents generic transferable words such as Excel/reporting from
        making an Accountant role look like a strong fit for a Data Analyst CV.
        """
        job_families = role.get("job_families") or self.extract_role_families(job_title)
        job_text = f"{job_title}\n{description}"
        job_n = normalize(job_text)
        cv_n = normalize(cv_text)

        detected: list[dict] = []
        matched: list[str] = []
        missing: list[str] = []

        for family in job_families:
            for signal in ROLE_DOMAIN_SIGNALS.get(family, []):
                if not contains_phrase(job_n, signal):
                    continue

                item = {
                    "family": family,
                    "signal": signal,
                    "matched": contains_phrase(cv_n, signal),
                }
                detected.append(item)
                if item["matched"]:
                    matched.append(signal)
                else:
                    missing.append(signal)

        # De-duplicate accent/spelling aliases by normalized meaning. Signals
        # such as "comptabilite" and "comptabilité" must count once.
        unique_map: dict[str, dict] = {}
        for item in detected:
            key = normalize(item["signal"])
            existing = unique_map.get(key)
            if existing is None:
                unique_map[key] = item
            elif item["matched"] and not existing["matched"]:
                unique_map[key] = item

        unique_items = list(unique_map.values())
        unique_detected = [item["signal"] for item in unique_items]
        matched = [item["signal"] for item in unique_items if item["matched"]]
        missing = [item["signal"] for item in unique_items if not item["matched"]]

        ratio = safe_ratio(len(matched), len(unique_detected)) if unique_detected else 0.0

        return {
            "applicable": bool(unique_detected),
            "ratio": ratio,
            "job_signals": unique_detected,
            "matched": matched,
            "missing": missing,
            "evidence": unique_items,
        }

    def title_similarity(self, title: str, cv_text: str) -> dict:
        title_tokens = meaningful_tokens(title, title=True)
        if not title_tokens:
            return {"ratio": 0.0, "direct": 0.0, "fuzzy": 0.0, "tokens": []}

        cv_tokens = set(meaningful_tokens(cv_text))
        direct = safe_ratio(sum(1 for token in title_tokens if token in cv_tokens), len(title_tokens))

        lines = [line.strip() for line in cv_text.splitlines() if line.strip()]
        fuzzy = 0.0
        normalized_title = normalize(title)
        for line in lines[:160]:
            if len(line) > 180:
                line = line[:180]
            fuzzy = max(fuzzy, SequenceMatcher(None, normalized_title, normalize(line)).ratio())

        return {
            "ratio": max(direct, fuzzy),
            "direct": direct,
            "fuzzy": fuzzy,
            "tokens": title_tokens,
        }

    def role_match(self, job_title: str, cv_text: str, job_description: str = "") -> dict:
        # Role/title alignment is a gate, not a cosmetic bonus. A CV that happens
        # to share Excel/SAP/reporting words with an unrelated profession must
        # never receive a very high score.
        job_families = self.extract_role_families(job_title)
        family_source = "title"

        if not job_families and job_description:
            # Some job-board titles are vague. Inspect only the opening part of
            # the description so the role is not inferred from an incidental
            # mention buried later in the ad.
            job_families = self.extract_role_families(job_description[:900])
            family_source = "description"

        cv_families = self.extract_cv_role_families(cv_text)
        title_similarity = self.title_similarity(job_title, cv_text)

        if job_families:
            best = 0.0
            relation = "No compatible role family found in the CV"
            matched_job_family = None
            matched_cv_family = None

            for job_family in job_families:
                if job_family in cv_families:
                    if best < 1.0:
                        best = 1.0
                        matched_job_family = job_family
                        matched_cv_family = job_family
                        relation = f"Direct role-family match: {job_family}"
                    continue

                related = RELATED_ROLE_FAMILIES.get(job_family, set())
                common = related.intersection(cv_families)

                if common and best < 0.68:
                    matched = sorted(common)[0]
                    best = 0.68
                    matched_job_family = job_family
                    matched_cv_family = matched
                    relation = f"Related role-family match: {job_family} ↔ {matched}"

            mismatch = best == 0.0

            if mismatch:
                # IMPORTANT: do not allow fuzzy title/token overlap to rescue an
                # explicitly unrelated role family. This is what previously let
                # generic Excel/reporting/accounting ads score absurdly high.
                ratio = min(0.12, title_similarity["ratio"] * 0.15)
                relation = (
                    f"Role-family mismatch: {', '.join(job_families)} is not "
                    "represented by the CV's role history"
                )
            else:
                # Direct/related family evidence is authoritative. Fuzzy title
                # similarity can only add a tiny refinement, never replace it.
                ratio = min(1.0, best + title_similarity["ratio"] * 0.05)

            return {
                "applicable": True,
                "ratio": ratio,
                "job_families": job_families,
                "cv_families": cv_families,
                "relation": relation,
                "title_similarity": title_similarity,
                "family_source": family_source,
                "mismatch": mismatch,
                "matched_job_family": matched_job_family,
                "matched_cv_family": matched_cv_family,
            }

        # Unknown/niche role: lexical title evidence is allowed, but capped.
        # A role that JAM cannot classify should not become a 90% match merely
        # because a couple of generic title words appear somewhere in the CV.
        if len(title_similarity["tokens"]) >= 2:
            ratio = min(0.60, title_similarity["ratio"])
            return {
                "applicable": True,
                "ratio": ratio,
                "job_families": [],
                "cv_families": cv_families,
                "relation": "Unclassified role: conservative lexical title comparison",
                "title_similarity": title_similarity,
                "family_source": "unclassified",
                "mismatch": ratio < 0.30,
                "matched_job_family": None,
                "matched_cv_family": None,
            }

        return {
            "applicable": False,
            "ratio": 0.0,
            "job_families": [],
            "cv_families": cv_families,
            "relation": "Job title is not specific enough to score",
            "title_similarity": title_similarity,
            "family_source": "none",
            "mismatch": False,
            "matched_job_family": None,
            "matched_cv_family": None,
        }

    # ------------------------------------------------------------------
    # Keyword / responsibility extraction
    # ------------------------------------------------------------------

    def extract_focus_keywords(self, job_title: str, description: str, limit: int = 18) -> list[str]:
        title_tokens = meaningful_tokens(job_title, title=True)
        units = split_evidence_units(description)
        counter: Counter[str] = Counter()

        for token in title_tokens:
            counter[token] += 4

        for unit in units:
            nu = normalize(unit)
            context_multiplier = 1
            if any(normalize(marker) in nu for marker in REQUIRED_MARKERS):
                context_multiplier = 3
            elif any(normalize(marker) in nu for marker in RESPONSIBILITY_MARKERS):
                context_multiplier = 2
            elif any(normalize(marker) in nu for marker in PREFERRED_MARKERS):
                context_multiplier = 1

            for token in meaningful_tokens(unit):
                counter[token] += context_multiplier

        # Ignore tokens that look like URL/domain debris.
        items = [
            (token, weight)
            for token, weight in counter.items()
            if not re.fullmatch(r"https?|www|com|fr|tn|html?", token)
        ]
        items.sort(key=lambda item: (-item[1], item[0]))
        return [token for token, _ in items[:limit]]

    # ------------------------------------------------------------------
    # Quality / analyzability
    # ------------------------------------------------------------------

    def evaluate_job_quality(
        self,
        job_title: str,
        description: str,
        skills: list[Mention],
        concepts: list[Mention],
        languages: list[dict],
        years: dict | None,
        degree: dict,
        roles: list[str],
    ) -> dict:
        desc_tokens = meaningful_tokens(description)
        all_tokens = tokenise(description)
        word_count = len(all_tokens)
        meaningful_count = len(desc_tokens)
        unique_ratio = safe_ratio(len(set(desc_tokens)), meaningful_count) if meaningful_count else 0.0

        n = normalize(description)
        requirement_markers = sum(1 for marker in REQUIRED_MARKERS + PREFERRED_MARKERS if normalize(marker) in n)
        professional_markers = sum(1 for marker in PROFESSIONAL_SIGNAL_WORDS if contains_phrase(n, marker))
        extracted_signals = (
            len(skills)
            + len(concepts)
            + len(languages)
            + (1 if years else 0)
            + (1 if degree["level"] else 0)
            + len(roles)
        )

        # Detect obvious placeholder/noise strings.
        suspicious_tokens = {
            "test", "testing", "random", "asdf", "qwerty", "lorem", "ipsum", "foo", "bar"
        }
        suspicious_count = sum(1 for token in desc_tokens if token in suspicious_tokens)
        suspicious_ratio = safe_ratio(suspicious_count, meaningful_count) if meaningful_count else 0.0

        title_specific = len(meaningful_tokens(job_title, title=True)) >= 2 or bool(roles)

        length_score = min(35.0, word_count / 100.0 * 35.0)
        signal_score = min(35.0, extracted_signals * 4.5 + professional_markers * 1.5)
        structure_score = min(20.0, requirement_markers * 4.0 + (5.0 if len(split_evidence_units(description)) >= 4 else 0.0))
        diversity_score = min(10.0, unique_ratio * 10.0)
        quality = int(round(max(0.0, length_score + signal_score + structure_score + diversity_score - suspicious_ratio * 45.0)))
        quality = max(0, min(100, quality))

        reasons: list[str] = []
        if word_count < 18 and extracted_signals < 3:
            reasons.append("The job description is too short to identify reliable requirements.")
        if extracted_signals < 2 and professional_markers < 2:
            reasons.append("JAM could not identify enough professional requirements or responsibilities.")
        if suspicious_ratio >= 0.20:
            reasons.append("The text looks like placeholder/test content rather than a real job offer.")
        if not title_specific and extracted_signals < 3:
            reasons.append("The job title is too generic to provide useful role evidence.")

        analyzable = (
            suspicious_ratio < 0.20
            and (
                (word_count >= 35 and extracted_signals >= 2)
                or extracted_signals >= 4
                or (word_count >= 70 and professional_markers >= 2)
            )
            and (title_specific or extracted_signals >= 4)
        )

        return {
            "analyzable": analyzable,
            "quality": quality,
            "word_count": word_count,
            "meaningful_word_count": meaningful_count,
            "unique_ratio": round(unique_ratio, 3),
            "extracted_signal_count": extracted_signals,
            "requirement_marker_count": requirement_markers,
            "professional_marker_count": professional_markers,
            "reasons": reasons,
        }

    def evaluate_cv_quality(
        self,
        cv_text: str,
        skills: list[Mention],
        languages: list[dict],
        degree: dict,
        experience: dict,
        roles: list[str],
    ) -> dict:
        words = tokenise(cv_text)
        signals = (
            len(skills)
            + len(languages)
            + len(roles)
            + (1 if degree["level"] else 0)
            + (1 if experience["years"] is not None else 0)
        )
        length_score = min(55.0, len(words) / 300.0 * 55.0)
        signal_score = min(45.0, signals * 2.5)
        quality = int(round(min(100.0, length_score + signal_score)))

        reasons = []
        if len(words) < 45:
            reasons.append("Very little readable CV text was extracted.")
        if signals < 3:
            reasons.append("The CV contains too little structured evidence for a reliable comparison.")

        return {
            "analyzable": len(words) >= 45 and signals >= 3,
            "quality": quality,
            "word_count": len(words),
            "signal_count": signals,
            "reasons": reasons,
        }

    # ------------------------------------------------------------------
    # Dimension matching
    # ------------------------------------------------------------------

    @staticmethod
    def _mention_map(mentions: list[Mention]) -> dict[str, Mention]:
        return {mention.name: mention for mention in mentions}

    def match_skills(self, job_skills: list[Mention], cv_skills: list[Mention]) -> dict:
        cv_map = self._mention_map(cv_skills)
        weights = {"required": 1.9, "neutral": 1.0, "preferred": 0.60, "optional": 0.20}

        total = 0.0
        matched_weight = 0.0
        matched: list[str] = []
        missing: list[str] = []
        missing_required: list[str] = []
        required_total = 0.0
        required_matched = 0.0
        evidence: list[dict] = []

        for mention in job_skills:
            weight = weights.get(mention.importance, 1.0)
            total += weight

            if mention.importance == "required":
                required_total += weight

            cv_mention = cv_map.get(mention.name)

            if cv_mention is not None:
                matched.append(mention.name)
                matched_weight += weight

                if mention.importance == "required":
                    required_matched += weight

                evidence.append({
                    "requirement": mention.name,
                    "importance": mention.importance,
                    "job_evidence": mention.evidence,
                    "cv_evidence": cv_mention.evidence,
                })
            else:
                missing.append(mention.name)

                if mention.importance == "required":
                    missing_required.append(mention.name)

        return {
            "applicable": bool(job_skills),
            "ratio": safe_ratio(matched_weight, total),
            "required_ratio": (
                safe_ratio(required_matched, required_total)
                if required_total
                else None
            ),
            "matched": sorted(matched),
            "missing": sorted(missing),
            "missing_required": sorted(missing_required),
            "job_count": len(job_skills),
            "cv_count": len(cv_skills),
            "evidence": evidence,
        }

    def match_concepts_keywords(
        self,
        job_title: str,
        description: str,
        job_concepts: list[Mention],
        cv_concepts: list[Mention],
        cv_text: str,
    ) -> dict:
        cv_concept_map = self._mention_map(cv_concepts)
        matched_concepts = [item.name for item in job_concepts if item.name in cv_concept_map]
        missing_concepts = [item.name for item in job_concepts if item.name not in cv_concept_map]
        concept_ratio = safe_ratio(len(matched_concepts), len(job_concepts)) if job_concepts else 0.0

        concept_evidence = []
        for item in job_concepts:
            cv_item = cv_concept_map.get(item.name)
            if cv_item is not None:
                concept_evidence.append({
                    "requirement": item.name,
                    "importance": item.importance,
                    "job_evidence": item.evidence,
                    "cv_evidence": cv_item.evidence,
                })

        keywords = self.extract_focus_keywords(job_title, description)
        cv_token_set = set(meaningful_tokens(cv_text))
        matched_keywords = [token for token in keywords if token in cv_token_set]
        missing_keywords = [token for token in keywords if token not in cv_token_set]
        keyword_ratio = safe_ratio(len(matched_keywords), len(keywords)) if keywords else 0.0

        # Responsibility/domain concepts are more meaningful than loose token
        # overlap, so keywords only refine the dimension.
        if job_concepts and keywords:
            ratio = concept_ratio * 0.78 + keyword_ratio * 0.22
        elif job_concepts:
            ratio = concept_ratio
        else:
            ratio = keyword_ratio

        applicable = bool(job_concepts) or len(keywords) >= 6

        return {
            "applicable": applicable,
            "ratio": max(0.0, min(1.0, ratio)),
            "matched_concepts": sorted(matched_concepts),
            "missing_concepts": sorted(missing_concepts),
            "matched_keywords": matched_keywords[:12],
            "missing_keywords": missing_keywords[:12],
            "focus_keywords": keywords,
            "evidence": concept_evidence,
        }

    def match_experience(self, required: dict | None, cv_experience: dict, seniority: str | None) -> dict:
        cv_years = cv_experience["years"]

        if required:
            required_years = required["min"]
            ratio = 0.0 if cv_years is None else min(1.0, cv_years / max(1, required_years))
            return {
                "applicable": True,
                "ratio": ratio,
                "required_years": required_years,
                "required_range_max": required.get("max"),
                "cv_years": cv_years,
                "source": "explicit years requirement",
            }

        seniority_thresholds = {
            "Internship": 0.0,
            "Junior": 0.5,
            "Senior": 4.0,
            "Lead": 6.0,
            "Manager": 5.0,
        }
        if seniority in seniority_thresholds:
            threshold = seniority_thresholds[seniority]
            if threshold <= 0:
                ratio = 1.0
            else:
                ratio = 0.0 if cv_years is None else min(1.0, cv_years / threshold)
            return {
                "applicable": True,
                "ratio": ratio,
                "required_years": threshold,
                "required_range_max": None,
                "cv_years": cv_years,
                "source": f"seniority signal: {seniority}",
            }

        return {
            "applicable": False,
            "ratio": 0.0,
            "required_years": None,
            "required_range_max": None,
            "cv_years": cv_years,
            "source": "not specified",
        }

    def match_education(self, job_degree: dict, cv_degree: dict) -> dict:
        required = int(job_degree.get("level") or 0)
        cv_level = int(cv_degree.get("level") or 0)
        required_fields = list(job_degree.get("fields") or [])
        cv_fields = list(cv_degree.get("fields") or [])

        if required <= 0 and not required_fields:
            return {
                "applicable": False,
                "ratio": 0.0,
                "level_ratio": 0.0,
                "field_ratio": None,
                "required": job_degree,
                "cv": cv_degree,
                "matched_field": None,
            }

        if required <= 0:
            level_ratio = 1.0
        elif cv_level >= required:
            level_ratio = 1.0
        elif cv_level == required - 1:
            level_ratio = 0.40
        else:
            level_ratio = 0.0

        matched_field = None
        field_ratio = None
        if required_fields:
            field_ratio = 0.0
            for required_field in required_fields:
                for cv_field in cv_fields:
                    similarity = self._education_field_similarity(required_field, cv_field)
                    if similarity > field_ratio:
                        field_ratio = similarity
                        matched_field = {
                            "required": required_field,
                            "cv": cv_field,
                        }

            # A higher degree in an unrelated subject is not a match for a
            # field-specific education requirement. This is the important gate
            # that prevents e.g. Business Analytics from satisfying Accounting
            # or Social/Labor Law education requirements.
            if field_ratio <= 0:
                ratio = 0.0
            else:
                ratio = level_ratio * (0.35 + 0.65 * field_ratio)
        else:
            ratio = level_ratio

        return {
            "applicable": True,
            "ratio": max(0.0, min(1.0, ratio)),
            "level_ratio": level_ratio,
            "field_ratio": field_ratio,
            "required": job_degree,
            "cv": cv_degree,
            "matched_field": matched_field,
        }

    def match_languages(self, job_languages: list[dict], cv_languages: list[dict]) -> dict:
        if not job_languages:
            return {
                "applicable": False,
                "ratio": 0.0,
                "matched": [],
                "missing": [],
                "details": [],
            }

        cv_map = {item["language"]: item for item in cv_languages}
        weights = {"required": 1.5, "neutral": 1.0, "preferred": 0.65, "optional": 0.25}
        total = 0.0
        achieved = 0.0
        matched: list[str] = []
        missing: list[str] = []
        details: list[dict] = []

        for job_item in job_languages:
            weight = weights.get(job_item["importance"], 1.0)
            total += weight
            cv_item = cv_map.get(job_item["language"])
            ratio = 0.0

            if cv_item:
                required_level = job_item["level"]
                if required_level <= 0:
                    ratio = 1.0
                elif cv_item["level"] <= 0:
                    # Language is present but CV does not state level.
                    ratio = 0.65
                else:
                    ratio = min(1.0, cv_item["level"] / required_level)

            achieved += ratio * weight
            if ratio > 0:
                matched.append(job_item["language"])
            else:
                missing.append(job_item["language"])

            details.append({
                "language": job_item["language"],
                "required_level": job_item["level_label"],
                "cv_level": cv_item["level_label"] if cv_item else "Not found",
                "ratio": round(ratio, 3),
                "importance": job_item["importance"],
            })

        return {
            "applicable": True,
            "ratio": safe_ratio(achieved, total),
            "matched": sorted(matched),
            "missing": sorted(missing),
            "details": details,
        }

    # ------------------------------------------------------------------
    # Score / confidence / suggestions
    # ------------------------------------------------------------------

    def calculate_score(
        self,
        *,
        skills: dict,
        role: dict,
        experience: dict,
        responsibilities: dict,
        critical_domain: dict,
        semantic: dict,
        education: dict,
        languages: dict,
        job_quality: dict,
        cv_quality: dict,
    ) -> dict:
        # JAM Match Engine v4 keeps the v3 hard-fact gates and adds an
        # independent local statistical-NLP requirement/evidence dimension.
        # shared tools (Excel, SAP, reporting, etc.) cannot outweigh a clearly
        # unrelated profession.
        role_ratio = role["ratio"] if role["applicable"] else 0.0
        experience_ratio = experience["ratio"]

        if role["applicable"] and role_ratio < 0.35 and experience["applicable"]:
            # Total professional years are not automatically relevant years in
            # an unrelated profession.
            experience_ratio *= 0.20

        # The old score could show 25/25 for "Required skills & tools" when
        # the only extracted tools were generic (Excel/SAP) even though the CV
        # lacked the profession-specific knowledge in the same job ad. Blend
        # technical-tool coverage with explicit core-domain requirements so the
        # displayed dimension reflects the whole required competency picture.
        skill_ratio = skills["ratio"] if skills["applicable"] else 0.0
        skill_dimension_applicable = bool(skills["applicable"] or critical_domain.get("applicable"))
        domain_signal_count = len(critical_domain.get("job_signals", []))
        if critical_domain.get("applicable") and domain_signal_count:
            if skills["applicable"]:
                technical_share = 0.55 if len(skills.get("matched", [])) + len(skills.get("missing", [])) >= 3 else 0.40
                skill_ratio = (skill_ratio * technical_share) + (critical_domain.get("ratio", 0.0) * (1.0 - technical_share))
            else:
                skill_ratio = critical_domain.get("ratio", 0.0)

        semantic_ratio = semantic.get("ratio", 0.0) if semantic.get("applicable") else 0.0

        dimensions = [
            Dimension("Role / title alignment", 22.0, role["applicable"], role_ratio, role["relation"]),
            Dimension("Required skills & tools", 22.0, skill_dimension_applicable, skill_ratio, "technical tools + profession-specific required competency coverage"),
            Dimension("Critical domain evidence", 16.0, critical_domain["applicable"], critical_domain["ratio"], "profession-specific evidence from the job description"),
            Dimension("Semantic requirement evidence", 15.0, semantic.get("applicable", False), semantic_ratio, "multilingual requirement-to-CV evidence matching"),
            Dimension("Relevant experience", 13.0, experience["applicable"], experience_ratio, experience["source"]),
            Dimension("Responsibilities / domain", 8.0, responsibilities["applicable"], responsibilities["ratio"], "responsibility/domain evidence"),
            Dimension("Education", 2.0, education["applicable"], education["ratio"], "degree requirement"),
            Dimension("Languages", 2.0, languages["applicable"], languages["ratio"], "language requirement"),
        ]

        active = [dimension for dimension in dimensions if dimension.applicable]
        active_weight = sum(item.weight for item in active)
        raw_numerator = sum(item.ratio * item.weight for item in active)
        raw_score = safe_ratio(raw_numerator, active_weight) * 100.0 if active_weight else 0.0

        positive_evidence = 0
        positive_evidence += len(skills["matched"])
        positive_evidence += 1 if role["applicable"] and role_ratio >= 0.50 else 0
        positive_evidence += 1 if experience["applicable"] and experience_ratio >= 0.50 else 0
        positive_evidence += len(languages["matched"])
        positive_evidence += len(responsibilities["matched_concepts"])
        positive_evidence += min(3, len(critical_domain.get("matched", [])))
        positive_evidence += min(2, len(responsibilities["matched_keywords"]))
        positive_evidence += 1 if education["applicable"] and education["ratio"] >= 0.45 else 0
        if (
            semantic.get("applicable")
            and semantic_ratio >= 0.55
            and len(semantic.get("strong", [])) >= 2
        ):
            positive_evidence += 1

        penalty = 1.0
        hard_cap = 100.0
        penalty_reasons: list[str] = []

        # Role gate. This is intentionally strong because experience and
        # generic tools are not transferable proof of professional fit by
        # themselves.
        if role["applicable"]:
            if role_ratio < 0.20:
                penalty *= 0.55
                hard_cap = min(hard_cap, 35.0)
                penalty_reasons.append("The target role family is not represented in the CV.")
            elif role_ratio < 0.45:
                penalty *= 0.75
                hard_cap = min(hard_cap, 55.0)
                penalty_reasons.append("The job title/role has weak alignment with the CV history.")

        if critical_domain.get("applicable"):
            domain_ratio = critical_domain.get("ratio", 0.0)
            signal_count = len(critical_domain.get("job_signals", []))

            if signal_count >= 2 and domain_ratio == 0:
                penalty *= 0.55
                hard_cap = min(hard_cap, 42.0)
                penalty_reasons.append(
                    "Core profession-specific requirements from the job description are not evidenced in the CV."
                )

                if role.get("mismatch"):
                    hard_cap = min(hard_cap, 24.0)
                    penalty *= 0.72
                    penalty_reasons.append(
                        "The target profession and its core domain evidence are both absent from the CV."
                    )
            elif signal_count >= 3 and domain_ratio < 0.34:
                penalty *= 0.72
                hard_cap = min(hard_cap, 55.0)
                penalty_reasons.append(
                    "Most profession-specific requirements are not evidenced in the CV."
                )
            elif signal_count >= 3 and domain_ratio < 0.60:
                penalty *= 0.88
                hard_cap = min(hard_cap, 72.0)
                penalty_reasons.append(
                    "Several profession-specific requirements are missing from the CV."
                )

        required_skill_ratio = skills.get("required_ratio")
        if critical_domain.get("applicable") and domain_signal_count:
            domain_ratio_for_required = critical_domain.get("ratio", 0.0)
            if required_skill_ratio is None:
                required_skill_ratio = domain_ratio_for_required
            else:
                required_skill_ratio = (required_skill_ratio * 0.55) + (domain_ratio_for_required * 0.45)

        if required_skill_ratio is not None:
            if required_skill_ratio == 0:
                penalty *= 0.55
                hard_cap = min(hard_cap, 48.0)
                penalty_reasons.append("No explicitly required skill was found in the CV.")
            elif required_skill_ratio < 0.50:
                penalty *= 0.72
                hard_cap = min(hard_cap, 65.0)
                penalty_reasons.append("Less than half of the explicitly required skills were found.")
            elif required_skill_ratio < 0.75:
                penalty *= 0.90
                penalty_reasons.append("Several explicitly required skills are not clearly evidenced in the CV.")

        if experience["applicable"] and experience["required_years"]:
            if experience["ratio"] < 0.34:
                penalty *= 0.70
                hard_cap = min(hard_cap, 50.0)
                penalty_reasons.append("Detected experience is far below the stated requirement.")
            elif experience["ratio"] < 0.60:
                penalty *= 0.84
                hard_cap = min(hard_cap, 68.0)
                penalty_reasons.append("Detected experience is below the stated requirement.")

        if education.get("applicable") and education.get("field_ratio") == 0:
            penalty *= 0.88
            hard_cap = min(hard_cap, 82.0)
            penalty_reasons.append(
                "The requested field of study is not evidenced by the CV education."
            )

        required_language_missing = [
            item["language"]
            for item in languages.get("details", [])
            if item["importance"] == "required" and item["ratio"] == 0
        ]
        if required_language_missing:
            penalty *= 0.90
            penalty_reasons.append(
                "Required language not found: " + ", ".join(required_language_missing)
            )

        adjusted_score = min(raw_score * penalty, hard_cap)

        breadth = safe_ratio(len(active), 8)
        confidence = round(
            job_quality["quality"] * 0.50
            + cv_quality["quality"] * 0.30
            + breadth * 100 * 0.20
        )
        if positive_evidence <= 1:
            confidence = min(confidence, 55)
        confidence = max(0, min(100, confidence))

        no_score_reasons: list[str] = []
        if not job_quality["analyzable"]:
            no_score_reasons.extend(job_quality["reasons"] or ["The job offer is not detailed enough to score reliably."])
        if not cv_quality["analyzable"]:
            no_score_reasons.extend(cv_quality["reasons"] or ["The CV could not be parsed reliably."])
        if len(active) < 2:
            no_score_reasons.append("Fewer than two reliable comparison dimensions were detected.")
        if positive_evidence == 0:
            no_score_reasons.append("No positive match evidence was found between the job offer and the CV.")
        if confidence < 30:
            no_score_reasons.append("The evidence confidence is too low for a meaningful percentage score.")

        score_available = not no_score_reasons
        score = int(round(max(0.0, min(100.0, adjusted_score)))) if score_available else None

        if score is None:
            label = "No reliable score"
        elif score >= 85:
            label = "Very strong evidence"
        elif score >= 70:
            label = "Strong evidence"
        elif score >= 55:
            label = "Moderate evidence"
        elif score >= 40:
            label = "Partial evidence"
        else:
            label = "Low evidence"

        compatibility_breakdown = {
            "skills": round(skill_ratio * 22),
            "title": round(role_ratio * 22),
            "critical_domain": round(critical_domain["ratio"] * 16) if critical_domain["applicable"] else 0,
            "semantic": round(semantic_ratio * 15) if semantic.get("applicable") else 0,
            "experience": round(experience_ratio * 13) if experience["applicable"] else 0,
            "responsibilities": round(responsibilities["ratio"] * 8) if responsibilities["applicable"] else 0,
            "education": round(education["ratio"] * 2) if education["applicable"] else 0,
            "languages": round(languages["ratio"] * 2) if languages["applicable"] else 0,
        }

        detail_breakdown = {
            item.name: {
                "applicable": item.applicable,
                "weight": item.weight,
                "ratio": round(item.ratio, 3),
                "raw_points": round(item.ratio * item.weight, 2) if item.applicable else 0.0,
                "note": item.note,
            }
            for item in dimensions
        }

        explanation = []
        for item in dimensions:
            if not item.applicable:
                continue
            explanation.append({
                "dimension": item.name,
                "points": round(item.ratio * item.weight, 1),
                "max_points": item.weight,
                "ratio": round(item.ratio, 3),
                "note": item.note,
            })

        return {
            "score_available": score_available,
            "score": score,
            "label": label,
            "confidence": confidence,
            "active_dimension_count": len(active),
            "active_weight": active_weight,
            "positive_evidence_count": positive_evidence,
            "raw_score_before_penalties": round(raw_score, 1),
            "penalty_multiplier": round(penalty, 3),
            "hard_cap": round(hard_cap, 1),
            "penalty_reasons": penalty_reasons,
            "no_score_reasons": list(dict.fromkeys(no_score_reasons)),
            "breakdown": compatibility_breakdown,
            "detail_breakdown": detail_breakdown,
            "score_explanation": explanation,
        }

    def build_suggestions(
        self,
        *,
        score_result: dict,
        skills: dict,
        role: dict,
        experience: dict,
        responsibilities: dict,
        critical_domain: dict,
        semantic: dict,
        education: dict,
        languages: dict,
        job_quality: dict,
        cv_quality: dict,
    ) -> list[str]:
        suggestions: list[str] = []

        if not score_result["score_available"]:
            suggestions.append(
                score_result["no_score_reasons"][0]
                if score_result["no_score_reasons"]
                else "JAM does not have enough reliable evidence to calculate a score."
            )

        if skills["missing_required"]:
            suggestions.append(
                "Required tools/skills not clearly found in the CV: "
                + ", ".join(skills["missing_required"][:10])
                + ". Only add them if they are genuinely part of your experience."
            )
        elif skills["missing"]:
            suggestions.append(
                "Job skills not clearly found in the CV: "
                + ", ".join(skills["missing"][:10])
                + "."
            )

        if critical_domain.get("applicable") and critical_domain.get("missing"):
            suggestions.append(
                "Profession-specific job requirements not clearly found in the CV: "
                + ", ".join(critical_domain["missing"][:10])
                + "."
            )

        if experience["applicable"] and experience["required_years"]:
            cv_years = experience["cv_years"]
            if cv_years is None:
                suggestions.append(
                    f"The job asks for about {experience['required_years']:g}+ years, but JAM could not reliably calculate years of experience from the CV timeline."
                )
            elif experience["ratio"] < 1.0:
                suggestions.append(
                    f"The job asks for about {experience['required_years']:g}+ years; JAM detected about {cv_years:g} years from the CV timeline/text."
                )

        if role["applicable"] and role["ratio"] < 0.60:
            suggestions.append(
                "The target role is not strongly reflected in the CV headline/job-title evidence. If accurate, align the profile/headline with the target role rather than inventing experience."
            )

        if languages["missing"]:
            suggestions.append(
                "Requested languages not clearly found in the CV: "
                + ", ".join(languages["missing"])
                + "."
            )

        if education["applicable"] and education["ratio"] < 1.0:
            required_fields = education["required"].get("fields") or []
            cv_fields = education["cv"].get("fields") or []
            field_text = ""
            if required_fields:
                field_text = (
                    "; required field: " + ", ".join(required_fields)
                    + "; CV field evidence: " + (", ".join(cv_fields) if cv_fields else "not found")
                )
            suggestions.append(
                "Education requirement detected: "
                + education["required"]["label"]
                + field_text
                + "; CV degree level: "
                + education["cv"]["label"]
                + "."
            )

        if responsibilities["missing_concepts"]:
            suggestions.append(
                "Responsibilities/domain concepts not clearly evidenced in the CV: "
                + ", ".join(responsibilities["missing_concepts"][:8])
                + "."
            )

        semantic_missing_required = [
            item.get("requirement", "")
            for item in semantic.get("missing", [])
            if item.get("importance") == "required"
        ]
        if semantic_missing_required:
            suggestions.append(
                "Local semantic matching found no strong CV evidence for required statements such as: "
                + " | ".join(semantic_missing_required[:3])
                + "."
            )

        if cv_quality["quality"] < 55:
            suggestions.append(
                "CV extraction confidence is limited. Check that the PDF/DOCX contains selectable text and that dates, skills and languages are written explicitly."
            )

        if score_result["score_available"] and not suggestions:
            suggestions.append(
                "The detected requirements are well represented. Review each claim against your real experience before tailoring the CV."
            )

        return suggestions[:8]

    # ------------------------------------------------------------------
    # Main analysis
    # ------------------------------------------------------------------

    def analyze(
        self,
        job_title: str,
        description: str,
        cv_path: str | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> dict:
        started = time.perf_counter()
        timings: dict[str, int] = {}

        def stage(name: str, percent: int, checkpoint: float) -> float:
            now = time.perf_counter()
            timings[name] = int(round((now - checkpoint) * 1000))
            self._emit(progress_callback, name, percent)
            return now

        title = (job_title or "").strip()
        description = (description or "").strip()
        if not title and not description:
            raise ValueError("Add a job title or description before analyzing.")

        self._emit(progress_callback, "Validating job offer", 5)
        checkpoint = time.perf_counter()

        job_text = f"{title}\n{description}".strip()
        job_skills = self.extract_skills(job_text, job=True)
        job_concepts = self.extract_concepts(job_text, job=True)
        job_languages = self.extract_languages(job_text, job=True)
        job_years = self.extract_required_years(job_text)
        job_degree = self.extract_education_profile(job_text, job=True)
        job_reference = self.extract_reference(job_text)
        job_roles = self.extract_role_families(title)
        job_seniority = self.extract_seniority(title + "\n" + description[:500])
        salary = self.extract_salary(job_text)
        job_quality = self.evaluate_job_quality(
            title,
            description,
            job_skills,
            job_concepts,
            job_languages,
            job_years,
            job_degree,
            job_roles,
        )
        checkpoint = stage("Extracting job requirements", 30, checkpoint)

        cv_path = cv_path or self.settings.get("cv_path")
        if not cv_path:
            raise ValueError("Add a CV first from JAM settings or the analyzer.")

        cv_text = self.extract_cv_text(cv_path)
        checkpoint = stage("Reading selected CV", 48, checkpoint)

        if not cv_text.strip():
            raise ValueError("JAM could not extract readable text from the selected CV.")

        cv_skills = self.extract_skills(cv_text)
        cv_concepts = self.extract_concepts(cv_text)
        cv_languages = self.extract_languages(cv_text)
        cv_degree = self.extract_education_profile(cv_text, job=False)
        cv_experience = self.estimate_cv_years(cv_text)
        cv_roles = self.extract_role_families(cv_text)
        cv_quality = self.evaluate_cv_quality(
            cv_text,
            cv_skills,
            cv_languages,
            cv_degree,
            cv_experience,
            cv_roles,
        )
        checkpoint = stage("Building CV evidence profile", 63, checkpoint)

        skill_match = self.match_skills(job_skills, cv_skills)
        role_match = self.role_match(title, cv_text, description)
        critical_domain_match = self.match_critical_domain(
            title,
            description,
            cv_text,
            role_match,
        )
        experience_match = self.match_experience(job_years, cv_experience, job_seniority)
        responsibility_match = self.match_concepts_keywords(
            title,
            description,
            job_concepts,
            cv_concepts,
            cv_text,
        )
        education_match = self.match_education(job_degree, cv_degree)
        language_match = self.match_languages(job_languages, cv_languages)
        checkpoint = stage("Comparing job and CV evidence", 78, checkpoint)

        semantic_match = self.semantic.analyze(
            title,
            description,
            cv_text,
        )
        checkpoint = stage("Running local semantic ML", 88, checkpoint)

        score_result = self.calculate_score(
            skills=skill_match,
            role=role_match,
            experience=experience_match,
            responsibilities=responsibility_match,
            critical_domain=critical_domain_match,
            semantic=semantic_match,
            education=education_match,
            languages=language_match,
            job_quality=job_quality,
            cv_quality=cv_quality,
        )

        target_min = self.settings.get("salary_target_min")
        target_max = self.settings.get("salary_target_max")
        salary_fit = None
        try:
            target_min_i = int(target_min) if target_min else None
            target_max_i = int(target_max) if target_max else None
        except ValueError:
            target_min_i = target_max_i = None

        target_currency = (self.settings.get("salary_currency", "EUR") or "EUR").upper()
        if (
            salary
            and salary["period"] == "annual"
            and salary.get("currency") in {None, target_currency}
            and (target_min_i or target_max_i)
        ):
            wanted_min = target_min_i or target_max_i or 0
            wanted_max = target_max_i or target_min_i or 10**9
            salary_fit = not (
                salary["max"] < wanted_min
                or salary["min"] > wanted_max
            )

        suggestions = self.build_suggestions(
            score_result=score_result,
            skills=skill_match,
            role=role_match,
            experience=experience_match,
            responsibilities=responsibility_match,
            critical_domain=critical_domain_match,
            semantic=semantic_match,
            education=education_match,
            languages=language_match,
            job_quality=job_quality,
            cv_quality=cv_quality,
        )
        checkpoint = stage("Calculating evidence-based score", 96, checkpoint)

        total_ms = int(round((time.perf_counter() - started) * 1000))
        timings["total"] = total_ms
        self._emit(progress_callback, "Analysis complete", 100)

        # Backward-compatible top-level fields + richer v2 evidence.
        return {
            "score": score_result["score"],
            "score_available": score_result["score_available"],
            "score_label": score_result["label"],
            "confidence": score_result["confidence"],
            "no_score_reasons": score_result["no_score_reasons"],
            "breakdown": score_result["breakdown"],
            "detail_breakdown": score_result["detail_breakdown"],
            "matched_skills": skill_match["matched"],
            "matched_skill_evidence": skill_match.get("evidence", []),
            "missing_skills": skill_match["missing"],
            "missing_required_skills": skill_match["missing_required"],
            "missing_required_competencies": sorted(set(skill_match["missing_required"] + critical_domain_match.get("missing", []))),
            "matched_required_competencies": sorted(set(skill_match["matched"] + critical_domain_match.get("matched", []))),
            "required_skills": [mention.name for mention in job_skills],
            "preferred_skills": [mention.name for mention in job_skills if mention.importance == "preferred"],
            "required_years": experience_match["required_years"],
            "cv_years": experience_match["cv_years"],
            "matched_languages": language_match["matched"],
            "missing_languages": language_match["missing"],
            "matched_concepts": responsibility_match["matched_concepts"],
            "matched_concept_evidence": responsibility_match.get("evidence", []),
            "missing_concepts": responsibility_match["missing_concepts"],
            "matched_keywords": responsibility_match["matched_keywords"],
            "missing_keywords": responsibility_match["missing_keywords"],
            "salary": salary,
            "salary_fit": salary_fit,
            "reference": job_reference,
            "suggestions": suggestions,
            "job_quality": job_quality,
            "cv_quality": cv_quality,
            "job_profile": {
                "title": title,
                "role_families": job_roles,
                "seniority": job_seniority,
                "skills": [mention.__dict__ for mention in job_skills],
                "concepts": [mention.__dict__ for mention in job_concepts],
                "languages": job_languages,
                "experience": job_years,
                "education": job_degree,
                "salary": salary,
                "focus_keywords": responsibility_match["focus_keywords"],
            },
            "cv_profile": {
                "role_families": cv_roles,
                "skills": [mention.__dict__ for mention in cv_skills],
                "concepts": [mention.__dict__ for mention in cv_concepts],
                "languages": cv_languages,
                "experience": cv_experience,
                "education": cv_degree,
            },
            "role_match": role_match,
            "experience_match": experience_match,
            "education_match": education_match,
            "language_match": language_match,
            "responsibility_match": responsibility_match,
            "critical_domain_match": critical_domain_match,
            "semantic_match": semantic_match,
            "semantic_coverage": semantic_match.get("coverage", 0),
            "semantic_requirement_evidence": semantic_match.get("evidence", []),
            "semantic_role_classifier": semantic_match.get("role_classifier", {}),
            "ml_engine": {
                "available": semantic_match.get("ml_available", False),
                "engine": semantic_match.get("engine_name"),
                "model": semantic_match.get("model"),
                "local_only": semantic_match.get("local_only", True),
            },
            "penalty_reasons": score_result["penalty_reasons"],
            "hard_cap": score_result.get("hard_cap"),
            "score_explanation": score_result.get("score_explanation", []),
            "raw_score_before_penalties": score_result["raw_score_before_penalties"],
            "cv_path": cv_path,
            "method": (
                f"JAM Match Engine v{self.ENGINE_VERSION} — hybrid rules + "
                f"{semantic_match.get('model', 'local semantic evidence')}"
            ),
            "timings_ms": timings,
        }
