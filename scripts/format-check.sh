#!/bin/bash

# Terraform format check script

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🎨 Checking Terraform formatting..."

cd "$BASE_DIR"

# Check formatting for all .tf files
if terraform fmt -check -recursive .; then
    echo "✅ All Terraform files are properly formatted"
else
    echo "❌ Some Terraform files need formatting"
    echo "Run 'terraform fmt -recursive .' to fix formatting issues"
    exit 1
fi