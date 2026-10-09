permit (
    principal,
    action in [
        HeatOps::Action::"assign_task",
        HeatOps::Action::"refresh_task",
        HeatOps::Action::"retry_task",
        HeatOps::Action::"list_tasks",
        HeatOps::Action::"list_escalations",
        HeatOps::Action::"view_ward",
        HeatOps::Action::"coordinate_response",
        HeatOps::Action::"query_agent",
        HeatOps::Action::"simulate_overdue",
        HeatOps::Action::"simulate_weather",
        HeatOps::Action::"escalate_task",
        HeatOps::Action::"reset_demo"
    ],
    resource
)
when { principal.role == "central" };

permit (
    principal,
    action in [
        HeatOps::Action::"view_task",
        HeatOps::Action::"update_task"
    ],
    resource
)
when {
    principal.role == "department" &&
    principal.department == resource.department
};
