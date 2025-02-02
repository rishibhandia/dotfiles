# -*-mode:bash-*- vim:ft=bash
#
# ~/.config/zsh/scripts.zsh
#
#If debug flag enabled (ZSH_DEBUG = 1), will print file path and name when sourced
[ ! -z "$ZSH_DEBUG" ] && printf "Sourcing file %s (path: %s)\n" "${(%):-%N}" "${(%):-%x}"

screenres() {
    system_profiler SPDisplaysDataType | grep -A2 "Resolution:" | grep "Retina\|Resolution:" | sed -n "${1:-1}p" | awk '{print $2"x"$4}'
}



shell_type="$(ps -p $$ -ocomm=)"

extract() {
    local verbose=false
    local target_dir=""
    local error_log=""
    local exit_code=0
    local here_flag=false
    local OPTIND=1  # Important for bash compatibility with getopts

    # Function to show help
    show_help() {
        cat << 'EOF'
Extract - Universal archive extraction utility

Usage: extract [options] <archive1> [archive2 ...]

Options:
    -h, --help     Show this help message
    -v, --verbose  Enable verbose output
    -d DIR         Extract into specific directory
    --here         Extract in current directory

Supported formats:
    .tar.bz2, .tbz2    tar+bzip2 archives
    .tar.gz, .tgz      tar+gzip archives
    .tar.xz, .txz      tar+xz archives
    .tar               tar archives
    .bz2               bzip2 compressed files
    .gz                gzip compressed files
    .zip, .epub, .cbz  zip archives
    .7z, .apk, .dmg    7zip archives
    .rar, .cbr         rar archives
    .xz                xz compressed files
    .iso               disk images

Examples:
    extract archive.zip                  # Extract to 'archive' directory
    extract --here archive.tar.gz        # Extract to current directory
    extract -d output_dir archive.zip    # Extract to specific directory
    extract -v multiple.zip files.rar    # Extract multiple archives verbosely
EOF
    }

    # Function to check if a command exists - compatible with both shells
    command_exists() {
        command -v "$1" >/dev/null 2>&1
    }

    # Function to log errors - compatible with both shells
    log_error() {
        printf "ERROR: %s\n" "$1" >&2
        error_log="${error_log}ERROR: $1\n"
        exit_code=1
    }

    # Function to get clean directory name - compatible with both shells
    get_extract_dir() {
        local archive="$1"
        local basename
        local dirname

        # Handle basename differently for bash/zsh
        if [ "$shell_type" = "bash" ]; then
            basename=$(basename "$archive")
        else
            basename="${archive:t}"
        fi

        # Remove common archive extensions
        dirname="$basename"
        for ext in ".tar.bz2" ".tar.gz" ".tar.xz" ".tbz2" ".tgz" ".txz" ".tar" \
                  ".bz2" ".gz" ".zip" ".7z" ".rar" ".xz" ".epub" ".cbz" ".cbr" \
                  ".dmg" ".apk" ".iso"; do
            dirname="${dirname%$ext}"
        done
        printf "%s" "$dirname"
    }

    # Parse options - compatible with both shells
    while [ $# -gt 0 ]; do
        case "$1" in
            --help)
                show_help
                return 0
                ;;
            -h)
                if [ "$2" = "--help" ] || [ $# -eq 1 ]; then
                    show_help
                    return 0
                else
                    here_flag=true
                fi
                shift
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            -d)
                if [ -n "$2" ]; then
                    target_dir="$2"
                    shift 2
                else
                    log_error "No directory specified for -d"
                    return 1
                fi
                ;;
            --here)
                here_flag=true
                shift
                ;;
            -*)
                log_error "Unknown option: $1"
                show_help
                return 1
                ;;
            *)
                break
                ;;
        esac
    done

    # Check if any archives were specified
    if [ $# -eq 0 ]; then
        show_help
        return 1
    fi

    # Process each archive
    for archive in "$@"; do
        if [ ! -f "$archive" ]; then
            log_error "'$archive' - file does not exist"
            continue
        fi

        # Get absolute path of archive - compatible with both shells
        local archive_path
        archive_path="$(cd "$(dirname "$archive")" && pwd)/$(basename "$archive")"

        # Determine and create extraction directory
        local current_target_dir="$target_dir"
        if [ "$here_flag" = true ]; then
            current_target_dir="."
        elif [ -z "$current_target_dir" ]; then
            current_target_dir="$(get_extract_dir "$archive")"
            mkdir -p "$current_target_dir" || { log_error "Failed to create directory: $current_target_dir"; continue; }
        fi

        # Save and change directory - compatible with both shells
        local original_dir
        original_dir="$(pwd)"
        if [ "$current_target_dir" != "." ]; then
            cd "$current_target_dir" || { log_error "Failed to change to directory: $current_target_dir"; continue; }
        fi

        [ "$verbose" = true ] && printf "Extracting '%s' to '%s'\n" "$archive" "$(pwd)"

        # Convert to lowercase for case-insensitive matching - compatible with both shells
        local archive_lower
        archive_lower="$(printf "%s" "$archive_path" | tr '[:upper:]' '[:lower:]')"

        # Extract based on file extension
        case "$archive_lower" in
            *.tar.bz2|*.tbz2)
                if command_exists tar; then
                    tar xjf "$archive_path" || log_error "Failed to extract tar.bz2: $archive"
                else
                    log_error "tar is not installed. Install tar first."
                fi
                ;;
            *.tar.gz|*.tgz)
                if command_exists tar; then
                    tar xzf "$archive_path" || log_error "Failed to extract tar.gz: $archive"
                else
                    log_error "tar is not installed. Try: brew install gnu-tar"
                fi
                ;;
            *.tar.xz|*.txz)
                if command_exists tar; then
                    tar xJf "$archive_path" || log_error "Failed to extract tar.xz: $archive"
                else
                    log_error "tar is not installed. Try: brew install gnu-tar"
                fi
                ;;
            *.tar)
                if command_exists tar; then
                    tar xf "$archive_path" || log_error "Failed to extract tar: $archive"
                else
                    log_error "tar is not installed. Try: brew install gnu-tar"
                fi
                ;;
            *.bz2)
                if command_exists bzip2; then
                    bzip2 -dk "$archive_path" || log_error "Failed to extract bz2: $archive"
                else
                    log_error "bzip2 is not installed. Try: brew install bzip2"
                fi
                ;;
            *.gz)
                if command_exists gunzip; then
                    gunzip -k "$archive_path" || log_error "Failed to extract gz: $archive"
                else
                    log_error "gzip is not installed. Try: brew install gzip"
                fi
                ;;
            *.zip|*.epub|*.cbz)
                if command_exists unzip; then
                    $verbose && local v_flag="-v" || local v_flag="-q"
                    unzip $v_flag "$archive_path" || log_error "Failed to extract zip: $archive"
                else
                    log_error "unzip is not installed. Try: brew install unzip"
                fi
                ;;
            *.7z|*.apk|*.dmg|*.iso)
                if command_exists 7z; then
                    7z x "$archive_path" || log_error "Failed to extract 7z: $archive"
                else
                    log_error "7zip is not installed. Try: brew install p7zip"
                fi
                ;;
            *.rar|*.cbr)
                if command_exists unrar; then
                    unrar x -ad "$archive_path" || log_error "Failed to extract rar: $archive"
                elif command_exists unar; then
                    unar "$archive_path" || log_error "Failed to extract rar: $archive"
                else
                    log_error "Neither unrar nor unar is installed. Try: brew install rar or brew install unar"
                fi
                ;;
            *.xz)
                if command_exists unxz; then
                    unxz -k "$archive_path" || log_error "Failed to extract xz: $archive"
                else
                    log_error "xz is not installed. Try: brew install xz"
                fi
                ;;
            *.lzma)
                if command_exists unlzma; then
                    unlzma -k "$archive_path" || log_error "Failed to extract lzma: $archive"
                else
                    log_error "lzma is not installed. Try: brew install xz"
                fi
                ;;
            *.Z)
                if command_exists uncompress; then
                    uncompress -k "$archive_path" || log_error "Failed to extract Z: $archive"
                else
                    log_error "compress is not installed. Try: brew install compress"
                fi
                ;;
            *.cpio)
                if command_exists cpio; then
                    cpio -id < "$archive_path" || log_error "Failed to extract cpio: $archive"
                else
                    log_error "cpio is not installed. Try: brew install cpio"
                fi
                ;;
            *.cab|*.exe)
                if command_exists cabextract; then
                    cabextract "$archive_path" || log_error "Failed to extract cabinet: $archive"
                else
                    log_error "cabextract is not installed. Try: brew install cabextract"
                fi
                ;;
            *.zpaq)
                if command_exists zpaq; then
                    zpaq x "$archive_path" || log_error "Failed to extract zpaq: $archive"
                else
                    log_error "zpaq is not installed. Try: brew install zpaq"
                fi
                ;;
            *)
                log_error "'$archive' - unknown archive method"
                ;;
        esac
		# Return to original directory - compatible with both shells
        cd "$original_dir" || log_error "Failed to return to original directory"
    done

   # Display any errors that occurred - compatible with both shells
    if [ -n "$error_log" ]; then
        printf "\nThe following errors occurred:\n%b" "$error_log"
    fi

    return $exit_code
}

