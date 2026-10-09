from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class CognitoIdentityMiddleware(BaseHTTPMiddleware):
    """Replace demo actor headers with identity claims verified by API Gateway."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        event = request.scope.get("aws.event", {})
        authorizer = event.get("requestContext", {}).get("authorizer", {})
        claims = authorizer.get("claims") or authorizer.get("jwt", {}).get("claims")
        if not isinstance(claims, dict):
            return JSONResponse({"detail": "A valid Cognito identity is required."}, status_code=401)

        groups = claims.get("cognito:groups", [])
        if isinstance(groups, str):
            groups = [group.strip() for group in groups.split(",") if group.strip()]
        groups = set(groups)
        department = claims.get("custom:department")
        if "central" in groups:
            role = "central"
            department = ""
        elif "department" in groups and department:
            role = "department"
        else:
            return JSONResponse(
                {"detail": "The authenticated user has no HeatOps operator role."},
                status_code=403,
            )

        headers = [
            (name, value)
            for name, value in request.scope["headers"]
            if name.lower() not in {
                b"x-heatops-role",
                b"x-heatops-department",
                b"x-heatops-actor",
            }
        ]
        headers.extend(
            [
                (b"x-heatops-role", role.encode("utf-8")),
                (b"x-heatops-department", department.encode("utf-8")),
                (
                    b"x-heatops-actor",
                    (claims.get("cognito:username") or claims.get("sub", "operator")).encode("utf-8"),
                ),
            ]
        )
        request.scope["headers"] = headers
        return await call_next(request)
