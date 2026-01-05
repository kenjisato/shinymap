# AI Agent Workflow

Patterns for maintaining context across sessions and recovering from memory loss.

## Two Types of Documentation

| Type | Purpose | Update Frequency |
|------|---------|------------------|
| `design/<feature>.md` | Implementation plan, checklist | Stable during implementation |
| `COMMUNICATION.*.md` | Session logs, progress, recovery | Every session |

**Design documents**: Define what to build. Created before implementation. Typically unchanged during coding (update checklist checkboxes only).

**COMMUNICATION files**: Track how it's going. Updated frequently. Contains session state, progress logs, next steps, recovery instructions.

## Starting a Session Checklist

```markdown
□ 1. Check branch: `git branch`
□ 2. Pull latest: `git pull` (if shared branch)
□ 3. Find COMMUNICATION file for current branch
□ 4. Read COMMUNICATION to understand current state
□ 5. If referenced, read design document for overall plan
□ 6. Check SPEC.md if touching core architecture
□ 7. Run `make test` to verify starting state
□ 8. Ready to continue from "Next Steps" in COMMUNICATION
```

### For New Tasks

1. Check if design document exists in `design/`
2. If large feature without design doc → create one first
3. Create appropriate branch (`feature/*` or `task/*`)
4. Create COMMUNICATION file for the branch

## During a Session

- Update COMMUNICATION file after significant progress
- Checkpoint before diversions or risky changes
- One intent per commit

## Ending a Session

Update COMMUNICATION with:
- Current branch and last commit
- What was completed
- Next steps (specific actions with file paths)
- Recovery instructions for next session

Then commit:
```bash
git add COMMUNICATION.*.md
git commit -m "docs: update session progress"
```

## Checkpoint Protocol

### When to Checkpoint

- Before any diversion
- Before risky or experimental changes
- At logical stopping points
- When context is getting full

### How to Checkpoint

```bash
# Empty checkpoint commit
git commit --allow-empty -m "chore: checkpoint before <reason>"

# With uncommitted changes
git add -A
git commit -m "chore: checkpoint - WIP <description>"
```

### Checkpoint Message Format

```
chore: checkpoint before <reason>

- Current: <what you were doing>
- Next: <what to do after>
- See: COMMUNICATION.<branch>.md
```

## Recovery from Memory Loss

### When You Don't Know What's Happening

1. `git branch` - find current branch
2. `git log --oneline -5` - see recent commits
3. Look for `COMMUNICATION.*.md` files
4. Read the design document if referenced
5. Check test status: `make test`

### Recovery Checklist

```markdown
� Current branch identified
� Recent commits reviewed
� COMMUNICATION file read
� Design document understood (if applicable)
� Tests pass
� Ready to continue
```

## Diversion Handling

### Recognizing a Diversion Trigger

Stop and create a diversion branch if:
- You need to change public API (rename, reshape)
- You need to reorganize module layout
- You need to fix something that "should have been done first"

### Diversion Workflow

1. **Checkpoint current work**
   ```bash
   git commit --allow-empty -m "chore: checkpoint before diversion"
   ```

2. **Update COMMUNICATION**
   ```markdown
   ### Diversion
   - Reason: <why>
   - Branch: div/<topic>-YYYYMMDD-HHMM
   - Return to: task/<item> after merge
   ```

3. **Create diversion branch** (from appropriate base)

4. **Complete diversion** and merge

5. **Return and rebase**
   ```bash
   git switch task/<item>
   git rebase <base>
   ```

6. **Update COMMUNICATION with recovery info**

## Parking Lot Pattern

When you discover unrelated issues:

1. Don't fix them now
2. Add to COMMUNICATION under "Parking Lot":
   ```markdown
   ### Parking Lot
   - [ ] Bug: <description> (file:line)
   - [ ] Improvement: <description>
   ```
3. Continue with current task
4. Address parking lot items in separate tasks/PRs

## COMMUNICATION File Management

### One File Per Branch Context

- `COMMUNICATION.feature.<name>.md` - Feature-level
- `COMMUNICATION.task.<item>.md` - Task-level (if multi-session)
- `COMMUNICATION.div.<topic>-YYYYMMDD-HHMM.md` - Diversion

### Cleanup After Merge

After PR is merged, the COMMUNICATION file can be:
- Deleted (if all info is in commit messages/PR)
- Archived (move to `archive/` if you want history)

### Don't Commit Sensitive Info

COMMUNICATION files are committed. Don't include:
- API keys or secrets
- Personal information
- Anything that shouldn't be in git history

## Ask vs Proceed Decision

### Stop and Ask

- Changing public API behavior
- Introducing new dependency
- Altering core architectural patterns
- Adding/renaming user-facing features
- Performance work not requested

### Proceed with Stated Assumptions

- Refactors local to requested files
- Test fixes consistent with spec
- Doc updates reflecting actual behavior
- Bug fixes with clear scope
