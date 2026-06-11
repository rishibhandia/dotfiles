" enables syntax highlighting
syntax on

" Better colors
set termguicolors

" number of spaces in a <Tab>
set tabstop=4
set softtabstop=4
set expandtab

" enable autoindents
set smartindent

" number of spaces used for autoindents
set shiftwidth=4

" adds line numbers
set number

" columns used for the line number
set numberwidth=4

" highlights the matched text pattern when searching
set incsearch
set nohlsearch

" open splits intuitively
set splitbelow
set splitright

" navigate buffers without losing unsaved work
set hidden

" start scrolling when 8 lines from top or bottom
set scrolloff=8

" Save undo history
set undofile

" Enable mouse support
set mouse=a

" case insensitive search unless capital letters are used
set ignorecase
set smartcase

" Auto-install vim-plug if missing (fallback for when run_once script hasn't run)
" stdpath('config') = ~/.config/nvim (Unix) or $LOCALAPPDATA/nvim (Windows);
" unlike $XDG_CONFIG_HOME it is always set, even for GUI-launched nvim
let s:plug_path = stdpath('config') . '/autoload/plug.vim'
if !filereadable(s:plug_path)
  silent execute '!curl -fLo "' . s:plug_path . '" --create-dirs
    \ https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim'
  autocmd VimEnter * PlugInstall --sync | source $MYVIMRC
endif

" Plugins
call plug#begin(stdpath('config') . '/plugged')

Plug 'catppuccin/nvim', { 'as': 'catppuccin' }
Plug 'nvim-lua/plenary.nvim'
Plug 'nvim-telescope/telescope.nvim'
Plug 'sudormrfbin/cheatsheet.nvim'

call plug#end()

" Color scheme
colorscheme catppuccin-macchiato

" Cheatsheet - <leader>? to open
nnoremap <leader>? <cmd>Cheatsheet<CR>

" Telescope
nnoremap <leader>ff <cmd>Telescope find_files<CR>
nnoremap <leader>fg <cmd>Telescope live_grep<CR>
