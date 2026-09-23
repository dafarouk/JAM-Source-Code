from __future__ import annotations

from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image as RLImage,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from config import BRANDING_DIR, EXPORT_DIR
from services.settings_service import SettingsService


NAVY = "111827"
GOLD = "BC965D"
GOLD_LIGHT = "D0AA70"
GRAPHITE = "374151"
MUTED = "6B7280"
SOFT_GOLD = "F6EFE3"
SOFT_ICE = "F7F9FC"
WHITE = "FFFFFF"
LINE = "D9DEE7"


class AnalyzerReportService:
    def __init__(self) -> None:
        self.settings = SettingsService()

    def _language(self) -> str:
        value = (self.settings.get("language", "en") or "en").strip().lower()
        return value if value in {"en", "fr"} else "en"

    def _filename(self) -> Path:
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return EXPORT_DIR / f"JAM_Analyzer_{stamp}.pdf"

    @staticmethod
    def _safe(value) -> str:
        return escape(str(value or "—"))

    @staticmethod
    def _paragraph_text(value: str) -> str:
        text = escape(str(value or "—"))
        return text.replace("\n", "<br/>")

    @staticmethod
    def _dimension_label(value: str, fr: bool) -> str:
        if not fr:
            return value
        mapping = {
            "Role / title alignment": "Alignement poste / intitulé",
            "Required skills & tools": "Compétences et outils requis",
            "Critical domain evidence": "Preuves métier essentielles",
            "Semantic requirement evidence": "Preuves sémantiques des exigences",
            "Relevant experience": "Expérience pertinente",
            "Responsibilities / domain": "Responsabilités / domaine",
            "Education": "Formation",
            "Languages": "Langues",
        }
        return mapping.get(value, value)

    @staticmethod
    def _fr_text(value: str) -> str:
        """Translate analyzer-generated labels/messages used in French reports.

        The original job description remains user content, except for common
        standalone section headings (handled separately). This function is for
        JAM-generated analysis text only.
        """
        raw = str(value or "")
        direct = {
            "Very strong evidence": "Preuves très fortes",
            "Strong evidence": "Preuves fortes",
            "Moderate evidence": "Preuves modérées",
            "Partial evidence": "Preuves partielles",
            "Low evidence": "Preuves faibles",
            "No reliable score": "Aucun score fiable",
            "Not specified": "Non spécifié",
            "Not found": "Non trouvé",
            "Unclear": "Incertain",
            "Not reliably detected": "Non détecté de manière fiable",
            "The target role is not strongly reflected in the CV headline/job-title evidence. If accurate, align the profile/headline with the target role rather than inventing experience.":
                "Le poste ciblé n’est pas clairement reflété dans le titre ou le profil du CV. Si cela correspond réellement à votre expérience, alignez le profil avec le poste ciblé sans inventer d’expérience.",
            "Core profession-specific requirements from the job description are not evidenced in the CV.":
                "Les exigences essentielles propres au métier ne sont pas démontrées dans le CV.",
            "The target profession and its core domain evidence are both absent from the CV.":
                "Le métier ciblé et ses principales preuves métier sont absents du CV.",
            "Most profession-specific requirements are not evidenced in the CV.":
                "La plupart des exigences spécifiques au métier ne sont pas démontrées dans le CV.",
            "Several explicitly required skills are not clearly evidenced in the CV.":
                "Plusieurs compétences explicitement requises ne sont pas clairement démontrées dans le CV.",
            "The requested field of study is not evidenced by the CV education.":
                "Le domaine d’études demandé n’est pas démontré par la formation du CV.",
            "The target role family is not represented in the CV.":
                "La famille de métier ciblée n’est pas représentée dans le CV.",
            "The job title/role has weak alignment with the CV history.":
                "L’intitulé ou le rôle ciblé correspond peu à l’historique du CV.",
            "Several profession-specific requirements are missing from the CV.":
                "Plusieurs exigences spécifiques au métier sont absentes du CV.",
            "Detected experience is far below the stated requirement.":
                "L’expérience détectée est très inférieure à l’exigence annoncée.",
            "Detected experience is below the stated requirement.":
                "L’expérience détectée est inférieure à l’exigence annoncée.",
            "CV extraction confidence is limited. Check that the PDF/DOCX contains selectable text and that dates, skills and languages are written explicitly.":
                "La confiance d’extraction du CV est limitée. Vérifiez que le PDF/DOCX contient du texte sélectionnable et que les dates, compétences et langues sont indiquées explicitement.",
            "The detected requirements are well represented. Review each claim against your real experience before tailoring the CV.":
                "Les exigences détectées sont bien représentées. Vérifiez chaque élément par rapport à votre expérience réelle avant d’adapter le CV.",
            "Fewer than two reliable comparison dimensions were detected.":
                "Moins de deux dimensions de comparaison fiables ont été détectées.",
            "No explicitly required skill was found in the CV.":
                "Aucune compétence explicitement requise n’a été trouvée dans le CV.",
            "Less than half of the explicitly required skills were found.":
                "Moins de la moitié des compétences explicitement requises ont été trouvées.",
            "Detected experience is well below the stated requirement.":
                "L’expérience détectée est nettement inférieure à l’exigence annoncée.",
            "No positive match evidence was found between the job offer and the CV.":
                "Aucune preuve positive de correspondance n’a été trouvée entre l’offre et le CV.",
            "The evidence confidence is too low for a meaningful percentage score.":
                "La confiance des preuves est trop faible pour produire un pourcentage pertinent.",
        }
        if raw in direct:
            return direct[raw]

        replacements = (
            ("Required tools/skills not clearly found in the CV:", "Outils/compétences requis non clairement trouvés dans le CV :"),
            ("Job skills not clearly found in the CV:", "Compétences de l’offre non clairement trouvées dans le CV :"),
            ("Requested languages not clearly found in the CV:", "Langues demandées non clairement trouvées dans le CV :"),
            ("Required language not found:", "Langue requise non trouvée :"),
            ("Profession-specific job requirements not clearly found in the CV:", "Exigences spécifiques au métier non clairement trouvées dans le CV :"),
            ("Responsibilities/domain concepts not clearly evidenced in the CV:", "Responsabilités/concepts métier non clairement démontrés dans le CV :"),
            ("Education requirement detected:", "Exigence de formation détectée :"),
            ("Local semantic matching found no strong CV evidence for required statements such as:", "La correspondance sémantique locale n’a trouvé aucune preuve forte dans le CV pour des exigences telles que :"),
            ("Only add them if they are genuinely part of your experience.", "Ajoutez-les uniquement s’ils font réellement partie de votre expérience."),
            ("required field:", "domaine requis :"),
            ("CV field evidence:", "domaine détecté dans le CV :"),
        )
        translated = raw
        for source, target in replacements:
            translated = translated.replace(source, target)
        return translated

    @staticmethod
    def _localized_description(value: str, fr: bool) -> str:
        """Keep the user's JD intact, while localising common section headings."""
        if not fr:
            return str(value or "—")

        heading_map = {
            "about the job": "À propos du poste",
            "about the role": "À propos du poste",
            "job responsibilities": "Responsabilités du poste",
            "responsibilities": "Responsabilités",
            "requirements": "Exigences",
            "qualifications": "Qualifications",
            "profile": "Profil",
            "about you": "À propos de vous",
            "must have": "Compétences indispensables",
            "must-have": "Compétences indispensables",
            "nice to have": "Atouts souhaités",
            "nice-to-have": "Atouts souhaités",
            "preferred qualifications": "Qualifications souhaitées",
            "education": "Formation",
            "experience": "Expérience",
        }

        output = []
        for line in str(value or "—").splitlines():
            stripped = line.strip()
            has_colon = stripped.endswith(":")
            lookup = stripped[:-1].strip().lower() if has_colon else stripped.lower()
            translated = heading_map.get(lookup)
            if translated:
                prefix = line[: len(line) - len(line.lstrip())]
                output.append(prefix + translated + (" :" if has_colon else ""))
            else:
                output.append(line)
        return "\n".join(output)

    def export(self, job_title: str, description: str, analysis: dict) -> str:
        if not isinstance(analysis, dict) or not analysis:
            raise ValueError("Analyze a role before exporting the Analyzer PDF.")

        path = self._filename()
        fr = self._language() == "fr"

        doc = SimpleDocTemplate(
            str(path),
            pagesize=A4,
            leftMargin=16 * mm,
            rightMargin=16 * mm,
            topMargin=12 * mm,
            bottomMargin=14 * mm,
            title=(
                "JAM — Rapport d'analyse d'offre"
                if fr
                else "JAM — Job Analyzer Report"
            ),
            author="JAM - By Farouk",
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "JAMAnalyzerTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            textColor=colors.HexColor(f"#{NAVY}"),
            alignment=TA_CENTER,
            leading=24,
            spaceAfter=2 * mm,
        )
        by_style = ParagraphStyle(
            "JAMAnalyzerBy",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=colors.HexColor(f"#{GOLD}"),
            alignment=TA_CENTER,
            leading=10,
        )
        section_style = ParagraphStyle(
            "JAMAnalyzerSection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=colors.HexColor(f"#{NAVY}"),
            leading=14,
            spaceAfter=2 * mm,
            spaceBefore=1 * mm,
        )
        body_style = ParagraphStyle(
            "JAMAnalyzerBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.4,
            textColor=colors.HexColor(f"#{GRAPHITE}"),
            leading=11.5,
            alignment=TA_LEFT,
        )
        description_style = ParagraphStyle(
            "JAMAnalyzerDescription",
            parent=body_style,
            backColor=colors.HexColor(f"#{SOFT_ICE}"),
            borderColor=colors.HexColor(f"#{LINE}"),
            borderWidth=0.5,
            borderPadding=8,
            leading=11.5,
            spaceAfter=2 * mm,
        )
        small_style = ParagraphStyle(
            "JAMAnalyzerSmall",
            parent=body_style,
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor(f"#{MUTED}"),
        )
        score_style = ParagraphStyle(
            "JAMAnalyzerScore",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=30,
            leading=34,
            textColor=colors.HexColor(f"#{GOLD}"),
            alignment=TA_CENTER,
        )

        story = []

        logo_path = BRANDING_DIR / "jam_logo.png"
        if logo_path.exists():
            try:
                with PILImage.open(logo_path) as image:
                    pixel_width, pixel_height = image.size
                # Branding is intentionally prominent. Preserve aspect ratio.
                target_width = 96 * mm
                aspect = (pixel_height / pixel_width) if pixel_width else 0.4
                target_height = target_width * aspect
                max_height = 48 * mm
                if target_height > max_height:
                    target_height = max_height
                    target_width = target_height / max(aspect, 0.01)
                logo = RLImage(
                    str(logo_path),
                    width=target_width,
                    height=target_height,
                )
                logo.hAlign = "CENTER"
                story.append(logo)
                story.append(Spacer(1, 1.5 * mm))
            except Exception:
                pass

        story.append(Paragraph("JAM — Job Application Manager", title_style))
        story.append(Paragraph("MADE BY FAROUK", by_style))
        story.append(Spacer(1, 5 * mm))

        report_title = "Rapport du Job Analyzer" if fr else "Job Analyzer Report"
        story.append(Paragraph(report_title, section_style))
        story.append(Paragraph(
            (
                f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
                if fr
                else f"Generated {datetime.now().strftime('%d %b %Y at %H:%M')}"
            ),
            small_style,
        ))
        story.append(Spacer(1, 3 * mm))

        ref = analysis.get("reference") or {}
        reference_value = ref.get("value") if isinstance(ref, dict) else None
        input_rows = [
            [
                Paragraph("Titre saisi" if fr else "Title entered", body_style),
                Paragraph(self._safe(job_title), body_style),
            ],
        ]
        if reference_value:
            input_rows.append([
                Paragraph("Référence détectée" if fr else "Detected reference", body_style),
                Paragraph(self._safe(reference_value), body_style),
            ])

        input_table = Table(input_rows, colWidths=[38 * mm, 134 * mm])
        input_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor(f"#{SOFT_GOLD}")),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor(f"#{NAVY}")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor(f"#{LINE}")),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(input_table)
        story.append(Spacer(1, 4 * mm))

        story.append(Paragraph("Description de l'offre" if fr else "Job description", section_style))
        # Do NOT put the complete job description inside a one-cell Table.
        # ReportLab cannot split a very tall table row across pages, which caused
        # long JDs (such as the Louis Vuitton legal offer) to fail on page 2.
        localized_description = self._localized_description(description, fr)
        story.append(Paragraph(self._paragraph_text(localized_description), description_style))
        story.append(Spacer(1, 5 * mm))

        score = analysis.get("score")
        score_text = "NO SCORE" if score is None else f"{score}%"
        score_label = analysis.get("score_label") or "—"
        if fr:
            score_label = self._fr_text(score_label)
        confidence = analysis.get("confidence") or 0

        score_box = Table(
            [[
                Paragraph(score_text, score_style),
                Paragraph(
                    f"<b>{self._safe(score_label)}</b><br/>"
                    + ("Confiance des preuves" if fr else "Evidence confidence")
                    + f": <b>{confidence}%</b>",
                    body_style,
                ),
            ]],
            colWidths=[44 * mm, 128 * mm],
        )
        score_box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(f"#{SOFT_GOLD}")),
            ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor(f"#{GOLD}")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(score_box)
        story.append(Spacer(1, 5 * mm))

        story.append(Paragraph("Détail du score" if fr else "Score breakdown", section_style))
        breakdown_rows = [[
            Paragraph("Critère" if fr else "Dimension", body_style),
            Paragraph("Points", body_style),
            Paragraph("Maximum", body_style),
        ]]
        for item in analysis.get("score_explanation") or []:
            breakdown_rows.append([
                Paragraph(self._safe(self._dimension_label(item.get("dimension") or "", fr)), body_style),
                Paragraph(self._safe(item.get("points")), body_style),
                Paragraph(self._safe(item.get("max_points")), body_style),
            ])
        breakdown = Table(breakdown_rows, colWidths=[112 * mm, 30 * mm, 30 * mm], repeatRows=1)
        breakdown.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(f"#{NAVY}")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor(f"#{LINE}")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(f"#{SOFT_ICE}")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(breakdown)
        story.append(Spacer(1, 5 * mm))

        semantic = analysis.get("semantic_match") or {}
        semantic_evidence = list(semantic.get("evidence") or [])
        classifier = semantic.get("role_classifier") or {}
        if semantic.get("applicable") or classifier.get("available"):
            story.append(Paragraph(
                "Preuves ML locales" if fr else "Local ML requirement evidence",
                section_style,
            ))

            coverage = semantic.get("coverage", 0)
            predicted_family = classifier.get("predicted_family") or ("Non détecté" if fr else "Not detected")
            model_name = semantic.get("model") or "—"
            summary_rows = [
                [
                    Paragraph("Couverture des exigences" if fr else "Requirement coverage", body_style),
                    Paragraph(self._safe(f"{coverage}%"), body_style),
                ],
                [
                    Paragraph("Famille de métier prédite" if fr else "Predicted job family", body_style),
                    Paragraph(self._safe(predicted_family), body_style),
                ],
                [
                    Paragraph("Moteur local" if fr else "Local engine", body_style),
                    Paragraph(self._safe(model_name), body_style),
                ],
            ]
            semantic_summary = Table(summary_rows, colWidths=[48 * mm, 124 * mm])
            semantic_summary.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor(f"#{SOFT_GOLD}")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor(f"#{LINE}")),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(semantic_summary)
            story.append(Spacer(1, 3 * mm))

            status_fr = {
                "strong": "forte",
                "partial": "partielle",
                "weak": "faible",
                "missing": "absente",
            }
            for item in semantic_evidence[:12]:
                status = str(item.get("status") or "missing")
                status_text = status_fr.get(status, status) if fr else status.title()
                similarity = item.get("similarity_pct", 0)
                story.append(KeepTogether([
                    Paragraph(
                        f"<b>{self._safe(item.get('requirement'))}</b> "
                        f"<font color='#{GOLD}'>[{self._safe(status_text)} · {self._safe(similarity)}%]</font>",
                        body_style,
                    ),
                    Paragraph(
                        ("Meilleure preuve CV : " if fr else "Best CV evidence: ")
                        + self._safe(item.get("cv_evidence") or "—"),
                        small_style,
                    ),
                    Spacer(1, 1.5 * mm),
                ]))

            story.append(Paragraph(
                "Analyse locale : aucun texte du CV ou de l’offre n’est envoyé vers un service cloud."
                if fr
                else "Local analysis: no CV or job-description text is sent to a cloud service.",
                small_style,
            ))
            story.append(Spacer(1, 5 * mm))

        exp = analysis.get("experience_match") or {}
        education = analysis.get("education_match") or {}
        salary = analysis.get("salary") or {}

        required_fields = (education.get("required") or {}).get("fields") or []
        cv_fields = (education.get("cv") or {}).get("fields") or []
        if fr:
            education_text = (
                f"Niveau requis : {(education.get('required') or {}).get('label', '—')}<br/>"
                f"Domaine requis : {', '.join(required_fields) if required_fields else 'Non spécifié'}<br/>"
                f"Niveau du CV : {(education.get('cv') or {}).get('label', '—')}<br/>"
                f"Domaine détecté dans le CV : {', '.join(cv_fields) if cv_fields else 'Non trouvé'}"
            )
            experience_text = (
                f"Exigence de l’offre : {exp.get('required_years') if exp.get('required_years') is not None else 'Non spécifié'} an(s)<br/>"
                f"Estimation chronologique du CV : {exp.get('cv_years') if exp.get('cv_years') is not None else 'Incertain'} an(s)"
            )
        else:
            education_text = (
                f"Required level: {(education.get('required') or {}).get('label', '—')}<br/>"
                f"Required field: {', '.join(required_fields) if required_fields else 'Not specified'}<br/>"
                f"CV level: {(education.get('cv') or {}).get('label', '—')}<br/>"
                f"CV field evidence: {', '.join(cv_fields) if cv_fields else 'Not found'}"
            )
            experience_text = (
                f"Job requirement: {exp.get('required_years') if exp.get('required_years') is not None else 'Not specified'} year(s)<br/>"
                f"CV timeline estimate: {exp.get('cv_years') if exp.get('cv_years') is not None else 'Unclear'} year(s)"
            )
        if salary:
            salary_text = (
                f"{salary.get('min', '—')}"
                + (f"–{salary.get('max')}" if salary.get('max') != salary.get('min') else "")
                + f" {salary.get('currency') or ''} {salary.get('period') or ''}"
            )
        else:
            salary_text = "Non détecté de manière fiable" if fr else "Not reliably detected"

        detail_rows = [
            [Paragraph("Expérience" if fr else "Experience", body_style), Paragraph(experience_text, body_style)],
            [Paragraph("Formation" if fr else "Education", body_style), Paragraph(education_text, body_style)],
            [Paragraph("Salaire" if fr else "Salary", body_style), Paragraph(self._safe(salary_text), body_style)],
        ]
        details = Table(detail_rows, colWidths=[38 * mm, 134 * mm])
        details.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor(f"#{SOFT_GOLD}")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor(f"#{LINE}")),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(details)
        story.append(Spacer(1, 5 * mm))

        def bullet_section(title_en: str, title_fr: str, values: list[str]) -> None:
            if not values:
                return
            story.append(Paragraph(title_fr if fr else title_en, section_style))
            for value in values:
                display_value = self._fr_text(value) if fr else value
                story.append(Paragraph("• " + self._safe(display_value), body_style))
            story.append(Spacer(1, 2 * mm))

        bullet_section(
            "Matched competencies",
            "Compétences correspondantes",
            list(analysis.get("matched_required_competencies") or analysis.get("matched_skills") or []),
        )
        bullet_section(
            "Missing / not clearly evidenced",
            "Manquant / non clairement démontré",
            list(analysis.get("missing_required_competencies") or analysis.get("missing_skills") or []),
        )
        bullet_section(
            "Score penalties / hard requirements",
            "Pénalités / exigences fortes",
            list(analysis.get("penalty_reasons") or []),
        )
        bullet_section(
            "JAM notes — what to review",
            "Notes JAM — points à vérifier",
            list(analysis.get("suggestions") or []),
        )

        evidence = list(analysis.get("matched_skill_evidence") or [])
        if evidence:
            story.append(Paragraph("CV evidence used" if not fr else "Preuves CV utilisées", section_style))
            for item in evidence[:12]:
                story.append(KeepTogether([
                    Paragraph(f"<b>{self._safe(item.get('requirement'))}</b>", body_style),
                    Paragraph(
                        ("Job: " if not fr else "Offre : ") + self._safe(item.get("job_evidence")),
                        small_style,
                    ),
                    Paragraph(
                        ("CV: " if not fr else "CV : ") + self._safe(item.get("cv_evidence")),
                        small_style,
                    ),
                    Spacer(1, 1.5 * mm),
                ]))

        story.append(Spacer(1, 5 * mm))
        disclaimer = (
            "JAM's Job Analyzer can make mistakes. This report is intentionally detailed so you can review the result yourself or verify it with another tool or AI model. A second check never hurts :)"
            if not fr
            else "Le Job Analyzer de JAM peut faire des erreurs. Ce rapport est volontairement détaillé afin que vous puissiez vérifier le résultat vous-même ou avec un autre outil ou modèle d'IA. Une deuxième vérification ne fait jamais de mal :)"
        )
        disclaimer_box = Table(
            [[Paragraph(("<b>Note de vérification</b><br/>" if fr else "<b>Verification note</b><br/>") + escape(disclaimer), small_style)]],
            colWidths=[172 * mm],
        )
        disclaimer_box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(f"#{SOFT_GOLD}")),
            ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor(f"#{GOLD}")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        story.append(disclaimer_box)

        doc.build(story)
        return str(path)
