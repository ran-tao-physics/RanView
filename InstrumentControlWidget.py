##import sys
import logging
##import pyqtgraph as pg

##from pymeasure.display.curves import Crosshairs

from pymeasure.display.Qt import QtCore, QtWidgets
#from pyqtgraph.Qt import QtCore, QtWidgets
from pymeasure.display.widgets.tab_widget import TabWidget
##from pymeasure.display.widgets.plot_frame import PlotFrame
##import numpy as np
from scipy.optimize import curve_fit
##from datetime import datetime
##from seabreeze.spectrometers import Spectrometer
from time import sleep
##import serial

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())
delay = 0.1

class InstrumentControltWidget(TabWidget, QtWidgets.QWidget):
    """ Tab for communicating with instrument via GPIB
    """

    def __init__(self, name, instrument, parent=None):
        super().__init__(name, parent)
        self.instrument = instrument
        self.model = self.instrument.model
        self._setup_ui()
        self._layout()

    def _setup_ui(self):
        self.delay = 0.1 # delay time in sending GPIB command
        ### instrument.model is manually added to each _ar class
        if self.model == "DSP72XX" or self.model == "SR830":  
            self.setOAButton = QtWidgets.QPushButton(text='Set amplitude')
            self.setOAButton.clicked.connect(self.set_OA)
            self.setOFButton = QtWidgets.QPushButton(text='Set frequency')
            self.setOFButton.clicked.connect(self.set_OF)
            self.setSENButton = QtWidgets.QPushButton(text='Set sensitivity')
            self.setSENButton.clicked.connect(self.set_SEN)
            self.setTCButton = QtWidgets.QPushButton(text='Set time constant')
            self.setTCButton.clicked.connect(self.set_TC)
            self.sendCommandButton = QtWidgets.QPushButton(text='Send GPIB command')
            self.sendCommandButton.clicked.connect(self.send_command)
            self.sendQueryButton = QtWidgets.QPushButton(text='Query GPIB command')
            self.sendQueryButton.clicked.connect(self.query_command)

            self.OAlabel = QtWidgets.QLabel(text='Amplitude (V): ')
            self.OAentry = QtWidgets.QLineEdit()
            self.OFlabel = QtWidgets.QLabel(text='Frequency (Hz): ')
            self.OFentry = QtWidgets.QLineEdit()
            self.SENlabel = QtWidgets.QLabel(text='Sensitivity (V): ')
            self.SENentry = QtWidgets.QLineEdit()
            self.TClabel = QtWidgets.QLabel(text='Time constant (s): ')
            self.TCentry = QtWidgets.QLineEdit()
            self.GPIBCommandlabel = QtWidgets.QLabel(text='GPIB command: ')
            self.GPIBCommandentry = QtWidgets.QLineEdit()
            self.GPIBReturnlabel = QtWidgets.QLabel(text='GPIB return: ')
            self.GPIBReturnentry = QtWidgets.QLineEdit()

            if self.model == "SR830":
                self.OAentry.setText(str(self.instrument.sine_voltage))
                self.OFentry.setText(str(self.instrument.frequency))
                self.SENentry.setText(str(self.instrument.sensitivity))
                self.TCentry.setText(str(self.instrument.time_constant))
            else:
                self.OAentry.setText(str(self.instrument.voltage))
                self.OFentry.setText(str(self.instrument.frequency))
                self.SENentry.setText(str(self.instrument.sensitivity))
                self.TCentry.setText(str(self.instrument.time_constant))
        elif self.model == "DSP52XX":
            self.setOAButton = QtWidgets.QPushButton(text='Set amplitude')
            self.setOAButton.clicked.connect(self.set_OA)
            self.setOFButton = QtWidgets.QPushButton(text='Set frequency')
            self.setOFButton.clicked.connect(self.set_OF)
            self.setSENButton = QtWidgets.QPushButton(text='Set sensitivity')
            self.setSENButton.clicked.connect(self.set_SEN)
            self.setTCButton = QtWidgets.QPushButton(text='Set time constant')
            self.setTCButton.clicked.connect(self.set_TC)
            self.OAlabel = QtWidgets.QLabel(text='Amplitude (V): ')
            self.OAentry = QtWidgets.QLineEdit()
            self.OFlabel = QtWidgets.QLabel(text='Frequency (Hz): ')
            self.OFentry = QtWidgets.QLineEdit()
            self.SENlabel = QtWidgets.QLabel(text='Sensitivity (V): ')
            self.SENentry = QtWidgets.QLineEdit()
            self.TClabel = QtWidgets.QLabel(text='Time constant (s): ')
            self.TCentry = QtWidgets.QLineEdit()
            self.OAentry.setText(str(self.instrument.voltage))
            sleep(delay)
            self.OFentry.setText(str(self.instrument.frequency))
            sleep(delay)
            self.SENentry.setText(str(self.instrument.sensitivity))
            sleep(delay)
            self.TCentry.setText(str(self.instrument.time_constant))
            sleep(delay)

            self.sendCommandButton = QtWidgets.QPushButton(text='Send GPIB command')
            self.sendCommandButton.clicked.connect(self.send_command)
            self.sendQueryButton = QtWidgets.QPushButton(text='Query GPIB command')
            self.sendQueryButton.clicked.connect(self.query_command)

            self.GPIBCommandlabel = QtWidgets.QLabel(text='GPIB command: ')
            self.GPIBCommandentry = QtWidgets.QLineEdit()
            self.GPIBReturnlabel = QtWidgets.QLabel(text='GPIB return: ')
            self.GPIBReturnentry = QtWidgets.QLineEdit()

            self.notelabel = QtWidgets.QLabel(text='Do not use this tab or GPIB query when a measurement is going on, DSP52XX will mess up the queries and the program will abort the measurement due to timeout. <br/> Also, the measurement might not queue at first due to communication problem. Just hit the button again.')
        
        if self.model == "DSP72XX" or self.model == "DSP52XX" or self.model == "SR830":
            XY_init = self.instrument.xy
            self.Xlabel = QtWidgets.QLabel(text='X (V) : ')
            self.Xentry = QtWidgets.QLineEdit()
            self.Ylabel = QtWidgets.QLabel(text='Y (V) : ')
            self.Yentry = QtWidgets.QLineEdit()
            self.Xentry.setText(str(XY_init[0]))
            self.Yentry.setText(str(XY_init[1]))
            self.measureXYButton = QtWidgets.QPushButton(text='Measure XY')
            self.measureXYButton.clicked.connect(self.measure_XY)

    def _layout(self):
        vbox = QtWidgets.QVBoxLayout(self)
        vbox.setSpacing(10)

        if self.model == "DSP72XX" or self.model == "SR830":

            OAbox = QtWidgets.QHBoxLayout()
            OAbox.setSpacing(10)
            OAbox.setContentsMargins(-1, 6, -1, 6)
            OAbox.addWidget(self.OAlabel)
            OAbox.addWidget(self.OAentry)
            OAbox.addWidget(self.setOAButton)

            OFbox = QtWidgets.QHBoxLayout()
            OFbox.setSpacing(10)
            OFbox.setContentsMargins(-1, 6, -1, 6)
            OFbox.addWidget(self.OFlabel)
            OFbox.addWidget(self.OFentry)
            OFbox.addWidget(self.setOFButton)

            SENbox = QtWidgets.QHBoxLayout()
            SENbox.setSpacing(10)
            SENbox.setContentsMargins(-1, 6, -1, 6)
            SENbox.addWidget(self.SENlabel)
            SENbox.addWidget(self.SENentry)
            SENbox.addWidget(self.setSENButton)

            TCbox = QtWidgets.QHBoxLayout()
            TCbox.setSpacing(10)
            TCbox.setContentsMargins(-1, 6, -1, 6)
            TCbox.addWidget(self.TClabel)
            TCbox.addWidget(self.TCentry)
            TCbox.addWidget(self.setTCButton)

            GPIBCommandbox = QtWidgets.QHBoxLayout()
            GPIBCommandbox.setSpacing(10)
            GPIBCommandbox.setContentsMargins(-1, 6, -1, 6)
            GPIBCommandbox.addWidget(self.GPIBCommandlabel)
            GPIBCommandbox.addWidget(self.GPIBCommandentry)
            GPIBCommandbox.addWidget(self.sendCommandButton)
            GPIBCommandbox.addWidget(self.sendQueryButton)
            GPIBCommandbox.addWidget(self.GPIBReturnlabel)
            GPIBCommandbox.addWidget(self.GPIBReturnentry)

            vbox.addLayout(OAbox)
            vbox.addLayout(OFbox)
            vbox.addLayout(SENbox)
            vbox.addLayout(TCbox)
            vbox.addLayout(GPIBCommandbox)

        elif self.model == "DSP52XX":
            Notebox = QtWidgets.QHBoxLayout()
            Notebox.setSpacing(10)
            Notebox.setContentsMargins(-1, 6, -1, 6)
            Notebox.addWidget(self.notelabel)

            OAbox = QtWidgets.QHBoxLayout()
            OAbox.setSpacing(10)
            OAbox.setContentsMargins(-1, 6, -1, 6)
            OAbox.addWidget(self.OAlabel)
            OAbox.addWidget(self.OAentry)
            OAbox.addWidget(self.setOAButton)

            OFbox = QtWidgets.QHBoxLayout()
            OFbox.setSpacing(10)
            OFbox.setContentsMargins(-1, 6, -1, 6)
            OFbox.addWidget(self.OFlabel)
            OFbox.addWidget(self.OFentry)
            OFbox.addWidget(self.setOFButton)

            SENbox = QtWidgets.QHBoxLayout()
            SENbox.setSpacing(10)
            SENbox.setContentsMargins(-1, 6, -1, 6)
            SENbox.addWidget(self.SENlabel)
            SENbox.addWidget(self.SENentry)
            SENbox.addWidget(self.setSENButton)

            TCbox = QtWidgets.QHBoxLayout()
            TCbox.setSpacing(10)
            TCbox.setContentsMargins(-1, 6, -1, 6)
            TCbox.addWidget(self.TClabel)
            TCbox.addWidget(self.TCentry)
            TCbox.addWidget(self.setTCButton)

            GPIBCommandbox = QtWidgets.QHBoxLayout()
            GPIBCommandbox.setSpacing(10)
            GPIBCommandbox.setContentsMargins(-1, 6, -1, 6)
            GPIBCommandbox.addWidget(self.GPIBCommandlabel)
            GPIBCommandbox.addWidget(self.GPIBCommandentry)
            GPIBCommandbox.addWidget(self.sendCommandButton)
            GPIBCommandbox.addWidget(self.sendQueryButton)
            GPIBCommandbox.addWidget(self.GPIBReturnlabel)
            GPIBCommandbox.addWidget(self.GPIBReturnentry)

            vbox.addLayout(Notebox)
            vbox.addLayout(OAbox)
            vbox.addLayout(OFbox)
            vbox.addLayout(SENbox)
            vbox.addLayout(TCbox)
            vbox.addLayout(GPIBCommandbox)

        if self.model == "DSP72XX" or self.model == "DSP52XX" or self.model == "SR830":
            XYbox = QtWidgets.QHBoxLayout()
            XYbox.setSpacing(10)
            XYbox.setContentsMargins(-1, 6, -1, 6)
            XYbox.addWidget(self.Xlabel)
            XYbox.addWidget(self.Xentry)
            XYbox.addWidget(self.Ylabel)
            XYbox.addWidget(self.Yentry)
            XYbox.addWidget(self.measureXYButton)
            vbox.addLayout(XYbox)

        self.setLayout(vbox)

    def preview_widget(self, parent=None):
        """ Return a widget suitable for preview during loading,
        not implemented really
        """
        return InstrumentControltWidget("Instrument control preview",
                                        instrument=None,
                          parent=parent,
                          )

    def set_OA(self):
        amplitude = float(self.OAentry.text())
        if self.model == "SR830":
            self.instrument.sine_voltage = amplitude
            self.OAentry.setText(str(self.instrument.sine_voltage))
            log.info(self.name + " oscillation voltage set to " + self.OAentry.text() + " V")
        elif self.model == "DSP72XX":
            self.instrument.voltage = amplitude
            self.OAentry.setText(str(self.instrument.voltage))
            log.info(self.name + " oscillation voltage set to " + self.OAentry.text() + " V")
        elif self.model == "DSP52XX":
            self.instrument.voltage = amplitude
            sleep(delay)
            self.OAentry.setText(str(self.instrument.voltage))
            log.info(self.name + " oscillation voltage set to " + self.OAentry.text() + " V")

    def set_OF(self):
        frequency = float(self.OFentry.text())
        if self.model == "SR830" or self.model == "DSP72XX":
            self.instrument.frequency = frequency
            self.OFentry.setText(str(self.instrument.frequency))
            log.info(self.name + " oscillation frequency set to " + self.OFentry.text() + " Hz")
        elif self.model == "DSP52XX":
            self.instrument.frequency = frequency
            sleep(delay)
            self.OFentry.setText(str(self.instrument.frequency))
            log.info(self.name + " oscillation frequency set to " + self.OFentry.text() + " Hz")
    
    def set_SEN(self):
        sensitivity = float(self.SENentry.text())
        if self.model == "SR830" or self.model == "DSP72XX":
            ### sr830 automatically truncates input value, so input can be just a float value,
            ### but dsp72xx only implemented discrete values allowed (should be modified now to allow any value)
            self.instrument.sensitivity = sensitivity
            self.SENentry.setText(str(self.instrument.sensitivity))
            log.info(self.name + " sensitivity set to " + str(self.instrument.sensitivity) + " V")
        elif self.model == "DSP52XX":
            self.instrument.sensitivity = sensitivity
            sleep(delay)
            self.SENentry.setText(str(self.instrument.sensitivity))
            log.info(self.name + " sensitivity set to " + str(self.instrument.sensitivity) + " V")


    def set_TC(self):
        time_constant = float(self.TCentry.text())
        if self.model == "SR830" or self.model == "DSP72XX":
            ### sr830 automatically truncates input value, so input can be just a float value,
            ### but dsp72xx only implemented discrete values allowed (should be modified now to allow any value)
            self.instrument.time_constant = time_constant
            self.TCentry.setText(str(self.instrument.time_constant))
            log.info(self.name + " time constant set to " + str(self.instrument.time_constant) + " s")
        elif self.model == "DSP52XX":
            self.instrument.time_constant = time_constant
            sleep(delay)
            self.TCentry.setText(str(self.instrument.time_constant))
            log.info(self.name + " time constant set to " + str(self.instrument.time_constant) + " s")


    def send_command(self):
        command = self.GPIBCommandentry.text()
        self.instrument.write(command)
        log.info("Command " + command + " sent to " + self.name)

    def query_command(self):
        command = self.GPIBCommandentry.text()
        query = self.instrument.ask(command)
        self.GPIBReturnentry.setText(query)
        log.info("Query " + command + " sent to " + self.name + ", return is " + query)

    def measure_XY(self):
        """ Measure the X and Y voltages measured by a lockin and 
        return a 2-element list of floating point values.
        """
        if self.model == "DSP72XX" or self.model == "DSP52XX":
            self.instrument.auto_range()
            XY = self.instrument.xy
            self.Xentry.setText(str(XY[0]))
            self.Yentry.setText(str(XY[1]))
            log.info(self.name + " measures voltage X = " + str(XY[0]) + ", Y = " + str(XY[1]))
            self.SENentry.setText(str(self.instrument.sensitivity))
            log.info(self.name + " sensitivity set to " + str(self.instrument.sensitivity) + " V")
        elif self.model == "DSP52XX":
            self.instrument.auto_range()
            sleep(delay)
            XY = self.instrument.xy
            self.Xentry.setText(str(XY[0]))
            self.Yentry.setText(str(XY[1]))
            log.info(self.name + " measures voltage X = " + str(XY[0]) + ", Y = " + str(XY[1]))
            sleep(delay)
            self.SENentry.setText(str(self.instrument.sensitivity))
            log.info(self.name + " sensitivity set to " + str(self.instrument.sensitivity) + " V")