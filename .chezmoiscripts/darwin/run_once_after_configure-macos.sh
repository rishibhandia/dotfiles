#!/bin/bash
# Configure macOS system preferences
# This runs once after dotfiles are applied

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { printf "${BLUE}[INFO]${NC} %s\n" "$1"; }
success() { printf "${GREEN}[OK]${NC} %s\n" "$1"; }

info "Configuring macOS preferences..."

# Close System Preferences to prevent conflicts
osascript -e 'tell application "System Preferences" to quit' 2>/dev/null || true

# =============================================================================
# General UI/UX
# =============================================================================

# Expand save panel by default
defaults write NSGlobalDomain NSNavPanelExpandedStateForSaveMode -bool true
defaults write NSGlobalDomain NSNavPanelExpandedStateForSaveMode2 -bool true

# Expand print panel by default
defaults write NSGlobalDomain PMPrintingExpandedStateForPrint -bool true
defaults write NSGlobalDomain PMPrintingExpandedStateForPrint2 -bool true

# Save to disk (not to iCloud) by default
defaults write NSGlobalDomain NSDocumentSaveNewDocumentsToCloud -bool false

# Disable the "Are you sure you want to open this application?" dialog
defaults write com.apple.LaunchServices LSQuarantine -bool false

# =============================================================================
# Keyboard
# =============================================================================

# Enable full keyboard access for all controls (Tab in dialogs)
defaults write NSGlobalDomain AppleKeyboardUIMode -int 3

# Disable press-and-hold for keys in favor of key repeat
defaults write NSGlobalDomain ApplePressAndHoldEnabled -bool false

# Set a fast keyboard repeat rate
defaults write NSGlobalDomain KeyRepeat -int 2
defaults write NSGlobalDomain InitialKeyRepeat -int 15

# =============================================================================
# Trackpad
# =============================================================================

# Enable tap to click
defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad Clicking -bool true
defaults -currentHost write NSGlobalDomain com.apple.mouse.tapBehavior -int 1

# =============================================================================
# Finder
# =============================================================================

# Show hidden files by default
defaults write com.apple.finder AppleShowAllFiles -bool true

# Show all filename extensions
defaults write NSGlobalDomain AppleShowAllExtensions -bool true

# Show status bar
defaults write com.apple.finder ShowStatusBar -bool true

# Show path bar
defaults write com.apple.finder ShowPathbar -bool true

# Keep folders on top when sorting by name
defaults write com.apple.finder _FXSortFoldersFirst -bool true

# When performing a search, search the current folder by default
defaults write com.apple.finder FXDefaultSearchScope -string "SCcf"

# Disable the warning when changing a file extension
defaults write com.apple.finder FXEnableExtensionChangeWarning -bool false

# Avoid creating .DS_Store files on network or USB volumes
defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true
defaults write com.apple.desktopservices DSDontWriteUSBStores -bool true

# Use list view in all Finder windows by default
defaults write com.apple.finder FXPreferredViewStyle -string "Nlsv"

# =============================================================================
# Dock
# =============================================================================

# Set the icon size of Dock items
defaults write com.apple.dock tilesize -int 48

# Minimize windows into their application's icon
defaults write com.apple.dock minimize-to-application -bool true

# Show indicator lights for open applications
defaults write com.apple.dock show-process-indicators -bool true

# Don't automatically rearrange Spaces based on most recent use
defaults write com.apple.dock mru-spaces -bool false

# Auto-hide the Dock
defaults write com.apple.dock autohide -bool true

# Remove the auto-hiding Dock delay
defaults write com.apple.dock autohide-delay -float 0

# =============================================================================
# Safari
# =============================================================================

# Enable Safari's debug menu
defaults write com.apple.Safari IncludeInternalDebugMenu -bool true

# Enable the Develop menu and the Web Inspector
defaults write com.apple.Safari IncludeDevelopMenu -bool true
defaults write com.apple.Safari WebKitDeveloperExtrasEnabledPreferenceKey -bool true

# =============================================================================
# Terminal
# =============================================================================

# Only use UTF-8 in Terminal.app
defaults write com.apple.terminal StringEncodings -array 4

# =============================================================================
# Activity Monitor
# =============================================================================

# Show the main window when launching Activity Monitor
defaults write com.apple.ActivityMonitor OpenMainWindow -bool true

# Show all processes in Activity Monitor
defaults write com.apple.ActivityMonitor ShowCategory -int 0

# =============================================================================
# Screenshots
# =============================================================================

# Save screenshots to ~/Pictures/Screenshots
mkdir -p "${HOME}/Pictures/Screenshots"
defaults write com.apple.screencapture location -string "${HOME}/Pictures/Screenshots"

# Save screenshots in PNG format
defaults write com.apple.screencapture type -string "png"

# Disable shadow in screenshots
defaults write com.apple.screencapture disable-shadow -bool true

# =============================================================================
# Kill affected applications
# =============================================================================

info "Restarting affected applications..."
for app in "Dock" "Finder" "SystemUIServer"; do
    killall "${app}" &>/dev/null || true
done

success "macOS preferences configured. Some changes require a logout/restart."
