# muon_simulations

Compilation of scripts + files to generate and run FLUKA simulations for muons incident on FASERnu.

 - `generateInputFiles.py`: Generates an input file in the `GeneratedFiles` directory for each energy in `negative_muon_flux.csv` from the `BaseInputFiles` directory.
    - Already Ran
 - `run_simulation.sh`: `zsh` script which runs each FLUKA input file in `GeneratedFiles` for 10 runs
    - Requires specification of the FLUPRO directory for FLUKA
 - `parseFLUKAOutput.py`: Scrapes the FLUKA output in `GeneratedFiles` and generates Numpy arrays with the data saved in `ParsedData`

Note: Python scripts require Python3
