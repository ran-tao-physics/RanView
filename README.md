# RanView
This is a code package based on PyMeasure library to measure lock-ins in conjunction with PPMS and an Ocean Optics spectrometer. 

# Requirements (for running with the PPMS)
Python 3.12.7 and the following packages (best installed with conda-forge channel): pyinstaller (for compressing python in to executable if needed), pymeasure, multipyvu, pyside6, scipy, seabreeze (for controlling spectrometer)
MultiVu also needs to be installed in the computer running the python scripts.

# Usage
If one only needs to measure lock-ins and the spectrometer, just download the GUI_lockin_spectrum.exe and run the executable. The starting window will be for you to add the lockin model and lockin port to measure. Set connection settings button will open a new window. On the left panel there is a place to enter the directory to save the data file to, a queue button which starts the measurement, and an abort button to abort the measurement. In the main panel there are a few tabs: a spectrum tab that controls the spectrometer or load/fit a saved spectrum (buttons are self-explanatory, and the only important settings are the USB port for the gadget that drives the laser and the load cell, as well as the serial number of the spectrometer); there will be same number of tabs as number of lockins for talking directly to the lockins (for 52XX lockins it may be best to not use this tab whilst a measurement is going on); a Dock tab that has two plots of the measurement data; and finally a log tab that displays the log.

If one needs to also measure PPMS temperature and field, then one needs to start MultiVu, download all the .py files and run the test_GUImpv.py file in an environment that meets the requirements stated above. The startup window will be the same as above but with an additional PPMS port entry (not used in practice since we are using the MultiPyVu package, so just leave it NOT blank), and there will be an additional PPMS Control tab in the main window (not to use when measurement is going on due to cross-talk between the queries sent within this tab and those sent in the measurement). The PPMS control tab should be self-explanatory, but not very useful, and true sequencing can only be done in MultiVu. Nevertheless, the code should measure the PPMS temperature and field, and with some modifications, should be able to also measure the 4 resistivity channels.
