#!/usr/bin/env bash

if [[ "$2" == "--exclude" ]]
then
    /usr/bin/rsync $1 --rsync-path "ionice -c 3 nice rsync" $2 $3 $4 $5
else
    /usr/bin/rsync $1 --rsync-path "ionice -c 3 nice rsync" $2 $3
fi
