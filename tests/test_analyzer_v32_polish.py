from pathlib import Path

from services.analyzer_service import AnalyzerService


DATA_CV = """
Farouk
Data Analyst
Master 2 Business Analytics
Data Analyst Internship | 2024 - 2026
SQL Python Power BI DAX Tableau Excel SAP BusinessObjects
Built dashboards, KPIs, reporting, data quality controls and automation.
French C1 English C1
"""


def service_with_cv() -> AnalyzerService:
    service = AnalyzerService()
    service.extract_cv_text = lambda _path: DATA_CV
    return service


def test_specific_education_field_is_not_satisfied_by_unrelated_higher_degree():
    service = AnalyzerService()

    accountant = service.extract_education_profile(
        "Formation supérieure en comptabilité / finance (Bac+2 ou Bac+3 : BTS ou DCG).",
        job=True,
    )
    legal = service.extract_education_profile(
        "Vous êtes titulaire d’un Master 2 en droit social, droit du travail ou équivalent.",
        job=True,
    )
    cv = service.extract_education_profile(
        "Master 2 Business Analytics",
        job=False,
    )

    assert accountant["level"] == 2
    assert "Accounting" in accountant["fields"]
    assert "Finance" in accountant["fields"]
    assert service.match_education(accountant, cv)["ratio"] == 0

    assert legal["level"] == 4
    assert "Labor / Social Law" in legal["fields"]
    assert service.match_education(legal, cv)["ratio"] == 0


def test_generic_master_requirement_can_match_master_level():
    service = AnalyzerService()
    job = service.extract_education_profile("Master degree required.", job=True)
    cv = service.extract_education_profile("Master 2 Business Analytics", job=False)
    result = service.match_education(job, cv)

    assert result["ratio"] == 1
    assert result["field_ratio"] is None


def test_reference_detection_supports_common_job_reference_formats():
    service = AnalyzerService()

    assert service.extract_reference("Référence : ABC-2026-17")["value"] == "ABC-2026-17"
    assert service.extract_reference("Job ID: LEG-12345")["value"] == "LEG-12345"
    assert service.extract_reference("Offre n° ACC-7788")["value"] == "ACC-7788"
    assert service.extract_reference("https://www.linkedin.com/jobs/view/4463346221/")["value"] == "4463346221"


def test_required_skills_dimension_includes_profession_specific_requirements():
    service = service_with_cv()
    description = """
    We are hiring a Junior Accountant to join the finance team.
    Formation supérieure en comptabilité / finance (Bac+2 ou Bac+3 : BTS ou DCG).
    Excel and SAP are required for daily work. The successful candidate must understand
    IFRS, general ledger accounting, journal entries, account reconciliation, month-end
    closing, VAT, accounts payable and accounts receivable. You will prepare financial
    statements, reconcile balances, support the monthly close and maintain accounting
    records. At least 2 years of accounting experience is required. Strong organization,
    accuracy and communication are expected in this permanent role.
    """

    result = service.analyze("Junior Accountant", description, cv_path="dummy")
    skills = next(
        item for item in result["score_explanation"]
        if item["dimension"] == "Required skills & tools"
    )

    # Excel/SAP overlap must not create a perfect skills score when the CV lacks
    # the accounting profession-specific requirements.
    assert skills["points"] < skills["max_points"]
    assert skills["points"] <= 12.5
    assert "IFRS".lower() in {value.lower() for value in result["missing_required_competencies"]}
    assert result["education_match"]["ratio"] == 0


def test_legal_education_and_domain_are_not_claimed_for_data_cv():
    service = service_with_cv()
    description = """
    Nous recherchons un Juriste droit social pour conseiller les équipes RH et les managers.
    Vous êtes titulaire d’un Master 2 en droit social, droit du travail ou équivalent.
    Vous maîtrisez le droit social, le droit du travail, le code du travail, les conventions
    collectives, le CSE, les relations sociales, les contrats de travail et le contentieux.
    Vous assurez la veille juridique, accompagnez les procédures disciplinaires et conseillez
    sur les relations individuelles et collectives. Une expérience de 3 ans en droit social
    est requise ainsi qu’une excellente capacité rédactionnelle et relationnelle.
    """

    result = service.analyze("Juriste droit social (F/H)", description, cv_path="dummy")

    assert result["education_match"]["ratio"] == 0
    assert result["critical_domain_match"]["ratio"] == 0
    assert result["role_match"]["mismatch"] is True
    if result["score"] is not None:
        assert result["score"] <= 24


def test_capture_work_mode_is_visible_segmented_control_and_analyzer_ui_has_export():
    root = Path(__file__).resolve().parents[1]
    capture = (root / "src" / "capture_app.py").read_text(encoding="utf-8")
    index = (root / "ui" / "index.html").read_text(encoding="utf-8")
    hotfix = (root / "ui" / "js" / "analyzer_hotfix.js").read_text(encoding="utf-8")

    assert "self.work_mode_buttons" in capture
    assert "def select_work_mode" in capture
    assert 'for index, mode in enumerate(("Onsite", "Hybrid", "Remote"))' in capture
    assert 'id="exportAnalyzerPdfBtn"' in index
    assert "exportCurrentAnalyzerPdf" in hotfix
    assert "analysis-experience-lines" in hotfix
    assert "data-copy-reference" in hotfix
