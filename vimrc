if empty(glob('~/.vim/autoload/plug.vim'))
    silent !curl -fLo ~/.vim/autoload/plug.vim --create-dirs
                \ https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
    autocmd VimEnter * PlugInstall --sync | source $MYVIMRC
endif

if filereadable($HOME . "/.vim/local/before.vim")
    source $HOME/.vim/local/before.vim
endif

" Vim-Plug{{{
if has("win64") || has("win32") || has("win16")
    call plug#begin('~/vimfiles/bundle')
else
    call plug#begin('~/.vim/bundle')
endif

if filereadable($HOME . "/.vim/local/plugins.vim")
    source $HOME/.vim/local/plugins.vim
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
if has("python") || has("python3")
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
" 设置编码{{{
set encoding=utf-8
set fileencodings=utf-8,gbk,gb18030,ucs-bom,cp936
set termencoding=utf-8
set ffs=unix,dos
"}}}
"gvim menu{{{
if has("gui_running")
    set langmenu=en_US.UTF-8
    source $VIMRUNTIME/delmenu.vim
    source $VIMRUNTIME/menu.vim
    language messages en_US.utf-8
endif
"}}}
" 设置Tab键的宽度{{{
set autoindent
set smartindent
set expandtab " Tab转空格
setlocal tabstop=4 " 统一缩进为4
setlocal shiftwidth=4 "自动缩进长度
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
let mapleader=";"
map <leader>s :w<CR>
imap <leader>s <Esc>:w<CR>
imap <leader><leader> <Esc>
vmap <leader><leader> <Esc>
map <space>v :e $HOME/.vim/vimrc<CR>
map <space>s :source $HOME/.vim/vimrc<CR>
map <space>= mLggVG='L
map <space>f :PymodeLintAuto<CR>
"}}}
" indentLine setup{{{
" let g:indentLine_setColors = 0
let g:indentLine_color_term = 239
let g:indentLine_concealcursor=""
let g:indentLine_conceallevel=1
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
" 回到上次退出位置{{{
au BufReadPost * exe "normal! g`\""
"}}}
" Auto open NERDTree{{{
autocmd VimEnter * if argc() == 1 && isdirectory(argv()[0]) && !exists("s:std_in") | exe 'NERDTree' argv()[0] | wincmd p | ene | endif
"}}}
"Quickly Run{{{
let timer="!time "
if has("win64") || has("win32") || has("win16")
    let timer="!"
endif
func! RunPro()
    exec "w"
    if &filetype == 'c'
        exec "!g++ % -o %< && time ./%<"
    elseif &filetype == 'cpp'
        exec "!g++ % -o %< && time ./%<"
    elseif &filetype == 'java'
        exec "!javac %"
        exec timer . "java %<"
    elseif &filetype == 'sh'
        exec timer . "bash %"
    elseif &filetype == 'python'
        exec timer . "python3 %"
    elseif &filetype == 'javascript'
        exec timer . "node %"
    elseif &filetype == 'go'
        exec timer . "go run %"
    endif
endfunc
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
if filereadable($HOME . "/.vim/local/after.vim")
    source $HOME/.vim/local/after.vim
endif
