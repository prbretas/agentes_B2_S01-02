# Summary Agent Rules

This agent maintains a structured customer interaction summary.

## Goal
Keep summary.json accurate and up to date, but avoid unnecessary rewrites.

## Decision rules
- Read interactions.txt and the current summary.json before taking action.
- Update the summary only if the new interaction changes the situation in a meaningful way.
- Meaningful changes include:
  - new issue
  - stronger negative sentiment
  - cancellation intent
  - complaint threat
  - request escalation
- If there is no meaningful change, keep the current summary.
- If customer frustration is strong, set priority to urgent.

## Output expectations
The agent may:
1. keep the existing summary
2. update summary.json
3. write a decision log to agent_decision.json
