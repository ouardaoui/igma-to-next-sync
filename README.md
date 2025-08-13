# review.py - Interactive Diff Reviewer 🎯

Lightning-fast tool for reviewing and applying changes from Figma exports. Review 50+ file changes in under 5 minutes with smart keyboard shortcuts and colored diffs.

## 🚀 Why This Tool?

**Problem:** Manually reviewing diff files is painful:
- Opening each `.diff` file individually
- Reading through walls of +/- text
- Copy-pasting changes manually
- Risk of breaking code with wrong edits

**Solution:** Interactive review with one-key decisions:
- See all changes with colors (green=added, red=removed)
- Press `a` to accept, `r` to reject
- Auto-apply all approved changes
- 10x faster than manual review

## 📋 Commands

### Quick Review (Fastest)
```bash
# Review ALL files quickly
python3 review.py --quick

# Output:
# [U001] App.tsx
#   Changes: +45 / -12
#   [a]ccept  [r]eject  [v]iew  [s]kip  [q]uit
#   Choice: a
#   ✅ Approved
```

### Detailed Review (For Complex Files)
```bash
# Review specific file in detail
python3 review.py --review U001

# Shows each change block separately
# You can accept/reject individual blocks
```

### Apply Approved Changes
```bash
# Apply all approved changes at once
python3 review.py --apply

# Creates backups automatically
# Shows progress for each file
```

### Fix Decisions (Important!)
```bash
# Fix decisions file (moves fully approved partials)
python3 review.py --fix-decisions

# Output:
# ✅ Moved U002 to approved (all 1 changes approved)
# ✅ Moved U003 to approved (all 1 changes approved)
# ✅ Decisions file fixed and saved!
```

### Show Current Decisions
```bash
# See what's approved, rejected, or partial
python3 review.py --show-decisions

# Output:
# ✅ APPROVED (5):
#   U001: App.tsx
#   U002: Button.tsx
# ❌ REJECTED (2):
#   U003: config.ts
# ⚠️ PARTIAL (1):
#   U004: Header.tsx
#     Approved: 2/3, Rejected: 1/3
```

### Smart Diff Analysis
```bash
# See intelligent analysis of changes
python3 review.py --smart-diff U001

# Shows:
# 📦 Import changes detected
# ⚡ Function changes detected  
# 🎨 Style changes detected
```

### Side-by-Side View
```bash
# View old vs new side-by-side
python3 review.py --side-by-side U001
```

## 🎮 Keyboard Shortcuts

During review, just press:

| Key | Action | Description |
|-----|--------|-------------|
| `a` | **Accept** | Approve this change |
| `r` | **Reject** | Skip this change |
| `v` | **View** | See full diff details |
| `s` | **Skip** | Decide later |
| `q` | **Quit** | Save progress and exit (changes NOT applied) |

## 🔄 How Decisions Work

### The Smart Decision System

When using **detailed review** (`--review`):
- **All blocks approved** → Automatically moves to "approved" ✅
- **All blocks rejected** → Automatically moves to "rejected" ❌
- **Mixed decisions** → Stays in "partial" ⚠️

When using **quick review** (`--quick`):
- Files go directly to "approved" or "rejected"

### Where Decisions Are Saved
```
figma-sync/
└── 00_REPORTS/
    └── review_decisions.json
```

Example `review_decisions.json`:
```json
{
  "approved": {
    "U001": "components/Button.tsx",
    "U002": "components/Card.tsx"
  },
  "rejected": {
    "U003": "App.tsx"
  },
  "partial": {
    "U004": {
      "file": "components/Header.tsx",
      "approved": 2,
      "rejected": 1,
      "total": 3
    }
  }
}
```

## 💡 Complete Workflow

### 1. Initial Setup
```bash
# First, run sync analysis
python3 sync.py --analyze ~/old-project ~/new-figma-export

# Navigate to results
cd figma-sync
```

### 2. Quick Review All Files
```bash
# Review everything in one go
python3 ../review.py --quick

# Takes ~30 seconds for 20 files
# Just press 'a' or 'r' for each file
```

### 3. Review Complex Files in Detail
```bash
# For files needing careful review
python3 ../review.py --review U008

# See each code block
# Accept/reject per block
```

### 4. Fix Decisions (If Needed)
```bash
# If you used --review and approved all blocks
# Run this to move them to "approved"
python3 ../review.py --fix-decisions
```

### 5. Apply All Approved Changes
```bash
# Apply everything you approved
python3 ../review.py --apply

# All changes applied with backups!
```

## 🚄 Speed Run Examples

### Example 1: Accept All UI Changes (30 seconds)
```bash
python3 review.py --quick
# Press 'a' for all component files
# Press 'r' for config files
python3 review.py --apply
# Done!
```

### Example 2: Selective Review (2 minutes)
```bash
# Quick review most files
python3 review.py --quick

# Detailed review for critical files
python3 review.py --review U001  # App.tsx
python3 review.py --review U015  # api/config.ts

# Fix decisions if needed
python3 review.py --fix-decisions

# Apply all approved
python3 review.py --apply
```

### Example 3: Fix Existing Partial Reviews
```bash
# You reviewed files but --apply says "No approved changes"
# This happens when detailed reviews are stuck in "partial"

# Step 1: Check what you have
python3 review.py --show-decisions

# Step 2: Fix the decisions file
python3 review.py --fix-decisions

# Step 3: Now apply works!
python3 review.py --apply
```

