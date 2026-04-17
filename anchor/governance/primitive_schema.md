# Anchor V5: Typed Primitive Vocabulary Schema

This document defines the intermediate structural layer used to decompose high-level risk statements into machine-parseable, lintable components.

## The 5-Part Primitive Set

Every risk in `constitution.anchor` (and its associated frameworks) should ideally be decomposed into these five fields:

### 1. ACTION
The foundational operation being performed.
- *Examples*: `modify`, `access`, `inject`, `generate`, `delete`, `exfiltrate`.

### 2. OBJECT
The resource, entity, or data type being acted upon.
- *Examples*: `governance_configuration`, `pii_data`, `model_weights`, `api_credentials`.

### 3. CONTEXT
Environmental, conditional, or state-based qualifiers of the action.
- *Examples*: `unrestricted`, `production_env`, `untrusted_prompt`, `runtime`, `cross_tenant`.

### 4. AUTHORITY
The entity or permission level required for the action (or the actor performing it).
- *Examples*: `unauthorised_actor`, `system_admin`, `generative_model`, `privileged_identity`.

### 5. FLOW
The data or control movement semantics involved in the risk.
- *Examples*: `direct_mutation`, `egress_stream`, `instruction_stack`, `lateral_movement`.

## Example: RI-24
**Risk Statement**: "Unrestricted modification of governance configuration by unauthorised actors."

| Primitive | Value |
| :--- | :--- |
| **ACTION** | `modify` |
| **OBJECT** | `governance_configuration` |
| **CONTEXT** | `unrestricted` |
| **AUTHORITY** | `unauthorised_actor` |
| **FLOW** | `direct_mutation` |

## Enforcement & Linting
The Anchor loader will now validate the `primitives` block in `.anchor` files.
- **Development Mode**: If a `seal` is set to `PENDING`, missing fields will trigger a `WARNING`.
- **Production Mode**: If a `seal` is verified (strict mode), missing fields in a defined `primitives` block will trigger a `FAIL`.
