#!/bin/bash
set -e

# Setup shorthands
grow="python ../growPatchyRomano.py"
simulate="/home/joakim/repo/oxDNA_torsion/build/bin/oxDNA"

# Species counts
# system.cubeTypeCount.map(c=>c*2).join(' ')
declare -a counts=(2 12 12 12 12 24 48 72 96 16 48 96 160 12)

cd octahedron

# Clear old files
rm -rf input_stage* stage* combined

# Stage 1
echo "Adding core species"
# Add the first five species all at once
# Density only has to be set in the first stage and will be preserved
$grow 0 ${counts[0]} ../empty.top ../empty.conf stage_core template_input 0 --density 0.1
$grow 1 ${counts[1]} stage_core/init.top stage_core/init.conf stage_core template_input 0
$grow 2 ${counts[2]} stage_core/init.top stage_core/init.conf stage_core template_input 0
$grow 3 ${counts[3]} stage_core/init.top stage_core/init.conf stage_core template_input 0
$grow 4 ${counts[4]} stage_core/init.top stage_core/init.conf stage_core template_input 1e8
$simulate input_stage_core

nCounts=${#counts[@]}
previous="stage_core"
for (( i=5; i<${nCounts}; i++ ));
do
    stageName="stage_species$i"
    echo "Adding species $i"
    $grow $i ${counts[$i]} ${previous}/init.top ${previous}/last_conf.dat ${stageName} template_input 1e8
    $simulate "input_${stageName}"
    previous=${stageName}
done

mkdir combined
cp stage3/init.top combined
cat stage_core/trajectory.dat >> combined/trajectory.dat
cat species*/trajectory.dat >> combined/trajectory.dat
python ../normaliseTraj.py combined/trajectory.dat combined/trajectory.dat

echo "Combined trajectories into ./quadraped/combined/"

cd ..