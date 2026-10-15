from __future__ import annotations

import json
import re
import unicodedata
from typing import Iterable


DEFAULT_SOURCES = (
    # Tunisia
    "Keejob",
    "Tanitjobs",
    "Emploi.nat.tn",
    "Tunisie Travail",
    "EmploiTunisie",
    "Optioncarriere Tunisie",
    "Careerjet Tunisie",
    # France
    "APEC",
    "France Travail",
    "Welcome to the Jungle",
    "JobTeaser",
    "HelloWork",
    "Cadremploi",
    "Meteojob",
    "LesJeudis",
    "L'Etudiant",
    "iQuesta",
    "Wizbii",
    "StudentJob",
    # International / general
    "LinkedIn",
    "Indeed",
    "Glassdoor",
    "Monster",
    "Talent.com",
    "Jooble",
    "Careerjet",
    "EURES",
    "EURAXESS",
    "Wellfound",
    "Remote OK",
    "We Work Remotely",
    # ATS / company careers
    "Workday",
    "SmartRecruiters",
    "Greenhouse",
    "Lever",
    "Ashby",
    "SAP SuccessFactors",
    "Oracle Careers",
    "Company Website",
    # MENA / wider region
    "Bayt",
    "GulfTalent",
    "NaukriGulf",
    # Other discovery channels
    "Recruiter / Agency",
    "Referral",
    "Direct Contact",
    "School / Alumni",
    "Other",
)

FEATURED_SOURCES = (
    "LinkedIn",
    "Company Website",
    "Indeed",
    "Welcome to the Jungle",
    "APEC",
    "France Travail",
    "Keejob",
    "Tanitjobs",
)

SOURCE_ALIASES = {
    "Company Website": (
        "web",
        "website",
        "site",
        "site web",
        "company site",
        "company website",
        "company career",
        "company careers",
        "company careers page",
        "career page",
        "careers page",
        "corporate website",
        "page carrieres",
        "page carriere",
    ),
    "Welcome to the Jungle": (
        "wttj",
        "welcome",
        "jungle",
        "welcome kit",
        "welcomekit",
    ),
    "France Travail": (
        "pole emploi",
        "pôle emploi",
        "france travail",
    ),
    "Recruiter / Agency": (
        "recruiter",
        "agency",
        "recruitment agency",
        "cabinet",
        "recruteur",
    ),
    "Referral": (
        "referral",
        "cooptation",
        "employee referral",
    ),
    "Direct Contact": (
        "direct",
        "direct contact",
        "contact direct",
        "recruiter contact",
    ),
    "LinkedIn": (
        "linkedin",
        "linked in",
    ),
    "HelloWork": (
        "hellowork",
        "hello work",
    ),
}

CUSTOM_SOURCES_SETTING = "custom_sources"


