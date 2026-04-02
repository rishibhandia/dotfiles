#!/bin/bash
# Claude Code statusline
# Format: user@host dir [git_branch ●●●] [ctx:N%] [Model] [rl:N%]

input=$(cat)
cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd')

# --- Context usage (color-coded) ---
context_info=""
current=$(echo "$input" | jq '(.context_window.current_usage.input_tokens // 0) + (.context_window.current_usage.cache_creation_input_tokens // 0) + (.context_window.current_usage.cache_read_input_tokens // 0)')
size=$(echo "$input" | jq '.context_window.context_window_size // 0')
if [ "$size" != "null" ] && [ "$size" -gt 0 ] 2>/dev/null; then
  pct=$((current * 100 / size))
  if   [ "$pct" -lt 50 ]; then color=$(printf '\033[32m')   # green
  elif [ "$pct" -lt 80 ]; then color=$(printf '\033[33m')   # yellow
  else                          color=$(printf '\033[31m')   # red
  fi
  context_info=$(printf " %s[ctx:%d%%]" "$color" "$pct")
fi

# --- Model ---
model_info=""
model=$(echo "$input" | jq -r '.model.display_name // .model.id // ""')
if [ -n "$model" ] && [ "$model" != "null" ]; then
  model_info=$(printf " \033[36m[%s]" "$model")
fi

# --- 5-hour rate limit (Max/Pro) ---
rl_info=""
rl_pct=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // ""')
if [ -n "$rl_pct" ] && [ "$rl_pct" != "null" ]; then
  rl_int=$(printf "%.0f" "$rl_pct")
  if   [ "$rl_int" -lt 50 ]; then rl_color=$(printf '\033[32m')   # green
  elif [ "$rl_int" -lt 80 ]; then rl_color=$(printf '\033[33m')   # yellow
  else                             rl_color=$(printf '\033[31m')   # red
  fi
  rl_info=$(printf " %s[rl:%d%%]" "$rl_color" "$rl_int")
fi

# --- User / host / dir ---
username=$(whoami)
hostname=$(hostname -s)
dir_display=$(basename "$cwd")

# --- Git info ---
git_info=""
if git -C "$cwd" rev-parse --git-dir > /dev/null 2>&1; then
  branch=$(git -C "$cwd" branch --show-current 2>/dev/null || echo "detached")
  git_status=$(git -C "$cwd" --no-optional-locks status --porcelain 2>/dev/null)
  staged="" unstaged="" untracked=""
  echo "$git_status" | grep -q '^[MADRCU]' && staged=$(printf '\033[32m●')
  echo "$git_status" | grep -q '^.[MD]'    && unstaged=$(printf '\033[33m●')
  echo "$git_status" | grep -q '^??'       && untracked=$(printf '\033[31m●')
  git_info=$(printf " [\033[32m%s%s%s%s\033[34m]" "$branch" "$staged" "$unstaged" "$untracked")
fi

printf '\033[37m%s@%s %s%s%s%s%s\033[0m' \
  "$username" "$hostname" "$dir_display" \
  "$git_info" "$context_info" "$model_info" "$rl_info"
