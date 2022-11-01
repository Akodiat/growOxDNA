import argparse
import re
from os import path

# Make sure to count particles bound to nothing as their own clusters
def countClusters(dirPath):
    p = re.compile("\(([0-9 ]+)\)  ")
    with open(path.join(dirPath,"clusters.txt"), "r") as f:
        for line in f:
            pass
        last = line
    clusters = [match.group(1).strip().split() for match in p.finditer(line)]

    with open(path.join(dirPath,"init.top"), "r") as f:
        nParticles = int(f.readline().split()[0])

    return len(clusters) + nParticles - sum(len(c) for c in clusters)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("dirPath", help="Path to the output directory (containing clusters.txt and init.top)")
    args = parser.parse_args()

    print(countClusters(
        args.dirPath
    ))