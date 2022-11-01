import math
import random
import os

def pbcDelta(a, b, side):
    delta = abs((a % side) - (b % side))
    return min(delta, side - delta)

# Calculate euclidian distance between vectors p and q
def dist(p, q, b = None):
    assert len(p) == len(q), "Vectors not the same length"
    return math.sqrt(sum((
        (p[i] - q[i]) if b is None else (
            pbcDelta(p[i], q[i], b[i])
        )
    )**2 for i in range(len(p))))

# Calculate magnitude (length) of vector p
def magnitude(p):
    return math.sqrt(sum(p[i]**2 for i in range(len(p))))

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

def add(p, q):
    assert len(p) == len(q), "Vectors not the same length"
    return [p[i] + q[i] for i in range(len(p))]


def divideScalar(p, s):
    return [p[i]/s for i in range(len(p))]

# Calculate center of mass taking periodic boundary conditions into account:
# https://doi.org/10.1080/2151237X.2008.10129266
# https://en.wikipedia.org/wiki/Center_of_mass#Systems_with_periodic_boundary_conditions
def calcCOM(positions, box):
    if len(positions) == 0:
        return [0, 0, 0]

    cm_x = [0, 0]
    cm_y = [0, 0]
    cm_z = [0, 0]

    for p in positions:
        # Calculate positions on unit circle for each dimension and that to the
        # sum.
        angle = [
            (p[0] * 2 * math.pi) / box[0],
            (p[1] * 2 * math.pi) / box[1],
            (p[2] * 2 * math.pi) / box[2]
        ]
        cm_x = add(cm_x, [math.cos(angle[0]), math.sin(angle[0])])
        cm_y = add(cm_y, [math.cos(angle[1]), math.sin(angle[1])])
        cm_z = add(cm_z, [math.cos(angle[2]), math.sin(angle[2])])

    # Divide center of mass sums to get the averages
    cm_x = divideScalar(cm_x, len(positions))
    cm_y = divideScalar(cm_y, len(positions))
    cm_z = divideScalar(cm_z, len(positions))

    # Convert back from unit circle coordinates into x,y,z
    cms = [
        box[0] / (2 * math.pi) * (math.atan2(-cm_x[1], -cm_x[0]) + math.pi),
        box[1] / (2 * math.pi) * (math.atan2(-cm_y[1], -cm_y[0]) + math.pi),
        box[2] / (2 * math.pi) * (math.atan2(-cm_z[1], -cm_z[0]) + math.pi)
    ]

    return cms

# Add `count` particles to the configuration
def addToConf(confLines, count, minDist=1.5, targetDensity=None, preserveBox=True):
    # Find box dimensions
    assert confLines[1][0] == 'b', "Did not find box in second row of config"
    box = [float(b) for b in confLines[1].split()[-3:]]

    if not preserveBox:
        cms = calcCOM([[float(v) for v in l.split()[:3]] for l in confLines[3:]], box)

        # Apply centering and bring everything into bounding box
        # (so as not to mess up if the box size changes)
        for i in range(len(confLines)):
            vs = confLines[i].split(' ')
            if len(vs) == 15:
                for j in range(3):
                    vs[j] = str((float(vs[j])-cms[j]) % box[j])
                confLines[i] = ' '.join(vs)

        # Keep track of particle positions
        positions = [[float(v) for v in l.split()[:3]] for l in confLines[3:]]

        # Update density
        currentVolume = box[0]*box[1]*box[2]
        if not targetDensity:
            if len(positions) > 0:
                # Default to current density if we have particles already
                targetDensity = len(positions) / currentVolume
            elif currentVolume > 0:
                # Or keep the volume as set if the config is empty
                targetDensity = (count+len(positions)) / currentVolume
            else:
                # Or just default to 0.1
                targetDensity = 0.1
        targetVolume = (count+len(positions)) / targetDensity
        scalingFactor = targetVolume/currentVolume
        assert scalingFactor >= 1, "Shrinking the bounding box is not safe, decrease your target density or leave it as is"
        sideScalingFactor = scalingFactor ** (1/3)
        box = [v*sideScalingFactor for v in box]
        confLines[1] = f"b = {box[0]} {box[1]} {box[2]}\n"
        print(f"Increasing the box size to {box}")
    else:
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


def grow(speciesId, count, topPath, confPath, stagePath, inputPath, nSteps, targetDensity, preserveBox=False):
    # Read empty topology and configuration files
    with open(topPath, "r") as f:
        topLines = f.readlines()
    with open(confPath, "r") as f:
        confLines = f.readlines()

    # Update topology:
    addToTop(topLines, count, speciesId)

    # Update configuration:
    addToConf(confLines, count, targetDensity=targetDensity, preserveBox=preserveBox)

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
    parser.add_argument("-d", "--density", help="Target density for the configuration", type=float)
    parser.add_argument("--preserveBox", help="Preserve the box size (don't increase it to maintain a constant density)", action="store_true")
    args = parser.parse_args()

    grow(
        args.speciesId,
        args.count,
        args.topPath,
        args.confPath,
        args.stagePath,
        args.inputPath,
        args.nSteps,
        args.density,
        args.preserveBox
    )
