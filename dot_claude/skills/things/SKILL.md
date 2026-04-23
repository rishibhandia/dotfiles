---
name: things
description: Task management with Things 3 on macOS. Create todos with checklists, manage projects, check today's tasks, search, and navigate views. Triggers on "add to things", "my todos", "what's on my list", "create task", "add project".
---

# Things 3 Task Management

macOS-only skill for managing tasks in Things 3. Reading uses AppleScript; writing uses the Things URL scheme.

## Creating Tasks

```bash
scripts/add_todo.sh "Buy groceries"
scripts/add_todo.sh "Review PR" --deadline tomorrow
scripts/add_todo.sh "Call John" --when today --list "Work"
scripts/add_todo.sh "Big task" --notes "Details here" --tags "urgent,work"
scripts/add_todo.sh "Sprint task" --list "App Redesign" --heading "Sprint 1"
scripts/add_todo.sh "Grocery run" --checklist "Milk,Eggs,Bread" --when today
```

| Parameter | Description |
|-----------|-------------|
| `--when DATE` | Start date: `today`, `tomorrow`, `evening`, `someday`, or `YYYY-MM-DD` |
| `--deadline DATE` | Due date: `YYYY-MM-DD` or natural language (`tomorrow`, `next friday`) |
| `--list PROJECT` | Target project name |
| `--heading NAME` | Place under a heading within the target project |
| `--notes TEXT` | Task description |
| `--tags TAGS` | Comma-separated tag names |
| `--checklist ITEMS` | Comma-separated checklist items (sub-tasks) |

## Creating Projects

```bash
scripts/add_project.sh "New Website"
scripts/add_project.sh "Q1 Goals" --area "Work"
scripts/add_project.sh "Home Renovation" --deadline 2026-06-01 --notes "Budget: $10k"
scripts/add_project.sh "Q2 Planning" --when 2026-05-01
```

| Parameter | Description |
|-----------|-------------|
| `--when DATE` | Start date: `today`, `tomorrow`, `evening`, `someday`, or `YYYY-MM-DD` |
| `--deadline DATE` | Project deadline (`YYYY-MM-DD`) |
| `--area AREA` | Target area name |
| `--notes TEXT` | Project description |
| `--tags TAGS` | Comma-separated tag names |

## Reading Tasks

Uses AppleScript — no external dependencies. Output format:

```
- [ ] Task Name  |  Project: X  |  Due: MM/DD/YYYY  |  Tags: tag1, tag2
```

Fields are omitted when not set.

### Today's Tasks

```bash
scripts/get_today.sh
scripts/get_today.sh --limit 5
```

### Inbox

```bash
scripts/get_inbox.sh
scripts/get_inbox.sh --limit 10
```

### Search

```bash
scripts/search.sh "meeting"
scripts/search.sh "deadline" --limit 5
scripts/search.sh "old task" --all          # include completed & cancelled
scripts/search.sh "report" --all --limit 10
```

| Parameter | Description |
|-----------|-------------|
| `--limit N` | Return at most N results |
| `--all` | Include completed and cancelled tasks (default: open only) |

### List Projects

```bash
scripts/get_projects.sh
```

### List Areas

```bash
scripts/get_areas.sh
```

## Navigation

```bash
scripts/show.sh today
scripts/show.sh inbox
scripts/show.sh tomorrow
scripts/show.sh upcoming
scripts/show.sh anytime
scripts/show.sh someday
scripts/show.sh logbook
scripts/show.sh deadlines
scripts/show.sh repeating
scripts/show.sh all-projects
scripts/show.sh logged-projects
```

## Limitations

- macOS only (requires Things 3 app)
- Things 3 will auto-launch if not running when read scripts are called
- Writing via URL scheme doesn't wait for Things to process — tasks appear shortly after
