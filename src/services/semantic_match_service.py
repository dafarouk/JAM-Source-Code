from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from difflib import SequenceMatcher

from config import SEMANTIC_MODEL_DIR

from services.analyzer_knowledge import (
    BUSINESS_CONCEPTS,
    LANGUAGES,
    LANGUAGE_LEVELS,
    PREFERRED_MARKERS,
    REQUIRED_MARKERS,
    RESPONSIBILITY_MARKERS,
    ROLE_DOMAIN_SIGNALS,
    ROLE_FAMILIES,
    SKILLS,
    STOPWORDS,
)

try:  # Optional at runtime so JAM still starts before dependencies are refreshed.
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.pipeline import FeatureUnion

    SKLEARN_AVAILABLE = True
except Exception:  # pragma: no cover - exercised only on machines without sklearn
    TfidfVectorizer = None
    LogisticRegression = None
    cosine_similarity = None
    FeatureUnion = None
    SKLEARN_AVAILABLE = False

# sentence-transformers / PyTorch are intentionally NOT imported here.
# They are the heaviest Analyzer dependencies and importing them during module
# startup noticeably delays both JAM and the separate Capture process.
# _get_embedder() imports them only when semantic analysis is actually used.
SentenceTransformer = None
SENTENCE_TRANSFORMERS_AVAILABLE: bool | None = None
_SENTENCE_TRANSFORMERS_IMPORT_ERROR: str | None = None


@dataclass(frozen=True)
class SemanticRequirement:
    text: str
    importance: str
    weight: float


