from pathlib import Path

from services.analyzer_service import AnalyzerService


CV = """
Farouk DAMERGI
Master 2 Data / Business Analytics - Double Diplôme
Data Analyst | BI Analyst | Business Data Analyst | Analyste Performance & Data

PROFIL
Data & BI Analyst. Spécialisé en analyse de performance, Business Intelligence,
fiabilisation des données, reporting décisionnel et automatisation de processus
avec Power BI, SQL, Python et Excel.

EXPÉRIENCES PROFESSIONNELLES
Stagiaire Data & Performance Analyst
Air France
Fiabilisation et analyse de données opérationnelles afin de sécuriser les prévisions,
KPI et reportings récurrents.
Conception et amélioration de 20+ visualisations et dashboards Power BI/Excel.
Automatisation de traitements et outils.
Outils : Excel avancé, VBA, Power BI, SAP BO, SharePoint, Power Automate, Python.

Analyste Qualité & Performance Opérationnelle
Suivi de 4 KPI clés pour piloter la performance ; reporting hebdomadaire, mensuel
et trimestriel au client.
Outils : Excel, VBA, Power BI, Salesforce, Jira.

FORMATION
Master 2 - Architecture des Données et Exploration Optimisée
Data engineering, BI, analyse avancée, machine learning.
Master 1 - Business Analytics
Business Intelligence, Big Data, bases de données, Business Process Management,
Strategic Management.

COMPÉTENCES TECHNIQUES
Data & SQL : SQL, Python, dbt, data quality.
BI & Reporting : Power BI, DAX, Power Query, Tableau, Excel avancé, KPI,
reporting, analyse de performance.
Automatisation & Outils métier : VBA, Power Automate, SAP BO, SharePoint, Jira,
Salesforce.

LANGUES
Français : C1 | Anglais : C1 | Arabe : Langue maternelle
"""


JOB = """
ROLE SUMMARY
Within the Group Leasing Department, you will support the management of the Group's
commercial performance and the deployment of cross-functional projects across Europe.
You will act as an analytical and operational partner to Leasing teams with strong
exposure to performance management, innovation, data, business tools, and continuous
improvement initiatives.

KEY RESPONSIBILITIES
Produce and analyze Leasing performance indicators at Group level.
Prepare management reports, dashboards, and analytical reviews.
Contribute to data quality enhancement and the harmonization of practices across countries.
Identify opportunities to simplify and improve processes.

WHO ARE WE LOOKING FOR?
Master's degree (Business School, Engineering School, or University).
Initial experience in analysis, consulting, real estate, retail, finance, or project management is a plus.

TECHNICAL SKILLS
Advanced proficiency in Excel and PowerPoint.
Strong analytical mindset and affinity for data.
Knowledge of Power BI, CRM systems, or data analytics tools is appreciated.
Interest in Artificial Intelligence topics.
Fluent English is essential.
"""


def _full_analysis(tmp_path: Path) -> dict:
    cv = tmp_path / "cv.txt"
    cv.write_text(CV, encoding="utf-8")
    return AnalyzerService().analyze(
        "CDI - Group Leasing Business Analyst (H/F)",
        JOB,
        str(cv),
    )


def test_english_c1_is_not_missing(tmp_path):
    result = _full_analysis(tmp_path)

    language_match = result["language_match"]
    assert "English" in language_match["matched"]
    assert "English" not in language_match["missing"]

    english_semantic = [
        item for item in result["semantic_requirement_evidence"]
        if "english" in item["requirement"].lower()
    ]
    assert english_semantic
    assert english_semantic[0]["status"] in {"strong", "partial"}


def test_engineering_school_does_not_become_engineering_field_requirement():
    service = AnalyzerService()
    profile = service.extract_education_profile(JOB, job=True)

    assert profile["level"] >= 4
    assert "Engineering" not in profile["fields"]


def test_cv_heading_is_never_selected_as_semantic_evidence():
    service = AnalyzerService()
    semantic = service.semantic.analyze(
        "CDI - Group Leasing Business Analyst (H/F)",
        JOB,
        CV,
    )

    for item in semantic["evidence"]:
        assert item["cv_evidence"].strip().upper() != "EXPÉRIENCES PROFESSIONNELLES"


def test_cross_language_performance_and_reporting_find_real_evidence():
    service = AnalyzerService()
    semantic = service.semantic.analyze(
        "CDI - Group Leasing Business Analyst (H/F)",
        JOB,
        CV,
    )

    relevant = [
        item for item in semantic["evidence"]
        if (
            "performance indicators" in item["requirement"].lower()
            or "management reports" in item["requirement"].lower()
            or "data quality" in item["requirement"].lower()
        )
    ]

    assert relevant
    assert any(item["status"] in {"strong", "partial"} for item in relevant)
