import re
import numpy as np

# Generates a string with the appropriate amount of whitespace
def str2WHAT(input):
    WHAT = input
    while len(WHAT) < 10:
        WHAT = ' ' + WHAT
    return WHAT

# Generates a string with the correct formatting for the beam information
def genBeamInfoLine(energy,dx,dy,particle):
    BEAM = 'BEAM      '
    # - here sets energy instead of momentum of the particle
    WHAT2 = str2WHAT('-' + str(energy))
    WHAT34 = '                    '
    WHAT5 = str2WHAT(str(dx))
    WHAT6 = str2WHAT(str(dy))
    # 1. here sets a rectangle
    WHAT7 = str2WHAT('1.')
    WHAT8 = particle + '\n'
    newLine = BEAM + WHAT2 + WHAT34 + WHAT5 + WHAT6 + WHAT7 + WHAT8
    return newLine

RNG = 3000.0

inputFileDir = 'BaseInputFiles/'
outputFileDir = 'GeneratedFiles/'
for filename in ['muons_bot', 'muons_left', 'muons_right', 'muons_top']:
    inputFile = open(inputFileDir + filename + '.inp')
    nmuData = np.loadtxt('negative_muon_flux.csv')

    m = re.split(r'_',filename)
    prefile = m[0]
    side    = m[1]

    nmuEn = nmuData[:,0]

    # Create a few file for each muon charge and energy
    nmuOut = []
    filenum = 1
    for en in nmuEn:
        nmuOut.append(open(outputFileDir + prefile + '_' + str(filenum) + '_' + side + '.inp','w'))
        filenum += 1

    # Write each new file line by line
    for line in inputFile:
        for n in range(np.size(nmuEn)):
            outputFile = nmuOut[n]
            if re.search(r'BEAM ',line):
                m = re.split(r'  *',line)
                energy = nmuEn[n]
                dx = m[2]
                dy = m[3]
                newLine = genBeamInfoLine(energy, dx, dy, 'MUON-')
            elif re.search(r'RANDOMIZ ',line):
                newLine = 'RANDOMIZ  ' + str2WHAT(str(1.0)) + str2WHAT(str(RNG)) + '\n'
                RNG = RNG + 1.0
            else:
                newLine = line
            outputFile.write(newLine)


    inputFile.close()
