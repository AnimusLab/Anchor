import re
from typing import Dict, List, Set


class MarkdownPolicyParser:
    """
    Parses GenAI-generated Threat Models (Markdown) to extract active Risk IDs.
    Implements the 'Dynamic Governance' feature for Issue #203.
    """

    # Regex to find patterns like "Risk ID: RI-24" or "| RI-24 |" in tables
    RISK_PATTERN = re.compile(r"\b(AI-\d+|RI-\d+)\b", re.IGNORECASE)

    def parse_file(self, file_path: str) -> Set[str]:
        """
        Scans a Markdown file and returns a set of detected Risk IDs.
        """
        detected_risks = set()

        try:
            # anchor: ignore RI-08
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Scan for all Risk IDs
            matches = self.RISK_PATTERN.findall(content)

            # Normalize to uppercase (e.g., 'ri-24' -> 'RI-24')
            for match in matches:
                detected_risks.add(match.upper())

            print(
                f"[DEBUG] Parsed Threat Model '{file_path}': Found {len(detected_risks)} risks.")
            return detected_risks

        except Exception as e:
            print(f"[WARN] Failed to parse threat model: {e}")
            return set()


# --- Quick Test ---
if __name__ == "__main__":
    # Create a dummy GenAI output file
    dummy_md = """
    # Threat Model for Agent V1
    
    ## Identified Risks
    Based on the architecture, the following risks are applicable:
    
    1. **Unauthorized Data Access** (Risk ID: RI-24)
       - Mitigation: Use MCP Client.
       
    2. **Model Hallucination** (Risk ID: AI-20)
       - Mitigation: Use Guardrails.
    """

    with open("temp_threat_model.md", "w") as f:  # anchor: ignore RI-08
        f.write(dummy_md)

    parser = MarkdownPolicyParser()
    risks = parser.parse_file("temp_threat_model.md")

    print("Detected Risks:", risks)
    # Expected: {'RI-24', 'AI-20'}
