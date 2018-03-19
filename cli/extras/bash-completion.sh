_popper_completion() {
    COMPREPLY=( $( env COMP_WORDS="${COMP_WORDS[*]}" \
                   COMP_CWORD=$COMP_CWORD \
                   _POPPER_COMPLETE=complete $1 ) )
    return 0
}

complete -F _popper_completion -o default popper;
