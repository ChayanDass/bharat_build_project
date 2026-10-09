from backend.security.cedar_authorizer import CedarAuthorizer


def test_cedar_allows_central_assignment_and_denies_department_assignment():
    authorizer = CedarAuthorizer()

    assert authorizer.is_allowed(
        role="central",
        action="assign_task",
        department=None,
        task_id="task-1",
        task_department="Water Dept",
    )
    assert not authorizer.is_allowed(
        role="department",
        action="assign_task",
        department="Water Dept",
        task_id="task-1",
        task_department="Water Dept",
    )


def test_cedar_limits_department_access_to_assigned_department():
    authorizer = CedarAuthorizer()

    assert authorizer.is_allowed(
        role="department",
        action="update_task",
        department="Water Dept",
        task_id="task-1",
        task_department="Water Dept",
    )
    assert not authorizer.is_allowed(
        role="department",
        action="update_task",
        department="Health Dept",
        task_id="task-1",
        task_department="Water Dept",
    )
    assert not authorizer.is_allowed(
        role="central",
        action="update_task",
        department=None,
        task_id="task-1",
        task_department="Water Dept",
    )
