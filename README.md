# Vimrc of AllanChain

New verion of my vim configuration using `vim-plug` as package manager

## Installation

Clone the repo:
```bash
git clone https://github.com/AllanChain/vimrc
```
Same as [vim-plug](https://github.com/junegunn/vim-plug):
```bash
curl -fLo ~/.vim/autoload/plug.vim --create-dirs \
    https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
```
Then launch vim. You will be informed that colorscheme `solarized8` not installed. Just ignore it. In vim, type:
```vim
:PlugInstall
```
And wait the process to end.

## Custom config

### `~/.vim/local/plugins.vim`

For example:
```vim
" Heavy Librarys
Plug 'ycm-core/YouCompleteMe', { 'do': './install.py' }
Plug 'python-mode/python-mode', { 'for': 'python', 'branch': 'develop' }
```
### `~/.vim/local/before.vim`
### `~/.vim/local/after.vim`

Please modify `fileencodings`
```vim
set fileencodings=utf-8,gbk,gb18030,ucs-bom,cp936
```
## Thing to notice

### Airline Mode Name

<details>
<summary>Default mode names at <code>bundle/vim-airline/autoload/init.vim</code></summary>
<!--Terminate HTML with a new line-->

```vim
call extend(g:airline_mode_map, {
        \ '__' : '------',
        \ 'c'  : 'COMMAND',
        \ 'i'  : 'INSERT',
        \ 'ic' : 'INSERT COMPL',
        \ 'ix' : 'INSERT COMPL',
        \ 'multi' : 'MULTI',
        \ 'n'  : 'NORMAL',
        \ 'ni' : '(INSERT)',
        \ 'no' : 'OP PENDING',
        \ 'R'  : 'REPLACE',
        \ 'Rv' : 'V REPLACE',
        \ 's'  : 'SELECT',
        \ 'S'  : 'S-LINE',
        \ '' : 'S-BLOCK',     " Ctrl+s
        \ 't'  : 'TERMINAL',
        \ 'v'  : 'VISUAL',
        \ 'V'  : 'V-LINE',
        \ '' : 'V-BLOCK',     " Ctrl+v
        \ }, 'keep')
```
</details>
