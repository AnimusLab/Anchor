import re

patterns = {
    "ANC_023": re.compile(r'^(?:[^"\'#]|(["\'])(?:(?!\1).|\\\1)*\1)*\bos\.environ\b(?!\s*\.get|["\'])'),
    "ANC_018": re.compile(r'^(?:[^"\'#]|(["\'])(?:(?!\1).|\\\1)*\1)*\bsubprocess\.(run|call|Popen|check_output)\s*\('),
    "ANC_001": re.compile(r'^(?:[^"\'#]|(["\'])(?:(?!\1).|\\\1)*\1)*\b(=\s*["\']https?://api\.(openai|anthropic|cohere)\.(com|ai)|openai\.Client|anthropic\.Anthropic\(|cohere\.Client)'),
    "ANC_002": re.compile(r'^(?:[^"\'#]|(["\'])(?:(?!\1).|\\\1)*\1)*\.\b(upsert|add_texts|add_documents|add)\s*\((?!.*encrypt)'),
}

lines = [
    ('healer.py:121', 'ANC_023', 'def _fix_anc_023(line: str):'),
    ('healer.py:121 (docstring)', 'ANC_023', '    """ANC-023: Bulk env access  os.environ \u2192 targeted os.environ.get()"""'),
    ('healer.py:133', 'ANC_023', '            "Replace os.environ with os.environ.get(\'KEY\', \'\') "'),
    ('healer.py:151 (string)', 'ANC_018', '            "Set shell=False and pass arguments as a list: subprocess.run([\'cmd\', \'arg1\']) "'),
    ('framework.py:339 (log)', 'ANC_001', '        logger.info("[Anchor] Patched: cohere.Client.chat")'),
    ('contexts.py:50 (set)', 'ANC_002', '                        self.current_scope_vars.add(target.id)'),
    ('markdown_parser.py:30 (set)', 'ANC_002', '                detected_risks.add(match.upper())'),
    ('canary.py:2 (real)', 'ANC_023', 'print(os.environ) # This should definitely fire MIT-023-A'),
]

for desc, p_id, line in lines:
    match = patterns[p_id].search(line)
    print(f"{desc:.<40} {'MATCH' if match else 'SKIP'}")
    if match:
        print(f"  Matched: {match.group(0)}")
