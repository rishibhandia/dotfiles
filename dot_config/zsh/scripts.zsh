#!/usr/bin/env zsh


[ ! -z "$ZSH_DEBUG" ] && printf "Sourcing file %s (path: %s)\n" "${(%):-%N}" "${(%):-%x}"

screenres() {
    system_profiler SPDisplaysDataType | grep -A2 "Resolution:" | grep "Retina\|Resolution:" | sed -n "${1:-1}p" | awk '{print $2"x"$4}'
}
