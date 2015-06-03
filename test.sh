#!/bin/bash

export PYTHONPATH=`pwd`

let failures=0

cd tests
for test in `ls test_*.sh`; do
    if ./$test; then
        echo "SUCCESS"
    else
        echo "FAILURE"
        let failures+=1
    fi
done

if [ "$failures" -eq "0" ]; then
  exit 0
else
  exit 1
fi

#end.
