"""
AWS Lambda Handler Bridge using Mangum / ASGIadapter.
Enables seamless execution of the FastAPI backend in AWS Lambda behind API Gateway.
"""
try:
    from mangum import Mangum
    from backend.main import app
    handler = Mangum(app)
except ImportError:
    # Mangum optional fallback for pure local dev
    def handler(event, context):
        return {"statusCode": 500, "body": "Mangum package not installed for Lambda execution."}
