---
name: fantastical
description: Calendar integration with Fantastical app on macOS. Use when Claude needs to create calendar events, add todos/reminders, or open calendar to specific dates. Triggers on requests like "add to calendar", "schedule meeting", "create reminder", "add todo".
---

# Fantastical Calendar Integration

macOS-only skill for creating calendar events and todos via Fantastical.

## Creating Events

Use `scripts/add_event.sh` with natural language:

```bash
scripts/add_event.sh "Meeting with John tomorrow at 3pm"
scripts/add_event.sh "Lunch with Sarah Friday noon at Cafe Roma"
scripts/add_event.sh "Team standup every weekday at 9am"
```

Fantastical's parser understands:
- Relative dates: "tomorrow", "next Tuesday", "in 2 weeks"
- Times: "3pm", "15:00", "noon", "morning"
- Durations: "for 30 minutes", "for 2 hours"
- Locations: "at [place]"
- Calendars: "calendar Work" or "/Work"
- Recurrence: "every day", "weekly", "monthly on the 15th"

## Creating Todos

Use `scripts/add_todo.sh`:

```bash
scripts/add_todo.sh "Review PR by Friday"
scripts/add_todo.sh "Call dentist tomorrow"
```

## Opening Calendar to Date

Use `scripts/show_date.sh` with YYYY-MM-DD format:

```bash
scripts/show_date.sh 2026-01-20
```

## Limitations

- macOS only (requires Fantastical app)
- Write-only: can create events/todos but not read schedule
- Event creation uses `add immediately` - no confirmation dialog
