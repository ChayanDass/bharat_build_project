# HeatOps Architecture Blueprint

HeatOps uses a **Single-Build Zero-Rewrite Architecture**. Development and Production environments share identical business logic, agent orchestration contracts, and domain models. Only infrastructure bindings change via configuration adapters.

```text
                 HEATOPS APPLICATION DOMAIN & AGENT
                                │
                        Stable Interfaces
                                │
          ┌─────────────────────┴─────────────────────┐
          │                                           │
     DEVELOPMENT                                 PRODUCTION
   Local Adapters                             AWS Adapters
          │                                           │
   SQLite Database                            Amazon DynamoDB
   FastAPI Runtime                            API Gateway + AWS Lambda
   Google Gemini API                          Amazon Bedrock
   Console Notifications                      AWS SNS
   Local Task Monitor                         AWS EventBridge
```

## Data Model Entities
- `Ward`: `ward_id`, `name`, `city`, `population`, `risk_metadata`
- `VulnerabilityProfile`: `outdoor_worker_count`, `elderly_count`, `children_count`, `high_risk_population`, `vulnerability_score`
- `Resource`: `cooling_centre`, `water_point`, `health_centre`, capacity, availability, owner
- `HeatEvent`: `temperature`, `humidity`, `heat_index`, `severity`, `duration`
- `ActionPlan`: `plan_id`, `event_id`, `priority`, `status`, summary
- `Task`: `action`, `responsible_team`, `priority`, `deadline`, `status` (`PENDING` -> `ACKNOWLEDGED` -> `IN_PROGRESS` -> `COMPLETED`, `OVERDUE`, `ESCALATED`)
- `Escalation`: `escalation_id`, `task_id`, `reason`, `severity`, `status`
