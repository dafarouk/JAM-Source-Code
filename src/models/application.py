from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional


@dataclass(slots=True)
class Application:
    company: str = ""
    job_title: str = ""
    description: str = ""
    url: str = ""
    location: str = ""
    work_mode: str = ""
    status: str = "Saved"
    rating: int = 0
    notes: str = ""
    contact_name: str = ""
    contact_url: str = ""
    source: str = ""
    salary_text: str = ""
    date_saved: str = ""
    date_applied: Optional[str] = None
    updated_at: str = ""
    match_score: Optional[int] = None
    analysis_json: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
