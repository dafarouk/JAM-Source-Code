from __future__ import annotations

import argparse
import ctypes
import os
import re
import sys
import threading
import tkinter as tk
from ctypes import wintypes
from datetime import datetime
from tkinter import messagebox, ttk

from PIL import Image, ImageTk

from config import (
    BRANDING_DIR,
    RECOVERY_DIR,
    CAPTURE_WINDOW_HEIGHT,
    CAPTURE_WINDOW_TITLE,
    CAPTURE_WINDOW_WIDTH,
    ensure_runtime_dirs,
)
from database import init_database
from repositories.application_repository import ApplicationRepository
from services.settings_service import SettingsService
from services.recovery_service import RecoveryService


# ============================================================
# VISUALS
# ============================================================

BG = "#0C121C"
PANEL = "#111A27"
FIELD = "#121B28"
FIELD_HOVER = "#172230"
TEXT = "#F5F7FA"
MUTED = "#9BA5B4"
GOLD = "#BC965D"
GOLD_LIGHT = "#D0AA70"
GREEN = "#10B981"
LINE = "#293343"
DANGER = "#EF4444"

STATUSES = (
    "Saved",
    "To Review",
    "Applied",
    "Interviewing",
    "Offer",
    "Accepted",
    "Rejected",
    "Withdrawn",
    "Archived",
)

STATUS_COLORS = {
    "Saved": "#A7B0BE",
    "To Review": "#B88CFF",
    "Applied": "#F4C35A",
    "Interviewing": "#55B8FF",
    "Offer": "#FF9E57",
    "Accepted": "#39D98A",
    "Rejected": "#FF6B6B",
    "Withdrawn": "#8D96A5",
    "Archived": "#6F7784",
}

# Balanced for Tunisia + France + international use.
SOURCES = (
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
    "Company careers page",

    # MENA / wider region
    "Bayt",
    "GulfTalent",
    "NaukriGulf",

    # Other discovery channels
    "Recruiter / Agency",
    "Referral",
    "School / Alumni",
    "Other",
)

FEATURED_SOURCES = (
    "LinkedIn",
    "Keejob",
    "Tanitjobs",
    "Indeed",
    "Welcome to the Jungle",
    "JobTeaser",
    "Glassdoor",
    "Bayt",
)

CORNER_META = {
    "top-left": ("↖", 0, 0),
    "top-right": ("↗", 0, 1),
    "bottom-left": ("↙", 1, 0),
    "bottom-right": ("↘", 1, 1),
}



CAPTURE_FR = {
    "JAM - Quick Capture": "JAM - Capture rapide",
    "QUICK CAPTURE": "CAPTURE RAPIDE",
    "Return to JAM": "Retour à JAM",
    "GUIDED TOUR": "TUTORIEL GUIDÉ",
    "This is Capture Mode": "Voici le mode Capture",
    "↗  Return to JAM to continue": "↗  Retour à JAM pour continuer",
    "● PINNED": "● ÉPINGLÉ",
    "Where should Capture Mode appear?": "Où le mode Capture doit-il apparaître ?",
    "Save Application": "Enregistrer",
    "Analyze": "Analyser",
    "Company": "Entreprise",
    "Job title": "Poste",
    "Location": "Localisation",
    "Work mode": "Mode de travail",
    "Onsite": "Sur site",
    "Hybrid": "Hybride",
    "Remote": "Télétravail",
    "Status": "Statut",
    "Job URL": "URL de l’offre",
    "Description": "Description",
    "Source": "Source",
    "Rating": "Note",
    "Clear": "Effacer",
    "Notes": "Notes",
    "Saved": "Enregistrée",
    "To Review": "À examiner",
    "Applied": "Candidature envoyée",
    "Interviewing": "Entretien",
    "Offer": "Offre reçue",
    "Accepted": "Acceptée",
    "Rejected": "Refusée",
    "Withdrawn": "Retirée",
    "Archived": "Archivée",
    "Add at least a company or job title.": "Ajoutez au moins une entreprise ou un poste.",
    "Application saved ✓": "Candidature enregistrée ✓",
    "Add a job title or description first.": "Ajoutez d’abord un poste ou une description.",
    "JAM Analyzer": "Analyseur JAM",
    "JAM - Analyzing": "JAM - Analyse en cours",
    "JAM MATCH ENGINE v3": "MOTEUR DE CORRESPONDANCE JAM v3",
    "Analyzing job offer + CV": "Analyse de l’offre + du CV",
    "Validating job offer": "Validation de l’offre",
    "Local analysis. No cloud AI call.": "Analyse locale. Aucun appel à une IA cloud.",
    "JAM - CV Match": "JAM - Correspondance CV",
    "CV MATCH RESULT": "RÉSULTAT DE CORRESPONDANCE CV",
    "NO SCORE": "AUCUN SCORE",
    "WHY THERE IS NO SCORE": "POURQUOI IL N’Y A PAS DE SCORE",
    "JAM does not have enough reliable evidence to calculate a percentage.":
        "JAM ne dispose pas de suffisamment de preuves fiables pour calculer un pourcentage.",
    "MATCHED SKILLS / TOOLS": "COMPÉTENCES / OUTILS CORRESPONDANTS",
    "MISSING / NOT FOUND": "MANQUANT / NON TROUVÉ",
    "MATCHED RESPONSIBILITIES / DOMAIN": "RESPONSABILITÉS / DOMAINE CORRESPONDANTS",
    "EXPERIENCE": "EXPÉRIENCE",
    "LANGUAGES": "LANGUES",
    "Matched": "Correspondances",
    "Missing": "Manquantes",
    "WHAT TO REVIEW": "POINTS À REVOIR",
    "ENGINE": "MOTEUR",
    "Done": "Terminé",
    "None detected": "Aucun élément détecté",
    "No major changes suggested.": "Aucune modification majeure suggérée.",
    "JAM Match Engine": "Moteur de correspondance JAM",
    "No reliable score": "Aucun score fiable",
    "Very strong evidence": "Preuves très fortes",
    "Strong evidence": "Preuves fortes",
    "Moderate evidence": "Preuves modérées",
    "Partial evidence": "Preuves partielles",
    "Low evidence": "Preuves faibles",
    "Analysis complete": "Analyse terminée",
    "Extracting requirements": "Extraction des exigences",
    "Reading CV": "Lecture du CV",
    "Building CV profile": "Construction du profil CV",
    "Comparing evidence": "Comparaison des preuves",
    "Calculating evidence-based score": "Calcul du score basé sur les preuves",
    "Company careers page": "Page carrières de l’entreprise",
    "Recruiter / Agency": "Recruteur / Agence",
    "Referral": "Cooptation",
    "School / Alumni": "École / Alumni",
    "Other": "Autre",
    "The selected CV file no longer exists.": "Le fichier CV sélectionné n’existe plus.",
    "Add a job title or description before analyzing.": "Ajoutez un poste ou une description avant de lancer l’analyse.",
    "Add a CV first from JAM settings or the analyzer.": "Ajoutez d’abord un CV depuis les paramètres JAM ou l’analyseur.",
    "JAM could not extract readable text from the selected CV.": "JAM n’a pas pu extraire de texte lisible du CV sélectionné.",
}

CAPTURE_FR_REGEX = (
    (
        re.compile(r"^Evidence confidence:\s*(\d+)%$"),
        lambda m: f"Confiance des preuves : {m.group(1)}%",
    ),
    (
        re.compile(r"^Job asks for about\s*(.+)\+\s*years\.\s*JAM detected about\s*(.+)\s*years in the CV\.$"),
        lambda m: f"L’offre demande environ {m.group(1)}+ ans. JAM a détecté environ {m.group(2)} ans dans le CV.",
    ),
    (
        re.compile(r"^Job asks for about\s*(.+)\+\s*years\.\s*JAM could not reliably calculate CV experience years\.$"),
        lambda m: f"L’offre demande environ {m.group(1)}+ ans. JAM n’a pas pu calculer de manière fiable les années d’expérience du CV.",
    ),
    (
        re.compile(r"^Matched:\s*(.+)$"),
        lambda m: f"Correspondances : {m.group(1)}",
    ),
    (
        re.compile(r"^Missing:\s*(.+)$"),
        lambda m: f"Manquantes : {m.group(1)}",
    ),
    (
        re.compile(r"^Local analysis time:\s*(.+)$"),
        lambda m: f"Temps d’analyse locale : {m.group(1)}",
    ),
    (
        re.compile(r"^Required tools/skills not clearly found in the CV:\s*(.+)\.\s*Only add them if they are genuinely part of your experience\.$"),
        lambda m: f"Outils/compétences requis non clairement trouvés dans le CV : {m.group(1)}. Ajoutez-les uniquement s’ils font réellement partie de votre expérience.",
    ),
    (
        re.compile(r"^Job skills not clearly found in the CV:\s*(.+)\.$"),
        lambda m: f"Compétences de l’offre non clairement trouvées dans le CV : {m.group(1)}.",
    ),
    (
        re.compile(r"^Requested languages not clearly found in the CV:\s*(.+)\.$"),
        lambda m: f"Langues demandées non clairement trouvées dans le CV : {m.group(1)}.",
    ),
    (
        re.compile(r"^Responsibilities/domain concepts not clearly evidenced in the CV:\s*(.+)\.$"),
        lambda m: f"Responsabilités/concepts métier non clairement démontrés dans le CV : {m.group(1)}.",
    ),
)

