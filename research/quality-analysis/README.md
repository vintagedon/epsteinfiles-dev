# Quality Analysis

Research artifacts from data quality auditing.

## Contents

| File | Description |
|------|-------------|
| `l0-quality-audit.md` | Comprehensive L0 quality report with findings and remediation proposals |
| `l0-audit-metrics.json` | Raw metrics from audit script (machine-readable) |

## Reproducing the Audit

```bash
# From repo root
python pipelines/validation/quality_audit_l0.py --output research/quality-analysis/l0-audit-metrics.json
```

## Related

- `pipelines/validation/validate_l0_schemas.py` — Schema validation
- `pipelines/validation/quality_audit_l0.py` — Quality audit script
- `data/layer-0-canonical/schema/` — JSON Schema definitions
