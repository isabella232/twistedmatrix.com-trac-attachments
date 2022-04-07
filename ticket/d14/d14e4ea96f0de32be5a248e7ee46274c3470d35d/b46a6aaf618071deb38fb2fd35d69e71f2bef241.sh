#!/bin/bash

t=/usr/bin/time
OUTPUT="output"

HEADERS="tag,name,average size (kb),elapsed wall clock,I/O faults,FS inputs,average memory,maximum resident,FS outputs,percent CPU,faults,kernel CPU,user CPU,swaps,average shared text,page size,full time slices,real time,signals,stack,socket messages in,socket messages out"
if [ -e "$OUTPUT" ]
then
    echo "Already exists."
else
    echo "Creating headers."
    echo "$HEADERS" > "$OUTPUT"
fi
tag=$1
shift
for x in $(seq 200)
do
    "$t" -o "$OUTPUT" -a -f "$tag,%C,%D,%E,%F,%I,%K,%M,%O,%P,%R,%S,%U,%W,%X,%Z,%c,%e,%k,%p,%r,%s" $@
done
