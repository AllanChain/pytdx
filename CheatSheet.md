# Vim Cheatsheet

## Navigate in Vim Help Pages

|Key     |Desciption|
|:-------|:---------|
|`Ctrl+[`|Follow    |
|`Ctrl+T`|Trace Back|


### Airline mode default

<details>
<summary>At <code>vim-airline/autoload/init.vim</code></summary>
<pre>
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
        \ '' : 'S-BLOCK',
        \ 't'  : 'TERMINAL',
        \ 'v'  : 'VISUAL',
        \ 'V'  : 'V-LINE',
        \ '' : 'V-BLOCK',
        \ }, 'keep')
</pre>
</details>