## 📊 Review Interface

### Quick Mode Display
```
📝 Reviewing: components/Button.tsx
==================================================
[U001] Button.tsx
  Changes: +25 / -10
  [a]ccept  [r]eject  [v]iew  [s]kip  [q]uit
  Choice: _
```

**After pressing 'q':**
```
⚠️  Review stopped. Changes saved but NOT applied.
ℹ️  To apply approved changes later, run:
    python3 review.py --apply

📊 Final Review Summary
==================================================
Approved: 5 files
Rejected: 2 files
Partial: 0 files
```

### Detailed Mode Display
```
==================================================
Change Block 1/3
Location: Line 45
Context: function Button({ children, variant })
Changes: +5 / -2
==================================================

- import { ButtonProps } from './types';
+ import { ButtonProps, ButtonVariant } from './types';
+ import { useButtonAnimation } from './hooks';

  export function Button({ children, variant = 'primary' }) {
+   const animation = useButtonAnimation(variant);

What would you like to do?
  [a] Accept this change
  [r] Reject this change
  [s] Skip (decide later)
  [v] View full context
  [q] Quit review

Choice: _
```

## 🔧 Troubleshooting

### Issue: "No approved changes to apply"

**Cause:** You used `--review` (detailed mode) and your approvals are stuck in "partial"

**Solution:**
```bash
# Fix the decisions file
python3 review.py --fix-decisions

# Now apply will work
python3 review.py --apply
```

### Issue: Lost track of decisions

**Solution:**
```bash
# See current state
python3 review.py --show-decisions

# Continue where you left off
python3 review.py --quick
```

### Issue: Want to change a decision

**Solution:**
```bash
# Option 1: Edit the JSON directly
nano figma-sync/00_REPORTS/review_decisions.json

# Option 2: Re-review the file
python3 review.py --review U001
```

## 📁 Output Files

### Review Decisions
Saved in `00_REPORTS/review_decisions.json`:
```json
{
  "approved": {
    "U001": "components/Button.tsx",
    "U003": "components/Card.tsx"
  },
  "rejected": {
    "U002": "App.tsx"
  },
  "partial": {
    "U004": {
      "file": "components/Header.tsx",
      "approved": 2,
      "rejected": 1,
      "total": 3,
      "timestamp": "2024-01-15T10:30:00"
    }
  }
}
```

### Auto-Generated Apply Script
Creates `apply_approved.sh`:
```bash
#!/bin/bash
echo '🚀 Applying approved changes...'
python3 sync.py --apply-update U001
python3 sync.py --apply-update U003
echo '✅ All approved changes applied!'
```

## 🎨 Color Coding

The tool uses colors for clarity:

- 🟢 **Green**: Added lines/approved changes
- 🔴 **Red**: Removed lines/rejected changes
- 🟡 **Yellow**: Warnings/skipped items
- 🔵 **Blue**: Information/context
- ⚪ **White**: Unchanged content

## ⚙️ Advanced Features

### Resume Previous Review
```bash
# Decisions are saved automatically
# If you quit, just run again to continue
python3 review.py --quick
# Previous decisions are remembered
```

### Apply Without Review Script
```bash
# If --apply doesn't work, use sync.py directly
python3 sync.py --apply-update U001
python3 sync.py --apply-update U002
```

### Reset All Decisions
```bash
# Start fresh
rm figma-sync/00_REPORTS/review_decisions.json
python3 review.py --quick
```

## 💪 Pro Tips

### 1. **Mixed Review Strategy**
```bash
# Use quick for simple files
python3 review.py --quick
# Press 'v' for complex files to switch to detailed

# Then fix and apply
python3 review.py --fix-decisions
python3 review.py --apply
```

### 2. **Batch Similar Files**
```bash
# Review all CSS files first (usually safe)
# Then components
# Then critical files like App.tsx last
```

### 3. **Safe Apply Pattern**
```bash
# Always check before applying
python3 review.py --show-decisions

# Apply to test environment first
python3 review.py --apply

# Test your app
npm run build
npm test

# If good, commit
git add -A && git commit -m "Applied Figma updates"
```

## 📈 Performance

Typical review times:
- **10 files**: ~1 minute
- **50 files**: ~5 minutes  
- **100 files**: ~10 minutes

Compare to manual review:
- **10 files manually**: ~30 minutes
- **50 files manually**: ~2 hours
- **100 files manually**: ~4 hours

**That's 20-30x faster!** 🚀

## 🎯 Best Practices

1. **Always run --fix-decisions** after detailed reviews
2. **Use --show-decisions** to verify before applying
3. **Backup before applying** (automatic with --apply)
4. **Test after applying** - Run your build/tests
5. **Commit after successful apply** - Keep git history clean

## 📝 Complete Example

### Real-World Scenario
```bash
# Monday: Receive Figma export
python3 sync.py --analyze ~/my-app ~/figma-export

# Review all changes
cd figma-sync
python3 ../review.py --quick

# Some files need detailed review
python3 ../review.py --review U045  # Complex logic file
python3 ../review.py --review U046  # API configuration

# Fix decisions (important!)
python3 ../review.py --fix-decisions

# Check what will be applied
python3 ../review.py --show-decisions

# Apply approved changes
python3 ../review.py --apply

# Test
cd ~/my-app
npm run build
npm test

# ✅ Figma changes integrated in 15 minutes!
```

---
*Script Version: 1.1 | Part of the Figma-to-Next Sync Suite*