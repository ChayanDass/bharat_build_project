# HeatOps Agent Specification

The HeatOps agent is orchestrated via AWS Strands Agents SDK and model providers.

## Agent Loop
**Sense → Assess → Prioritize → Plan → Act → Monitor → Escalate**

## Eight Logical Tools
1. `get_weather`: Fetch temperature, humidity, heat index, and forecast for ward.
2. `calculate_heat_risk`: Deterministically calculate heat severity (LOW, MODERATE, HIGH, CRITICAL).
3. `get_vulnerability`: Inspect outdoor workers, elderly, children counts.
4. `get_resources`: Query cooling centers, water points, health centers & identify gaps.
5. `create_action_plan`: Formulate action plan for heat event.
6. `assign_task`: Dispatch intervention to responsible department (Health, Water, Labour, Ward Officers) with deadline.
7. `check_task_status`: Inspect task progress and detect overdue status.
8. `escalate_task`: Trigger emergency escalation for missed deadlines.

## Strict Factuality Rules
- Deterministic rules calculate heat risk (`calculate_heat_risk`).
- The LLM never invents weather values, population figures, task statuses, or safety thresholds. All facts come from database/tools.
