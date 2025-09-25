#!/bin/bash

# Terraform validation script

set -e

ENVIRONMENT=${1:-"dev"}
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENVIRONMENT_DIR="${BASE_DIR}/environments/${ENVIRONMENT}"

echo "🔍 Validating Terraform configuration for environment: ${ENVIRONMENT}"

if [ ! -d "$ENVIRONMENT_DIR" ]; then
    echo "❌ Environment directory not found: $ENVIRONMENT_DIR"
    exit 1
fi

cd "$ENVIRONMENT_DIR"

echo "📝 Formatting check..."
terraform fmt -check -recursive

echo "⚡ Initializing Terraform..."
terraform init -backend=false

echo "✅ Validating configuration..."
terraform validate

echo "🎉 Validation completed successfully for environment: ${ENVIRONMENT}"