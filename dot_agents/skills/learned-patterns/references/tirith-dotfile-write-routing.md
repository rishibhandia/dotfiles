# Tirith blocks dotfile writes from Bash, keep it that way

**Extracted:** 2026-09-18
**Context:** Claude Code with the tirith PreToolUse hook on Bash (installed by the dotfiles cli-tools script)

## Problem
A compound Bash command that edits project files and then writes under `~/.claude` with a heredoc or redirection is refused whole: "Tirith: [HIGH] Dotfile overwrite detected". The project edits chained before it do not run either, so it can look like an unrelated failure. The refusal is correct. A shell command reaching into dotfiles as a side effect of other work is the pattern the hook exists to catch.

## Solution
Do not work around the hook. Never disable it, never edit its configuration, never add exclusions, never encode or split a command to slip past it, and never ask the user to run such a command with `!` on your behalf. Keep the two kinds of write apart instead: project files in Bash, and the small set of dotfile writes the harness expects (a memory note in the project memory folder, a skill file the user asked for) through the Write or Edit tool, which the harness governs with its own permission rules and its own hook that blocks arbitrary documents. Anything outside those expected locations, or anything under `~/.ssh`, `~/.config` or shell startup files, is the user's to change: stop and ask. Related refusals from the same hook are also to be respected as written: `curl ... | python3` (write the response to a file and read the file), and commands containing Unicode confusables (put such text in a file via the Write tool).

## When to Use
Any time a Bash command would create or overwrite a file under a dotfile path, or a compound command fails with a tirith message that does not match the part you were focused on. Read the message, split the command, and keep the guard.
