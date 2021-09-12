if has('nvim')
    let $VIMHOME=stdpath('data')
elseif has('win32') || has ('win64')
    let $VIMHOME=$HOME . '/vimfiles'
else
    let $VIMHOME=$HOME . '/.vim'
endif

if filereadable($VIMHOME . '/local/before.vim')
    exec 'source ' . $VIMHOME . '/local/before.vim'
endif

" vim plugs{{{
call plug#begin($VIMHOME . '/plugged')
Plug 'tpope/vim-surround'
if !exists('g:vscode')
    Plug 'vim-airline/vim-airline'
    Plug 'vim-airline/vim-airline-themes'
    " Common Tools
    Plug 'scrooloose/nerdtree', { 'on': 'NERDTreeToggle' }
    Plug 'mbbill/undotree', { 'on': 'UndotreeToggle' }
    Plug 'yegappan/mru'
    Plug 'mhinz/vim-startify'
    Plug 'Yggdroot/indentLine'
    Plug 'skywind3000/asyncrun.vim'
    Plug 'airblade/vim-gitgutter'
    " Color Scheme
    Plug 'lifepillar/vim-solarized8'
    " Movement & Key Bindings
    Plug 'tpope/vim-commentary'
    " Syntax & Highlight
    Plug 'dense-analysis/ale'
    Plug 'sheerun/vim-polyglot'
    Plug 'ap/vim-css-color', { 'for': ['html', 'css', 'vue'] }
    " Snippets
    if has('python3')
        Plug 'honza/vim-snippets'
        Plug 'SirVer/ultisnips'
    endif
    if filereadable($VIMHOME . '/local/plugins.vim')
        exec 'source ' . $VIMHOME . '/local/plugins.vim'
    endif
endif
call plug#end()
"}}}
" Set backup files{{{
let $VIMTEMP=$VIMHOME . '/.vimtemp'
if !isdirectory($VIMTEMP)
    call mkdir($VIMTEMP, "p")
endif

set undofile
set swapfile
set backup
set undodir=$VIMTEMP
set directory=$VIMTEMP
set backupdir=$VIMTEMP
"}}}
"gvim menu{{{
if has('gui_running')
    set langmenu=en_US.UTF-8
    source $VIMRUNTIME/delmenu.vim
    source $VIMRUNTIME/menu.vim
    language messages en_US.utf-8
endif
"}}}
" Encoding and EOL{{{
set encoding=utf-8
set fileencodings=utf-8,gbk,gb18030,ucs-bom,cp936
set termencoding=utf-8
set ffs=unix,dos
"}}}

set clipboard+=unnamedplus

if exists('g:vscode') " VSCode extension
    nnoremap == <Cmd>call VSCodeNotify('editor.action.formatDocument')<CR>
    xmap gc  <Plug>VSCodeCommentary
    nmap gc  <Plug>VSCodeCommentary
    omap gc  <Plug>VSCodeCommentary
    nmap gcc <Plug>VSCodeCommentaryLine
else " ordinary neovim
    imap jk <Esc>
    set number
    set relativenumber
    set foldmethod=marker
    set mouse=a
    " indent and tab{{{
    set autoindent
    set smartindent
    set expandtab          " Tab to space
    set tabstop=4     " indent 4 spaces
    set shiftwidth=4  " 4 space for auto indent
    set softtabstop=4
    "}}}
    " 24bit true color theme{{{
    if exists('+termguicolors')
        let &t_8f = "\<Esc>[38;2;%lu;%lu;%lum"
        let &t_8b = "\<Esc>[48;2;%lu;%lu;%lum"
        set termguicolors
    endif
    set background=dark " Terminal Compatible
    let g:solarized_italics=0  " 斜体中文很难受
    colorscheme solarized8
    "}}}
    " airline setting{{{
    let g:airline_theme = 'badwolf'
    let g:airline#extensions#ale#enabled = 1
    let g:airline#extensions#wordcount#enabled = 0
    let g:airline_section_z = '%2l/%L|%2v'
    let g:airline_skip_empty_sections = 1
    let g:airline#extensions#tabline#enabled=1
    let g:airline#extensions#tabline#formatter = 'unique_tail'
    "}}}
    " indentLine setup{{{
    let g:indentLine_color_term = 239
    let g:indentLine_concealcursor=''
    let g:indentLine_conceallevel=2
    "}}}
    " ALE settings{{{
    let g:ale_lint_on_text_changed=0
    let g:ale_linters = {
                \   'python': ['flake8', 'pyflakes', 'pylint'],
                \   'javascript': ['eslint'],
                \}
    let g:ale_fixers = {
                \   'python': ['autopep8', 'yapf', 'isort'],
                \   'javascript': ['prettier', 'eslint'],
                \   'vue': ['prettier', 'eslint'],
                \}
    let g:ale_completion_enabled = 0
    let g:ale_lint_on_enter = 0
    let g:ale_fix_on_save = 0
    "}}}
    " language setting
    autocmd FileType toml setlocal commentstring=#\ %s
endif
if filereadable($VIMHOME . '/local/after.vim')
    exec 'source ' . $VIMHOME . '/local/after.vim'
endif
