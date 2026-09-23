import json
from pathlib import Path

from services.analyzer_service import AnalyzerService


class FakeSettings:
    def get(self, key: str, default: str = "") -> str:
        values = {
            "salary_target_min": "40000",
            "salary_target_max": "60000",
            "salary_currency": "EUR",
        }
        return values.get(key, default)


def make_cv(tmp_path: Path) -> Path:
    path = tmp_path / "cv.txt"
    path.write_text(
        """
Alex Example
Data Analyst / BI Analyst

Experience
Data Analyst | Jan 2023 - Present
Built Power BI dashboards and KPI reporting using DAX, Power Query, SQL and Python.
Automated recurring reporting and improved data-quality controls.
Worked with stakeholders on data governance and business requirements.

Education
Master 2 Business Analytics

Languages
French C1
English C1
Arabic native

Skills
Power BI, SQL, Python, Excel, Tableau, SAP BusinessObjects, Data Quality,
Data Governance, Git, Jira, Power Automate
""".strip(),
        encoding="utf-8",
    )
    return path


def make_service() -> AnalyzerService:
    service = AnalyzerService()
    service.settings = FakeSettings()
    return service


def test_v4_adds_local_ml_requirement_evidence(tmp_path: Path):
    service = make_service()
    cv = make_cv(tmp_path)

    result = service.analyze(
        "Data Analyst",
        """
We are hiring a Data Analyst for the analytics team.
Required: Power BI, SQL, Python and Excel.
You will build dashboards, own KPI reporting, automate recurring analysis,
work with stakeholders and improve data quality and governance.
Minimum 2 years of experience required. French and English are required.
Master degree preferred. Salary 45k-55k EUR annually.
""",
        cv_path=str(cv),
    )

    assert result["score_available"] is True
    assert result["score"] >= 75
    assert result["method"].startswith("JAM Match Engine v4.0")
    assert result["ml_engine"]["local_only"] is True
    assert result["semantic_match"]["applicable"] is True
    assert result["semantic_coverage"] >= 55
    assert result["semantic_role_classifier"]["predicted_family"] == "Data Analyst"
    assert any(
        "Power BI" in item["requirement"] and item["status"] in {"strong", "partial"}
        for item in result["semantic_requirement_evidence"]
    )
    # The analysis payload must remain safe to pass through pywebview/JSON.
    json.dumps(result)


def test_v4_semantic_layer_does_not_rescue_unrelated_legal_role(tmp_path: Path):
    service = make_service()
    cv = make_cv(tmp_path)

    result = service.analyze(
        "Juriste droit social",
        """
Nous recherchons un Juriste droit social pour accompagner les équipes RH.
Master 2 en droit social ou droit du travail requis. Minimum 7 ans d'expérience.
Vous conseillez les managers, rédigez des documents juridiques et gérez le CSE,
les conventions collectives, les contrats de travail, le contentieux et la veille juridique.
Anglais professionnel requis.
""",
        cv_path=str(cv),
    )

    assert result["role_match"]["mismatch"] is True
    assert result["semantic_role_classifier"]["predicted_family"] == "Legal"
    assert result["semantic_coverage"] <= 25
    if result["score"] is not None:
        assert result["score"] <= 24


def test_v4_ui_and_currency_flags_are_wired():
    root = Path(__file__).resolve().parents[1]
    batch2 = (root / "ui" / "js" / "batch2.js").read_text(encoding="utf-8")
    analyzer_ui = (root / "ui" / "js" / "analyzer_hotfix.js").read_text(encoding="utf-8")
    requirements = (root / "requirements.txt").read_text(encoding="utf-8")

    assert "${item.flag} ${item.code}" in batch2
    assert "Semantic requirement evidence" in analyzer_ui
    assert "LOCAL ML" in analyzer_ui
    assert "Requirement coverage" in analyzer_ui
    assert "JAM Match Engine v4.0" in analyzer_ui
    assert "scikit-learn" in requirements
