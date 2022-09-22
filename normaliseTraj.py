def normaliseTraj(readPath, writePath):
    currentStep = None
    steps = []
    maxParticles = 0
    with open(readPath, "r") as f:
        for line in f:
            if line[0] == 't':
                if currentStep is not None:
                    maxParticles = max(maxParticles, len(currentStep['particles']))
                currentStep = {'particles': [], 't': line}
                steps.append(currentStep)
            elif line[0] == 'b':
                currentStep['b'] = line
            elif line[0] == 'E':
                currentStep['E'] = line
            elif len(line.split(' ')) == 15:
                currentStep['particles'].append(line)

    print(f"Increasing the number of particles in each step to {maxParticles}")

    with open(writePath, "w") as f:
        for step in steps:
            f.write(step['t'])
            f.write(step['b'])
            f.write(step['E'])
            for line in (step['particles']):
                f.write(line)
            for _ in range(maxParticles - len(step['particles'])):
                f.write(' '.join('0' for _ in range(15)) + '\n')


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("readPath", help="Path to trajectory to normalise")
    parser.add_argument("writePath", help="Path to write normalised trajectory")
    args = parser.parse_args()

    normaliseTraj(args.readPath, args.writePath)