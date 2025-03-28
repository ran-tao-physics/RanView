# RanView
This is a code package based on PyMeasure library to measure lock-ins in conjunction with PPMS and an Ocean Optics spectrometer. 

# Requirements
Python 3.12.7 and the following packages (best installed with conda-forge channel): pyinstaller (for compressing python in to executable if needed), pymeasure, multipyvu, pyside6, scipy, seabreeze (for controlling spectrometer)
For connecting to PPMS, MultiVu also needs to be installed in the computer running the python scripts.

# Usage
If one only needs to measure lock-ins and the spectrometer, just run GUI_lockin_spectrum.py (alternatively, go to download folder in command prompt, and use pyinstaller command (pyinstaller --onefile --windowed --exclude-module PyQt5 GUI_lockin_spectrum.py) for packaging into an executable file that can be used on PCs without python installed). The starting window will be for you to add the lockin model and lockin port to measure. Set connection settings button will open a new window. On the left panel there is a place to enter the directory to save the data file to, a queue button which starts the measurement, and an abort button to abort the measurement. In the main panel there are a few tabs: a spectrum tab that controls the spectrometer or load/fit a saved spectrum (buttons are self-explanatory, and the only important settings are the USB port for the gadget that drives the laser and the load cell, as well as the serial number of the spectrometer); there will be same number of tabs as number of lockins for talking directly to the lockins (for 52XX lockins it may be best to not use this tab whilst a measurement is going on); a Dock tab that has two plots of the measurement data---the lockins are automatically auto-ranged as signal rises above 0.9*sensitivity or falls below 0.1*sensitivity, and there is a small unavoidable spike associated with changing the sensitivity; and finally a log tab that displays the log.

If one needs to also measure PPMS temperature and field, then one needs to start MultiVu, download all the .py files and run the test_GUImpv.py file in an environment that meets the requirements stated above (pyinstaller doesn't like packaaging this file supposedly because multipyvu package starts a server on the computer). The startup window will be the same as above but with an additional PPMS port entry (not used in practice since we are using the MultiPyVu package, so just leave it NOT blank), and there will be an additional PPMS Control tab in the main window (not to use when measurement is going on due to cross-talk between the queries sent within this tab and those sent in the measurement). The PPMS control tab should be self-explanatory, but not very useful, and true sequencing can only be done in MultiVu. Nevertheless, the code should measure the PPMS temperature and field, and with some modifications, should be able to also measure the 4 resistivity channels. A possible thing to try may be to run the sequence commands in the python file by directly communicating to the GPIB port and reading values with multipyvu, but I suspect there will still be cross-talk (doing everything in GPIB has cross-talk, and so does doing everything in multipyvu).

For post-processing the .txt data files, an example script to extract the header and data is:

import numpy as np
with open(FILENAME) as fp:
    for i, line in enumerate(fp):
        if i == 3:
            # 4th line for data files produced by pymeasure
            header = line.replace("\n","").split(",") # get rid of ending "\n" and split with comma in between
            break
data=np.loadtxt(FILENAME,skiprows=4,delimiter=",")
