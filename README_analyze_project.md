# analyze_project.py - Project Analysis & Optimization Tool 🔍

Comprehensive analysis tool for Next.js/TypeScript projects exported from Figma. Identifies issues, suggests optimizations, and generates API integration layers.

## 🎯 Purpose

This script helps you:
- Analyze project structure and identify Figma export issues
- Generate API integration boilerplate
- Identify performance optimizations
- Create project backups
- Generate diff reports between versions

## 📋 Commands

### Basic Analysis
```bash
# Simple analysis
python3 analyze_project.py /path/to/your/project

# Analysis with backup
python3 analyze_project.py /path/to/your/project --backup

# Save report to file
python3 analyze_project.py /path/to/your/project --output report.txt
```

### Auto-Fix Issues
```bash
# Apply automatic fixes (creates API layer, env templates, etc.)
python3 analyze_project.py /path/to/your/project --auto-fix

# Backup + Auto-fix (recommended)
python3 analyze_project.py /path/to/your/project --backup --auto-fix
```

### Generate Diffs
```bash
# Compare two project versions
python3 analyze_project.py --diff /original/project /modified/project --output changes.diff

# Example: Compare your project with Figma export
python3 analyze_project.py --diff ~/Desktop/labgenz.ai/frontend ~/Desktop/frontend --output figma-changes.diff
```

## 📊 What It Analyzes

### 1. **Project Structure**
- Total files count
- Components organization
- Pages and API routes
- TypeScript types
- Styling files

### 2. **Common Figma Issues**
- Hardcoded dimensions (width/height in px)
- Missing TypeScript types (usage of 'any')
- Unused SVG imports
- Missing error handling in async code
- Missing API configuration

### 3. **Dependencies**
- Missing packages for API integration
- Suggests common requirements (axios, swr, react-query)

### 4. **Performance**
- Suggests dynamic imports for heavy components
- Image optimization configuration
- Bundle analyzer setup

## 📁 Generated Files

When using `--auto-fix`, the script creates:

### API Layer Structure
```
lib/
├── api/
│   ├── config.ts      # Axios configuration with interceptors
│   ├── hooks.ts       # React hooks for API calls
│   └── types.ts       # TypeScript interfaces
```

### Configuration Files
```
.env.local.example     # Environment variables template
```

### Updated package.json
- Adds useful scripts (analyze, lint:fix)
- Prepared for bundle analysis

## 📈 Report Output

The analysis report includes:

```
============================
FIGMA PROJECT ANALYSIS REPORT
============================
Project Path: /path/to/project
Analysis Date: 2024-01-15 10:30:00

PROJECT STRUCTURE:
  Total Files: 156
  Components: 45
  Pages: 12
  API Routes: 0
  Styles: 8
  Types: 5
  Figma Imports: 23

ISSUES FOUND: 15
  1. [missing_dependency] Missing axios for API integration
     Fix: npm install axios
  2. [code_quality] Using 'any' type in Button.tsx
     Fix: Manual review required
  ...

PERFORMANCE OPTIMIZATIONS: 10
  - Use dynamic imports for heavy components
  ...

API INTEGRATION:
  - Generate: lib/api/config.ts
  - Generate: lib/api/hooks.ts
  - Generate: lib/api/types.ts
============================
```

## 🔄 Backup System

Backups are created with timestamps:
```
backups/
├── backup_20240115_103000/   # Full project backup
├── backup_20240115_143000/
└── backup_20240116_091500/
```

## 💡 Use Cases

### Case 1: New Figma Export
```bash
# Analyze and fix issues
python3 analyze_project.py ~/Desktop/figma-export --backup --auto-fix
cd ~/Desktop/figma-export
npm install
npm run build
```

### Case 2: Compare Before/After
```bash
# See what changed
python3 analyze_project.py --diff ~/project-before ~/project-after --output changes.diff

# Open in VS Code with syntax highlighting
code changes.diff
```

### Case 3: Regular Maintenance
```bash
# Weekly analysis
python3 analyze_project.py ~/my-project --output "reports/analysis_$(date +%Y%m%d).txt"
```

## ⚙️ Advanced Options

### Custom Ignore Patterns
The script automatically ignores:
- node_modules
- .next
- dist
- .git

### File Hash Tracking
Uses MD5 hashing to track file changes accurately.

## 🚨 Important Notes

1. **Always backup first** - Use `--backup` flag for safety
2. **Review before auto-fix** - Check report before applying `--auto-fix`
3. **Test after changes** - Run `npm run build` to verify

## 📝 Examples

### Full Workflow
```bash
# 1. Backup and analyze
python3 analyze_project.py ~/Desktop/my-app --backup --output initial-report.txt

# 2. Review the report
cat initial-report.txt

# 3. Apply fixes if needed
python3 analyze_project.py ~/Desktop/my-app --auto-fix

# 4. Verify changes
cd ~/Desktop/my-app
npm install
npm run build
```

### Diff Workflow
```bash
# 1. Compare versions
python3 analyze_project.py --diff ./v1 ./v2 --output version-diff.diff

# 2. View in VS Code
code version-diff.diff
```

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Permission denied | `chmod +x analyze_project.py` |
| Module not found | Ensure Python 3.6+ |
| Path not found | Use absolute paths |
| Encoding errors | Files saved as UTF-8 |

---
*Script Version: 1.0*