#!/bin/bash
set -e

# Setup shorthands
grow="python ../growPatchyRomano.py"
simulate="/home/joakim/repo/oxDNA_torsion/build/bin/oxDNA"

cd quadraped

# Clear old files
rm -rf input_stage* stage* combined

# Stage 1
echo "Starting stage 1"
$grow 0 10 empty.top empty.conf stage1 input_template 5e5
$simulate input_stage1

# Stage 2
echo "Starting stage 2"
$grow 1 40 stage1/init.top stage1/last_conf.dat stage2 input_template 1e7
$simulate input_stage2

# Stage 3
echo "Starting stage 3"
$grow 2 40 stage2/init.top stage2/last_conf.dat stage3 input_template 2e7
$simulate input_stage3

echo "Finished simulations"

mkdir combined
cp stage3/init.top combined
cat stage1/trajectory.dat >> combined/trajectory.dat
cat stage2/trajectory.dat >> combined/trajectory.dat
cat stage3/trajectory.dat >> combined/trajectory.dat
python ../normaliseTraj.py combined/trajectory.dat combined/trajectory.dat

echo "Combined trajectories into ./quadraped/combined/"

cd ..