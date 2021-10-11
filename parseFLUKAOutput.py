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

def pullTrData(fileID,evNum):

    files = [fileID + '_fort.' + str(fnum) for fnum in [30,31,32,33]]

    trackers = []
    for file in files:
        with open(file, 'r') as f:
            eNum = None
            while not(eNum == evNum):
                line = f.readline()
                if re.search(r'Event',line):
                    m = re.match(r'.*Event #: *([0-9]*).*',line)
                    eNum = m[1]
            m = re.match(r'.*tr([0-9]) .*Event #: *([0-9]*).*',line)
            curTrack = int(m[1])

            # Read whether bin was hit
            line = f.readline()
            m = re.match('.* ([0-9][0-9]*)',line)
            numHits = int(m[1])
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
        trackers.append([cells, flues])
    return trackers

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

def scrapeFLUKA(history, entries, threshold, basedir):
    #Scrape files
    ls = listdir(basedir)
    fileIDs = [basedir + re.match(r'(.*)_fort.24',fname)[1]
                    for fname in ls if re.match(r'(.*)[0-9][0-9][0-9]_fort.24',fname)]
    fileIDs.sort()

    for fileID in fileIDs:
        scFile = open(fileID + '_fort.24')
        fid = re.split('/',fileID)
        fid = fid[len(fid)-1]
        arraydir =  'ParsedData/'

        primEn, totSim, zposition = pullSimData(fileID)
        if not(alreadyExists(arraydir, arraydir + fid + '.npy')):
            print(fid)
            
            scLine, evNum = pushFileToEvent(scFile)
            evNum_tmp = evNum
            
            data = []
            # if zposition > 120:
            #     volLead = 30 * 40 * 2 # Volume of lead slice for neutrino interaction
            #     rhoLead = 11.35 # Density of Lead
            #     volTung = 25 * 30 * 8 # Volume of tungsten slice for neutrino interaction
            #     rhoTung = 19.3 # Density of Tungsten
            #     weight =  (rhoLead * volLead)/(volTung*rhoTung)
            # else:
            #     weight = 1

            while scLine:

                # Pull scintillator/calorimeter energy until you reach a new event
                enHist   = []
                while evNum == evNum_tmp:
                    energy = pullScData(scFile, scLine)
                    scLine, evNum_tmp = pushFileToEvent(scFile)
                    enHist.append(energy)

                # print(enHist)
                # Read data into self
                enHist = np.array(enHist)
                scintillator = np.array([int(value > threshold) for value in enHist])
                if np.equal(scintillator[entries], history).all():
                # if np.equal(evHist, history).all() and enHist[9] > 10:
                    calEnergy = enHist[len(enHist)-1]
                    trackers = pullTrData(fileID,evNum)
                    

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
                # Reset evNum to continue running reader
                evNum = evNum_tmp
                # print('----------------')
            np.save(arraydir + fid + '.npy',data)

history = np.array([0, 0, 1, 1])
entries = np.array([0, 1, 2, 3])
threshold = 10**-4

basedir = 'GeneratedFiles/'

scrapeFLUKA(history, entries, threshold, basedir)

