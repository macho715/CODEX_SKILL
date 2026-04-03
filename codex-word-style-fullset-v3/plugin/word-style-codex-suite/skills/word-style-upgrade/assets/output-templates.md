# Output Templates

## audit-only
```md
# Executive Summary
- Verdict:
- Selected preset:
- Risk level:
- Recommended action:

# Findings
| No | Section | Issue | Severity | Recommendation | Evidence |
|---|---|---|---|---|---|

# AMBER layout checks
- item

# QA Gate
- [ ] Heading hierarchy
- [ ] Paragraph logic
- [ ] Alignment and spacing
- [ ] Font policy
- [ ] Table discipline
- [ ] Accessibility gate
```

## patch-list-only
```md
# Patch List
| No | Section/Page | Before | After | Why |
|---|---|---|---|---|

# AMBER layout checks
- item

# QA Summary
- selected preset:
- facts preserved:
- font mapping recorded:
- unresolved layout dependencies:
```

## patched-document
```md
# Revised Document

[corrected content]

## QA Summary
- selected preset:
- facts preserved:
- numbering preserved:
- table intent preserved:
- font policy:
- AMBER layout checks:
```

## style-spec-only
```md
# Recommended Style Spec
- selected preset:
- reason:

## Font Mapping
- Latin:
- East Asian:

## Style Map
| Element | Target |
|---|---|

## Table Rules
| Element | Rule |
|---|---|

## Accessibility Gate
- item
- item
```