# ============================================================
# WINDOWS / DPI
# ============================================================


def enable_dpi_awareness() -> None:
    if os.name != "nt":
        return

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass

    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class POINT(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_long),
        ("y", ctypes.c_long),
    ]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
    ]


def parse_args():
    """
    The legacy monitor bounds are kept for compatibility with bridge.py.
    The Capture process now determines its own real monitor work area, so
    corner movement no longer depends on those values.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--corner", default="top-right")
    parser.add_argument("--left", type=int, default=0)
    parser.add_argument("--top", type=int, default=0)
    parser.add_argument("--right", type=int, default=1920)
    parser.add_argument("--bottom", type=int, default=1080)
    parser.add_argument("--tutorial", action="store_true")
    return parser.parse_args()


# ============================================================
# SOURCE MATCHING
# ============================================================


def source_matches(query: str) -> list[str]:
    """
    Empty query -> balanced featured sources.
    Typed query -> prefix only, exactly as requested.

    Examples:
      "L" -> LinkedIn, LesJeudis, L'Etudiant, Lever
      "W" -> Welcome to the Jungle, Wellfound, We Work Remotely, Workday
    """
    query = str(query or "").strip().casefold()

    if not query:
        return list(FEATURED_SOURCES)

    return [
        source
        for source in SOURCES
        if source.casefold().startswith(query)
    ][:8]


# ============================================================
# CAPTURE APP
# ============================================================


class CaptureApp:
    def __init__(self, args) -> None:
        self.args = args
        self.repo = ApplicationRepository()
        self.settings = SettingsService()
        # Keep Capture lightweight. The Analyzer imports sentence-transformers
        # and PyTorch, so create it only after the user clicks Analyze.
        self.analyzer = None
        self._analyzer_lock = threading.Lock()
        self.recovery = RecoveryService()
        self.language = self.settings.get("language", "en").strip().lower()
        if self.language not in {"en", "fr"}:
            self.language = "en"

        self.draft_started_at: str | None = None
        self.rating = 0
        self.logo_photo = None
        self._scroll_window_id = None
        self._status_open = False
        self._source_open = False
        self._source_match_values: list[str] = []
        self._suppress_source_focus_once = False
        self._scroll_velocity = 0.0
        self._scroll_animation_id = None
        self._scroll_target_px: float | None = None
        self._native_icon_handles: list[int] = []
        self._initial_work_area: tuple[int, int, int, int] | None = None
        self._loading_recovery = False
        self._geometry_ready = False
        self._geometry_save_after_id = None
        self._tutorial_hint = None

        self._configure_windows_app_identity()

        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title(self._t("JAM - Quick Capture"))
        self.root.configure(bg=BG)
        self.root.resizable(True, True)
        self.root.minsize(330, 360)
        self.root.attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self._configure_icon()
        self._configure_styles()
        self._build_ui()
        self._restore_capture_draft()

        # Determine the monitor from the cursor position left behind by the
        # user's click on the main JAM Capture Mode button.
        self._initial_work_area = self._work_area_from_cursor()

        # Restore the user's exact Capture position/size when enabled.
        restored_geometry = self._apply_saved_geometry()
        if not restored_geometry:
            self.root.geometry(
                f"{CAPTURE_WINDOW_WIDTH}x{CAPTURE_WINDOW_HEIGHT}"
            )
        self.root.update_idletasks()

        # Avoid any top-left flash while Windows creates the real decorated
        # toplevel HWND.
        try:
            self.root.attributes("-alpha", 0.0)
        except Exception:
            pass

        self.root.deiconify()
        self.root.update_idletasks()
        self.root.update()
        self._apply_native_taskbar_icon()

        if not restored_geometry:
            self.position_window(args.corner, use_initial_monitor=True)

        try:
            self.root.attributes("-alpha", 1.0)
        except Exception:
            pass

        self.root.lift()
        self.root.attributes("-topmost", True)

        self._geometry_ready = True
        self.root.bind("<Configure>", self._on_root_configure, add="+")
        self.root.after(200, self._save_geometry_now)

        self.root.after(
            120,
            lambda: self.root.attributes("-topmost", True),
        )

        if bool(getattr(self.args, "tutorial", False)):
            self.root.after(350, self._show_tutorial_hint)

    def _t(self, text: str) -> str:
        if self.language != "fr":
            return text

        if text in CAPTURE_FR:
            return CAPTURE_FR[text]

        for pattern, replacer in CAPTURE_FR_REGEX:
            match = pattern.match(str(text))
            if match:
                return replacer(match)

        return text

    def _status_label(self, status: str) -> str:
        return self._t(status)

    def _source_label(self, source: str) -> str:
        return self._t(source)

    def _work_mode_label(self, value: str) -> str:
        return self._t(value) if value else ""

    def _canonical_work_mode(self, value: str) -> str:
        value = (value or "").strip()
        if not value:
            return ""

        for canonical in ("Onsite", "Hybrid", "Remote"):
            if value == canonical or value == self._t(canonical):
                return canonical

        return ""

    # ======================================================
    # NATIVE WINDOW / POSITIONING
    # ======================================================

    def _remember_geometry_enabled(self) -> bool:
        value = self.settings.get(
            "capture_remember_geometry",
            "1",
        ).strip().lower()
        return value not in {
            "0",
            "false",
            "no",
            "off",
        }

    def _saved_geometry(self) -> tuple[int, int, int, int] | None:
        if not self._remember_geometry_enabled():
            return None
        try:
            x = int(self.settings.get("capture_x", ""))
            y = int(self.settings.get("capture_y", ""))
            width = int(self.settings.get("capture_width", ""))
            height = int(self.settings.get("capture_height", ""))
        except Exception:
            return None
        if width < 330 or height < 360:
            return None
        return (x, y, width, height)

    def _apply_saved_geometry(self) -> bool:
        geometry = self._saved_geometry()
        if not geometry:
            return False

        x, y, width, height = geometry
        left, top, right, bottom = (
            self._initial_work_area
            or self._work_area_from_cursor()
        )
        margin = 8
        max_width = max(330, right - left - (margin * 2))
        max_height = max(360, bottom - top - (margin * 2))
        width = max(330, min(width, max_width))
        height = max(360, min(height, max_height))
        x = max(left + margin, min(x, right - width - margin))
        y = max(top + margin, min(y, bottom - height - margin))

        try:
            self.root.geometry(
                f"{width}x{height}{x:+d}{y:+d}"
            )
            return True
        except Exception:
            return False

    def _on_root_configure(self, _event=None) -> None:
        if not self._geometry_ready or not self._remember_geometry_enabled():
            return
        if self._geometry_save_after_id is not None:
            try:
                self.root.after_cancel(self._geometry_save_after_id)
            except Exception:
                pass
        self._geometry_save_after_id = self.root.after(
            260,
            self._save_geometry_now,
        )

    def _save_geometry_now(self) -> None:
        self._geometry_save_after_id = None
        if not self._geometry_ready or not self._remember_geometry_enabled():
            return
        try:
            self.root.update_idletasks()
            self.settings.set("capture_x", str(int(self.root.winfo_x())))
            self.settings.set("capture_y", str(int(self.root.winfo_y())))
            self.settings.set("capture_width", str(max(330, int(self.root.winfo_width()))))
            self.settings.set("capture_height", str(max(360, int(self.root.winfo_height()))))
        except Exception:
            pass

    def _configure_windows_app_identity(self) -> None:
        """Make Capture Mode use JAM's Windows identity instead of python.exe."""
        if sys.platform != "win32":
            return

        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "Farouk.JAM.JobApplicationManager"
            )
        except Exception:
            pass

    def _configure_icon(self) -> None:
        ico = BRANDING_DIR / "jam_runtime.ico"

        if ico.exists():
            try:
                self.root.iconbitmap(default=str(ico))
            except Exception:
                pass

    def _apply_native_taskbar_icon(self) -> None:
        """
        Tk's iconbitmap changes the window icon, but Windows can still show the
        python.exe icon on the taskbar for a separate Capture process. Set the
        native HWND icons explicitly after the decorated window exists.
        """
        if sys.platform != "win32":
            return

        ico = BRANDING_DIR / "jam_runtime.ico"
        if not ico.exists():
            return

        try:
            user32 = ctypes.windll.user32

            IMAGE_ICON = 1
            LR_LOADFROMFILE = 0x0010
            WM_SETICON = 0x0080
            ICON_SMALL = 0
            ICON_BIG = 1
            GA_ROOT = 2

            hwnd = wintypes.HWND(self.root.winfo_id())

            try:
                root_hwnd = user32.GetAncestor(hwnd, GA_ROOT)
                if root_hwnd:
                    hwnd = root_hwnd
            except Exception:
                pass

            big_icon = user32.LoadImageW(
                None,
                str(ico),
                IMAGE_ICON,
                64,
                64,
                LR_LOADFROMFILE,
            )
            small_icon = user32.LoadImageW(
                None,
                str(ico),
                IMAGE_ICON,
                32,
                32,
                LR_LOADFROMFILE,
            )

            if big_icon:
                user32.SendMessageW(
                    hwnd,
                    WM_SETICON,
                    ICON_BIG,
                    big_icon,
                )
                self._native_icon_handles.append(int(big_icon))

            if small_icon:
                user32.SendMessageW(
                    hwnd,
                    WM_SETICON,
                    ICON_SMALL,
                    small_icon,
                )
                self._native_icon_handles.append(int(small_icon))

        except Exception:
            pass

    def _user32(self):
        user32 = ctypes.windll.user32

        # Explicit pointer-sized signatures are essential on 64-bit Windows.
        # Without them GetAncestor/MonitorFromWindow can truncate handles and
        # SetWindowPos silently fails, which was the old corner-selection bug.
        user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
        user32.GetAncestor.restype = wintypes.HWND

        user32.GetWindowRect.argtypes = [
            wintypes.HWND,
            ctypes.POINTER(RECT),
        ]
        user32.GetWindowRect.restype = wintypes.BOOL

        user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
        user32.GetCursorPos.restype = wintypes.BOOL

        user32.MonitorFromPoint.argtypes = [POINT, wintypes.DWORD]
        user32.MonitorFromPoint.restype = wintypes.HANDLE

        user32.MonitorFromWindow.argtypes = [
            wintypes.HWND,
            wintypes.DWORD,
        ]
        user32.MonitorFromWindow.restype = wintypes.HANDLE

        user32.GetMonitorInfoW.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(MONITORINFO),
        ]
        user32.GetMonitorInfoW.restype = wintypes.BOOL

        user32.SetWindowPos.argtypes = [
            wintypes.HWND,
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        ]
        user32.SetWindowPos.restype = wintypes.BOOL

        return user32

    def _native_root_hwnd(self) -> int:
        if os.name != "nt":
            return 0

        try:
            user32 = self._user32()
            GA_ROOT = 2
            tk_hwnd = wintypes.HWND(int(self.root.winfo_id()))
            root_hwnd = user32.GetAncestor(tk_hwnd, GA_ROOT)
            return int(root_hwnd or tk_hwnd.value or 0)
        except Exception:
            return 0

    def _work_area_for_monitor(self, monitor) -> tuple[int, int, int, int] | None:
        if not monitor:
            return None

        try:
            info = MONITORINFO()
            info.cbSize = ctypes.sizeof(MONITORINFO)

            if not self._user32().GetMonitorInfoW(
                monitor,
                ctypes.byref(info),
            ):
                return None

            return (
                int(info.rcWork.left),
                int(info.rcWork.top),
                int(info.rcWork.right),
                int(info.rcWork.bottom),
            )
        except Exception:
            return None

    def _work_area_from_cursor(self) -> tuple[int, int, int, int]:
        if os.name == "nt":
            try:
                user32 = self._user32()
                point = POINT()

                if user32.GetCursorPos(ctypes.byref(point)):
                    MONITOR_DEFAULTTONEAREST = 2
                    monitor = user32.MonitorFromPoint(
                        point,
                        MONITOR_DEFAULTTONEAREST,
                    )
                    area = self._work_area_for_monitor(monitor)
                    if area:
                        return area
            except Exception:
                pass

        return self._fallback_work_area()

    def _current_work_area(self) -> tuple[int, int, int, int]:
        if os.name == "nt":
            try:
                hwnd = self._native_root_hwnd()

                if hwnd:
                    MONITOR_DEFAULTTONEAREST = 2
                    monitor = self._user32().MonitorFromWindow(
                        wintypes.HWND(hwnd),
                        MONITOR_DEFAULTTONEAREST,
                    )
                    area = self._work_area_for_monitor(monitor)
                    if area:
                        return area
            except Exception:
                pass

        if self._initial_work_area:
            return self._initial_work_area

        return self._fallback_work_area()

    def _fallback_work_area(self) -> tuple[int, int, int, int]:
        # Legacy values passed by bridge.py are useful as a final fallback.
        left = int(getattr(self.args, "left", 0))
        top = int(getattr(self.args, "top", 0))
        right = int(getattr(self.args, "right", 0))
        bottom = int(getattr(self.args, "bottom", 0))

        if right > left and bottom > top:
            return (left, top, right, bottom)

        return (
            0,
            0,
            int(self.root.winfo_screenwidth()),
            int(self.root.winfo_screenheight()),
        )

    def _outer_window_size(self) -> tuple[int, int]:
        if os.name == "nt":
            try:
                hwnd = self._native_root_hwnd()

                if hwnd:
                    rect = RECT()
                    if self._user32().GetWindowRect(
                        wintypes.HWND(hwnd),
                        ctypes.byref(rect),
                    ):
                        width = max(1, int(rect.right - rect.left))
                        height = max(1, int(rect.bottom - rect.top))
                        return (width, height)
            except Exception:
                pass

        return (
            max(CAPTURE_WINDOW_WIDTH, self.root.winfo_width()),
            max(CAPTURE_WINDOW_HEIGHT, self.root.winfo_height()),
        )

    def position_window(
        self,
        corner: str,
        *,
        use_initial_monitor: bool = False,
    ) -> None:
        if corner not in CORNER_META:
            corner = "top-right"

        if use_initial_monitor and self._initial_work_area:
            left, top, right, bottom = self._initial_work_area
        else:
            left, top, right, bottom = self._current_work_area()

        width, height = self._outer_window_size()
        margin = 18

        positions = {
            "top-left": (
                left + margin,
                top + margin,
            ),
            "top-right": (
                right - width - margin,
                top + margin,
            ),
            "bottom-left": (
                left + margin,
                bottom - height - margin,
            ),
            "bottom-right": (
                right - width - margin,
                bottom - height - margin,
            ),
        }

        x, y = positions[corner]

        x = max(
            left + margin,
            min(x, right - width - margin),
        )
        y = max(
            top + margin,
            min(y, bottom - height - margin),
        )

        # Tk fallback is deliberately applied first.
        # The signed format supports monitors with negative coordinates.
        try:
            client_width = max(330, int(self.root.winfo_width() or CAPTURE_WINDOW_WIDTH))
            client_height = max(360, int(self.root.winfo_height() or CAPTURE_WINDOW_HEIGHT))
            self.root.geometry(
                f"{client_width}x{client_height}"
                f"{int(x):+d}{int(y):+d}"
            )
            self.root.update_idletasks()
        except Exception:
            pass

        if os.name == "nt":
            try:
                hwnd = self._native_root_hwnd()

                if hwnd:
                    HWND_TOPMOST = wintypes.HWND(-1)
                    SWP_NOSIZE = 0x0001
                    SWP_NOACTIVATE = 0x0010
                    SWP_SHOWWINDOW = 0x0040

                    self._user32().SetWindowPos(
                        wintypes.HWND(hwnd),
                        HWND_TOPMOST,
                        int(x),
                        int(y),
                        0,
                        0,
                        SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW,
                    )
            except Exception:
                pass

        self.root.lift()
        self.root.attributes("-topmost", True)

    # ======================================================
    # STYLES / BASIC WIDGETS
    # ======================================================

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)

        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "Gold.Vertical.TScrollbar",
            troughcolor=BG,
            background=GOLD,
            bordercolor=BG,
            lightcolor=GOLD_LIGHT,
            darkcolor=GOLD,
            arrowcolor=GOLD_LIGHT,
            gripcount=0,
            width=9,
        )
        style.configure(
            "Jam.TCombobox",
            fieldbackground=FIELD,
            background=FIELD,
            foreground=TEXT,
            arrowcolor=GOLD_LIGHT,
            bordercolor=LINE,
            lightcolor=FIELD,
            darkcolor=FIELD,
            padding=5,
        )
        style.map(
            "Jam.TCombobox",
            fieldbackground=[("readonly", FIELD)],
            foreground=[("readonly", TEXT)],
            background=[("readonly", FIELD)],
            arrowcolor=[("readonly", GOLD_LIGHT)],
        )

    def _label(self, parent, text: str):
        return tk.Label(
            parent,
            text=text,
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        )

    def _entry(self, parent, variable: tk.StringVar):
        return tk.Entry(
            parent,
            textvariable=variable,
            bg=FIELD,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=LINE,
            highlightcolor=GOLD,
            font=("Segoe UI", 9),
        )

    def _section_label(self, parent, text: str):
        label = self._label(parent, text)
        label.pack(fill="x", pady=(6, 3))
        return label

    # ======================================================
    # BUILD UI
    # ======================================================

    def _build_ui(self) -> None:
        self._build_header()

        # Keep only the JAM header and action footer fixed.
        # The PINNED / position selector belongs to the scrollable content,
        # so it naturally disappears when the user scrolls down the form.
        self._build_footer()
        self._build_scroll_body()

        # Wheel scroll works anywhere over Capture Mode.
        self.root.bind_all("<MouseWheel>", self._on_mousewheel, add="+")

    def _build_header(self) -> None:
        header = tk.Frame(
            self.root,
            bg=BG,
            height=48,
        )
        header.pack(
            fill="x",
            padx=11,
            pady=(7, 2),
        )
        header.pack_propagate(False)

        logo_path = BRANDING_DIR / "jam_logo.png"

        if logo_path.exists():
            try:
                image = Image.open(logo_path).convert("RGBA")
                image.thumbnail(
                    (42, 25),
                    Image.Resampling.LANCZOS,
                )
                self.logo_photo = ImageTk.PhotoImage(image)

                tk.Label(
                    header,
                    image=self.logo_photo,
                    bg=BG,
                ).pack(
                    side="left",
                    padx=(0, 7),
                )
            except Exception:
                pass

        brand = tk.Frame(header, bg=BG)
        brand.pack(side="left", fill="y")

        tk.Label(
            brand,
            text="JAM",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        ).pack(anchor="w", pady=(4, 0))

        tk.Label(
            brand,
            text=self._t("QUICK CAPTURE"),
            bg=BG,
            fg=GOLD_LIGHT,
            font=("Segoe UI", 6, "bold"),
            anchor="w",
        ).pack(anchor="w")

        tk.Button(
            header,
            text=self._t("Return to JAM"),
            command=self.close,
            bg="#171E28",
            fg=TEXT,
            activebackground="#212A37",
            activeforeground=TEXT,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=LINE,
            font=("Segoe UI", 7, "bold"),
            cursor="hand2",
        ).pack(
            side="right",
            ipadx=7,
            ipady=4,
            pady=6,
        )

    def _build_position_panel(self) -> None:
        panel = tk.Frame(
            self.form,
            bg=BG,
        )
        panel.pack(
            fill="x",
            pady=(0, 8),
        )
        panel.columnconfigure(0, weight=1)

        text_side = tk.Frame(panel, bg=BG)
        text_side.grid(row=0, column=0, sticky="w")

        tk.Label(
            text_side,
            text=self._t("● PINNED"),
            bg=BG,
            fg=GREEN,
            font=("Segoe UI", 7, "bold"),
        ).pack(anchor="w")

        tk.Label(
            text_side,
            text=self._t("Where should Capture Mode appear?"),
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 7),
        ).pack(anchor="w", pady=(2, 0))

        selector_border = tk.Frame(
            panel,
            bg=LINE,
            padx=1,
            pady=1,
        )
        selector_border.grid(row=0, column=1, sticky="e")

        selector = tk.Frame(selector_border, bg=LINE)
        selector.pack()

        self.corner_buttons: dict[str, tk.Button] = {}

        for code, (symbol, row, column) in CORNER_META.items():
            button = tk.Button(
                selector,
                text=symbol,
                command=lambda value=code: self.select_corner(value),
                bg=FIELD,
                fg=MUTED,
                activebackground=GOLD,
                activeforeground="#16120C",
                relief="flat",
                bd=0,
                font=("Segoe UI Symbol", 10, "bold"),
                width=3,
                height=1,
                cursor="hand2",
            )
            button.grid(
                row=row,
                column=column,
                padx=(0 if column == 0 else 1, 0),
                pady=(0 if row == 0 else 1, 0),
                ipadx=1,
                ipady=1,
            )
            self.corner_buttons[code] = button

        self._refresh_corner_buttons(self.args.corner)

    def _build_scroll_body(self) -> None:
        shell = tk.Frame(self.root, bg=BG)
        shell.pack(
            fill="both",
            expand=True,
            padx=(11, 5),
            pady=(0, 4),
        )
        shell.rowconfigure(0, weight=1)
        shell.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            shell,
            bg=BG,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.scrollbar = ttk.Scrollbar(
            shell,
            orient="vertical",
            command=self.canvas.yview,
            style="Gold.Vertical.TScrollbar",
        )
        self.scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
            padx=(4, 0),
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.form = tk.Frame(self.canvas, bg=BG)
        self._scroll_window_id = self.canvas.create_window(
            (0, 0),
            window=self.form,
            anchor="nw",
        )

        self.form.bind("<Configure>", self._on_form_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self._build_position_panel()
        self._build_form()

    def _build_footer(self) -> None:
        footer = tk.Frame(self.root, bg=BG)
        footer.pack(
            side="bottom",
            fill="x",
            padx=11,
            pady=(3, 8),
        )
        footer.columnconfigure(0, weight=1)

        tk.Button(
            footer,
            text=self._t("Save Application"),
            command=self.save_job,
            bg=GOLD_LIGHT,
            fg="#16120C",
            activebackground=GOLD,
            activeforeground="#16120C",
            relief="flat",
            bd=0,
            font=("Segoe UI", 8, "bold"),
            cursor="hand2",
        ).grid(
            row=0,
            column=0,
            sticky="ew",
            ipady=6,
        )

        tk.Button(
            footer,
            text=self._t("Analyze"),
            command=self.analyze_job,
            bg="#171E28",
            fg=TEXT,
            activebackground="#212A37",
            activeforeground=TEXT,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=LINE,
            font=("Segoe UI", 7, "bold"),
            cursor="hand2",
        ).grid(
            row=0,
            column=1,
            sticky="e",
            padx=(6, 0),
            ipadx=8,
            ipady=6,
        )

    def _build_form(self) -> None:
        self.company_var = tk.StringVar()
        self.title_var = tk.StringVar()
        self.location_var = tk.StringVar()
        self.work_mode_var = tk.StringVar()
        self.url_var = tk.StringVar()
        self.source_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Saved")

        for variable in (
            self.company_var,
            self.title_var,
            self.location_var,
            self.work_mode_var,
            self.url_var,
            self.source_var,
        ):
            variable.trace_add("write", self._mark_draft_from_vars)

        # Company
        self._section_label(self.form, self._t("Company"))
        self.company_entry = self._entry(self.form, self.company_var)
        self.company_entry.pack(fill="x", ipady=5)

        # Job title
        self._section_label(self.form, self._t("Job title"))
        self._entry(self.form, self.title_var).pack(fill="x", ipady=5)

        # Location
        self._section_label(self.form, self._t("Location"))
        self._entry(self.form, self.location_var).pack(fill="x", ipady=5)

        # Work mode - visible segmented buttons so the field is impossible to
        # miss in the compact Capture window. Values stay canonical internally.
        self._section_label(self.form, self._t("Work mode"))
        work_mode_frame = tk.Frame(self.form, bg=BG)
        work_mode_frame.pack(fill="x", pady=(0, 1))
        self.work_mode_buttons: dict[str, tk.Button] = {}

        for index, mode in enumerate(("Onsite", "Hybrid", "Remote")):
            work_mode_frame.columnconfigure(index, weight=1)
            button = tk.Button(
                work_mode_frame,
                text=self._work_mode_label(mode),
                command=lambda value=mode: self.select_work_mode(value),
                bg=FIELD,
                fg=MUTED,
                activebackground=GOLD,
                activeforeground="#16120C",
                relief="flat",
                bd=0,
                highlightthickness=1,
                highlightbackground=LINE,
                font=("Segoe UI", 8, "bold"),
                cursor="hand2",
            )
            button.grid(
                row=0,
                column=index,
                sticky="ew",
                padx=(0 if index == 0 else 3, 0),
                ipady=5,
            )
            self.work_mode_buttons[mode] = button

        self._refresh_work_mode_buttons()

        # Status - INLINE. No Toplevel, no z-order problem.
        self._section_label(self.form, self._t("Status"))
        self.status_holder = tk.Frame(self.form, bg=BG)
        self.status_holder.pack(fill="x")

        self.status_button = tk.Button(
            self.status_holder,
            text=f"●  {self._status_label('Saved')}   ▾",
            command=self.toggle_status_options,
            anchor="w",
            bg=FIELD,
            fg=TEXT,
            activebackground=FIELD_HOVER,
            activeforeground=TEXT,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=LINE,
            font=("Segoe UI", 9),
            cursor="hand2",
        )
        self.status_button.pack(fill="x", ipady=5)

        self.status_options = tk.Frame(
            self.status_holder,
            bg=PANEL,
            highlightthickness=1,
            highlightbackground=LINE,
        )

        for status in STATUSES:
            status_color = STATUS_COLORS.get(status, TEXT)

            tk.Button(
                self.status_options,
                text=f"●  {self._status_label(status)}",
                command=lambda value=status: self.select_status(value),
                anchor="w",
                bg=PANEL,
                fg=status_color,
                activebackground=status_color,
                activeforeground="#0C121C",
                relief="flat",
                bd=0,
                font=("Segoe UI", 8, "bold"),
                cursor="hand2",
            ).pack(fill="x", ipadx=6, ipady=3)

        self._update_status_button_arrow()

        # URL
        self._section_label(self.form, self._t("Job URL"))
        self._entry(self.form, self.url_var).pack(fill="x", ipady=5)

        # Description
        self._section_label(self.form, self._t("Description"))
        self.description = tk.Text(
            self.form,
            height=5,
            wrap="word",
            bg=FIELD,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=LINE,
            highlightcolor=GOLD,
            font=("Segoe UI", 9),
            padx=7,
            pady=6,
        )
        self.description.pack(fill="x")
        self.description.bind("<KeyRelease>", self._mark_draft_from_text)

        # Source autocomplete. Suggestions live INSIDE this holder, directly
        # under the Source field, so they can never jump below Notes again.
        self._section_label(self.form, self._t("Source"))
        self.source_holder = tk.Frame(self.form, bg=BG)
        self.source_holder.pack(fill="x")

        self.source_entry = self._entry(self.source_holder, self.source_var)
        self.source_entry.pack(fill="x", ipady=5)
        self.source_entry.bind("<FocusIn>", self._source_focus_in)
        self.source_entry.bind("<ButtonRelease-1>", self._source_focus_in)
        self.source_entry.bind("<KeyRelease>", self._source_key_release)
        self.source_entry.bind("<Down>", self._source_focus_suggestions)
        self.source_entry.bind("<Escape>", lambda _e: self._hide_source_suggestions())

        self.source_suggestions = tk.Frame(
            self.source_holder,
            bg=PANEL,
            highlightthickness=1,
            highlightbackground=LINE,
        )

        self.source_list = tk.Listbox(
            self.source_suggestions,
            height=5,
            bg=PANEL,
            fg=TEXT,
            selectbackground=GOLD,
            selectforeground="#16120C",
            relief="flat",
            bd=0,
            highlightthickness=0,
            activestyle="none",
            exportselection=False,
            font=("Segoe UI", 8),
        )
        self.source_list.pack(fill="both", expand=True)
        self.source_list.bind("<ButtonRelease-1>", self._source_click)
        self.source_list.bind("<Return>", self._source_choose)
        self.source_list.bind("<Escape>", lambda _e: self._hide_source_suggestions())

        # Rating - clickable five-star row.
        self._section_label(self.form, self._t("Rating"))
        rating_frame = tk.Frame(self.form, bg=BG)
        rating_frame.pack(fill="x", pady=(0, 1))

        self.star_buttons: list[tk.Button] = []

        for index in range(1, 6):
            button = tk.Button(
                rating_frame,
                text="☆",
                command=lambda value=index: self.set_rating(value),
                bg=BG,
                fg=GOLD_LIGHT,
                activebackground=BG,
                activeforeground=GOLD_LIGHT,
                relief="flat",
                bd=0,
                font=("Segoe UI Symbol", 18),
                cursor="hand2",
                padx=1,
                pady=0,
            )
            button.pack(side="left")
            button.bind(
                "<Enter>",
                lambda _e, value=index: self._preview_rating(value),
            )
            button.bind("<Leave>", lambda _e: self._refresh_stars())
            self.star_buttons.append(button)

        tk.Button(
            rating_frame,
            text=self._t("Clear"),
            command=lambda: self.set_rating(0),
            bg=BG,
            fg=MUTED,
            activebackground=BG,
            activeforeground=TEXT,
            relief="flat",
            bd=0,
            font=("Segoe UI", 7),
            cursor="hand2",
        ).pack(side="left", padx=(7, 0))

        # Notes
        self._section_label(self.form, self._t("Notes"))
        self.notes = tk.Text(
            self.form,
            height=3,
            wrap="word",
            bg=FIELD,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=LINE,
            highlightcolor=GOLD,
            font=("Segoe UI", 9),
            padx=7,
            pady=6,
        )
        self.notes.pack(fill="x", pady=(0, 8))
        self.notes.bind("<KeyRelease>", self._mark_draft_from_text)

        self.company_entry.focus_set()

    # ======================================================
    # SCROLLING
    # ======================================================

    def _on_form_configure(self, _event=None) -> None:
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=bbox)

    def _on_canvas_configure(self, event) -> None:
        if self._scroll_window_id is not None:
            self.canvas.itemconfigure(
                self._scroll_window_id,
                width=event.width,
            )

    def _on_mousewheel(self, event) -> None:
        # bind_all is used by the main Capture window, but events coming from
        # Analyzer/result Toplevel windows must never scroll the main form.
        # More importantly, Analyzer must never unbind this global handler.
        try:
            if event.widget.winfo_toplevel() is not self.root:
                return
        except Exception:
            pass

        # Let the Source Listbox handle its own wheel if the pointer is over it.
        try:
            hovered = self.root.winfo_containing(
                self.root.winfo_pointerx(),
                self.root.winfo_pointery(),
            )
            if hovered is self.source_list:
                return
        except Exception:
            pass

        if event.delta:
            # Smooth, controlled wheel scrolling:
            # - each wheel notch moves a modest distance
            # - movement eases over several frames instead of jumping
            # - repeated wheel input extends the target without huge momentum
            bbox = self.canvas.bbox("all")
            if not bbox:
                return

            content_height = max(1, bbox[3] - bbox[1])
            viewport_height = max(1, self.canvas.winfo_height())
            max_scroll = max(0.0, float(content_height - viewport_height))

            if max_scroll <= 0:
                return

            start, _end = self.canvas.yview()
            current_px = start * content_height

            if self._scroll_target_px is None:
                self._scroll_target_px = current_px

            notches = event.delta / 120.0
            self._scroll_target_px += -notches * 68.0
            self._scroll_target_px = max(
                0.0,
                min(max_scroll, self._scroll_target_px),
            )

            if self._scroll_animation_id is None:
                self._animate_smooth_scroll()

    def _animate_smooth_scroll(self) -> None:
        bbox = self.canvas.bbox("all")
        if not bbox or self._scroll_target_px is None:
            self._scroll_target_px = None
            self._scroll_animation_id = None
            return

        content_height = max(1, bbox[3] - bbox[1])
        viewport_height = max(1, self.canvas.winfo_height())
        max_scroll = max(0.0, float(content_height - viewport_height))

        start, _end = self.canvas.yview()
        current_px = start * content_height
        target_px = max(
            0.0,
            min(max_scroll, self._scroll_target_px),
        )
        remaining = target_px - current_px

        if abs(remaining) <= 0.9:
            self.canvas.yview_moveto(
                target_px / content_height
                if content_height
                else 0.0
            )
            self._scroll_target_px = None
            self._scroll_animation_id = None
            return

        # Ease toward the requested target. This feels continuous without
        # skipping several form fields from one small wheel movement.
        step = remaining * 0.28

        # Keep tiny end-of-animation movements visible and stable.
        if 0 < abs(step) < 1.0:
            step = 1.0 if step > 0 else -1.0

        next_px = max(
            0.0,
            min(max_scroll, current_px + step),
        )
        self.canvas.yview_moveto(
            next_px / content_height
            if content_height
            else 0.0
        )

        self._scroll_animation_id = self.root.after(
            12,
            self._animate_smooth_scroll,
        )

    # ======================================================
    # CORNER SELECTOR
    # ======================================================

    def _refresh_corner_buttons(self, selected: str) -> None:
        for code, button in self.corner_buttons.items():
            active = code == selected
            button.configure(
                bg=GOLD if active else FIELD,
                fg="#16120C" if active else MUTED,
                activebackground=GOLD if active else FIELD_HOVER,
                activeforeground="#16120C" if active else TEXT,
            )

    def select_corner(self, corner: str) -> None:
        if corner not in CORNER_META:
            return

        self.args.corner = corner
        self.settings.set("capture_corner", corner)
        self._refresh_corner_buttons(corner)
        self.position_window(corner)
        self.root.after(180, self._save_geometry_now)

    # ======================================================
    # WORK MODE
    # ======================================================

    def select_work_mode(self, mode: str) -> None:
        if mode not in {"Onsite", "Hybrid", "Remote"}:
            mode = ""

        # Clicking the already selected mode clears it, matching the optional
        # blank state available in the normal Add Job form.
        if self.work_mode_var.get() == mode:
            mode = ""

        self.work_mode_var.set(mode)
        if mode:
            self._ensure_draft_started()
        self._refresh_work_mode_buttons()

    def _refresh_work_mode_buttons(self) -> None:
        if not hasattr(self, "work_mode_buttons"):
            return

        selected = self._canonical_work_mode(self.work_mode_var.get())
        for mode, button in self.work_mode_buttons.items():
            active = mode == selected
            button.configure(
                bg=GOLD if active else FIELD,
                fg="#16120C" if active else MUTED,
                activebackground=GOLD if active else FIELD_HOVER,
                activeforeground="#16120C" if active else TEXT,
                highlightbackground=GOLD if active else LINE,
            )

    # ======================================================
    # STATUS - INLINE DROPDOWN
    # ======================================================

    def toggle_status_options(self) -> None:
        self._hide_source_suggestions()

        if self._status_open:
            self._hide_status_options()
            return

        self.status_options.pack(fill="x", pady=(2, 0))
        self._status_open = True
        self._update_status_button_arrow()
        self.root.after_idle(self._on_form_configure)

    def _hide_status_options(self) -> None:
        if self._status_open:
            self.status_options.pack_forget()
            self._status_open = False
            self._update_status_button_arrow()
            self.root.after_idle(self._on_form_configure)

    def _update_status_button_arrow(self) -> None:
        arrow = "▴" if self._status_open else "▾"
        status = self.status_var.get() or "Saved"
        status_color = STATUS_COLORS.get(status, TEXT)

        self.status_button.configure(
            text=f"●  {self._status_label(status)}   {arrow}",
            fg=status_color,
            activeforeground=status_color,
            highlightbackground=status_color,
        )

    def select_status(self, status: str) -> None:
        self.status_var.set(status)
        self._ensure_draft_started()
        self._hide_status_options()

    # ======================================================
    # SOURCE AUTOCOMPLETE
    # ======================================================

    def _source_focus_in(self, _event=None) -> None:
        self._hide_status_options()

        if self._suppress_source_focus_once:
            self._suppress_source_focus_once = False
            return

        self.root.after_idle(self._refresh_source_suggestions)

    def _source_key_release(self, event) -> None:
        if event.keysym == "Down":
            return

        if event.keysym == "Escape":
            self._hide_source_suggestions()
            return

        if event.keysym in {"Up", "Return", "Tab"}:
            return

        self._refresh_source_suggestions()

    def _refresh_source_suggestions(self) -> None:
        matches = source_matches(self.source_var.get())

        self.source_list.delete(0, "end")

        self._source_match_values = list(matches)

        for source in matches:
            self.source_list.insert(
                "end",
                self._source_label(source),
            )

        if not matches:
            self._hide_source_suggestions()
            return

        if not self._source_open:
            self.source_suggestions.pack(fill="x", pady=(2, 0))
            self._source_open = True

        # Use fewer rows when only a few prefix matches remain.
        self.source_list.configure(height=max(1, min(5, len(matches))))
        self.root.after_idle(self._on_form_configure)

    def _source_focus_suggestions(self, _event=None):
        if not self._source_open:
            self._refresh_source_suggestions()

        if self._source_open and self.source_list.size() > 0:
            self.source_list.focus_set()
            self.source_list.selection_clear(0, "end")
            self.source_list.selection_set(0)
            self.source_list.activate(0)
            return "break"

        return None

    def _source_click(self, event) -> str:
        if self.source_list.size() <= 0:
            return "break"

        index = self.source_list.nearest(event.y)

        if index < 0 or index >= self.source_list.size():
            return "break"

        value = self._source_match_values[index]
        self.source_var.set(value)
        self._ensure_draft_started()

        # Close the suggestions and keep them closed after the chosen value
        # receives focus again.
        self._suppress_source_focus_once = True
        self._hide_source_suggestions()
        self.source_entry.focus_set()
        self.source_entry.icursor("end")

        return "break"

    def _source_choose(self, _event=None) -> str | None:
        selection = self.source_list.curselection()

        if selection:
            index = selection[0]
        else:
            index = self.source_list.index("active")
            if self.source_list.size() <= 0:
                return None

        value = self._source_match_values[index]
        self.source_var.set(value)
        self._ensure_draft_started()

        # Keyboard selection should behave exactly like mouse selection:
        # once chosen, the suggestion list disappears.
        self._suppress_source_focus_once = True
        self._hide_source_suggestions()
        self.source_entry.focus_set()
        self.source_entry.icursor("end")

        return "break"

    def _hide_source_suggestions(self) -> None:
        if self._source_open:
            self.source_suggestions.pack_forget()
            self._source_open = False
            self.root.after_idle(self._on_form_configure)

    # ======================================================
    # RATING
    # ======================================================

    def set_rating(self, value: int) -> None:
        self.rating = max(0, min(5, int(value)))
        if self.rating:
            self._ensure_draft_started()
        self._refresh_stars()

    def _preview_rating(self, value: int) -> None:
        for index, button in enumerate(self.star_buttons, start=1):
            button.configure(text="★" if index <= value else "☆")

    def _refresh_stars(self) -> None:
        for index, button in enumerate(self.star_buttons, start=1):
            button.configure(text="★" if index <= self.rating else "☆")

    # ======================================================
    # DRAFT / PAYLOAD
    # ======================================================

    def _ensure_draft_started(self) -> None:
        if not self.draft_started_at:
            self.draft_started_at = (
                datetime.now()
                .astimezone()
                .isoformat(timespec="seconds")
            )

    def _has_capture_content(self) -> bool:
        try:
            return any(
                (
                    self.company_var.get().strip(),
                    self.title_var.get().strip(),
                    self.location_var.get().strip(),
                    self.work_mode_var.get().strip(),
                    self.url_var.get().strip(),
                    self.source_var.get().strip(),
                    self.description.get("1.0", "end-1c").strip(),
                    self.notes.get("1.0", "end-1c").strip(),
                )
            ) or self.rating > 0 or self.status_var.get() != "Saved"
        except Exception:
            return False

    def _autosave_capture_draft(self) -> None:
        if self._loading_recovery:
            return

        if not self._has_capture_content():
            self.recovery.clear("capture_job")
            return

        self._ensure_draft_started()

        try:
            self.recovery.save(
                "capture_job",
                self.payload(),
            )
        except Exception:
            pass

    def _restore_capture_draft(self) -> None:
        recovered = self.recovery.get("capture_job")
        if not recovered:
            return

        payload = recovered.get("payload") or {}
        if not isinstance(payload, dict):
            self.recovery.clear("capture_job")
            return

        self._loading_recovery = True
        try:
            self.company_var.set(str(payload.get("company") or ""))
            self.title_var.set(str(payload.get("job_title") or ""))
            self.location_var.set(str(payload.get("location") or ""))
            work_mode = str(payload.get("work_mode") or "")
            if work_mode not in {"", "Onsite", "Hybrid", "Remote"}:
                work_mode = ""
            self.work_mode_var.set(work_mode)
            self._refresh_work_mode_buttons()
            self.url_var.set(str(payload.get("url") or ""))
            self.source_var.set(str(payload.get("source") or ""))

            status = str(payload.get("status") or "Saved")
            if status not in STATUSES:
                status = "Saved"
            self.status_var.set(status)

            try:
                recovered_rating = int(float(payload.get("rating") or 0))
            except (TypeError, ValueError):
                recovered_rating = 0
            self.rating = max(0, min(5, recovered_rating))
            self._refresh_stars()

            self.description.delete("1.0", "end")
            self.description.insert("1.0", str(payload.get("description") or ""))

            self.notes.delete("1.0", "end")
            self.notes.insert("1.0", str(payload.get("notes") or ""))

            self.draft_started_at = str(payload.get("date_saved") or "") or None
            self._update_status_button_arrow()
        except Exception:
            # A stale/corrupt recovery file must never stop Capture Mode from
            # opening. Discard only the bad draft and continue with a clean form.
            self.recovery.clear("capture_job")
            self.draft_started_at = None
        finally:
            self._loading_recovery = False

    def _mark_draft_from_vars(self, *_args) -> None:
        if self._loading_recovery:
            return

        if self._has_capture_content():
            self._ensure_draft_started()

        self.root.after_idle(self._autosave_capture_draft)

    def _mark_draft_from_text(self, _event=None) -> None:
        if self._loading_recovery:
            return

        if self._has_capture_content():
            self._ensure_draft_started()

        self.root.after_idle(self._autosave_capture_draft)

    def payload(self) -> dict:
        return {
            "company": self.company_var.get().strip(),
            "job_title": self.title_var.get().strip(),
            "location": self.location_var.get().strip(),
            "work_mode": self._canonical_work_mode(self.work_mode_var.get()),
            "status": self.status_var.get().strip() or "Saved",
            "url": self.url_var.get().strip(),
            "description": self.description.get("1.0", "end-1c").strip(),
            "source": self.source_var.get().strip(),
            "rating": self.rating,
            "notes": self.notes.get("1.0", "end-1c").strip(),
            "date_saved": (
                self.draft_started_at
                or datetime.now().astimezone().isoformat(timespec="seconds")
            ),
        }

    def clear_form(self) -> None:
        self.company_var.set("")
        self.title_var.set("")
        self.location_var.set("")
        self.work_mode_var.set("")
        self._refresh_work_mode_buttons()
        self.url_var.set("")
        self.source_var.set("")
        self.status_var.set("Saved")

        self.description.delete("1.0", "end")
        self.notes.delete("1.0", "end")

        self.rating = 0
        self._refresh_stars()
        self._hide_status_options()
        self._hide_source_suggestions()
        self._update_status_button_arrow()

        self.draft_started_at = None
        self.recovery.clear("capture_job")

        self.canvas.yview_moveto(0)
        self.company_entry.focus_set()

    # ======================================================
    # SAVE / ANALYZE
    # ======================================================

    def save_job(self) -> None:
        data = self.payload()

        if not data["company"] and not data["job_title"]:
            messagebox.showwarning(
                "JAM",
                self._t("Add at least a company or job title."),
                parent=self.root,
            )
            return

        try:
            self.repo.create(data)
            try:
                RECOVERY_DIR.mkdir(parents=True, exist_ok=True)
                (RECOVERY_DIR / "capture_changed.flag").write_text(
                    datetime.now().astimezone().isoformat(timespec="seconds"),
                    encoding="utf-8",
                )
            except Exception:
                pass
            self.clear_form()
            self._flash_title(self._t("Application saved ✓"))
        except Exception as exc:
            messagebox.showerror(
                "JAM",
                self._t(str(exc)),
                parent=self.root,
            )

    def _get_analyzer(self):
        """Create and cache the heavy Analyzer on first use only."""
        if self.analyzer is not None:
            return self.analyzer

        with self._analyzer_lock:
            if self.analyzer is None:
                from services.analyzer_service import AnalyzerService

                self.analyzer = AnalyzerService()

        return self.analyzer

    def analyze_job(self) -> None:
        data = self.payload()

        if not data["job_title"] and not data["description"]:
            messagebox.showwarning(
                "JAM",
                self._t("Add a job title or description first."),
                parent=self.root,
            )
            return

        progress_win = self._show_analysis_progress()
        progress_state = {
            "label": progress_win._jam_label,
            "percent": progress_win._jam_percent,
            "bar": progress_win._jam_bar,
        }

        def progress(label: str, percent: int) -> None:
            def apply_update() -> None:
                if not progress_win.winfo_exists():
                    return
                progress_state["label"].configure(text=self._t(label))
                progress_state["percent"].configure(text=f"{percent}%")
                progress_state["bar"]["value"] = percent

            try:
                self.root.after(0, apply_update)
            except Exception:
                pass

        def worker() -> None:
            try:
                result = self._get_analyzer().analyze(
                    data["job_title"],
                    data["description"],
                    progress_callback=progress,
                )
            except Exception as exc:
                def show_error() -> None:
                    try:
                        if progress_win.winfo_exists():
                            progress_win.destroy()
                    except Exception:
                        pass
                    messagebox.showerror(
                        self._t("JAM Analyzer"),
                        self._t(str(exc)),
                        parent=self.root,
                    )

                self.root.after(0, show_error)
                return

            def show_result() -> None:
                try:
                    if progress_win.winfo_exists():
                        progress_win.destroy()
                except Exception:
                    pass
                self.show_analysis(result)

            self.root.after(0, show_result)

        threading.Thread(
            target=worker,
            name="JAM-Analyzer",
            daemon=True,
        ).start()

    def _show_analysis_progress(self):
        win = tk.Toplevel(self.root)
        win.title(self._t("JAM - Analyzing"))
        win.configure(bg=BG)
        win.resizable(False, False)
        win.attributes("-topmost", True)
        win.transient(self.root)
        win.protocol("WM_DELETE_WINDOW", lambda: None)

        width = 315
        height = 210

        self.root.update_idletasks()
        x = self.root.winfo_x() + max(0, (self.root.winfo_width() - width) // 2)
        y = self.root.winfo_y() + 55
        win.geometry(f"{width}x{height}{x:+d}{y:+d}")

        frame = tk.Frame(win, bg=BG)
        frame.pack(fill="both", expand=True, padx=18, pady=16)

        tk.Label(
            frame,
            text=self._t("JAM MATCH ENGINE v3"),
            bg=BG,
            fg=GOLD_LIGHT,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w")

        tk.Label(
            frame,
            text=self._t("Analyzing job offer + CV"),
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", pady=(8, 5))

        label = tk.Label(
            frame,
            text=self._t("Validating job offer"),
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
            anchor="w",
        )
        label.pack(fill="x", pady=(0, 10))

        style = ttk.Style(win)
        try:
            style.configure(
                "JAMAnalyzer.Horizontal.TProgressbar",
                troughcolor=FIELD,
                background=GOLD_LIGHT,
                bordercolor=FIELD,
                lightcolor=GOLD_LIGHT,
                darkcolor=GOLD,
                thickness=9,
            )
        except Exception:
            pass

        bar = ttk.Progressbar(
            frame,
            orient="horizontal",
            mode="determinate",
            maximum=100,
            value=5,
            style="JAMAnalyzer.Horizontal.TProgressbar",
        )
        bar.pack(fill="x")

        percent = tk.Label(
            frame,
            text="5%",
            bg=BG,
            fg=GOLD_LIGHT,
            font=("Segoe UI", 8, "bold"),
        )
        percent.pack(anchor="e", pady=(5, 0))

        tk.Label(
            frame,
            text=self._t("Local analysis. No cloud AI call."),
            bg=BG,
            fg="#697487",
            font=("Segoe UI", 7),
        ).pack(anchor="w", pady=(9, 0))

        win._jam_label = label
        win._jam_percent = percent
        win._jam_bar = bar
        return win

    def show_analysis(self, result: dict) -> None:
        win = tk.Toplevel(self.root)
        win.title(self._t("JAM - CV Match"))
        win.configure(bg=BG)
        win.resizable(False, False)
        win.attributes("-topmost", True)
        win.transient(self.root)

        width = 345
        height = 500

        self.root.update_idletasks()
        x = self.root.winfo_x() + max(0, (self.root.winfo_width() - width) // 2)
        y = self.root.winfo_y() + 25
        win.geometry(f"{width}x{height}{x:+d}{y:+d}")

        outer = tk.Frame(win, bg=BG)
        outer.pack(fill="both", expand=True, padx=(14, 6), pady=12)
        outer.rowconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1)

        canvas = tk.Canvas(
            outer,
            bg=BG,
            highlightthickness=0,
            bd=0,
        )
        canvas.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            outer,
            orient="vertical",
            command=canvas.yview,
            style="Gold.Vertical.TScrollbar",
        )
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(4, 0))
        canvas.configure(yscrollcommand=scrollbar.set)

        frame = tk.Frame(canvas, bg=BG)
        frame_id = canvas.create_window((0, 0), window=frame, anchor="nw")

        def sync_scroll(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def sync_width(event):
            canvas.itemconfigure(frame_id, width=event.width)

        frame.bind("<Configure>", sync_scroll)
        canvas.bind("<Configure>", sync_width)

        def wheel(event):
            if event.delta:
                canvas.yview_scroll(
                    int(-1 * (event.delta / 120)),
                    "units",
                )
            return "break"

        # Bind the Analyzer wheel to its own Toplevel only.
        # The old implementation used bind_all/unbind_all here; when the mouse
        # left or the Analyzer closed, unbind_all deleted Capture Mode's global
        # wheel binding as well. That is why the scrollbar still dragged but
        # the mouse wheel stopped working afterward.
        win.bind("<MouseWheel>", wheel, add="+")

        tk.Label(
            frame,
            text=self._t("CV MATCH RESULT"),
            bg=BG,
            fg=GOLD_LIGHT,
            font=("Segoe UI", 7, "bold"),
        ).pack(anchor="w")

        score_available = bool(result.get("score_available"))
        score = result.get("score")
        score_text = f"{score}%" if score_available and score is not None else self._t("NO SCORE")

        tk.Label(
            frame,
            text=score_text,
            bg=BG,
            fg=GOLD_LIGHT if score_available else DANGER,
            font=("Segoe UI", 27 if score_available else 20, "bold"),
        ).pack(pady=(7, 1))

        tk.Label(
            frame,
            text=self._t(result.get("score_label", "JAM Match Engine")),
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 9, "bold"),
        ).pack()

        confidence = result.get("confidence")
        if confidence is not None:
            tk.Label(
                frame,
                text=self._t(f"Evidence confidence: {confidence}%"),
                bg=BG,
                fg=MUTED,
                font=("Segoe UI", 7),
            ).pack(pady=(2, 2))

        def section(title: str, content: str, color: str = GOLD_LIGHT):
            box = tk.Frame(
                frame,
                bg=PANEL,
                highlightthickness=1,
                highlightbackground=LINE,
            )
            box.pack(fill="x", pady=(7, 0))

            tk.Label(
                box,
                text=title,
                bg=PANEL,
                fg=color,
                font=("Segoe UI", 7, "bold"),
                anchor="w",
            ).pack(fill="x", padx=8, pady=(6, 2))

            tk.Label(
                box,
                text=content,
                bg=PANEL,
                fg=MUTED,
                justify="left",
                wraplength=285,
                font=("Segoe UI", 8),
                anchor="w",
            ).pack(fill="x", padx=8, pady=(0, 6))

        if not score_available:
            section(
                self._t("WHY THERE IS NO SCORE"),
                "\n".join(self._t(item) for item in result.get("no_score_reasons", []))
                or self._t("JAM does not have enough reliable evidence to calculate a percentage."),
                DANGER,
            )

        section(
            self._t("MATCHED SKILLS / TOOLS"),
            ", ".join(result.get("matched_skills", [])) or self._t("None detected"),
            GREEN,
        )

        missing_required = result.get("missing_required_skills", [])
        missing_all = result.get("missing_skills", [])
        section(
            self._t("MISSING / NOT FOUND"),
            ", ".join(missing_required or missing_all) or self._t("None detected"),
            DANGER if (missing_required or missing_all) else GOLD_LIGHT,
        )

        matched_concepts = result.get("matched_concepts", [])
        if matched_concepts:
            section(
                self._t("MATCHED RESPONSIBILITIES / DOMAIN"),
                ", ".join(matched_concepts[:10]),
                GREEN,
            )

        experience_required = result.get("required_years")
        cv_years = result.get("cv_years")
        if experience_required is not None:
            section(
                self._t("EXPERIENCE"),
                self._t(
                    f"Job asks for about {experience_required:g}+ years. "
                    + (
                        f"JAM detected about {cv_years:g} years in the CV."
                        if cv_years is not None
                        else "JAM could not reliably calculate CV experience years."
                    )
                ),
            )

        matched_languages = result.get("matched_languages", [])
        missing_languages = result.get("missing_languages", [])
        if matched_languages or missing_languages:
            text = []
            if matched_languages:
                text.append(self._t("Matched") + ": " + ", ".join(matched_languages))
            if missing_languages:
                text.append(self._t("Missing") + ": " + ", ".join(missing_languages))
            section(self._t("LANGUAGES"), "\n".join(text))

        section(
            self._t("WHAT TO REVIEW"),
            "\n\n".join(self._t(item) for item in result.get("suggestions", [])[:5])
            or self._t("No major changes suggested."),
        )

        timings = result.get("timings_ms", {})
        if timings:
            engine_method = self._t(result.get("method", "JAM Match Engine"))
            engine_time = self._t(
                "Local analysis time: {} ms".format(timings.get("total", 0))
            )
            section(
                self._t("ENGINE"),
                "{}\n{}".format(engine_method, engine_time),
                "#7C8798",
            )

        tk.Button(
            frame,
            text=self._t("Done"),
            command=win.destroy,
            bg=GOLD_LIGHT,
            fg="#16120C",
            relief="flat",
            bd=0,
            font=("Segoe UI", 8, "bold"),
        ).pack(fill="x", pady=(10, 5), ipady=5)

        win.after_idle(sync_scroll)

    # ======================================================
    # GUIDED TOUR HINT
    # ======================================================

    def _show_tutorial_hint(self) -> None:
        """Show a lightweight coach card beside Capture during the guided tour."""
        if self._tutorial_hint is not None:
            try:
                if self._tutorial_hint.winfo_exists():
                    self._tutorial_hint.lift()
                    return
            except Exception:
                pass

        hint = tk.Toplevel(self.root)
        self._tutorial_hint = hint
        hint.withdraw()
        hint.overrideredirect(True)
        hint.configure(bg=GOLD_LIGHT)
        try:
            hint.attributes("-topmost", True)
        except Exception:
            pass

        shell = tk.Frame(hint, bg="#111827", padx=18, pady=16)
        shell.pack(fill="both", expand=True, padx=1, pady=1)

        tk.Label(
            shell,
            text=self._t("GUIDED TOUR"),
            bg="#111827",
            fg=GOLD_LIGHT,
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            shell,
            text=self._t("This is Capture Mode"),
            bg="#111827",
            fg=TEXT,
            font=("Segoe UI", 14, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(5, 8))

        message = (
            "It stays pinned above other windows while you browse and apply, "
            "so you can save an opportunity without leaving the job page.\n\n"
            "To continue the tour, click Return to JAM in the Capture window."
        )
        if self.language == "fr":
            message = (
                "Il reste épinglé au-dessus des autres fenêtres pendant votre navigation "
                "et vos candidatures, afin d’enregistrer une offre sans quitter la page.\n\n"
                "Pour continuer le tutoriel, cliquez sur Retour à JAM dans la fenêtre Capture."
            )

        tk.Label(
            shell,
            text=message,
            bg="#111827",
            fg="#C7D0DE",
            font=("Segoe UI", 9),
            justify="left",
            wraplength=330,
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            shell,
            text=self._t("↗  Return to JAM to continue"),
            bg="#111827",
            fg=GOLD_LIGHT,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(12, 0))

        hint.update_idletasks()
        width = max(360, hint.winfo_reqwidth())
        height = max(170, hint.winfo_reqheight())

        self.root.update_idletasks()
        rx = self.root.winfo_rootx()
        ry = self.root.winfo_rooty()
        rw = self.root.winfo_width()
        rh = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()

        x = rx - width - 14
        y = ry + 18
        if x < 12:
            x = rx + rw + 14
        if x + width > sw - 12:
            x = max(12, sw - width - 12)
        if y + height > sh - 12:
            y = max(12, sh - height - 12)

        hint.geometry(f"{width}x{height}+{int(x)}+{int(y)}")
        hint.deiconify()
        hint.lift()

    # ======================================================
    # SMALL UX HELPERS / CLOSE
    # ======================================================

    def _flash_title(self, text: str) -> None:
        self.root.title(f"JAM - {text}")
        self.root.after(
            1000,
            lambda: self.root.title(self._t("JAM - Quick Capture")),
        )

    def close(self) -> None:
        if self._tutorial_hint is not None:
            try:
                self._tutorial_hint.destroy()
            except Exception:
                pass
            self._tutorial_hint = None

        # Preserve the proven close behavior: exiting this process is what the
        # parent JAM process watches for before restoring the main window.
        try:
            self._save_geometry_now()
        except Exception:
            pass

        try:
            self.root.attributes("-topmost", False)
        except Exception:
            pass

        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    args = parse_args()

    # DPI awareness MUST happen before Tk creates any window.
    enable_dpi_awareness()
    ensure_runtime_dirs()
    init_database()

    app = CaptureApp(args)
    app.run()


if __name__ == "__main__":
    main()
