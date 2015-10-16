#!/bin/bash


for i in $(seq 0 8); do
    ./pvcheck example.test ./program $i
    echo -----------------------------------------------
done
