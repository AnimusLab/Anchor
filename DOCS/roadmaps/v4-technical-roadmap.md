# Technical Roadmap: Anchor V4 (Sovereign Control Plane)

The V4 lifecycle expands Anchor from a developer-focused CLI tool into a federated enterprise compliance mesh.

---

## 🎯 Milestones

### 1. The Hub-and-Spoke Sovereign Mesh
*   Design and deploy the master control plane (**Hub Node**) managing user directories, capability mappings, and aggregated dashboards.
*   Develop the on-premises database agent (**Spoke Node**) to ingest transaction logs locally inside the corporate network VPC.
*   Establish complete separation of concerns: source code and raw prompt logs remain inside the Spoke; only cryptographic hashes and rule verdicts route to the Hub.

### 2. The Brokered WebSocket Relay Protocol
*   Develop a persistent WebSocket connection interface between Hub and Spoke.
*   Implement lightweight metadata headers (`AUDIT_HEADER` ~200 bytes) containing transaction signatures and rule hashes.
*   Implement the **On-Demand Forensic Pull** workflow: auditors request raw payloads via the Hub; the Spoke fetches records locally, encrypts them using **AES-256-GCM**, and routes them back securely.

### 3. Regulatory Dialect Translators
*   Implement multi-jurisdictional compliance exports inside `AuditEntry`:
    *   **RBI (India)**: Maps violations to the FREE-AI pillars (Fairness, Robustness, Explainability, Ethics, Accountability).
    *   **SEC (US)**: Triggers cybersecurity materiality flags for Form 8-K reporting.
    *   **EU AI Act**: Formats execution records to comply with Article 12 (Automatic Event Logging).

### 4. Role-Based Access Control Surface
*   Enforce capability gates via JWT attributes.
*   Differentiate visibility permissions across Standard Auditors (hub-only), Cross-Hub internal auditors (org-wide), and Regulatory Inspectors (jurisdiction-scoped).
*   Programmatically block all auditor roles from accessing `CODEBASE` or `DATABASE` entity assets.
