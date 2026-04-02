# Output Contract

Use this structure unless the user provided a stricter format.

## Required sections
1. Executive summary
2. Planner summary
3. Specialist findings
4. Verifier verdict
5. Final recommendation
6. Assumptions and evidence gaps

## Acceptance checks
- Planner speaks first in the reasoning structure.
- Every specialist lane contributes at least one scoped finding.
- Verifier clearly separates PASS and FAIL.
- At most one replan loop is allowed.
- The final answer is structured enough that another person can reproduce the reasoning path.
- If 3 or more options are compared, the scoring criteria and weights are visible before the recommendation.
- If all three skills are active, the answer discloses that scoring and verification were performed by independent agents.

## Minimal planner template
- Objective:
- Success criteria:
- Lanes:
- Parallelizable tasks:
- Verifier checklist:

## Minimal specialist template
- Scope:
- Findings:
- Assumptions:
- Evidence gaps:
- Recommendation:

## Minimal verifier template
- PASS items:
- FAIL items:
- Missing evidence:
- Required patch:
