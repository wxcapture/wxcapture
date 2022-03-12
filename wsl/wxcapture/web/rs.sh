#!/usr/bin/env bash

echo "rsync with ionice"
echo $1 $2 $3 $4 $5

if [[ "$2" == "--exclude" ]]
then
    echo "--exclude"
    /usr/bin/rsync $1 --rsync-path "ionice -c 3 nice rsync" $2 $3 $4 $5
else
    echo "non--exclude"
    /usr/bin/rsync $1 --rsync-path "ionice -c 3 nice rsync" $2 $3
fi