# Create alias - compatible with both shells
alias x='extract'


# Searches history for a string, or lists all history.
# Syntax: `historysearch <string>`
function history_search() {
    if [ -z "$1" ]; then
        history
    else
        history | grep "$1"
    fi
}

# Searches session history for a string, or lists all session history.
# Syntax: `history_session_search <string>`
function history_session_search() {
    prefix=$(date +"$HISTTIMEFORMAT")
    offset=$((8 + ${#prefix}))
    comm -23 <(history | cut -c ${offset}-) "${HISTFILE:-'~/.bash_history'}" | grep "$1"
}

# Creates a directory and changes to it.
# Syntax: `mkcd <directory>`
function mkcd() {
    if [ -z "$1" ]; then
        echo "Usage: mkcd <path>"
        echo "Help: mkcd creates a directory if it doesn't exist, then changes to it."
        return 0
    fi

    mkdir -p -- "$@" && cd -P -- "$_" || exit;
}
alias take=mkcd

# Repeats a command a set number of times.
# Syntax: `repeat <count> <command>`
function repeat() {
    if [ -z "$1" ] || [ "$#" -lt 2 ]; then
        echo "Usage: repeat <count> <command> ..."
        echo "Help: repeat runs a command x number of times."
        return $#
    fi

    local i max
    max=$1; shift;
    for ((i=1; i <= max ; i++)); do
        eval "$@";
    done
}
alias r=repeat

# Sysadmin
# -----------------------------------------------------------------------------

# Keeps all apps and packages up to date.
# Syntax: `update [all]`
function update() {
    if command -v softwarepudate &> /dev/null; then
        echo 'Checking for system updates...'
        softwareupdate -l -i -a
    fi

    if command -v brew &> /dev/null; then
        echo 'Updating packages with Homebrew/Linuxbrew...'
        brew update
        brew upgrade
        brew cask update
        brew cleanup
    fi

    if [[ "$1" == 'all' ]]; then
        if command -v mas &> /dev/null; then
            echo 'Updating App Store applications...'
            mas upgrade
        fi
    fi

    if ! [[ "$OSTYPE" =~ ^darwin ]]; then
        if command -v apt &> /dev/null; then
            echo 'Updating packages with apt...'
            apt update
            apt full-upgrade
            apt autoremove
            apt clean
            apt autoclean
        fi

        if command -v apt-get &> /dev/null; then
            echo 'Updating packages with apt-get...'
            apt-get update
            apt-get upgrade
            apt-get dist-upgrade
        fi
    fi

    if command -v npm &> /dev/null; then
        echo 'Updating Node.js packages with npm...'
        which npm
        npm update -g
    fi

    if command -v npm &> /dev/null; then
        echo 'Updating Ruby gems...'
        which gem
        gem update --system
        gem update
        gem cleanup
    fi
}


# Applications
# -----------------------------------------------------------------------------

# Opens file/URL in Microsoft Edge.
# Syntax: `microsoft-edge <url>`
if [[ "$OSTYPE" =~ ^(cygwin|mingw|msys) ]]; then
    function microsoft-edge() {
        start microsoft-edge:"$1"
    }
fi


# LLM functions
#------------------------------------------------------------------------------
function q {
    # String literal needs to be properly escaped in zsh
    url="$1"
    question="$2"
    content=$(curl -s "https://r.jina.ai/$url")
    system="You are a helpful assistant that can answer questions about the content.
Reply concisely, in a few sentences.
The content:
${content}"
    llm prompt "${question}" -s "${system}"
}

function qv {
    url="$1"
    question="$2"
    
    if ! command -v yt-dlp >/dev/null 2>&1; then
        echo "yt-dlp is required but not found"
        return 1
    fi
    
    subtitle_url=$(yt-dlp -q --skip-download --convert-subs srt --write-sub \
                  --sub-langs "en" --write-auto-sub --print "requested_subtitles.en.url" "$url")
    
    content=$(curl -s "$subtitle_url" | \
              sed '/^$/d' | \
              grep -v '^[0-9]*$' | \
              grep -v '\-->' | \
              sed 's/<[^>]*>//g' | \
              tr '\n' ' ')
              
    system="You are a helpful assistant that can answer questions about YouTube videos.
Reply concisely, in a few sentences.
The content:
${content}"
    
    llm prompt "${question}" -s "${system}"
}


function gcm {
  # Check dependencies
  command -v git >/dev/null 2>&1 || {
    echo "Error: git not found"
    return 1
  }
  
  command -v llm >/dev/null 2>&1 || {
    echo "Error: llm not found"
    return 1
  }

  # Check repository status
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
    echo "Error: Not in a git repository"
    return 1
  }

  git diff --cached --quiet && {
    echo "Error: No changes staged for commit"
    return 1
  }

  # Save IFS
  OLD_IFS="$IFS"
  IFS=$'\n'

  echo "Generating AI-powered commit message..."
  commit_message=$(git diff --cached | llm "Generate a concise, descriptive commit message")
  
  [ -z "$commit_message" ] && {
    echo "Error: Failed to generate commit message"
    IFS="$OLD_IFS"
    return 1
  }

  while true; do
    printf "\nProposed commit message:\n%s\n" "$commit_message"
    printf "Do you want to (a)ccept, (e)dit, (r)egenerate, or (c)ancel? "
    read -r choice
    
    case "${choice:0:1}" in
      [aA])
        if git commit -m "$commit_message"; then
          echo "Changes committed successfully!"
          IFS="$OLD_IFS"
          return 0
        else
          echo "Error: Commit failed"
          IFS="$OLD_IFS"
          return 1
        fi
        ;;
      [eE])
        printf "Enter your commit message: "
        read -r commit_message
        if [ -n "$commit_message" ] && git commit -m "$commit_message"; then
          echo "Changes committed successfully!"
          IFS="$OLD_IFS"
          return 0
        else
          echo "Error: Commit failed"
          IFS="$OLD_IFS"
          return 1
        fi
        ;;
      [rR])
        echo "Regenerating commit message..."
        commit_message=$(git diff --cached | llm "Generate a concise, descriptive commit message")
        [ -z "$commit_message" ] && {
          echo "Error: Failed to regenerate commit message"
          IFS="$OLD_IFS"
          return 1
        }
        ;;
      [cC])
        echo "Commit cancelled."
        IFS="$OLD_IFS"
        return 1
        ;;
      *)
        echo "Invalid choice. Please try again."
        ;;
    esac
  done
}
# Development
# -----------------------------------------------------------------------------

