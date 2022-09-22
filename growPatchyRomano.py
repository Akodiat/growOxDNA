from logging import error
from math import sqrt
import random
import os

def pbcDelta(a, b, side):
    delta = abs((a % side) - (b % side))
    return min(delta, side - delta)

# Calculate euclidian distance between vectors p and q
def dist(p, q, b = None):
    assert len(p) == len(q), "Vectors not the same length"
    return sqrt(sum((
        (p[i] - q[i]) if b is None else (
            pbcDelta(p[i], q[i], b[i])
        )
    )**2 for i in range(len(p))))

# Calculate magnitude (length) of vector p
def magnitude(p):
    return sqrt(sum(p[i]**2 for i in range(len(p))))

# Normalize vector p
def norm(p):
    length = magnitude(p)
    return [p[i]/length for i in range(len(p))]

# Calculate the cross product between 3D vectors p and q
def cross(p, q):
    assert len(p) == len(q) == 3, "Vectors not the length 3"
    return [
        p[1]*q[2] - p[2]*q[1],
        p[2]*q[0] - p[0]*q[2],
        p[0]*q[1] - p[1]*q[0]
    ]

# Add `count` particles to the configuration
def addToConf(confLines, count, minDist=1.5):
    # Find box dimensions
    assert confLines[1][0] == 'b', "Did not find box in second row of config"
    box = [float(b) for b in confLines[1].split()[-3:]]

    # Keep track of particle positions
    positions = [[float(v) for v in l.split()[:3]] for l in confLines[3:]]
    # Add "count" particles to the configuration
    for _ in range(count):
        # Make sure position is not too close to any other particle
        tries = 0
        while True:
            # Position is randomly selected within the simulation box
            p = [random.uniform(0, b) for b in box]
            for q in positions:
                if dist(p,q, box) < minDist:
                    # Distance too small, find another random position
                    tries += 1
                    if tries >= 1e6:
                        raise RuntimeError(f"Tried {tries} times and still couldn't find room for another particle. Try increasing the box size (or decreasing minDist)")
                    break
            else:
                # Got through the whole for loop without breaking
                # All distances were sufficiently large
                positions.append(p)
                break

        # Orientation vectors selected at random
        a1 = norm([random.random(), random.random(), random.random()])
        while True:
            tmp = [random.random(), random.random(), random.random()]
            try:
                a3 = norm(cross(a1, tmp))
            except:
                # In the unlikely event that tmp is on the same line as a1
                continue
            break

        # Add particle to conf
        confLines.append(f"{' '.join(str(v) for v in p)} {' '.join(str(v) for v in a1)} {' '.join(str(v) for v in a3)} 0 0 0 0 0 0\n")

# Add `count` particles to the topology
def addToTop(topLines, count, speciesId):
    nParticles, nSpecies = [int(n) for n in topLines[0].split()]
    topLines[0] = f"{nParticles+count} {nSpecies+1}\n"
    if len(topLines) > 1:
        # Add a space before additonal species
        topLines[1] += ' '
    else:
        # If empty topology, add a new line
        topLines.append('')
    topLines[1] += ' '.join(str(speciesId) for _ in range(count))


def grow(speciesId, count, topPath, confPath, stagePath, inputPath, nSteps):
    # Read empty topology and configuration files
    with open(topPath, "r") as f:
        topLines = f.readlines()
    with open(confPath, "r") as f:
        confLines = f.readlines()

    # Update topology:
    addToTop(topLines, count, speciesId)

    # Update configuration:
    addToConf(confLines, count)

    # Create subdirectory
    os.makedirs(stagePath, exist_ok = True)

    # Write topology and configuration files
    with open(os.path.join(stagePath, "init.top"), "w") as f:
        f.writelines(topLines)
    with open(os.path.join(stagePath, "init.conf"), "w") as f:
        f.writelines(confLines)

    # Read and write new input file
    inputDir = os.path.dirname(inputPath)
    relStagePath = os.path.relpath(stagePath, inputDir)
    with open(inputPath, "r") as f:
        inputLines = [line.replace(
            "[stage]", relStagePath
        ).replace(
            "[nSteps]", nSteps
        ) for line in f]
    with open(os.path.join(inputDir, "input_"+relStagePath), "w") as f:
        f.writelines(inputLines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("speciesId", help="Id of species to add", type=int)
    parser.add_argument("count", help="Number of particles to add", type=int)
    parser.add_argument("topPath", help="Path to input topology to grow from")
    parser.add_argument("confPath", help="Path to input configuration to grow from")
    parser.add_argument("stagePath", help="Path at which to create simulation stage directory")
    parser.add_argument("inputPath", help="Path to input file template to use")
    parser.add_argument("nSteps", help="Number of steps to set in the input file")
    args = parser.parse_args()

    grow(
        args.speciesId,
        args.count,
        args.topPath,
        args.confPath,
        args.stagePath,
        args.inputPath,
        args.nSteps
    )
