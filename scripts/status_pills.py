"""One status vocabulary for every program pill on the site (rebate cards and hub tables). 2026-10-14.

A fact's status (data/verified-facts/*.json) maps to one label and one tone. The label is always a word, never colour
alone. Tones and their colours live in the shared CSS (_partials/nav-footer.html, 'program status pills').
Card pills keep their old classes (status-open / status-limited / status-closed) because build_powerscore.py reads them;
"Info" stays "Info" because PowerScore treats an Info card as not a home rebate.
"""

STATUS = {
    #  status      label           tone      card class (rebate cards; read by PowerScore)
    "active":   ("Open",          "open",   "status-open"),
    "upcoming": ("Starts soon",   "soon",   "status-limited"),
    "waitlist": ("On hold",       "soon",   "status-limited"),
    "paused":   ("Paused",        "soon",   "status-limited"),
    "check":    ("Check first",   "soon",   "status-limited"),
    "closed":   ("Closed",        "closed", "status-closed"),
    "info":     ("Info",          "info",   "status-open"),
}

LABELS = sorted({v[0] for v in STATUS.values()})


def card_pill(status: str) -> tuple:
    """(class, label) for a rebate card pill."""
    label, _, cls = STATUS[status]
    return cls, label


def hub_pill(status: str) -> str:
    label = STATUS[status][0]
    return f'<span class="rb-status rb-{status}">{label}</span>'
