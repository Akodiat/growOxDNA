#!/bin/bash
#SBATCH --job-name="adGrowOctahedron"  # Name of the job in the queue
#SBATCH --error="adGrowOctahedron.%j.out"  # Name of stderr file
#SBATCH --output="adGrowOctahedron.%j.out" # Name of the stdout file
#SBATCH -p run                       # Run is the only partition on javelina
#SBATCH -c 1                         # Number of CPU cores
#SBATCH --gres=gpu:0                 # Number of GPUs
#SBATCH -t 14-00:00:00               # There is no max wall time but be nice

set -e

# Setup shorthands
grow="python ../growPatchyRomano.py"
simulate="/home/joakim/repo/oxDNA_torsion/build/bin/oxDNA"

# Species counts
# system.cubeTypeCount.join(' ')
declare -a counts=(1 6 6 6 6 12 24 36 48 8 24 48 80 6)

cd octahedron

# Clear old files
rm -rf input_stage* stage* combined

# Stage 1
echo "Adding core species"
# Add the first five species all at once
# Use box size from local empty.conf and preserve it
$grow 0 ${counts[0]} ../empty.top empty.conf stage_core template_input 0 --preserveBox
$grow 1 ${counts[1]} stage_core/init.top stage_core/init.conf stage_core template_input 0 --preserveBox
$grow 2 ${counts[2]} stage_core/init.top stage_core/init.conf stage_core template_input 0 --preserveBox
$grow 3 ${counts[3]} stage_core/init.top stage_core/init.conf stage_core template_input 0 --preserveBox
$grow 4 ${counts[4]} stage_core/init.top stage_core/init.conf stage_core template_input 1e7 --preserveBox

cp stage_core/init.conf stage_core/last_conf.dat
nClusters="0"
while (($nClusters != "1")); do
    sed -i "s/init.conf/last_conf.dat/g" input_stage_core
    $simulate input_stage_core
    nClusters=$(python ../countClusters.py stage_core)
    echo "$nClusters clusters!"
done

nCounts=${#counts[@]}
previous="stage_core"
for (( i=5; i<${nCounts}; i++ ));
do
    stageName="stage_species$i"
    echo "Adding species $i"
    $grow $i ${counts[$i]} ${previous}/init.top ${previous}/last_conf.dat ${stageName} template_input 1e7 --preserveBox
    cp "${stageName}/init.conf" "${stageName}/last_conf.dat"
    nClusters="0"
    while (($nClusters != "1")); do
        sed -i "s/init.conf/last_conf.dat/g" "input_${stageName}"
        $simulate "input_${stageName}"
        nClusters=$(python ../countClusters.py ${stageName})
        echo "$nClusters clusters!"
    done
    previous=${stageName}
done

mkdir combined
cp stage_core/init.top combined
cat stage_core/trajectory.dat >> combined/trajectory.dat
for (( i=5; i<${nCounts}; i++ ));
do
    cat "stage_species${i}/trajectory.dat" >> combined/trajectory.dat
done
python ../normaliseTraj.py combined/trajectory.dat combined/trajectory.dat

echo "Combined trajectories into ./quadraped/combined/"

cd ..
