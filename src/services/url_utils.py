from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import re


# Tracking/query parameters that do not identify the actual job offer.
TRACKING_KEYS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "gclid",
    "fbclid",
    "msclkid",
    "trk",
    "trkinfo",
    "trackingid",
    "refid",
    "ref",
    "source",
    "src",
    "campaign",
    "campaignid",
    "sessionid",
    "original_referer",
    "lipi",
    "midtoken",
    "midsig",
    "ebp",
    "recommendedflavor",
}


def normalize_job_url(value: str | None) -> str:
    """Return a stable, shareable job URL without common tracking noise.

    The function is deliberately conservative: it removes known tracking
    parameters but preserves unknown query parameters because some job boards
    use them as part of the offer identifier.
    """
    raw = str(value or "").strip()
    if not raw:
        return ""

    # Do not invent a scheme for arbitrary text. Only normalize valid-looking
    # web URLs; otherwise return what the user typed.
    if not re.match(r"^https?://", raw, flags=re.IGNORECASE):
        return raw

    try:
        parts = urlsplit(raw)
    except Exception:
        return raw

    scheme = parts.scheme.lower()
    host = parts.netloc.lower()
    if host.startswith("www."):
        host = host[4:]

    path = re.sub(r"/{2,}", "/", parts.path or "/")
    if path != "/":
        path = path.rstrip("/")

    query_pairs = parse_qsl(parts.query, keep_blank_values=True)

    # LinkedIn job URLs have a stable /jobs/view/<id> path. Everything else
    # in the query string is browsing/recommendation tracking.
    if host.endswith("linkedin.com"):
        match = re.search(r"/jobs/view/(?:[^/?]*-)?(\d+)", path)
        if match:
            path = f"/jobs/view/{match.group(1)}"
            query_pairs = []

    # Indeed's stable offer identifier is the jk value.
    elif host.endswith("indeed.com") or ".indeed." in host:
        jk = next(
            (value for key, value in query_pairs if key.lower() == "jk" and value),
            "",
        )
        if jk:
            path = "/viewjob"
            query_pairs = [("jk", jk)]
        else:
            query_pairs = [
                (key, value)
                for key, value in query_pairs
                if key.lower() not in TRACKING_KEYS
                and not key.lower().startswith("utm_")
            ]

    else:
        query_pairs = [
            (key, value)
            for key, value in query_pairs
            if key.lower() not in TRACKING_KEYS
            and not key.lower().startswith("utm_")
        ]

    query = urlencode(query_pairs, doseq=True)

    return urlunsplit((scheme, host, path, query, ""))
