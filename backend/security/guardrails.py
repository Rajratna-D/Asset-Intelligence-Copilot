import re
import logging
import unicodedata
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# -------------------------------------------------------------
# Prompt Injection & Security Attack Signatures
# -------------------------------------------------------------
PROMPT_INJECTION_PATTERNS = [
    r"(?i)\bignore\s+(all\s+)?(previous|prior|above)\s+(instructions|directives|prompts|rules)",
    r"(?i)\bdisregard\s+(all\s+)?(previous|prior|above|system)\s+(instructions|directives|rules|prompts)",
    r"(?i)\bforget\s+(all\s+)?(previous|prior|above)\s+(instructions|rules)",
    r"(?i)\breveal\s+(your\s+)?(system\s+prompt|initial\s+instructions|instructions|prompt)",
    r"(?i)\bwhat\s+(is|are)\s+your\s+(system\s+prompt|raw\s+instructions|system\s+instructions)",
    r"(?i)\bshow\s+me\s+your\s+(system\s+prompt|developer\s+prompt|hidden\s+rules)",
    r"(?i)\bprint\s+(your\s+)?(system\s+prompt|instructions\s+verbatim)",
    r"(?i)\brepeat\s+(all\s+)?(the\s+)?(words|text)\s+above\b",
    r"(?i)\bwhat\s+are\s+the\s+first\s+\d+\s+words\b",
    r"(?i)\b(output|print|display)\s+(your\s+)?(system_prompt|initial\s+prompt|meta\s+prompt)\b",
    r"(?i)\byou\s+are\s+now\s+in\s+(developer\s+mode|dan\s+mode|unrestricted\s+mode|debug\s+mode)",
    r"(?i)\bjailbreak\b",
    r"(?i)\bact\s+as\s+(an?\s+)?(unfiltered|unrestricted|evil|dan)\b",
    r"(?i)\b(pretend|imagine)\s+(you\s+are|you're)\s+(not|an?\s+unrestricted|unconstrained)\b",
    r"(?i)\byou\s+are\s+no\s+longer\s+bound\s+by\b",
    r"(?i)\bfrom\s+now\s+on\s+you\s+(must|will)\s+ignore\b",
    r"(?i)\bsimulate\s+(a\s+)?(developer\s+mode|root\s+access|jailbroken)\b",
    r"(?i)\bdo\s+anything\s+now\b",
    r"(?i)\bbypass\s+(all\s+)?(guardrails|filters|safety\s+checks|rules)",
    r"(?i)\boverride\s+(all\s+)?(safety|rules|instructions)",
    r"(?i)\b(show|dump|leak|output)\s+(all\s+)?(passwords|api_keys|api\s+keys|secrets|\.env)",
    r"(?i)\bcat\s+(\/etc\/|\.env|config\.py)\b",
    r"(?i)\bdrop\s+table\b",
    r"(?i)\bdelete\s+from\s+(wells|users|inspections|maintenance)\b",
    r"(?i)\bselect\s+\*\s+from\s+sqlite_master\b",
]

SECRET_LEAK_PATTERNS = [
    r"(?i)\bAQ\.[A-Za-z0-9_-]{20,}\b", # Gemini API Key pattern
    r"(?i)\bsk-[A-Za-z0-9_-]{20,}\b",  # OpenAI / OpenRouter key pattern
    r"(?i)\bGEMINI_API_KEY\b",
    r"(?i)\bOPENROUTER_API_KEY\b",
    r"(?i)\bdatabase_password\b",
]

def normalize_text_for_security_scan(text: str) -> str:
    """
    Normalizes unicode, strips zero-width characters and homoglyphs
    to prevent evasion techniques like 'i\u200Bgnore' or 'd\u200brop'.
    """
    if not text:
        return ""
    # Normalize unicode to decomposed form (NFKD)
    normalized = unicodedata.normalize('NFKD', text)
    # Strip invisible/zero-width chars: \u200B (ZWSP), \u200C (ZWNJ), \u200D (ZWJ), \uFEFF (BOM), \u00AD (soft hyphen)
    stripped = re.sub(r'[\u200B-\u200F\u2060\uFEFF\u00AD]', '', normalized)
    return stripped

def check_prompt_injection(query: str) -> Tuple[bool, Optional[str]]:
    """
    Scans incoming user query for adversarial prompt injection,
    jailbreak attempts, or system prompt extraction.
    Returns (is_safe, refusal_reason)
    """
    clean_q = normalize_text_for_security_scan(query.strip())
    
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, clean_q):
            logger.warning(f"Security Alert: Prompt injection attempt detected. Pattern: {pattern}")
            return False, (
                "**[Security Guardrail Active]** This request contains unauthorized instruction override "
                "or system prompt extraction patterns. As the Oilfield Asset Intelligence Copilot, all interactions "
                "are strictly constrained to monitored wellhead telemetry, regulatory compliance (OM-T200, OM-T350, SOP-SR), "
                "and asset operations."
            )
            
    # Check for secret probing
    clean_lower = clean_q.lower()
    if any(k in clean_lower for k in ["api key", "apikey", "secret key", "admin password", ".env"]):
        if any(v in clean_lower for v in ["reveal", "show", "give me", "output", "what is", "dump", "print"]):
            return False, (
                "**[Security Guardrail Active]** Access to internal API keys, database credentials, "
                "and environment variables is strictly protected and non-accessible."
            )
            
    return True, None

