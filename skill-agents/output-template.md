# Output template — lab run status

```markdown
# Lab `<run_id>` — <title>

**Stage**: `<stage>`  
**Thread**: `<thread_id|—>`  
**Hypothesis**: ...

## Model routing
| Tier | Model |
|------|-------|
| fast | ... |
| standard | ... |
| deep | ... |

## Task board
| id | role | task | tier | status |
|----|------|------|------|--------|
| ... | retrieve | query_rewrite | standard | done |

## Ready now
- `<task_id>` · **retrieve** · tier=`standard` · hint=...

## Brain decisions (recent)
- ADVANCE_TO_VERIFY — mini-verify passed on subset

## Blockers
- _(none)_ / Accept REJECT: empty registry
```
