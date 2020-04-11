if has('win64') || has('win32') || has('win16')
    let g:dot_vim = $HOME . '/vimfiles'
else
    let g:dot_vim = $HOME . '/.vim'
endif

if filereadable(g:dot_vim . '/local/before.vim')
    exec 'source ' . g:dot_vim . '/local/before.vim'
endif

" Vim-Plug{{{
call plug#begin(g:dot_vim . '/bundle')

if filereadable(g:dot_vim . '/local/plugins.vim')
    exec 'source ' . g:dot_vim . '/local/plugins.vim'
endif

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
Plug 'tpope/vim-surround'
" Syntax & Highlight
Plug 'dense-analysis/ale'
Plug 'sheerun/vim-polyglot'
Plug 'ap/vim-css-color', { 'for': ['html', 'css', 'vue'] }
" Snippets
if has('python') || has('python3')
    Plug 'honza/vim-snippets'
    Plug 'SirVer/ultisnips'
endif
call plug#end()
"}}}
source $VIMRUNTIME/defaults.vim
syntax on " Fix csv plugin error
set mouse=a
set showcmd
set cursorcolumn
set cursorline
set foldmethod=marker
set updatetime=700  " vim-gitgutter
set nu
" Encoding and EOL{{{
set encoding=utf-8
set fileencodings=utf-8,gbk,gb18030,ucs-bom,cp936
set termencoding=utf-8
set ffs=unix,dos
"}}}
"gvim menu{{{
if has('gui_running')
    set langmenu=en_US.UTF-8
    source $VIMRUNTIME/delmenu.vim
    source $VIMRUNTIME/menu.vim
    language messages en_US.utf-8
endif
"}}}
" Tab{{{
set autoindent
set smartindent
set expandtab          " Tab to space
setlocal tabstop=4     " indent 4 spaces
setlocal shiftwidth=4  " 4 space for auto indent
setlocal softtabstop=4
func! SetTab()
    setlocal sw=2
    setlocal ts=2
    setlocal sts=2
endfunc
autocmd FileType javascript,html,htmldjango,css,xml,scss,vue call SetTab()
"}}}
" Vue fold{{{
func! JSFold()
    setlocal foldmethod=syntax
    setlocal foldenable
    setlocal foldlevel=2
endfunc
autocmd FileType vue call JSFold()
"}}}
" Enable 24bit true color{{{
if exists('+termguicolors')
    let &t_8f = "\<Esc>[38;2;%lu;%lu;%lum"
    let &t_8b = "\<Esc>[48;2;%lu;%lu;%lum"
    set termguicolors
endif
set background=dark " Terminal Compatible
let g:solarized_italics=0  " 斜体中文很难受
colorscheme solarized8
"}}}
" backup, undo and auto save{{{
set autowrite
set autoread
set undofile
set swapfile
set backup
set undodir=$HOME/.vim_temp/
set directory=$HOME/.vim_temp/
set backupdir=$HOME/.vim_temp/
"}}}
" Shortcut keys{{{
map <F2> :NERDTreeToggle<CR>
map <F5> :call RunPro()<CR>
imap <F5> <Esc>:call RunPro()<CR>
let mapleader=';'
map <leader>s :w<CR>
imap <leader>s <Esc>:w<CR>
imap <leader><leader> <Esc>
vmap <leader><leader> <Esc>
if has('win64') || has('win32') || has('win16')
    imap <C-V> <C-R>+
    map <space>v :e $HOME/vimfiles/vimrc<CR>
    map <space>s :source $HOME/vimfiles/vimrc<CR>
else
    map <space>v :e $HOME/.vim/vimrc<CR>
    map <space>s :source $HOME/.vim/vimrc<CR>
endif
map <space>= mLggVG='L
map <space>f :PymodeLintAuto<CR>
imap · ``<Left>
imap 》<space> ><space>
"}}}
" Back to the exit place{{{
au BufReadPost * exe 'normal! g`"'
"}}}
"Quickly Run{{{
let g:timer='!time '
if has('win64') || has('win32') || has('win16')
    let g:timer='!'
endif
func! RunPro()
    exec 'w'
    if &filetype == 'c'
        exec '!g++ % -o %< && time ./%<'
    elseif &filetype == 'cpp'
        exec '!g++ % -o %< && time ./%<'
    elseif &filetype == 'java'
        exec '!javac %'
        exec g:timer . 'java %<'
    elseif &filetype == 'sh'
        exec g:timer . 'bash %'
    elseif &filetype == 'python'
        exec g:timer . 'python3 %'
    elseif &filetype == 'javascript'
        exec g:timer . 'node %'
    elseif &filetype == 'go'
        exec g:timer . 'go run %'
    endif
endfunc
"}}}
" Auto open NERDTree{{{
autocmd VimEnter * if argc() == 1 && isdirectory(argv()[0]) && !exists('s:std_in') | exe 'NERDTree' argv()[0] | wincmd p | ene | endif
"}}}
" indentLine setup{{{
" let g:indentLine_setColors = 0
let g:indentLine_color_term = 239
let g:indentLine_concealcursor=''
let g:indentLine_conceallevel=2
"}}}
" airline setup{{{
let g:airline_theme = 'badwolf'
let g:airline_powerline_fonts = 1
let g:airline#extensions#ale#enabled = 1
let g:airline#extensions#wordcount#enabled = 0
let g:airline_section_z = '%2l/%L☰%2v'
let g:airline_skip_empty_sections = 1
let g:airline#extensions#tabline#enabled=1
let g:airline#extensions#tabline#formatter = 'unique_tail'
let g:airline_mode_map = {
            \ '__' : '--',
            \ 'c'  : 'C',
            \ 'i'  : 'I',
            \ 'ic' : 'IC',
            \ 'ix' : 'IC',
            \ 'multi' : 'M',
            \ 'n'  : 'N',
            \ 'ni' : '(I)',
            \ 'no' : 'OP PENDING',
            \ 'R'  : 'R',
            \ 'Rv' : 'VR',
            \ 's'  : 'S',
            \ 'S'  : 'SL',
            \ '' : 'SB',
            \ 't'  : 'TERM',
            \ 'v'  : 'V',
            \ 'V'  : 'VL',
            \ '' : 'VB'}
"}}}
" ale setup{{{
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
" UltiSnips{{{
let g:UltiSnipsExpandTrigger="<leader>q"
let g:UltiSnipsJumpForwardTrigger="<c-p>"
let g:UltiSnipsJumpBackwardTrigger="<c-b>"
"}}}
if filereadable(g:dot_vim . '/local/after.vim')
    exec 'source ' . g:dot_vim . '/local/after.vim'
endif
