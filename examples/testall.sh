#!/bin/bash


for i in $(seq 0 10); do
    ./pvcheck example.test ./program $i
    echo -----------------------------------------------
done
