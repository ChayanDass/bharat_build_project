#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AWS_REGION="${AWS_REGION:-$(aws configure get region)}"
STACK_NAME="${HEATOPS_STACK_NAME:-heatops}"
APPLICATION_NAME="${HEATOPS_APPLICATION_NAME:-heatops}"
BEDROCK_MODEL_ID="${BEDROCK_MODEL_ID:-anthropic.claude-3-5-sonnet-20241022-v2:0}"

if [[ -z "$AWS_REGION" ]]; then
  echo "Set AWS_REGION or configure a default region with the AWS CLI." >&2
  exit 1
fi

cd "$ROOT_DIR"
rm -rf .aws-sam/lambda-src
mkdir -p .aws-sam/lambda-src
cp -R backend data requirements.txt .aws-sam/lambda-src/
sed 's|CodeUri: ../|CodeUri: lambda-src|' \
  infrastructure/template.yaml > .aws-sam/deploy-template.yaml
sam build \
  --template-file .aws-sam/deploy-template.yaml \
  --build-dir .aws-sam/build
sam deploy \
  --template-file .aws-sam/build/template.yaml \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  --capabilities CAPABILITY_IAM \
  --resolve-s3 \
  --no-confirm-changeset \
  --parameter-overrides \
    "ApplicationName=$APPLICATION_NAME" \
    "BedrockModelId=$BEDROCK_MODEL_ID"

read_stack_output() {
  aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue | [0]" \
    --output text
}

WEB_URL="$(read_stack_output HeatOpsWebUrl)"
BUCKET_NAME="$(read_stack_output HeatOpsWebBucketName)"
DISTRIBUTION_ID="$(read_stack_output HeatOpsCloudFrontDistributionId)"
USER_POOL_ID="$(read_stack_output HeatOpsUserPoolId)"
USER_POOL_CLIENT_ID="$(read_stack_output HeatOpsUserPoolClientId)"

cd "$ROOT_DIR/frontend"
npm ci
VITE_API_BASE_URL= \
VITE_AUTH_MODE=cognito \
VITE_COGNITO_USER_POOL_ID="$USER_POOL_ID" \
VITE_COGNITO_USER_POOL_CLIENT_ID="$USER_POOL_CLIENT_ID" \
  npm run build

aws s3 sync dist "s3://$BUCKET_NAME" \
  --region "$AWS_REGION" \
  --delete \
  --cache-control no-cache
aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths '/*' >/dev/null

printf 'HeatOps deployed at %s\n' "$WEB_URL"
