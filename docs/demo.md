# HeatOps Demo Scenario — Ward 12

## 3-Minute Hackathon Demo Script

### 1. Dashboard Overview
- Open HeatOps Command Centre dashboard.
- Active heat events:
  - 🔴 Ward 12 — Karol Bagh North (CRITICAL, Temp 44°C, Humidity 58%, Heat Index 52°C)
  - 🟠 Ward 18 — Lajpat Nagar West (HIGH)
  - 🟡 Ward 25 — Vasant Kunj (MODERATE)

### 2. Ward Intelligence & Vulnerability
- Select Ward 12.
- Inspect vulnerable population:
  - 1,200 outdoor workers
  - 3,400 elderly residents
  - 5,100 children
  - Total 9,700 at-risk

### 3. Agent Response Plan Generation
- Click **"Trigger Agent Response Workflow"**.
- HeatOps agent executes tools:
  1. `get_weather` -> 44°C, 58% RH
  2. `calculate_heat_risk` -> CRITICAL (Heat Index 52°C)
  3. `get_vulnerability` -> 1,200 outdoor workers
  4. `get_resources` -> Cooling center capacity gap & water point deficit detected
  5. `create_action_plan` -> Plan ID generated
  6. `assign_task` -> 4 targeted interventions assigned to Labour, Ward Officers, Health, Water Depts.

### 4. Closed-Loop Task Execution & Escalation
- Tasks display status lifecycle (`PENDING` -> `ACKNOWLEDGED` -> `IN_PROGRESS` -> `COMPLETED`).
- Click **"Simulate Overdue"** on Water Dept task ("Dispatch emergency water tanker").
- System automatically detects missed deadline, transitions status to `OVERDUE` -> `ESCALATED`, creates Escalation record, and fires emergency alert notification.

### 5. Agent Decision Support Query
- Click preset question chip: *"Why was the water supply task escalated?"* or *"Why is Ward 12 critical?"*
- HeatOps agent provides concise, evidence-grounded explanation citing exact temperature, heat index, and deadline timestamps.
