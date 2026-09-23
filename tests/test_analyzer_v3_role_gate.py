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


def make_service() -> AnalyzerService:
    service = AnalyzerService()
    service.settings = FakeSettings()
    return service


def write_data_cv(tmp_path: Path) -> Path:
    path = tmp_path / "cv.txt"
    path.write_text(
        """
Alex Example
Data Analyst / BI Analyst

Experience
Data Analyst | Jan 2023 - Present
Built Power BI dashboards and KPI reporting using DAX, Power Query, SQL and Python.
Worked with stakeholders on data quality, automation and process improvement.
Business Analyst | 2022 - 2023
Requirements gathering, Excel reporting, Salesforce and Tableau.

Education
Master in Business Analytics

Languages
French C1
English C1
Arabic native

Skills
Power BI, DAX, Power Query, SQL, Python, Excel, Tableau, SAP BusinessObjects,
Salesforce, Talend, PySpark, dbt, Data Quality, Data Governance, Git, Jira,
SharePoint, Power Automate
""".strip(),
        encoding="utf-8",
    )
    return path


def test_accountant_role_is_hard_capped_for_data_cv(tmp_path: Path):
    service = make_service()
    cv = write_data_cv(tmp_path)

    result = service.analyze(
        "Comptable",
        """
Nous recrutons un Comptable. Missions: tenue de la comptabilité générale,
saisie des factures, rapprochements bancaires, clôture mensuelle, déclarations
fiscales, TVA et préparation du bilan. Maîtrise Excel et SAP requise.
Minimum 2 ans d'expérience en comptabilité. Bac+5 finance/comptabilité.
Salaire 35k-40k EUR.
""",
        cv_path=str(cv),
    )

    assert result["score_available"] is True
    assert result["score"] <= 35
    assert result["role_match"]["mismatch"] is True
    assert "Accountant" in result["role_match"]["job_families"]
    assert result["salary"]["period"] == "annual"
    assert any("role family" in reason.lower() for reason in result["penalty_reasons"])


def test_matching_data_analyst_role_scores_strongly(tmp_path: Path):
    service = make_service()
    cv = write_data_cv(tmp_path)

    result = service.analyze(
        "Data Analyst",
        """
We are hiring a Data Analyst. Required: Power BI, SQL, Python and Excel.
Build dashboards, KPI reporting and recurring analysis. Minimum 2 years of
experience. French and English are required. Salary 45k-55k EUR annually.
""",
        cv_path=str(cv),
    )

    assert result["score_available"] is True
    assert result["score"] >= 80
    assert result["role_match"]["mismatch"] is False
    assert result["role_match"]["ratio"] >= 0.95
    assert result["salary_fit"] is True
    assert len(result["score_explanation"]) >= 4
    assert result["matched_skill_evidence"]
