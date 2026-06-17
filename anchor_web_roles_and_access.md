# Anchor Web Portal: Role-Based Access Control Matrix

This document defines the roles, permissions, visibility scopes, and dynamic user interface rendering mechanics of the Anchor Web portals.

---

## 1. Role Definitions & Access Limits

Anchor enforces strict separation of concerns. The interface is not designed as a series of dashboards, but rather as **Dynamic Constitutional Surfaces** that materialize only the features permitted by the user's authenticated token.

### A. Enterprise Operations Roles (`app.anchorgovernance.tech`)

#### 1. Hub Owner
*   **Clearance ID Format**: `OWN-[ORG]-[HUB]-[NUM]` (e.g. `OWN-AN-SOLAPUR-999`)
*   **Token Scope**: `owner_relay`
*   **Access Level**: `OWNER_ROOT`
*   **Definition**: The local administrative authority for a single deployment hub.
*   **Key Privileges**: 
    *   Full access to hub configuration and keys.
    *   Can add developers or request-based auditors to the hub.
    *   Can modify `policy.anchor` overrides.
    *   Can inspect and decrypt runtime compliance replays.
    *   Cannot access metrics or data belonging to other organizations.

#### 2. Developer
*   **Clearance ID Format**: `DEV-[ORG]-[HUB]-[NUM]` (e.g. `DEV-AN-SOLAPUR-142`)
*   **Token Scope**: `dev_member`
*   **Access Level**: `DEV_OPERATIONAL`
*   **Definition**: Operational team members who write code and deploy agents.
*   **Key Privileges**:
    *   Can register AI agents and deploy static policies.
    *   Can read operational logs and system metrics.
    *   Can view policies (read-only).
    *   *Denied*: Cannot modify rule scopes, manage keys, invite users, or view decrypted forensic replays without owner approval.

---

### B. Oversight & Auditing Roles (`oversight.anchorgovernance.tech`)

#### 3. Standard Auditor (Hub-Scoped)
*   **Clearance ID Format**: `AUD-HUB-[ORG]-[NUM]`
*   **Token Scope**: `standard_auditor`
*   **Visibility Scope**: `HUB_ONLY`
*   **Definition**: An auditor (internal or external third party) assigned to audit a single hub's compliance trail.
*   **Key Privileges**:
    *   Can view hub compliance violations and history.
    *   Can export compliance reports.
    *   *Denied*: Blocked from viewing source code, databases, webhook configs, or requesting forensic replays.

#### 4. Cross-Hub Auditor (Enterprise Governance)
*   **Clearance ID Format**: `AUD-ENT-[ORG]-[NUM]`
*   **Token Scope**: `cross_hub_auditor`
*   **Visibility Scope**: `ORG_WIDE` (All hubs belonging to the company)
*   **Definition**: Enterprise internal auditors responsible for security across the organization's entire fleet.
*   **Key Privileges**:
    *   Can view fleet-wide aggregated metrics, comparative heatmaps, and lineage details.
    *   Can request forensic session decryption (subject to Owner approval).
    *   *Denied*: Blocked from viewing codebase repositories directly.

#### 5. Regulatory Auditor (Jurisdiction-Scoped)
*   **Clearance ID Format**: `AUD-[REGULATOR]-[NAME]-[NUM]` (e.g., `AUD-RB-INDIA-359`)
*   **Token Scope**: `regulatory_auditor`
*   **Visibility Scope**: `JURISDICTIONAL` (Filtered by jurisdiction, e.g., India, EU)
*   **Definition**: External government inspectors verifying compliance under regulatory mandates (like RBI or the EU AI Act).
*   **Key Privileges**:
    *   Can inspect compliance verification dashboards.
    *   Can issue regulatory notices and remediation warnings.
    *   Can request decryption of specific violating decision sessions.
    *   *Denied*: Blocked from browsing company codebase repositories or viewing databases, unless an explicit escalation ticket is approved.

---

### C. Master Platform Role

#### 6. Admin Root
*   **Clearance ID Format**: `ADM-PLATFORM-[NUM]`
*   **Token Scope**: `platform_admin`
*   **Visibility Scope**: `SYSTEM_WIDE`
*   **Definition**: Global platform administrator managing SaaS infrastructure, billing, and system tenancy.
*   **Key Privileges**:
    *   Can provision new organizations, audit hubs, and manage service nodes.
    *   *Denied*: Cannot read private user keys, decrypt private organizational ledgers, or access user-agent prompt payloads (isolated by cryptographic enclaves).

---

## 2. Capability Access Matrix

| Capability | Standard Auditor | Cross-Hub Auditor | Regulatory Auditor | Hub Owner | Developer | Admin Root |
|---|---|---|---|---|---|---|
| **View Codebases** | ✗ DENIED | ✗ DENIED | ✗ DENIED (Escalable) | ✓ YES | ✓ YES | ✗ DENIED |
| **View Hub Violations** | ✓ HUB ONLY | ✓ ORG WIDE | ✓ JURISDICTIONAL | ✓ YES | ✓ YES | ✗ DENIED |
| **Request Replays** | ✗ DENIED | ✓ YES (Needs Approval) | ✓ YES (Needs Approval) | ✓ YES | ✓ YES (Needs Approval) | ✗ DENIED |
| **Approve Replays** | ✗ DENIED | ✗ DENIED | ✗ DENIED | ✓ YES | ✗ DENIED | ✗ DENIED |
| **Modify Constitution** | ✗ DENIED | ✗ DENIED | ✗ DENIED | ✓ YES | ✗ DENIED | ✗ DENIED |
| **Provision Spoke Nodes** | ✗ DENIED | ✗ DENIED | ✗ DENIED | ✓ YES | ✗ DENIED | ✓ YES |
| **Access Databases** | ✗ DENIED | ✗ DENIED | ✗ DENIED | ✓ YES | ✗ DENIED | ✗ DENIED |
| **Issue Notices** | ✗ DENIED | ✗ DENIED | ✓ YES | ✗ DENIED | ✗ DENIED | ✗ DENIED |

---

## 3. Dynamic Capability Injection (The Code Pattern)

Rather than checking roles on the frontend, the backend resolves the permission matrix during auth handshake and injects an active capability token inside the JWT payload.

### Backend Token Resolution (`server/auth.py`)
```python
def generate_token_payload(user):
    # Retrieve capabilities dynamically based on role and subtype
    capabilities = get_capabilities_for_role(user.role, user.auditor_type)
    
    return {
        "sub": user.id,
        "role": user.role,
        "org": user.assigned_org,
        "scope": capabilities["scope"],
        "permissions": capabilities["permissions"],
        "jurisdiction": user.jurisdiction,
        "exp": datetime.utcnow() + timedelta(minutes=Config.JWT_EXPIRY_MINUTES)
    }
```

### Frontend Surface Rendering (`dashboard/src/components/GatedPanel.tsx`)
```typescript
import React from 'react';
import { useAuth } from '../hooks/useAuth';

interface GatedPanelProps {
  requiredPermission: string;
  children: React.ReactNode;
}

export function GatedPanel({ requiredPermission, children }: GatedPanelProps) {
  const { user } = useAuth();

  // If the backend did not inject the permission into the JWT, do not render the component
  if (!user.permissions.includes(requiredPermission)) {
    return null; 
  }

  return <>{children}</>;
}
```
This ensures that UI manipulation on the frontend cannot bypass compliance bounds; the API backend validates the capability token on every incoming request.