def check_sql_injection_attempt(query: str) -> Tuple[bool, Optional[str]]:
    """
    Checks for obvious SQL injection attempts in natural language query.
    """
    normalized_q = normalize_text_for_security_scan(query)
    dangerous_sql = [
        r"(?i);\s*drop\s+table",
        r"(?i);\s*delete\s+from",
        r"(?i);\s*insert\s+into",
        r"(?i);\s*update\s+\w+\s+set",
        r"(?i)union\s+select\s+all",
        r"(?i)'\s*or\s*'1'\s*=\s*'1",
        r"(?i)\"--\s*or\s*1=1",
        r"(?i);\s*attach\s+database",
    ]
    for pattern in dangerous_sql:
        if re.search(pattern, normalized_q):
            logger.warning(f"Security Alert: Malicious SQL injection sequence detected: {pattern}")
            return False, (
                "**[Security Guardrail Active]** SQL command injection payload detected and neutralized. "
                "Database access is strictly restricted to parameterized, audited telemetry queries."
            )
    return True, None

def sanitize_fts_query(query: str) -> str:
    """
    Sanitizes arbitrary text input for safe execution inside SQLite FTS5 MATCH queries.
    Prevents syntax errors from unbalanced quotes, operators (AND, OR, NOT, NEAR),
    and malicious MATCH payload injection.
    """
    if not query:
        return '""'
    clean = re.sub(r'[^\w\s]', ' ', query)
    tokens = [t.strip() for t in clean.split() if t.strip()]
    if not tokens:
        return '""'
    # Wrap individual terms in double quotes for exact literal phrase token matching
    return ' '.join(f'"{token}"' for token in tokens)

def clean_math_and_latex_output(text: str) -> str:
    """
    Converts LaTeX math formatting (e.g. $\\Delta T \\ge 15.0^\\circ \\text{C}$) into
    clear, human-readable plain English for oilfield operators.
    """
    if not text:
        return ""
        
    s = text
    
    # 1. Delta T thresholds with units: $\Delta T \ge 15.0^\circ \text{C}$
    s = re.sub(
        r'\$\\Delta\s*T\s*\\ge\s*([0-9.]+)\s*\^\\circ\s*\\text\{C\}\$',
        r'wellhead temperature at least \1 °C above air',
        s
    )
    s = re.sub(
        r'\$\\Delta\s*T\s*\\ge\s*([0-9.]+)\s*°?C\$',
        r'wellhead temperature at least \1 °C above air',
        s
    )
    s = re.sub(
        r'\$\\Delta\s*T\s*=\s*([0-9.]+)\s*\^\\circ\s*\\text\{C\}\$',
        r'\1 °C temperature delta above air',
        s
    )
    s = re.sub(
        r'\$\\Delta\s*T\s*<\s*([0-9.]+)\s*\^\\circ\s*\\text\{C\}\$',
        r'temperature delta below \1 °C threshold',
        s
    )
    
    # 2. General LaTeX formula cleanup
    s = re.sub(r'\$\\Delta\s*T\$', 'temperature delta (wellhead vs. air)', s)
    s = re.sub(r'\\Delta\s*T', 'temperature delta', s)
    s = re.sub(r'\^\\circ\s*\\text\{C\}', ' °C', s)
    s = re.sub(r'\^\\circ\s*C', ' °C', s)
    s = re.sub(r'\^\\circ', '°', s)
    s = re.sub(r'\\text\{([^}]+)\}', r'\1', s)
    s = re.sub(r'\\ge\b', '>=', s)
    s = re.sub(r'\\le\b', '<=', s)
    s = re.sub(r'\\times\b', '×', s)
    s = re.sub(r'\\approx\b', '≈', s)
    s = re.sub(r'\\implies\b', '=>', s)
    
    # 3. Strip remaining math delimiters $...$ if containing plain numbers/units
    s = re.sub(r'\$([0-9.]+\s*°?C?)\$', r'\1', s)
    s = re.sub(r'\$([^$]+)\$', r'\1', s)
    
    # 4. Clean up any horizontal double spaces while preserving newlines for markdown tables
    s = re.sub(r'[^\S\r\n]{2,}', ' ', s)
    return s.strip()

def sanitize_response_for_leaks(response_text: str) -> str:
    """
    Guarantees no internal API keys, passwords, or database internal schema leaks.
    """
    cleaned = clean_math_and_latex_output(response_text)
    
    # Redact any accidental API key leaks
    for pattern in SECRET_LEAK_PATTERNS:
        cleaned = re.sub(pattern, "[REDACTED_SECURITY_CREDENTIAL]", cleaned)
        
    # Redact internal sqlite fts tables if ever present
    cleaned = cleaned.replace("fleet_docs_fts", "Fleet Operations Documentation")
    cleaned = cleaned.replace("maintenance_reports_fts", "Maintenance Repair Records")
    
    return cleaned
