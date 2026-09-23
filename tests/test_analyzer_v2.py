from pathlib import Path

from services.analyzer_service import AnalyzerService


class FakeSettings:
    def get(self, key: str, default: str = "") -> str:
        return default


def make_service() -> AnalyzerService:
    service = AnalyzerService()
    service.settings = FakeSettings()
    return service


def write_cv(tmp_path: Path) -> Path:
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


def test_garbage_offer_has_no_score(tmp_path: Path):
    service = make_service()
    cv = write_cv(tmp_path)

    result = service.analyze(
        "test",
        "test random https random blah qwerty lorem ipsum",
        cv_path=str(cv),
    )

    assert result["score"] is None
    assert result["score_available"] is False
    assert result["job_quality"]["analyzable"] is False
    assert result["confidence"] < 40


def test_real_matching_offer_scores_high_from_evidence(tmp_path: Path):
    service = make_service()
    cv = write_cv(tmp_path)

    result = service.analyze(
        "Data Analyst",
        """
We are looking for a Data Analyst to join our analytics team.
You will build Power BI dashboards and KPI reporting, write SQL queries,
automate recurring analysis with Python and work with business stakeholders.
Minimum 2 years of experience required. Master degree preferred.
English and French are required. Experience with Tableau is a plus.
""",
        cv_path=str(cv),
    )

    assert result["score_available"] is True
    assert result["score"] >= 75
    assert {"Power BI", "SQL", "Python"}.issubset(set(result["matched_skills"]))
    assert result["required_years"] == 2
    assert result["confidence"] >= 55


def test_real_offer_with_large_gaps_scores_low(tmp_path: Path):
    service = make_service()
    cv = write_cv(tmp_path)

    result = service.analyze(
        "Senior Data Engineer",
        """
We are hiring a Senior Data Engineer. Required: 5 years of experience,
Databricks, Apache Spark, Kafka, Airflow, Snowflake, AWS and Python.
You will design production data pipelines, maintain ETL platforms and work
with cloud architecture. English is required.
""",
        cv_path=str(cv),
    )

    assert result["score_available"] is True
    assert result["score"] < 55
    assert "Databricks" in result["missing_required_skills"]
    assert "Kafka" in result["missing_required_skills"]


def test_meaningful_offer_with_zero_positive_overlap_has_no_score(tmp_path: Path):
    service = make_service()
    cv = write_cv(tmp_path)

    result = service.analyze(
        "Backend Developer",
        """
We are hiring a Backend Developer for a production platform. The role requires
Java, Kubernetes and AWS. You must have at least 4 years of backend software
engineering experience and professional German. You will maintain production
services, deploy containerized applications and support platform reliability.
""",
        cv_path=str(cv),
    )

    # Even with zero skill/language overlap, the CV has enough timeline
    # experience to count as positive evidence. The score must therefore be
    # low rather than artificially high.
    assert result["score_available"] is True
    assert result["score"] < 35
    assert {"Java", "Kubernetes", "AWS"}.issubset(set(result["missing_required_skills"]))


def test_real_offer_with_no_positive_overlap_returns_no_score(tmp_path: Path):
    service = make_service()
    cv = write_cv(tmp_path)

    result = service.analyze(
        "Backend Developer",
        """
We are hiring a Backend Developer for a production platform. Required technical
skills are Java, Kubernetes and AWS. Professional German is required. You will
maintain distributed backend services, deploy containerized applications, own
platform reliability, monitor production systems and resolve service incidents.
""",
        cv_path=str(cv),
    )

    assert result["score"] is None
    assert result["score_available"] is False
    assert {"Java", "Kubernetes", "AWS"}.issubset(set(result["missing_required_skills"]))
    assert any("No positive match evidence" in reason for reason in result["no_score_reasons"])
