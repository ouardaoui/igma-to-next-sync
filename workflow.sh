#!/bin/bash

# Workflow automation script
PROJECT_DIR="./my-project"
BACKUP_DIR="./backups"

echo "🚀 Starting workflow..."

# 1. Create backup
python analyze_project.py $PROJECT_DIR --backup

# 2. Run analysis
python analyze_project.py $PROJECT_DIR --output analysis.txt

# 3. Install dependencies
cd $PROJECT_DIR
npm install axios swr react-query @next/bundle-analyzer

# 4. Run linting
npm run lint:fix

# 5. Build project
npm run build

echo "✅ Workflow complete!"