# Calls Python's pip3 at the global level.
if command -v pip3 > /dev/null; then
    function gpip3() {
        PIP_REQUIRE_VIRTUALENV="0" pip3 "$@"
    }
fi


# Varia
# -----------------------------------------------------------------------------

# Copies contents to the clipboard.
function cb() {
    if [ -z "$1" ]; then
        echo "Usage: cb <path>"
        echo "Help: cb copies a file contents to the clipboard."
        return 0
    fi

    if command -v pbcopy > /dev/null; then
        pbcopy < "$1"
    elif command -v xclip > /dev/null; then
        xclip -selection clipboard < "$1"
    elif command -v xsel > /dev/null; then
        xsel -ib < "$1"
    elif command -v clipboard > /dev/null; then # node.js clipboard-cli
        clipboard < "$1"
    elif command -v clip > /dev/null; then
        clip < "$1"
    elif command -v powershell > /dev/null; then
        powershell -NoProfile -Command "Set-Clipboard"
    fi
}


#Syncing with Katsumi Lab Google Drive 
#-------------------------------------------------------------------------------
function sync_tise2() {
    target_dir="/Users/rishi/Documents/Scientific Data/NYU_Lab"
    if [ "$PWD" != "$target_dir" ]; then
        echo "Changing directory to NYU_Lab..."
        cd "$target_dir"
    fi
    rclone copy --drive-shared-with-me -v -M --check-first NYU_Katsumi_Lab:'Katsumi lab'/'Astrella and OPA'/Data/TiSe2_TPOP_2025/ ./TiSe2_TPOP_2025
}