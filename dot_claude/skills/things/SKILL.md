---
name: things
description: Task management with Things 3 on macOS. Use when Claude needs to add todos, create projects, check today's tasks, search tasks, or manage task lists. Triggers on "add to things", "my todos", "what's on my list", "create task", "add project".
---

# Things 3 Task Management

macOS-only skill for task management via Things 3.

## Reading Tasks (CLI)

Uses `~/.cargo/bin/things3` CLI for read-only database access.

### Get Today's Tasks

```bash
scripts/get_today.sh
scripts/get_today.sh --limit 5
```

### Get Inbox Tasks

```bash
scripts/get_inbox.sh
scripts/get_inbox.sh --limit 10
```

### List Projects

```bash
scripts/get_projects.sh
```

### List Areas

```bash
scripts/get_areas.sh
```

### Search Tasks

```bash
scripts/search.sh "meeting"
scripts/search.sh "deadline" --limit 5
```

## Writing Tasks (URL Scheme)

Uses Things URL scheme via `open` command.

### Add a Todo

```bash
scripts/add_todo.sh "Buy groceries"
scripts/add_todo.sh "Review PR" --deadline tomorrow
scripts/add_todo.sh "Call John" --when today --list "Work"
scripts/add_todo.sh "Big task" --notes "Details here" --tags "urgent,work"
```

Parameters:
- `--deadline DATE` - Due date (YYYY-MM-DD or natural: tomorrow, next friday)
- `--when DATE` - Start date (today, tomorrow, evening, someday, YYYY-MM-DD)
- `--list PROJECT` - Target project name
- `--notes TEXT` - Task description/notes
- `--tags TAGS` - Comma-separated tags

### Add a Project

```bash
scripts/add_project.sh "New Website"
scripts/add_project.sh "Q1 Goals" --area "Work"
scripts/add_project.sh "Home Renovation" --deadline 2026-06-01 --notes "Budget: $10k"
```

Parameters:
- `--deadline DATE` - Project deadline
- `--area AREA` - Target area name
- `--notes TEXT` - Project description/notes
- `--tags TAGS` - Comma-separated tags

### Open Things to View

```bash
scripts/show.sh today
scripts/show.sh inbox
scripts/show.sh upcoming
scripts/show.sh anytime
scripts/show.sh someday
scripts/show.sh logbook
```

## Limitations

- macOS only (requires Things 3 app)
- Reading requires `things3` CLI installed (`cargo install things3`)
- Writing doesn't wait for Things to process - tasks appear shortly after
