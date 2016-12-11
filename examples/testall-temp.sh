#!/bin/bash


for i in $(seq 0 10); do
    python3 ../src/pvcheck.py example.test ./program $i
    echo -----------------------------------------------
done
