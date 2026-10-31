import re


def generate(source, traditional_result=None):
    """Apply safe local source rewrites while retaining the user's statement layout."""
    out = source
    out = re.sub(r"\b([A-Za-z_]\w*)\s*\*\s*1\b", r"\1", out)
    out = re.sub(r"\b([A-Za-z_]\w*)\s*\+\s*0\b", r"\1", out)
    out = re.sub(
        r"\b([A-Za-z_]\w*)\s*\*\s*([248])\b",
        lambda m: f"({m[1]} << {int(m[2]).bit_length() - 1})",
        out,
    )
    return out
