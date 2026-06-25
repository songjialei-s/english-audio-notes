---
name: neat
description: Use when the user says "neat", "审查", "整理", "存档", or after completing a task/fixing a bug to review and update all project documentation, memory files, and CLAUDE.md to keep them accurate and clean.
---

# 洁癖.skill (Neat)

## Purpose
Review and update all project documentation, memory files, and configuration to ensure they accurately reflect the current state of the codebase. Prevents "context rot" where docs become outdated.

## When to Use
- After completing a feature or bug fix
- Before ending a session (like "saving" progress)
- When user says: /neat, 审查一下, 整理一下, 存档

## Execution Steps

### Step 1: Mechanical Inventory
List and read ALL markdown files in the project:
- `*.md` files in root and subdirectories
- `CLAUDE.md` or equivalent AI instruction files
- `docs/` directory contents
- `README.md`
- Any memory or notes files

### Step 2: Change Impact Matrix
Identify what changed in this session:
- New features added?
- APIs changed?
- Dependencies modified?
- File structure changed?
- New environment variables?

Map changes to which docs need updating.

### Step 3: Update Documentation (in order)
1. **docs/** - User-facing documentation first
2. **CLAUDE.md** - AI instruction file (project conventions, routes, constraints)
3. **README.md** - Project overview, version history
4. **Memory files** - Session notes, decisions

### Step 4: Self-Check Checklist
- [ ] New environment variables documented in all relevant files?
- [ ] API changes reflected in integration guides?
- [ ] Version number updated if applicable?
- [ ] No stale/outdated information remaining?
- [ ] Consistent naming across all docs?
- [ ] No duplicate information?

### Step 5: Output Change Summary
Provide a concise summary of what was updated:
```
📄 Updated Files:
- README.md: Added v1.3 version record
- CLAUDE.md: Updated API endpoint list
- docs/api.md: Added new /transcribe endpoint

🗑️ Removed:
- None

📝 Notes:
- All docs now reflect current project state
```

## Core Principles
1. **Merge over append** - Combine related info instead of adding new sections
2. **Delete over keep** - Remove outdated info; don't keep "just in case"
3. **Accurate over complete** - One correct fact > ten vague ones

## Output Format
Always end with a clear summary showing:
- Files updated
- Files removed (if any)
- Key changes made
- Any notes or concerns
