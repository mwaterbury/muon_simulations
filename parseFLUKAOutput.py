import numpy as np
import matplotlib
import matplotlib.pyplot as pyplot
from os import listdir 
import re
import csv

# Pushes the file reader to the next event line
def pushFileToEvent(file):
    while True:
        line = file.readline()
        if line == '':
            return None, None
        if re.search(r'Event',line):
            m = re.match(r'.*Event #: *([0-9]*).*',line)
            eNum = m[1]
            return line, eNum

# Pushes all tracker files to next event
def pushTrackersToNextEvent(trFiles, evNum):
    evNum_tmp = evNum
    while evNum_tmp == evNum:
        trLines = []
        for trFile in trFiles:
            trLine, evNum_tmp = pushFileToEvent(trFile)
            trLines.append(trLine)
    return trLines

# Reads the energy of the primary particle from the corresponding input file
def pullPrimEn(fileID):
    inputFile = open(fileID[:-3] + '.inp')
    for line in inputFile:
        if re.search(r'BEAM ',line):
            m = re.split(r'  *', line)
            primaryEn = -1*float(m[1])
    return primaryEn

# Reads the energy of the primary particle from the corresponding input file
def pullSimData(fileID):
    inputFile = open(fileID[:-3] + '.inp')
    for line in inputFile:
        if re.search(r'BEAM ',line):
            m = re.split(r'  *', line)
            primaryEn = -1*float(m[1])
        elif re.search(r'START ',line):
            m = re.split(r'  *',line)
            try:
                totSim = int(m[1])
            except ValueError:
                totSim = int(m[1][:-2])
        elif re.search(r'BEAMPOS ',line):
            m = re.split(r'  *',line)
            zpos = float(m[3])
    return primaryEn, totSim, zpos

# Reads the energy in the scintillator/calorimeter from the event line
def pullScData(f, line):
    # Read whether bin was hit
    line = f.readline()
    m = re.split(r'  *',line)
    try:
        hit = int(re.split(r'\n',m[len(m)-1])[0])
    except ValueError:
        print(line)
    en  = 0
    if hit:
        # Skip lines to energy line
        line = f.readline()
        # Extract energy from line
        m = re.split(r'  *',line)
        # Separate amplitude from exponent from scientific notation
        if re.search(r'E',m[len(m)-1]):
            [amp, exp] = re.split(r'E',m[len(m)-1])
            # Remove newline character from exponent
            exp = re.split(r'\n',exp)[0]
            en = float(amp) * 10 ** float(exp)
        else:
            en = float(m[len(m)-2])

    return en

# Reads the tracker data from the event line
def pullTrData(f, line):
    # Read number of hits in tracker
    line = f.readline()
    m = re.match('.* ([0-9][0-9]*)',line)
    numHits = int(m[1])
    # Determine how many lines need to be read for tracker
    numLines = int(np.floor(numHits/2))
    cells = []
    flues = []
    for n in range(numLines):
        line = f.readline()
        m = re.split('  *',line)
        c1 = int(m[1])
        fl1 = float(m[2])
        c2 = int(m[3])
        fl2 = float(m[4])
        cells.append(c1)
        cells.append(c2)
        flues.append(fl1)
        flues.append(fl2)
    if (numHits % 2) == 1:
        line = f.readline()
        m = re.split('  *',line)
        cl = int(m[1])
        fl = float(m[2])
        cells.append(cl)
        flues.append(fl)
    return [cells, flues]

def reformatTracker(tracker, size=25):
    cells = tracker[0]
    flues = tracker[1]

    hits = []
    for n in range(len(cells)):
        if flues[n] > 0.1:
            cell = cells[n]
            x = cell % size
            y = np.floor(cell / size)

            x = x - 12
            y = y - 12
            count = int(flues[n]/0.1)

            hits.append([x,y,count])
    return np.array(hits)

def alreadyExists(basedir, fname):
    ls = listdir(basedir)
    ls = np.array([basedir + file for file in ls])
    if len(ls) == 0:
        return False
    value = (ls == fname).any()
    if value: print(fname + ' already exists!\n-----')
    return value

def scrapeFLUKA(history, entries, threshold, basedir, simid=''):
    #Scrape files
    ls = listdir(basedir)
    fileIDs = [basedir + re.match(r'(.*)_fort.24',fname)[1]
        for fname in ls if re.match(r'(.*)[0-9][0-9][0-9]_fort.24',fname)]
    fileIDs.sort()

    arraydir =  'ParsedData/'
    for fileID in fileIDs:
        scFile = open(fileID + '_fort.24')
        tr1File = open(fileID + '_fort.30')
        tr2File = open(fileID + '_fort.31')
        tr3File = open(fileID + '_fort.32')
        tr4File = open(fileID + '_fort.33')
        trFiles = [tr1File, tr2File, tr3File, tr4File]

        fid = re.split('/',fileID)
        fid = fid[len(fid)-1]

        primEn, totSim, zposition = pullSimData(fileID)
        if not(alreadyExists(arraydir, arraydir + simid + fid + '.npy')):
            print(fid)
            
            scLine, evNum = pushFileToEvent(scFile)
            trLines = pushTrackersToNextEvent(trFiles, None) 
            evNum_tmp = evNum
            
            data = []

            while scLine:

                # Pull Tracker Data
                trackers = [pullTrData(trFile, trLine)
                        for (trFile, trLine) in zip(trFiles, trLines)]
                # Pull scintillator/calorimeter energy until you reach a new event
                enHist   = []
                while evNum == evNum_tmp:
                    energy = pullScData(scFile, scLine)
                    scLine, evNum_tmp = pushFileToEvent(scFile)
                    enHist.append(energy)
                # Progress Tracker Files to Next Event
                pushTrackersToNextEvent(trFiles, evNum)
                # Reset evNum for next iteration
                evNum = evNum_tmp

                # print(enHist)
                # Read data into self
                enHist = np.array(enHist)
                scintillator = np.array([int(value > threshold) 
                                            for value in enHist])
                if re.match(r'.*_center.*',fid):
                        scintillator[0] = 0
                        scintillator[1] = 0
                if np.equal(scintillator[entries], history).all():
                # if np.equal(evHist, history).all() and enHist[9] > 10:
                    calEnergy = enHist[len(enHist)-1]

                    eventdata = {}
                    eventdata['primaryEnergy']       = primEn
                    eventdata['zposition']    = zposition
                    # eventdata['weight']       = weight
                    eventdata['scintillator'] = np.array(scintillator)
                    eventdata['calorimeter']  = round(calEnergy,3)
                    eventdata['hits1']        = reformatTracker(trackers[0])
                    eventdata['hits2']        = reformatTracker(trackers[1])
                    eventdata['hits3']        = reformatTracker(trackers[2])
                    eventdata['hits4']        = reformatTracker(trackers[3])

                    data.append(eventdata)
                # print('----------------')
            np.save(arraydir + simid + fid + '.npy',data)

history = np.array([0, 0, 1, 1])
entries = np.array([0, 1, 2, 3])
threshold = 10**-4

basedir = 'GeneratedFiles/'

scrapeFLUKA(history, entries, threshold, basedir, simid='')

