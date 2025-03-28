# -*-mode:bash-*- vim:ft=bash
#
# ~/.config/zsh/completion.zsh
#
# ____ ___  __  __ ____  _     _____ _____ ___ ___  _   _ 
#  / ___/ _ \|  \/  |  _ \| |   | ____|_   _|_ _/ _ \| \ | |
# | |  | | | | |\/| | |_) | |   |  _|   | |  | | | | |  \| |
# | |__| |_| | |  | |  __/| |___| |___  | |  | | |_| | |\  |
#  \____\___/|_|  |_|_|   |_____|_____| |_| |___\___/|_| \_|
#

# +---------+
# | General |
# +---------+
#
#

#If debug flag enabled (ZSH_DEBUG = 1), will print file path and name when sourced
[ ! -z "$ZSH_DEBUG" ] && printf "Sourcing file %s (path: %s)\n" "${(%):-%N}" "${(%):-%x}"


#adding Homebrew's completionns in zsh
if type brew &>/dev/null
then
  FPATH="$(brew --prefix)/share/zsh/site-functions:${FPATH}"
fi

# Do menu-driven completion.
zstyle ':completion:*' menu select

# Color completion for some things.
# http://linuxshellaccount.blogspot.com/2008/12/color-completion-using-zsh-modules-on.html
zstyle ':completion:*' list-colors ${(s.:.)LS_COLORS}

# formatting and messages
# http://www.masterzen.fr/2009/04/19/in-love-with-zsh-part-one/
zstyle ':completion:*' verbose yes
zstyle ':completion:*:descriptions' format "$fg[yellow]%B--- %d%b"
zstyle ':completion:*:messages' format '%d'
zstyle ':completion:*:warnings' format "$fg[red]No matches for:$reset_color %d"
zstyle ':completion:*:corrections' format '%B%d (errors: %e)%b'
zstyle ':completion:*' group-name ''

# Add completion for uv and uvx Python package manager
if command -v uv &>/dev/null; then
  eval "$(uv generate-shell-completion zsh)"
fi

if command -v uvx &>/dev/null; then
  eval "$(uvx --generate-shell-completion zsh)"
fi
