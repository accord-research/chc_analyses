# Issuance skill

The process for producing one outlook, versioned with the code it drives.

| file | what it is |
|---|---|
| `SKILL.md` | The five steps of an issuance, the recurring defect classes, and the standing facts |
| `templates/report_template.md` | Section-by-section outline, naming which output file each number comes from |
| `templates/audit_prompts.md` | The scientific/code audit and the stylistic audit, both mandatory |

To use it with Claude Code, copy this directory to `ACCORD/.claude/skills/iod-outlook/`
so it is discovered as a skill. It is kept here as well because the process and the
pipeline change together, and a process description that drifts from the code it
describes is worse than none.

Both audits are mandatory. Each has caught errors that would otherwise have been
published, including numbers that were wrong in a report already drafted.