def _norm(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.casefold().strip()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_custom_sources(value: object) -> list[str]:
    if value in (None, ""):
        return []
    try:
        items = json.loads(str(value))
    except Exception:
        return []
    if not isinstance(items, list):
        return []
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = str(item or "").strip()
        key = _norm(text)
        if not text or not key or key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def serialize_custom_sources(items: Iterable[object]) -> str:
    clean: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = str(item or "").strip()
        key = _norm(text)
        if not text or not key or key in seen:
            continue
        seen.add(key)
        clean.append(text)
    return json.dumps(clean, ensure_ascii=False)


def merge_source_options(*groups: Iterable[object]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for item in group:
            text = str(item or "").strip()
            key = _norm(text)
            if not text or not key or key in seen:
                continue
            seen.add(key)
            result.append(text)
    return result


def source_matches(query: object, sources: Iterable[object] | None = None, limit: int = 10) -> list[str]:
    options = merge_source_options(DEFAULT_SOURCES, sources or ())
    needle = _norm(query)
    if not needle:
        featured_keys = {_norm(item) for item in FEATURED_SOURCES}
        featured = [item for item in options if _norm(item) in featured_keys]
        return featured[:limit]

    query_tokens = needle.split()
    scored: list[tuple[int, int, str]] = []
    for index, source in enumerate(options):
        source_norm = _norm(source)
        aliases = [_norm(item) for item in SOURCE_ALIASES.get(source, ())]
        words = source_norm.split()

        score: int | None = None
        if source_norm == needle:
            score = 0
        elif source_norm.startswith(needle):
            score = 1
        elif any(word.startswith(needle) for word in words):
            score = 2
        elif any(alias == needle or alias.startswith(needle) for alias in aliases):
            score = 3
        elif needle in source_norm:
            score = 4
        elif any(needle in alias for alias in aliases):
            score = 5
        else:
            haystack = " ".join([source_norm, *aliases])
            if query_tokens and all(token in haystack for token in query_tokens):
                score = 6

        if score is not None:
            scored.append((score, index, source))

    scored.sort(key=lambda item: (item[0], item[1], item[2].casefold()))
    return [source for _, _, source in scored[: max(1, int(limit))]]


def is_known_source(value: object, sources: Iterable[object] | None = None) -> bool:
    needle = _norm(value)
    if not needle:
        return False
    return any(_norm(item) == needle for item in merge_source_options(DEFAULT_SOURCES, sources or ()))


# ---------------------------------------------------------------------------
# Applicant-count enrichment
# ---------------------------------------------------------------------------

_APPLICANT_PATTERNS = (
    re.compile(r"\b([0-9][0-9\s,.]{0,10})\s+people\s+clicked\s+apply\b", re.I),
    re.compile(r"\b([0-9][0-9\s,.]{0,10})\s+people\s+(?:have\s+)?applied\b", re.I),
    re.compile(r"\b([0-9][0-9\s,.]{0,10})\s+applicants?\b", re.I),
    re.compile(r"\b([0-9][0-9\s,.]{0,10})\s+candidates?\b", re.I),
    re.compile(r"\b([0-9][0-9\s,.]{0,10})\s+candidats?\b", re.I),
)


def infer_applicant_count(notes: object) -> int | None:
    text = str(notes or "")
    for pattern in _APPLICANT_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        digits = re.sub(r"\D", "", match.group(1))
        if not digits:
            continue
        value = int(digits)
        if 0 <= value <= 10_000_000:
            return value
    return None


def normalize_applicant_count(value: object, *, notes: object = "", infer_when_missing: bool = False) -> int | None:
    if value is None or str(value).strip() == "":
        return infer_applicant_count(notes) if infer_when_missing else None

    if isinstance(value, bool):
        raise ValueError("Applicant count must be a non-negative whole number.")

    if isinstance(value, int):
        number = value
    elif isinstance(value, float) and value.is_integer():
        number = int(value)
    else:
        text = str(value).strip()
        if not re.fullmatch(r"\d+", text):
            raise ValueError("Applicant count must contain numbers only.")
        number = int(text)

    if number < 0:
        raise ValueError("Applicant count cannot be negative.")
    return number


def applicant_competition_color(value: object) -> str:
    try:
        count = int(value)
    except Exception:
        return "#6B7280"
    if count < 20:
        return "#047857"
    if count < 40:
        return "#34D399"
    if count < 60:
        return "#EAB308"
    if count < 80:
        return "#F97316"
    if count < 100:
        return "#EF4444"
    return "#B91C1C"


# ---------------------------------------------------------------------------
# Offline location normalization / future map metadata
# ---------------------------------------------------------------------------

COUNTRY_ALIASES = {
    "France": ("france", "fr", "fra"),
    "Tunisia": ("tunisia", "tunisie", "tn", "tun"),
    "Germany": ("germany", "deutschland", "allemagne", "de", "deu"),
    "Belgium": ("belgium", "belgique", "be", "bel"),
    "Switzerland": ("switzerland", "suisse", "schweiz", "ch", "che"),
    "Luxembourg": ("luxembourg", "lu", "lux"),
    "Netherlands": ("netherlands", "pays bas", "holland", "nl", "nld"),
    "Spain": ("spain", "espagne", "espana", "es", "esp"),
    "Italy": ("italy", "italie", "italia", "it", "ita"),
    "United Kingdom": ("united kingdom", "uk", "gb", "gbr", "england", "britain"),
    "Ireland": ("ireland", "irlande", "ie", "irl"),
    "Portugal": ("portugal", "pt", "prt"),
    "Austria": ("austria", "autriche", "at", "aut"),
    "United States": ("united states", "united states of america", "usa", "us", "america"),
    "Canada": ("canada", "ca", "can"),
    "Morocco": ("morocco", "maroc", "ma", "mar"),
    "Algeria": ("algeria", "algerie", "algérie", "dz", "dza"),
    "United Arab Emirates": ("united arab emirates", "uae", "emirats arabes unis", "ae", "are"),
    "Saudi Arabia": ("saudi arabia", "arabie saoudite", "sa", "sau"),
    "Qatar": ("qatar", "qa", "qat"),
    "Turkey": ("turkey", "turkiye", "türkiye", "turquie", "tr", "tur"),
}

# Canonical display name, country, latitude, longitude, aliases.
LOCATION_CATALOG = (
    ("Paris", "France", 48.8566, 2.3522, ("paris", "paris la defense", "paris la défense", "fra paris", "la defense", "la défense")),
    ("Neuilly-sur-Seine", "France", 48.8847, 2.2685, ("neuilly sur seine", "neuilly-sur-seine")),
    ("Courbevoie", "France", 48.8970, 2.2521, ("courbevoie",)),
    ("Montereau-sur-le-Jard", "France", 48.5913, 2.6775, ("montereau sur le jard", "montereau-sur-le-jard")),
    ("Toulouse", "France", 43.6047, 1.4442, ("toulouse",)),
    ("Lyon", "France", 45.7640, 4.8357, ("lyon",)),
    ("Lille", "France", 50.6292, 3.0573, ("lille",)),
    ("Marseille", "France", 43.2965, 5.3698, ("marseille",)),
    ("Bordeaux", "France", 44.8378, -0.5792, ("bordeaux",)),
    ("Nantes", "France", 47.2184, -1.5536, ("nantes",)),
    ("Rennes", "France", 48.1173, -1.6778, ("rennes",)),
    ("Nice", "France", 43.7102, 7.2620, ("nice",)),
    ("Montpellier", "France", 43.6108, 3.8767, ("montpellier",)),
    ("Strasbourg", "France", 48.5734, 7.7521, ("strasbourg",)),
    ("Grenoble", "France", 45.1885, 5.7245, ("grenoble",)),
    ("Tunis", "Tunisia", 36.8065, 10.1815, ("tunis",)),
    ("Ariana", "Tunisia", 36.8665, 10.1647, ("ariana",)),
    ("Sfax", "Tunisia", 34.7406, 10.7603, ("sfax",)),
    ("Sousse", "Tunisia", 35.8256, 10.6084, ("sousse",)),
    ("Monastir", "Tunisia", 35.7643, 10.8113, ("monastir",)),
    ("Frankfurt", "Germany", 50.1109, 8.6821, ("frankfurt", "frankfurt am main")),
    ("Berlin", "Germany", 52.5200, 13.4050, ("berlin",)),
    ("Munich", "Germany", 48.1351, 11.5820, ("munich", "muenchen", "münchen")),
    ("Hamburg", "Germany", 53.5511, 9.9937, ("hamburg",)),
    ("Cologne", "Germany", 50.9375, 6.9603, ("cologne", "koln", "köln")),
    ("Stuttgart", "Germany", 48.7758, 9.1829, ("stuttgart",)),
    ("Düsseldorf", "Germany", 51.2277, 6.7735, ("dusseldorf", "düsseldorf")),
    ("Brussels", "Belgium", 50.8503, 4.3517, ("brussels", "bruxelles")),
    ("Amsterdam", "Netherlands", 52.3676, 4.9041, ("amsterdam",)),
    ("Luxembourg", "Luxembourg", 49.6116, 6.1319, ("luxembourg city", "luxembourg")),
    ("Geneva", "Switzerland", 46.2044, 6.1432, ("geneva", "geneve", "genève")),
    ("Zurich", "Switzerland", 47.3769, 8.5417, ("zurich", "zürich")),
    ("London", "United Kingdom", 51.5074, -0.1278, ("london",)),
    ("Dublin", "Ireland", 53.3498, -6.2603, ("dublin",)),
    ("Madrid", "Spain", 40.4168, -3.7038, ("madrid",)),
    ("Barcelona", "Spain", 41.3874, 2.1686, ("barcelona",)),
    ("Milan", "Italy", 45.4642, 9.1900, ("milan", "milano")),
    ("Rome", "Italy", 41.9028, 12.4964, ("rome", "roma")),
    ("Lisbon", "Portugal", 38.7223, -9.1393, ("lisbon", "lisboa", "lisbonne")),
    ("Vienna", "Austria", 48.2082, 16.3738, ("vienna", "wien", "vienne")),
    ("Casablanca", "Morocco", 33.5731, -7.5898, ("casablanca",)),
    ("Rabat", "Morocco", 34.0209, -6.8416, ("rabat",)),
    ("Algiers", "Algeria", 36.7538, 3.0588, ("algiers", "alger",)),
    ("Dubai", "United Arab Emirates", 25.2048, 55.2708, ("dubai", "dubaï")),
    ("Abu Dhabi", "United Arab Emirates", 24.4539, 54.3773, ("abu dhabi",)),
    ("Riyadh", "Saudi Arabia", 24.7136, 46.6753, ("riyadh", "riyad")),
    ("Doha", "Qatar", 25.2854, 51.5310, ("doha",)),
    ("Istanbul", "Turkey", 41.0082, 28.9784, ("istanbul",)),
    ("New York", "United States", 40.7128, -74.0060, ("new york", "nyc")),
    ("Toronto", "Canada", 43.6532, -79.3832, ("toronto",)),
)


def _clean_location_text(value: object) -> str:
    text = str(value or "").strip()
    text = text.replace("\r", "\n")
    text = re.sub(r"\n+", ", ", text)
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r"(?:,\s*){2,}", ", ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" ,")


def _country_from_text(normalized_text: str, parts: list[str]) -> str:
    # Prefer exact trailing comma-part matches because short aliases such as FR
    # should not be searched as arbitrary substrings.
    for part in reversed(parts):
        part_norm = _norm(part)
        for country, aliases in COUNTRY_ALIASES.items():
            if part_norm in {_norm(alias) for alias in aliases}:
                return country

    words = set(normalized_text.split())
    for country, aliases in COUNTRY_ALIASES.items():
        for alias in aliases:
            alias_norm = _norm(alias)
            if len(alias_norm) <= 3:
                continue
            if alias_norm in normalized_text or set(alias_norm.split()).issubset(words):
                return country
    return ""


def normalize_location(value: object) -> dict[str, object]:
    raw = str(value or "").strip()
    clean = _clean_location_text(raw)
    if not clean:
        return {
            "raw": "",
            "display": "",
            "city": "",
            "region": "",
            "country": "",
            "lat": None,
            "lon": None,
        }

    normalized = _norm(clean)
    parts = [part.strip() for part in clean.split(",") if part.strip()]
    country = _country_from_text(normalized, parts)

    matches: list[tuple[str, str, float, float]] = []
    for city, city_country, lat, lon, aliases in LOCATION_CATALOG:
        alias_norms = sorted({_norm(alias) for alias in aliases}, key=len, reverse=True)
        if any(re.search(rf"(?:^|\b){re.escape(alias)}(?:\b|$)", normalized) for alias in alias_norms if alias):
            if not any(existing[0] == city for existing in matches):
                matches.append((city, city_country, lat, lon))

    if matches:
        if country:
            same_country = [item for item in matches if item[1] == country]
            if same_country:
                matches = same_country
        elif len({item[1] for item in matches}) == 1:
            country = matches[0][1]

        # LinkedIn and job boards sometimes return several valid cities in one
        # location (e.g. "Paris, Toulouse"). Keep both rather than inventing one.
        unique_cities: list[str] = []
        for city, _, _, _ in matches:
            if city not in unique_cities:
                unique_cities.append(city)

        if len(unique_cities) > 1 and country:
            return {
                "raw": raw,
                "display": f"{' / '.join(unique_cities)}, {country}",
                "city": " / ".join(unique_cities),
                "region": "",
                "country": country,
                "lat": None,
                "lon": None,
            }

        city, city_country, lat, lon = matches[0]
        country = country or city_country
        return {
            "raw": raw,
            "display": f"{city}, {country}" if country else city,
            "city": city,
            "region": "",
            "country": country,
            "lat": lat,
            "lon": lon,
        }

    # Generic LinkedIn-style "City, Region, Country" fallback.
    if country and parts:
        city = parts[0]
        if _norm(city) in {_norm(alias) for aliases in COUNTRY_ALIASES.values() for alias in aliases}:
            city = ""
        # Avoid pretending a street number is a city.
        if city and not re.fullmatch(r"\d+", city) and not re.match(r"^\d+[\s,-]", city):
            region = parts[-2] if len(parts) >= 3 else ""
            return {
                "raw": raw,
                "display": f"{city}, {country}",
                "city": city,
                "region": region,
                "country": country,
                "lat": None,
                "lon": None,
            }

    # Unknown values are preserved exactly enough for the user to recognize
    # them. JAM never fabricates a city/country when it is not confident.
    return {
        "raw": raw,
        "display": clean,
        "city": "",
        "region": "",
        "country": country,
        "lat": None,
        "lon": None,
    }
