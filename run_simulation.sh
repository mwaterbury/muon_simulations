#!/bin/zsh

# Set FLUKA directory
export FLUPRO=~/.local/fluka-old/

cd GeneratedFiles

# Get input files for runs

# Input files for specific energies
NUMS=($NUMS $(seq 1 18))
for NUM in $NUMS; do
    FILES=($FILES muons_$(echo $NUM)_left.inp muons_$(echo $NUM)_right.inp muons_$(echo $NUM)_top.inp muons_$(echo $NUM)_bot.inp )
done

# Set number of processes you want to run simultaneously
MAXCPU=8
for FILE in $FILES; do
    ((i=i%$MAXCPU)); ((i++==0)) && wait
    $FLUPRO/flutil/rfluka -N0 -M10 $FILE &
done

cd ..