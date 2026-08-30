# Policy and Authority Boundary

TiRCorder's live policy substrate is `tircorder.rights_policy`.

It exists to keep four things distinct:

```text
observed data != requested action != stated purpose != authority
```

The initial implementation is intentionally small and in-process.  It gives us
a deterministic semantic kernel that can later be projected into OPA/Rego (or
another mature policy engine) without changing the user-rights model.

## Current actions

- `ingest`
- `process`
- `share`
- `export`
- `contact_service`

## Current sensitive data classes

- general
- health
- disability
- location
- cultural
- sacred
- policing

## Authority receipts

An `AuthorityReceipt` records:

- authority kind
- subject identifier
- permitted purposes
- permitted actions
- permitted data classes
- optional jurisdiction
- optional expiry

The evaluator requires the receipt to match the same subject, purpose, action,
and data class before sensitive processing or disclosure is allowed.

## BIDI non-collapse rules

The implementation deliberately refuses the reverse promotions:

```text
possession of data         ->/ authority
observed behaviour         ->/ legal capacity
health/disability label    ->/ access permission
```

These are regression-tested boundaries rather than documentation-only values.

See [Rights-First BIDI Architecture](RIGHTS_FIRST_BIDI.md) for the wider
product model around disability, cultural governance, policing, safety, and
global health integration.

## External policy-engine direction

OPA/Rego remains a useful scale-up target for deployer-specific rules,
jurisdiction overlays, and human-readable policy receipts.  It is **not** a
currently shipped dependency of this repository.

A future adapter should preserve the current typed semantics:

```text
PolicyRequest
  -> OPA input document
  -> allow / deny / transform decision
  -> human-readable reason
  -> provenance/audit receipt
```

Do not infer an authority receipt merely because an external policy happens to
return `allow`.

## Historical note

An earlier version of this document described a `src.policy.engine` module and
`CulturalFlags` example.  Those surfaces were aspirational and were not present
in the live repository.  This document now names the actual owner and separates
implemented policy semantics from future external-engine integration.