class SemanticMatchService:
    """Local statistical NLP layer used by JAM Match Engine v4.

    v4 deliberately keeps the deterministic v3 rules as the source of truth for
    hard facts (years, explicit skills, degree, languages and profession gates).
    This service adds a second, independent evidence channel:

    * requirement -> CV evidence matching with TF-IDF word + character models;
    * a small local job-family classifier trained from JAM's role taxonomy;
    * transparent best-evidence lines and similarity scores.

    Nothing is sent to a cloud service and the user's CV never leaves JAM.
    """

    _SHARED_CLASSIFIER = None
    _SHARED_VECTORIZER = None
    _SHARED_ERROR: str | None = None
    _SHARED_READY = False

    ENGINE_NAME = "JAM multilingual hybrid semantic layer"
    MODEL_NAME = "Multilingual MiniLM + bilingual evidence rules + TF-IDF fallback"
    EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    _SHARED_EMBEDDER = None
    _SHARED_EMBEDDER_ATTEMPTED = False
    _SHARED_EMBEDDER_ERROR: str | None = None

    _BOILERPLATE = (
        "about us",
        "who we are",
        "our company",
        "equal opportunity",
        "diversity",
        "inclusion",
        "privacy policy",
        "cookie",
        "apply now",
        "join us",
        "why join",
        "company benefits",
        "avantages",
        "qui sommes nous",
        "qui sommes-nous",
        "a propos de nous",
        "à propos de nous",
        "politique de confidentialite",
        "politique de confidentialité",
    )

    _ACTION_HINTS = (
        "build", "create", "develop", "design", "maintain", "manage",
        "analyze", "analyse", "monitor", "deliver", "prepare", "support",
        "coordinate", "lead", "implement", "automate", "document", "ensure",
        "review", "draft", "advise", "reconcile", "report", "optimize",
        "construire", "creer", "créer", "developper", "développer", "concevoir",
        "maintenir", "gerer", "gérer", "analyser", "piloter", "produire",
        "preparer", "préparer", "accompagner", "coordonner", "mettre en oeuvre",
        "mettre en œuvre", "rediger", "rédiger", "conseiller", "assurer",
    )

    _CV_HEADINGS = {
        "profil", "profile",
        "experiences professionnelles", "experience professionnelle",
        "professional experience", "work experience", "experience",
        "formation", "formations", "education",
        "competences techniques", "competences", "skills", "technical skills",
        "projets data & bi", "projets", "projects",
        "langues", "languages",
        "certifications", "certification",
    }

    _JD_HEADINGS = {
        "role summary", "key responsibilities", "responsibilities",
        "performance analysis & decision support",
        "market intelligence & strategic retailer support",
        "innovation, ai & digital tools",
        "project management & process improvement",
        "who are we looking for", "education & experience",
        "technical skills", "soft skills", "working conditions",
        "why join", "why join us", "about the job",
    }

    # Small deterministic bilingual bridge used even when the embedding model
    # is unavailable. It is not a translator; it only canonicalizes common
    # professional concepts so French CV evidence can be compared to English
    # requirements without pretending the words are unrelated.
    _BILINGUAL_BRIDGE = {
        "analyse de performance": "performance analysis",
        "analyse des performances": "performance analysis",
        "analyse de donnees": "data analysis",
        "analyse de données": "data analysis",
        "analyse avancee": "advanced analytics",
        "analyse avancée": "advanced analytics",
        "reporting decisionnel": "management reporting",
        "reporting décisionnel": "management reporting",
        "reporting": "reporting",
        "tableau de bord": "dashboard",
        "tableaux de bord": "dashboards",
        "visualisations": "dashboards",
        "indicateurs": "indicators kpi",
        "kpi": "kpi indicators",
        "fiabilisation des donnees": "data quality",
        "fiabilisation des données": "data quality",
        "qualite des donnees": "data quality",
        "qualité des données": "data quality",
        "automatisation de processus": "process automation process improvement",
        "automatisation": "automation",
        "amelioration de processus": "process improvement",
        "amélioration de processus": "process improvement",
        "amelioration continue": "continuous improvement",
        "amélioration continue": "continuous improvement",
        "besoins metiers": "business needs",
        "besoins métiers": "business needs",
        "outils metiers": "business tools",
        "outils métier": "business tools",
        "parties prenantes": "stakeholders",
        "pilotage": "performance management",
        "performance operationnelle": "operational performance",
        "performance opérationnelle": "operational performance",
        "gestion": "management",
        "gestion de projet": "project management",
        "gestion des projets": "project management",
        "gestion documentaire": "document management",
        "strategie": "strategy",
        "stratégie": "strategy",
        "commerce": "business retail commerce",
        "vente": "sales",
        "ventes": "sales",
        "marge": "margin",
        "rentabilite": "profitability",
        "rentabilité": "profitability",
        "anglais": "english",
        "francais": "french",
        "français": "french",
        "arabe": "arabic",
        "langue maternelle": "native",
        "courant": "fluent",
        "courante": "fluent",
        "master 1": "master degree",
        "master 2": "master degree",
        "double diplome": "double master degree",
        "double diplôme": "double master degree",
        "informatique": "computer science",
        "business analytics": "business analytics",
        "business intelligence": "business intelligence",
        "analyse": "analysis",
        "donnees": "data",
        "données": "data",
        "decisionnel": "decision support",
        "décisionnel": "decision support",
        "previsions": "forecasting",
        "prévisions": "forecasting",
        "dimensionnements": "capacity planning",
        "controle": "control",
        "contrôle": "control",
        "anomalies": "issues anomalies",
        "productivite": "productivity",
        "productivité": "productivity",
        "flux d'activite": "activity flows",
        "flux d’activité": "activity flows",
        "client": "client stakeholder",
        "coaching": "coaching",
    }

    def _get_embedder(self):
        cls = type(self)

        if cls._SHARED_EMBEDDER_ATTEMPTED:
            return cls._SHARED_EMBEDDER

        cls._SHARED_EMBEDDER_ATTEMPTED = True

        global SentenceTransformer
        global SENTENCE_TRANSFORMERS_AVAILABLE
        global _SENTENCE_TRANSFORMERS_IMPORT_ERROR

        # Lazy import: JAM and Capture stay lightweight until Analyze is used.
        if SENTENCE_TRANSFORMERS_AVAILABLE is None:
            try:
                from sentence_transformers import (
                    SentenceTransformer as _SentenceTransformer,
                )

                SentenceTransformer = _SentenceTransformer
                SENTENCE_TRANSFORMERS_AVAILABLE = True
            except Exception as exc:  # pragma: no cover - optional dependency
                SentenceTransformer = None
                SENTENCE_TRANSFORMERS_AVAILABLE = False
                _SENTENCE_TRANSFORMERS_IMPORT_ERROR = str(exc)

        if not SENTENCE_TRANSFORMERS_AVAILABLE or SentenceTransformer is None:
            cls._SHARED_EMBEDDER_ERROR = (
                _SENTENCE_TRANSFORMERS_IMPORT_ERROR
                or "sentence-transformers is not installed"
            )
            return None

        try:
            model_source = (
                str(SEMANTIC_MODEL_DIR)
                if SEMANTIC_MODEL_DIR.exists()
                else self.EMBEDDING_MODEL
            )
            cls._SHARED_EMBEDDER = SentenceTransformer(
                model_source
            )
        except Exception as exc:  # pragma: no cover - environment/network dependent
            cls._SHARED_EMBEDDER = None
            cls._SHARED_EMBEDDER_ERROR = str(exc)

        return cls._SHARED_EMBEDDER

    @classmethod
    def _canonicalize_cross_language(cls, text: str) -> str:
        normalized = cls._normalize(text)

        # Longest phrases first so "analyse de performance" is not partially
        # consumed by the generic "analyse" mapping.
        for source, target in sorted(
            cls._BILINGUAL_BRIDGE.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        ):
            source_norm = cls._normalize(source)
            normalized = re.sub(
                rf"(?<![a-z0-9]){re.escape(source_norm)}(?![a-z0-9])",
                f" {target} ",
                normalized,
            )

        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    @classmethod
    def _looks_like_heading(cls, text: str, *, cv: bool = False) -> bool:
        cleaned = cls._normalize(text).strip(" :")
        headings = cls._CV_HEADINGS if cv else cls._JD_HEADINGS

        if cleaned in headings:
            return True

        words = cleaned.split()
        if len(words) <= 6 and text.strip().isupper():
            return True

        if cleaned.endswith(":") and len(words) <= 7:
            return True

        return False

    @classmethod
    def _explicit_language_match(cls, requirement: str, cv_text: str) -> float:
        req_norm = cls._normalize(requirement)
        cv_norm = cls._normalize(cv_text)

        for language, aliases in LANGUAGES.items():
            alias_norms = [cls._normalize(alias) for alias in aliases]
            if not any(re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", req_norm) for alias in alias_norms):
                continue

            if any(re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", cv_norm) for alias in alias_norms):
                return 0.97

        return 0.0

    @classmethod
    def _explicit_skill_match(cls, requirement: str, evidence: str) -> float:
        req_norm = cls._normalize(requirement)
        ev_norm = cls._normalize(evidence)
        best = 0.0

        for spec in SKILLS.values():
            aliases = [cls._normalize(alias) for alias in spec.get("aliases", [])]
            req_hit = any(
                re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", req_norm)
                for alias in aliases
            )
            if not req_hit:
                continue
            ev_hit = any(
                re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", ev_norm)
                for alias in aliases
            )
            if ev_hit:
                best = max(best, 0.94)

        return best


    @classmethod
    def _explicit_concept_match(cls, requirement: str, evidence: str) -> float:
        req_norm = cls._normalize(requirement)
        ev_norm = cls._normalize(evidence)
        best = 0.0

        # BUSINESS_CONCEPTS already contains bilingual aliases. Matching two
        # aliases of the same concept is stronger evidence than raw lexical
        # similarity. Example:
        #   "management reports / dashboards" <->
        #   "reporting décisionnel / tableaux de bord"
        for aliases in BUSINESS_CONCEPTS.values():
            alias_norms = [
                cls._normalize(alias)
                for alias in aliases
            ]

            req_hit = any(
                re.search(
                    rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])",
                    req_norm,
                )
                for alias in alias_norms
            )

            if not req_hit:
                continue

            ev_hit = any(
                re.search(
                    rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])",
                    ev_norm,
                )
                for alias in alias_norms
            )

            if ev_hit:
                best = max(
                    best,
                    0.90,
                )

        # Role aliases are also bilingual. This prevents an explicit
        # "Business Data Analyst / Analyste Performance" CV headline from
        # looking unrelated to a Business Analyst / Performance Analyst role.
        for aliases in ROLE_FAMILIES.values():
            alias_norms = [
                cls._normalize(alias)
                for alias in aliases
            ]

            req_aliases = [
                alias
                for alias in alias_norms
                if alias and alias in req_norm
            ]

            if not req_aliases:
                continue

            if any(
                alias in ev_norm
                for alias in alias_norms
                if alias
            ):
                best = max(
                    best,
                    0.88,
                )

        return best

    def __init__(self) -> None:
        cls = type(self)

        if SKLEARN_AVAILABLE and not cls._SHARED_READY:
            self._classifier = None
            self._classifier_vectorizer = None
            self._classifier_error: str | None = None
            self._build_role_classifier()
            cls._SHARED_CLASSIFIER = self._classifier
            cls._SHARED_VECTORIZER = self._classifier_vectorizer
            cls._SHARED_ERROR = self._classifier_error
            cls._SHARED_READY = True
        else:
            self._classifier = cls._SHARED_CLASSIFIER
            self._classifier_vectorizer = cls._SHARED_VECTORIZER
            self._classifier_error = cls._SHARED_ERROR

    # ------------------------------------------------------------------
    # Normalization / splitting
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_accents(text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text or "")
        return "".join(ch for ch in normalized if not unicodedata.combining(ch))

    @classmethod
    def _normalize(cls, text: str) -> str:
        value = cls._strip_accents(text).lower()
        value = value.replace("’", "'").replace("`", "'")
        value = re.sub(r"[^a-z0-9+#./' -]+", " ", value)
        value = re.sub(r"\s+", " ", value)
        return value.strip()

    @classmethod
    def _tokens(cls, text: str) -> list[str]:
        values = re.findall(r"[a-z0-9][a-z0-9+#./-]*", cls._normalize(text))
        return [
            token.strip("./-")
            for token in values
            if token.strip("./-")
            and token.strip("./-") not in STOPWORDS
            and (len(token.strip("./-")) >= 3 or token in {"sql", "dax", "etl", "aws", "gcp"})
            and not token.isdigit()
        ]

    @staticmethod
    def _split_units(text: str) -> list[str]:
        raw_lines = [line.strip(" \t•*-–—") for line in (text or "").splitlines()]
        units: list[str] = []
        for line in raw_lines:
            if not line:
                continue
            # Do not split on ':' because requirement headings such as
            # "Required: SQL, Python..." belong to the text that follows.
            parts = re.split(r"(?<=[.!?;])\s+", line)
            for part in parts:
                part = re.sub(r"\s+", " ", part).strip()
                if part:
                    units.append(part)
        return units

    @classmethod
    def _is_boilerplate(cls, text: str) -> bool:
        normalized = cls._normalize(text)
        return any(marker in normalized for marker in cls._BOILERPLATE)

    @classmethod
    def _importance(cls, text: str) -> tuple[str, float]:
        normalized = cls._normalize(text)
        if any(cls._normalize(marker) in normalized for marker in REQUIRED_MARKERS):
            return "required", 1.55
        if any(cls._normalize(marker) in normalized for marker in PREFERRED_MARKERS):
            return "preferred", 0.75
        if any(cls._normalize(marker) in normalized for marker in RESPONSIBILITY_MARKERS):
            return "responsibility", 1.05
        if any(hint in normalized for hint in cls._ACTION_HINTS):
            return "responsibility", 0.95
        return "context", 0.55

    def extract_requirements(
        self,
        title: str,
        description: str,
        limit: int = 24,
    ) -> list[SemanticRequirement]:
        candidates: list[SemanticRequirement] = []
        seen: set[str] = set()

        if title.strip():
            candidates.append(
                SemanticRequirement(
                    text=f"Target role: {title.strip()}",
                    importance="role",
                    weight=1.45,
                )
            )

        explicit_requirement_hints = (
            "proficiency", "proficient", "knowledge of", "experience in",
            "experience with", "strong interest", "interest in",
            "fluent", "fluency", "essential", "required", "must",
            "appreciated", "preferred", "plus", "analytical mindset",
            "analytical skills", "interpersonal skills", "team player",
            "rigor", "organisation", "organization", "curiosity",
            "maitrise", "maîtrise", "connaissance", "experience en",
            "expérience en", "anglais", "francais", "français",
        )

        for unit in self._split_units(description):
            normalized = self._normalize(unit)

            if (
                not normalized
                or normalized in seen
                or self._looks_like_heading(unit, cv=False)
            ):
                continue

            seen.add(normalized)
            tokens = self._tokens(unit)

            if len(tokens) < 2 or len(unit) > 360:
                continue

            if self._is_boilerplate(unit):
                continue

            # Structured facts are handled by deterministic extractors.
            if re.search(
                r"\b(?:minimum|min\.?|at least|au moins)?\s*\d+(?:[.,]\d+)?\s*\+?\s*(?:years?|yrs?|ans?)\b.*\b(?:experience|expérience)\b",
                normalized,
            ):
                continue

            if any(word in normalized for word in (
                "salary", "salaire", "remuneration", "rémunération",
            )):
                continue

            if len(tokens) <= 18 and re.search(
                r"\b(?:master|bachelor|licence|bac\s*\+?\s*\d|degree|diploma|diplome|diplôme|bts|dcg)\b",
                normalized,
            ):
                continue

            importance, weight = self._importance(unit)

            has_action = any(hint in normalized for hint in self._ACTION_HINTS)
            has_requirement_hint = any(
                self._normalize(hint) in normalized
                for hint in explicit_requirement_hints
            )

            # Drop company marketing / descriptive prose. Keep actual duties,
            # requirements and preferences only.
            if importance == "context" and not (has_action or has_requirement_hint):
                continue

            if importance == "context":
                importance = "preferred" if has_requirement_hint else "responsibility"
                weight = 0.75 if has_requirement_hint else 0.95

            candidates.append(
                SemanticRequirement(
                    text=unit,
                    importance=importance,
                    weight=weight,
                )
            )

        priority = {
            "required": 0,
            "role": 1,
            "responsibility": 2,
            "preferred": 3,
            "context": 4,
        }

        indexed = list(enumerate(candidates))
        indexed.sort(
            key=lambda item: (
                priority.get(item[1].importance, 5),
                item[0],
            )
        )

        return [
            item
            for _, item in indexed[:limit]
        ]

    def extract_cv_units(
        self,
        cv_text: str,
        limit: int = 320,
    ) -> list[str]:
        units: list[str] = []
        seen: set[str] = set()

        for unit in self._split_units(cv_text):
            normalized = self._normalize(unit)

            if (
                not normalized
                or normalized in seen
                or self._looks_like_heading(unit, cv=True)
            ):
                continue

            seen.add(normalized)
            tokens = self._tokens(unit)

            if len(tokens) < 2 or len(unit) > 420:
                continue

            # Reject naked labels / page furniture that can never constitute
            # evidence for a job requirement.
            if re.fullmatch(
                r"(?:profil|profile|formation|education|langues|languages|certifications?|projects?|projets?|experience|experiences professionnelles?)",
                normalized,
            ):
                continue

            units.append(unit)

            if len(units) >= limit:
                break

        return units

    # ------------------------------------------------------------------
    # Local job-family classifier
    # ------------------------------------------------------------------

    def _build_role_classifier(self) -> None:
        if not SKLEARN_AVAILABLE:
            return

        samples: list[str] = []
        labels: list[str] = []

        for family, aliases in ROLE_FAMILIES.items():
            signals = ROLE_DOMAIN_SIGNALS.get(family, [])
            clean_aliases = list(dict.fromkeys(aliases))
            clean_signals = list(dict.fromkeys(signals))

            for alias in clean_aliases:
                samples.append(alias)
                labels.append(family)

            for alias in clean_aliases[:4]:
                for signal in clean_signals[:8]:
                    samples.append(f"{alias}. {signal}.")
                    labels.append(family)

            # Domain-only examples make the classifier useful when a job board
            # uses a vague title but the description is specific.
            for signal in clean_signals[:10]:
                samples.append(f"Responsibilities include {signal}.")
                labels.append(family)

        if len(set(labels)) < 2:
            return

        try:
            self._classifier_vectorizer = FeatureUnion([
                (
                    "word",
                    TfidfVectorizer(
                        strip_accents="unicode",
                        lowercase=True,
                        ngram_range=(1, 2),
                        sublinear_tf=True,
                        min_df=1,
                        max_features=7000,
                    ),
                ),
                (
                    "char",
                    TfidfVectorizer(
                        strip_accents="unicode",
                        lowercase=True,
                        analyzer="char_wb",
                        ngram_range=(3, 5),
                        sublinear_tf=True,
                        min_df=1,
                        max_features=9000,
                    ),
                ),
            ])
            matrix = self._classifier_vectorizer.fit_transform(samples)
            self._classifier = LogisticRegression(
                max_iter=1600,
                class_weight="balanced",
                random_state=42,
                C=4.0,
            )
            self._classifier.fit(matrix, labels)
        except Exception as exc:  # pragma: no cover - defensive runtime fallback
            self._classifier = None
            self._classifier_vectorizer = None
            self._classifier_error = str(exc)

    def classify_role(self, title: str, description: str) -> dict:
        # Repeat the explicit title so the classifier does not let one
        # incidental responsibility word override a clear job title.
        text = (f"{title}\n{title}\n{title}\n" + description[:2200]).strip()
        if not text:
            return {
                "available": False,
                "predicted_family": None,
                "confidence": 0,
                "top_predictions": [],
            }

        if self._classifier is None or self._classifier_vectorizer is None:
            # Transparent lexical fallback. It is deliberately not presented as
            # ML when sklearn is unavailable.
            normalized = self._normalize(text)
            scored: list[tuple[str, float]] = []
            for family, aliases in ROLE_FAMILIES.items():
                signal_hits = sum(
                    1 for signal in ROLE_DOMAIN_SIGNALS.get(family, [])
                    if self._normalize(signal) in normalized
                )
                alias_hits = sum(
                    1 for alias in aliases
                    if self._normalize(alias) in normalized
                )
                score = alias_hits * 2.0 + signal_hits * 0.7
                if score > 0:
                    scored.append((family, score))
            scored.sort(key=lambda item: item[1], reverse=True)
            if not scored:
                return {
                    "available": False,
                    "predicted_family": None,
                    "confidence": 0,
                    "top_predictions": [],
                }
            total = sum(score for _, score in scored) or 1.0
            top = [
                {"family": family, "confidence": round(score / total * 100)}
                for family, score in scored[:3]
            ]
            return {
                "available": True,
                "predicted_family": top[0]["family"],
                "confidence": top[0]["confidence"],
                "top_predictions": top,
                "engine": "taxonomy fallback",
            }

        vector = self._classifier_vectorizer.transform([text])
        probabilities = self._classifier.predict_proba(vector)[0]
        classes = list(self._classifier.classes_)
        ranked = sorted(
            zip(classes, probabilities),
            key=lambda item: item[1],
            reverse=True,
        )[:3]
        top = [
            {"family": str(family), "confidence": round(float(probability) * 100)}
            for family, probability in ranked
        ]
        return {
            "available": True,
            "predicted_family": top[0]["family"] if top else None,
            "confidence": top[0]["confidence"] if top else 0,
            "top_predictions": top,
            "engine": "logistic regression",
        }

    # ------------------------------------------------------------------
    # Requirement -> CV evidence similarity
    # ------------------------------------------------------------------

    @classmethod
    def _fallback_similarity(cls, left: str, right: str) -> float:
        left_tokens = set(cls._tokens(left))
        right_tokens = set(cls._tokens(right))
        if not left_tokens or not right_tokens:
            return 0.0
        intersection = len(left_tokens.intersection(right_tokens))
        union = len(left_tokens.union(right_tokens)) or 1
        jaccard = intersection / union
        sequence = SequenceMatcher(None, cls._normalize(left), cls._normalize(right)).ratio()
        return max(0.0, min(1.0, jaccard * 0.72 + sequence * 0.28))

    @classmethod
    def _requirement_token_coverage(cls, requirement: str, evidence: str) -> float:
        noise = {
            "required", "requirement", "requirements", "must", "preferred",
            "plus", "target", "role", "candidate", "experience", "years",
            "year", "responsible", "responsibilities", "mission", "missions",
        }
        left = {token for token in cls._tokens(requirement) if token not in noise}
        right = {token for token in cls._tokens(evidence) if token not in noise}
        if not left or not right:
            return 0.0
        return len(left.intersection(right)) / len(left)

    def _similarity_matrix(
        self,
        requirements: list[str],
        cv_units: list[str],
        cv_text: str = "",
    ):
        if not requirements or not cv_units:
            return [], "none"

        embedder = self._get_embedder()

        if embedder is not None:
            try:
                req_embeddings = embedder.encode(
                    requirements,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                )
                cv_embeddings = embedder.encode(
                    cv_units,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                )

                matrix = (
                    req_embeddings @ cv_embeddings.T
                ).tolist()

                # Explicit structured evidence must outrank vague semantic
                # neighbors. This also prevents English requirements from being
                # marked missing when the CV explicitly says "Anglais : C1".
                for row_index, requirement in enumerate(requirements):
                    language_score = self._explicit_language_match(
                        requirement,
                        cv_text,
                    )

                    for col_index, evidence in enumerate(cv_units):
                        skill_score = self._explicit_skill_match(
                            requirement,
                            evidence,
                        )

                        concept_score = self._explicit_concept_match(
                            requirement,
                            evidence,
                        )

                        matrix[row_index][col_index] = max(
                            float(matrix[row_index][col_index]),
                            skill_score,
                            concept_score,
                        )

                    if language_score > 0:
                        # Put the boost on the most language-looking CV unit.
                        best_lang_index = max(
                            range(len(cv_units)),
                            key=lambda idx: self._fallback_similarity(
                                self._canonicalize_cross_language(requirement),
                                self._canonicalize_cross_language(cv_units[idx]),
                            ),
                        )
                        matrix[row_index][best_lang_index] = max(
                            matrix[row_index][best_lang_index],
                            language_score,
                        )

                return matrix, "multilingual MiniLM"

            except Exception as exc:  # pragma: no cover - defensive fallback
                type(self)._SHARED_EMBEDDER_ERROR = str(exc)

        # Robust offline fallback: bilingual canonicalization + word/char TF-IDF.
        canonical_requirements = [
            self._canonicalize_cross_language(text)
            for text in requirements
        ]
        canonical_cv = [
            self._canonicalize_cross_language(text)
            for text in cv_units
        ]

        if not SKLEARN_AVAILABLE:
            matrix = [
                [
                    self._fallback_similarity(req, unit)
                    for unit in canonical_cv
                ]
                for req in canonical_requirements
            ]
            engine = "bilingual lexical fallback"
        else:
            corpus = canonical_requirements + canonical_cv

            word_vectorizer = TfidfVectorizer(
                strip_accents="unicode",
                lowercase=True,
                ngram_range=(1, 2),
                sublinear_tf=True,
                min_df=1,
                max_features=10000,
            )

            char_vectorizer = TfidfVectorizer(
                strip_accents="unicode",
                lowercase=True,
                analyzer="char_wb",
                ngram_range=(3, 5),
                sublinear_tf=True,
                min_df=1,
                max_features=12000,
            )

            word_matrix = word_vectorizer.fit_transform(corpus)
            char_matrix = char_vectorizer.fit_transform(corpus)
            req_count = len(requirements)

            word_sim = cosine_similarity(
                word_matrix[:req_count],
                word_matrix[req_count:],
            )
            char_sim = cosine_similarity(
                char_matrix[:req_count],
                char_matrix[req_count:],
            )

            matrix = (
                word_sim * 0.78 +
                char_sim * 0.22
            ).tolist()
            engine = "bilingual TF-IDF fallback"

        for row_index, requirement in enumerate(requirements):
            language_score = self._explicit_language_match(
                requirement,
                cv_text,
            )

            for col_index, evidence in enumerate(cv_units):
                coverage = self._requirement_token_coverage(
                    self._canonicalize_cross_language(requirement),
                    self._canonicalize_cross_language(evidence),
                )

                coverage_signal = coverage * 0.80
                skill_signal = self._explicit_skill_match(
                    requirement,
                    evidence,
                )

                concept_signal = self._explicit_concept_match(
                    requirement,
                    evidence,
                )

                matrix[row_index][col_index] = max(
                    float(matrix[row_index][col_index]),
                    coverage_signal,
                    skill_signal,
                    concept_signal,
                )

            if language_score > 0:
                best_lang_index = max(
                    range(len(cv_units)),
                    key=lambda idx: self._fallback_similarity(
                        self._canonicalize_cross_language(requirement),
                        self._canonicalize_cross_language(cv_units[idx]),
                    ),
                )

                matrix[row_index][best_lang_index] = max(
                    matrix[row_index][best_lang_index],
                    language_score,
                )

        return matrix, engine

    @staticmethod
    def _evidence_credit(similarity: float) -> tuple[float, str]:
        if similarity >= 0.62:
            return 1.0, "strong"
        if similarity >= 0.45:
            return 0.72, "partial"
        if similarity >= 0.30:
            return 0.35, "weak"
        return 0.0, "missing"

    def match_requirements(self, title: str, description: str, cv_text: str) -> dict:
        requirements = self.extract_requirements(title, description)
        cv_units = self.extract_cv_units(cv_text)

        if not requirements or not cv_units:
            return {
                "applicable": False,
                "ratio": 0.0,
                "coverage": 0,
                "matched_count": 0,
                "requirement_count": len(requirements),
                "evidence": [],
                "engine": self.MODEL_NAME if SKLEARN_AVAILABLE else "lexical fallback",
            }

        matrix, similarity_engine = self._similarity_matrix(
            [item.text for item in requirements],
            cv_units,
            cv_text,
        )

        evidence: list[dict] = []
        achieved = 0.0
        total_weight = 0.0
        matched_count = 0

        for index, requirement in enumerate(requirements):
            row = matrix[index] if index < len(matrix) else []
            if row:
                best_index = max(range(len(row)), key=lambda value: row[value])
                similarity = float(row[best_index])
                cv_evidence = cv_units[best_index]
            else:
                similarity = 0.0
                cv_evidence = ""

            credit, status = self._evidence_credit(similarity)
            total_weight += requirement.weight
            achieved += credit * requirement.weight
            if status in {"strong", "partial"}:
                matched_count += 1

            evidence.append({
                "requirement": requirement.text,
                "importance": requirement.importance,
                "weight": round(requirement.weight, 2),
                "similarity": round(similarity, 3),
                "similarity_pct": round(similarity * 100),
                "status": status,
                "cv_evidence": cv_evidence,
            })

        ratio = achieved / total_weight if total_weight else 0.0
        evidence.sort(
            key=lambda item: (
                {"required": 0, "role": 1, "responsibility": 2, "preferred": 3, "context": 4}.get(item["importance"], 5),
                -item["similarity"],
            )
        )

        return {
            "applicable": bool(evidence),
            "ratio": max(0.0, min(1.0, ratio)),
            "coverage": round(ratio * 100),
            "matched_count": matched_count,
            "requirement_count": len(evidence),
            "evidence": evidence,
            "strong": [item for item in evidence if item["status"] == "strong"],
            "partial": [item for item in evidence if item["status"] == "partial"],
            "missing": [item for item in evidence if item["status"] == "missing"],
            "engine": similarity_engine,
        }

    def analyze(self, title: str, description: str, cv_text: str) -> dict:
        requirement_match = self.match_requirements(title, description, cv_text)
        role_classifier = self.classify_role(title, description)

        return {
            **requirement_match,
            "role_classifier": role_classifier,
            "ml_available": bool(
                SENTENCE_TRANSFORMERS_AVAILABLE or SKLEARN_AVAILABLE
            ),
            "engine_name": self.ENGINE_NAME,
            "model": requirement_match.get(
                "engine",
                self.MODEL_NAME,
            ),
            "embedding_model": self.EMBEDDING_MODEL,
            "embedding_model_available": self._get_embedder() is not None,
            "embedding_error": type(self)._SHARED_EMBEDDER_ERROR,
            "local_only": True,
        }
