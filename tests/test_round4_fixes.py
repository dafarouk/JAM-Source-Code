from __future__ import annotations

from pathlib import Path

import fitz

from services.analyzer_service import AnalyzerService
import services.analyzer_report_service as report_module
from services.analyzer_report_service import AnalyzerReportService


def test_reference_detection_lvm_and_no_reflexions_false_positive():
    service = AnalyzerService()

    assert service.extract_reference("Reference LVM33836")["value"] == "LVM33836"
    assert service.extract_reference("Nous participons aux réflexions stratégiques.") is None


def test_long_analyzer_pdf_splits_and_localizes_generated_labels(tmp_path, monkeypatch):
    service = AnalyzerReportService()
    monkeypatch.setattr(service, "_language", lambda: "fr")
    monkeypatch.setattr(report_module, "EXPORT_DIR", tmp_path)
    monkeypatch.setattr(report_module, "BRANDING_DIR", tmp_path / "missing-branding")

    description = "\n\n".join([
        "About the job",
        "Juriste droit social (F/H)",
        "Job responsibilities",
        " ".join(["Accompagner les équipes RH sur les problématiques individuelles, les contrats de travail, le contentieux et la veille juridique."] * 45),
        "Profile",
        "Vous êtes titulaire d’un Master 2 en droit social, droit du travail ou équivalent.",
        "Vous avez minimum 7 ans d’expérience sur un poste similaire.",
        "Nice to Have",
        "Pack Office et anglais.",
        "Reference LVM33836",
    ])

    analysis = {
        "score": 1,
        "score_label": "Moderate evidence",
        "confidence": 71,
        "reference": {"label": "Reference", "value": "LVM33836"},
        "score_explanation": [
            {"dimension": "Role / title alignment", "points": 0, "max_points": 20},
        ],
        "experience_match": {"required_years": 7, "cv_years": 8.5},
        "education_match": {
            "required": {"label": "Master", "fields": ["Labor / Social Law"]},
            "cv": {"label": "Master", "fields": ["Business / Analytics"]},
        },
        "salary": {},
        "matched_required_competencies": [],
        "missing_required_competencies": ["Labor law"],
        "penalty_reasons": ["The requested field of study is not evidenced by the CV education."],
        "suggestions": ["No positive match evidence was found between the job offer and the CV."],
        "matched_skill_evidence": [],
    }

    output = Path(service.export("Juriste droit social (F/H)", description, analysis))
    assert output.exists()

    doc = fitz.open(output)
    assert len(doc) >= 2
    text = "\n".join(page.get_text() for page in doc)
    doc.close()

    assert "LVM33836" in text
    assert "Preuves modérées" in text
    assert "Atouts souhaités" in text
    assert "Nice to Have" not in text


def test_analyzer_export_modal_is_above_analysis_overlay():
    root = Path(__file__).resolve().parents[1]
    css = (root / "ui" / "css" / "app.css").read_text(encoding="utf-8")
    assert ".modal-root" in css
    assert "z-index: 2600" in css


def test_data_locations_are_editable_per_category():
    root = Path(__file__).resolve().parents[1]
    batch1 = (root / "ui" / "js" / "batch1.js").read_text(encoding="utf-8")
    bridge = (root / "src" / "bridge.py").read_text(encoding="utf-8")
    config = (root / "src" / "config.py").read_text(encoding="utf-8")

    assert "data-edit-location" in batch1
    assert "edit_data_location" in batch1
    assert "def edit_data_location" in bridge
    assert "save_data_location_override" in bridge
    assert "DATA_LOCATIONS_PATH" in config
    assert "database" in config and "exports" in config and "logs" in config
