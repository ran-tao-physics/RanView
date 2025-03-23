##import sys
import logging
##import pyqtgraph as pg

##from pymeasure.display.curves import Crosshairs
#from pyqtgraph.Qt import QtCore, QtWidgets
from pymeasure.display.widgets.tab_widget import TabWidget
##from pymeasure.display.widgets.plot_frame import PlotFrame
import numpy as np
from scipy.optimize import curve_fit
from datetime import datetime
##from seabreeze.spectrometers import Spectrometer
from time import sleep
##import serial
from pymeasure.display.Qt import QtCore, QtWidgets, QtGui
#from pyqtgraph.Qt.QtWidgets import QTreeWidget, QTreeWidgetItem
##from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem
#from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt.QtCore import QObject, QThread, Signal, QThreadPool, Slot, QRunnable

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())
delay = 0.1

class PPMSControlWidget(TabWidget, QtWidgets.QWidget):
    """ Tab for communicating with PPMS via GPIB
    """
    sequence_commands = ['Set temperature (fast settle)','Set field driven','Set field persistent','Wait minutes','Shutdown in PotOps mode','Shutdown in continuous mode']
    chamber_commands = ['Seal chamber', 'Purge and seal chamber', 'Vent and seal chamber', 'Pump continuously', 'Vent continuously']
    
    def __init__(self, name, instrument=None, refresh_time=0.5, check_interval=30, parent=None):
        super().__init__(name, parent)
        if instrument != None:
            self.instrument = instrument
            self.refresh_time = refresh_time # default is 0.5s refresh rate
            self.check_interval = check_interval # check if a step has finished every 30 seconds
            ### Because running commands takes a long time and freeze up the GUI, we need to put it on a different thread
            self.threadmanager = QThreadPool()
            self._setup_ui()
            self._layout()

    def _setup_ui(self):
        self.delay = 0.1 # delay time in sending GPIB command

        self.sequencedropdown = QtWidgets.QComboBox()
        self.sequencedropdown.addItems(self.sequence_commands)

        self.sequencevaluelabel = QtWidgets.QLabel(text='Value : ')
        self.sequencevalueentry = QtWidgets.QLineEdit()
        self.sequenceratelabel = QtWidgets.QLabel(text='Rate : ')
        self.sequencerateentry = QtWidgets.QLineEdit()

        self.chamberdropdown = QtWidgets.QComboBox()
        self.chamberdropdown.addItems(self.chamber_commands)

        # self.updateStatusButton = QtWidgets.QPushButton(text='Update status')
        # self.updateStatusButton.clicked.connect(self.update_status)

        self.setChamberButton = QtWidgets.QPushButton(text='Set chamber')
        self.setChamberButton.clicked.connect(self.set_chamber)

        self.bridge1excitationlabel = QtWidgets.QLabel(text='Bridge 1 excitation (uA) : ')
        self.bridge1excitationentry = QtWidgets.QLineEdit()
        self.bridge1powerlabel = QtWidgets.QLabel(text='Bridge 1 power (uW) : ')
        self.bridge1powerentry = QtWidgets.QLineEdit()
        self.setbridge1Button = QtWidgets.QPushButton(text='Set Bridge 1')
        self.setbridge1Button.clicked.connect(self.set_bridge1)
        self.measbridge1Button = QtWidgets.QPushButton(text='Measure Bridge 1')
        self.measbridge1Button.clicked.connect(self.meas_bridge1)
        self.bridge1resistancelabel = QtWidgets.QLabel(text='Bridge 1 resistance (ohm) : ')
        self.bridge1resistanceentry = QtWidgets.QLineEdit()

        self.bridge2excitationlabel = QtWidgets.QLabel(text='Bridge 2 excitation (uA) : ')
        self.bridge2excitationentry = QtWidgets.QLineEdit()
        self.bridge2powerlabel = QtWidgets.QLabel(text='Bridge 2 power (uW) : ')
        self.bridge2powerentry = QtWidgets.QLineEdit()
        self.setbridge2Button = QtWidgets.QPushButton(text='Set Bridge 2')
        self.setbridge2Button.clicked.connect(self.set_bridge2)
        self.measbridge2Button = QtWidgets.QPushButton(text='Measure Bridge 2')
        self.measbridge2Button.clicked.connect(self.meas_bridge2)
        self.bridge2resistancelabel = QtWidgets.QLabel(text='Bridge 2 resistance (ohm) : ')
        self.bridge2resistanceentry = QtWidgets.QLineEdit()

        self.bridge3excitationlabel = QtWidgets.QLabel(text='Bridge 3 excitation (uA) : ')
        self.bridge3excitationentry = QtWidgets.QLineEdit()
        self.bridge3powerlabel = QtWidgets.QLabel(text='Bridge 3 power (uW) : ')
        self.bridge3powerentry = QtWidgets.QLineEdit()
        self.setbridge3Button = QtWidgets.QPushButton(text='Set Bridge 3')
        self.setbridge3Button.clicked.connect(self.set_bridge3)
        self.measbridge3Button = QtWidgets.QPushButton(text='Measure Bridge 3')
        self.measbridge3Button.clicked.connect(self.meas_bridge3)
        self.bridge3resistancelabel = QtWidgets.QLabel(text='Bridge 3 resistance (ohm) : ')
        self.bridge3resistanceentry = QtWidgets.QLineEdit()

        self.bridge4excitationlabel = QtWidgets.QLabel(text='Bridge 4 excitation (uA) : ')
        self.bridge4excitationentry = QtWidgets.QLineEdit()
        self.bridge4powerlabel = QtWidgets.QLabel(text='Bridge 4 power (uW) : ')
        self.bridge4powerentry = QtWidgets.QLineEdit()
        self.setbridge4Button = QtWidgets.QPushButton(text='Set Bridge 4')
        self.setbridge4Button.clicked.connect(self.set_bridge4)
        self.measbridge4Button = QtWidgets.QPushButton(text='Measure Bridge 4')
        self.measbridge4Button.clicked.connect(self.meas_bridge4)
        self.bridge4resistancelabel = QtWidgets.QLabel(text='Bridge 4 resistance (ohm) : ')
        self.bridge4resistanceentry = QtWidgets.QLineEdit()

        self.sequencetree = QtWidgets.QTreeWidget()
        self.sequencetree.setColumnCount(3)
        self.sequencetree.setHeaderLabels(["Command", "Final value (K, T)", "Rate (K / min, T / min)"])

        self.addCommandButton = QtWidgets.QPushButton(text='Add command to end or below selected row')
        self.addCommandButton.clicked.connect(self.add_command)

        self.removeCommandButton = QtWidgets.QPushButton(text='Remove command at end or at selected row')
        self.removeCommandButton.clicked.connect(self.remove_command)

        self.clearSequenceButton = QtWidgets.QPushButton(text='Clear sequence')
        self.clearSequenceButton.clicked.connect(self.clear_sequence)

        self.runSequenceButton = QtWidgets.QPushButton(text='Run sequence')
        self.runSequenceButton.clicked.connect(self.run_sequence_thread)

        self.stopSequenceButton = QtWidgets.QPushButton(text='Stop sequence')
        self.stopSequenceButton.clicked.connect(self.stop_sequence)

        self.temperaturelabel = QtWidgets.QLabel(text='Temperature (K): ')
        self.temperatureentry = QtWidgets.QLineEdit()
        self.temperaturestatuslabel = QtWidgets.QLabel(text='Temperature status: ')
        self.temperaturestatusentry = QtWidgets.QLineEdit()
        self.fieldlabel = QtWidgets.QLabel(text='Field (T): ')
        self.fieldentry = QtWidgets.QLineEdit()
        self.magnetstatuslabel = QtWidgets.QLabel(text='Magnet status: ')
        self.magnetstatusentry = QtWidgets.QLineEdit()
        self.pressurelabel = QtWidgets.QLabel(text='Chamber pressure (torr): ')
        self.pressureentry = QtWidgets.QLineEdit()
        self.heliumlabel = QtWidgets.QLabel(text='Helium level (%): ')
        self.heliumentry = QtWidgets.QLineEdit()
        self.chamberlabel = QtWidgets.QLabel(text='Chamber status: ')
        self.chamberentry = QtWidgets.QLineEdit()

        self.GPIBCommandlabel = QtWidgets.QLabel(text='GPIB command: ')
        self.GPIBCommandentry = QtWidgets.QLineEdit()
        self.GPIBReturnlabel = QtWidgets.QLabel(text='GPIB return: ')
        self.GPIBReturnentry = QtWidgets.QLineEdit()
        self.sendCommandButton = QtWidgets.QPushButton(text='Write GPIB command')
        self.sendCommandButton.clicked.connect(self.send_command)
        self.sendQueryButton = QtWidgets.QPushButton(text='Query GPIB command')
        self.sendQueryButton.clicked.connect(self.query_command)

        self.update_status()

        ### refresh status
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(int(self.refresh_time * 1e3))


    def _layout(self):
        vbox = QtWidgets.QVBoxLayout(self)
        vbox.setSpacing(10)

        statusbox = QtWidgets.QHBoxLayout()
        statusbox.setSpacing(10)
        statusbox.setContentsMargins(-1, 6, -1, 6)
        statusbox.addWidget(self.temperaturelabel)
        statusbox.addWidget(self.temperatureentry)
        statusbox.addWidget(self.temperaturestatuslabel)
        statusbox.addWidget(self.temperaturestatusentry)
        statusbox.addWidget(self.fieldlabel)
        statusbox.addWidget(self.fieldentry)
        statusbox.addWidget(self.magnetstatuslabel)
        statusbox.addWidget(self.magnetstatusentry)
        statusbox.addWidget(self.heliumlabel)
        statusbox.addWidget(self.heliumentry)

        chamberbox = QtWidgets.QHBoxLayout()
        chamberbox.setSpacing(10)
        chamberbox.setContentsMargins(-1, 6, -1, 6)
        chamberbox.addWidget(self.pressurelabel)
        chamberbox.addWidget(self.pressureentry)
        chamberbox.addWidget(self.chamberdropdown)
        chamberbox.addWidget(self.setChamberButton)
        chamberbox.addWidget(self.chamberlabel)
        chamberbox.addWidget(self.chamberentry)
            
        GPIBCommandbox = QtWidgets.QHBoxLayout()
        GPIBCommandbox.setSpacing(10)
        GPIBCommandbox.setContentsMargins(-1, 6, -1, 6)
        GPIBCommandbox.addWidget(self.GPIBCommandlabel)
        GPIBCommandbox.addWidget(self.GPIBCommandentry)
        GPIBCommandbox.addWidget(self.sendCommandButton)
        GPIBCommandbox.addWidget(self.sendQueryButton)
        GPIBCommandbox.addWidget(self.GPIBReturnlabel)
        GPIBCommandbox.addWidget(self.GPIBReturnentry)

        commandbox = QtWidgets.QHBoxLayout()
        commandbox.setSpacing(10)
        commandbox.setContentsMargins(-1, 6, -1, 6)
        commandbox.addWidget(self.sequencedropdown)
        commandbox.addWidget(self.sequencevaluelabel)
        commandbox.addWidget(self.sequencevalueentry)
        commandbox.addWidget(self.sequenceratelabel)
        commandbox.addWidget(self.sequencerateentry)

        commandbuttonbox = QtWidgets.QHBoxLayout()
        commandbuttonbox.setSpacing(10)
        commandbuttonbox.setContentsMargins(-1, 6, -1, 6)
        commandbuttonbox.addWidget(self.addCommandButton)
        commandbuttonbox.addWidget(self.removeCommandButton)
        commandbuttonbox.addWidget(self.clearSequenceButton)
        commandbuttonbox.addWidget(self.runSequenceButton)
        commandbuttonbox.addWidget(self.stopSequenceButton)

        bridge1box = QtWidgets.QHBoxLayout()
        bridge1box.setSpacing(10)
        bridge1box.setContentsMargins(-1, 6, -1, 6)
        bridge1box.addWidget(self.bridge1excitationlabel)
        bridge1box.addWidget(self.bridge1excitationentry)
        bridge1box.addWidget(self.bridge1powerlabel)
        bridge1box.addWidget(self.bridge1powerentry)
        bridge1box.addWidget(self.setbridge1Button)
        bridge1box.addWidget(self.measbridge1Button)
        bridge1box.addWidget(self.bridge1resistancelabel)
        bridge1box.addWidget(self.bridge1resistanceentry)

        bridge2box = QtWidgets.QHBoxLayout()
        bridge2box.setSpacing(10)
        bridge2box.setContentsMargins(-1, 6, -1, 6)
        bridge2box.addWidget(self.bridge2excitationlabel)
        bridge2box.addWidget(self.bridge2excitationentry)
        bridge2box.addWidget(self.bridge2powerlabel)
        bridge2box.addWidget(self.bridge2powerentry)
        bridge2box.addWidget(self.setbridge2Button)
        bridge2box.addWidget(self.measbridge2Button)
        bridge2box.addWidget(self.bridge2resistancelabel)
        bridge2box.addWidget(self.bridge2resistanceentry)

        bridge3box = QtWidgets.QHBoxLayout()
        bridge3box.setSpacing(10)
        bridge3box.setContentsMargins(-1, 6, -1, 6)
        bridge3box.addWidget(self.bridge3excitationlabel)
        bridge3box.addWidget(self.bridge3excitationentry)
        bridge3box.addWidget(self.bridge3powerlabel)
        bridge3box.addWidget(self.bridge3powerentry)
        bridge3box.addWidget(self.setbridge3Button)
        bridge3box.addWidget(self.measbridge3Button)
        bridge3box.addWidget(self.bridge3resistancelabel)
        bridge3box.addWidget(self.bridge3resistanceentry)

        bridge4box = QtWidgets.QHBoxLayout()
        bridge4box.setSpacing(10)
        bridge4box.setContentsMargins(-1, 6, -1, 6)
        bridge4box.addWidget(self.bridge4excitationlabel)
        bridge4box.addWidget(self.bridge4excitationentry)
        bridge4box.addWidget(self.bridge4powerlabel)
        bridge4box.addWidget(self.bridge4powerentry)
        bridge4box.addWidget(self.setbridge4Button)
        bridge4box.addWidget(self.measbridge4Button)
        bridge4box.addWidget(self.bridge4resistancelabel)
        bridge4box.addWidget(self.bridge4resistanceentry)

        sequencetreebox = QtWidgets.QHBoxLayout()
        sequencetreebox.setSpacing(10)
        sequencetreebox.setContentsMargins(-1, 6, -1, -1)
        sequencetreebox.addWidget(self.sequencetree)

        vbox.addLayout(statusbox)
        vbox.addLayout(chamberbox)
        vbox.addLayout(bridge1box)
        vbox.addLayout(bridge2box)
        vbox.addLayout(bridge3box)
        vbox.addLayout(bridge4box)
        vbox.addLayout(GPIBCommandbox)
        vbox.addLayout(commandbox)
        vbox.addLayout(commandbuttonbox)
        vbox.addLayout(sequencetreebox)

        self.setLayout(vbox)

    defaultbrush = QtGui.QBrush()
    stoppedbrush = QtGui.QBrush(QtGui.QColor(255, 0, 0, 100)) # semi-transparent red
    ongoingbrush = QtGui.QBrush(QtGui.QColor(0, 255, 0, 100)) # semi-transparent green
    finishedbrush = QtGui.QBrush(QtGui.QColor(0, 0, 255, 100)) # semi-transparent blue
    current_step = 0
    should_stop = False
    step_finished = False

    def add_command(self):
        """ Add command to sequencetree at bottom if no row selected or below selected row. """
        command = self.sequencedropdown.currentText()
        value = self.sequencevalueentry.text()
        rate = self.sequencerateentry.text()
        if value != "":
            item = QtWidgets.QTreeWidgetItem([command,value,rate])
            if len(self.sequencetree.selectedItems()) == 0:
                # no selected row, insert at bottom
                i = self.sequencetree.topLevelItemCount()
                self.sequencetree.insertTopLevelItem(i, item)
            else: 
                # insert below selected first row
                i = self.sequencetree.indexOfTopLevelItem(self.sequencetree.selectedItems()[0])
                self.sequencetree.insertTopLevelItem(i+1, item)
                # change selected item to inserted item
                self.sequencetree.topLevelItem(i).setSelected(False)
                self.sequencetree.topLevelItem(i).setSelected(True)


    def remove_command(self):
        """ Remove selected command or command at bottom if none selected. """
        if len(self.sequencetree.selectedItems()) == 0:
            # remove bottom row
            i = self.sequencetree.topLevelItemCount()-1
            self.sequencetree.takeTopLevelItem(i)
        else:
            # remove selected row
            for item in self.sequencetree.selectedItems():
                i = self.sequencetree.indexOfTopLevelItem(item)
                self.sequencetree.takeTopLevelItem(i)

    def clear_sequence(self):
        """ Clear sequence. """
        self.sequencetree.clear()

    def set_chamber(self):
        """ Set chamber status according to chamberdropdown. """
        i = self.chamberdropdown.currentIndex()
        self.instrument.set_chamber(i)

    def set_bridge1(self):
        """ Set bridge channel 1 according to bridge1excitationentry and bridge1powerentry"""
        excitation = float(self.bridge1excitationentry.text())
        power = float(self.bridge1powerentry.text())
        self.instrument.set_bridge(1,excitation,power)

    def set_bridge2(self):
        """ Set bridge channel 2 according to bridge2excitationentry and bridge2powerentry"""
        excitation = float(self.bridge2excitationentry.text())
        power = float(self.bridge2powerentry.text())
        self.instrument.set_bridge(2,excitation,power)

    def set_bridge3(self):
        """ Set bridge channel 3 according to bridge3excitationentry and bridge3powerentry"""
        excitation = float(self.bridge3excitationentry.text())
        power = float(self.bridge3powerentry.text())
        self.instrument.set_bridge(3,excitation,power)

    def set_bridge4(self):
        """ Set bridge channel 4 according to bridge4excitationentry and bridge4powerentry"""
        excitation = float(self.bridge4excitationentry.text())
        power = float(self.bridge4powerentry.text())
        self.instrument.set_bridge(4,excitation,power)

    def meas_bridge1(self):
        """ Measure bridge channel 1 resistance in ohms. """
        self.bridge1resistanceentry.setText(str(self.instrument.bridge1))

    def meas_bridge2(self):
        """ Measure bridge channel 2 resistance in ohms. """
        self.bridge2resistanceentry.setText(str(self.instrument.bridge2))

    def meas_bridge3(self):
        """ Measure bridge channel 3 resistance in ohms. """
        self.bridge3resistanceentry.setText(str(self.instrument.bridge3))

    def meas_bridge4(self):
        """ Measure bridge channel 4 resistance in ohms. """
        self.bridge4resistanceentry.setText(str(self.instrument.bridge4))

    def update_status(self):
        """ Update entries of temperatureentry, temperaturestatusentry, 
            fieldentry, magnetstatusentry, pressureentry, heliumentry, chamberentry. 
        """
        self.temperatureentry.setText(str(self.instrument.temperature))
        #sleep(delay)
        self.temperaturestatusentry.setText(self.instrument.temperature_status)
        #sleep(delay)
        self.fieldentry.setText(str(self.instrument.field))
        #sleep(delay)
        self.magnetstatusentry.setText(self.instrument.magnet_status)
        #sleep(delay)
        self.pressureentry.setText(str(self.instrument.pressure))
        #sleep(delay)
        #self.heliumentry.setText(str(self.instrument.helium_level))
        #sleep(delay)
        self.chamberentry.setText(self.instrument.chamber)
        #sleep(delay)

    def run_step(self,command,value,rate):
        """ Execute command specified by index in the sequencedropdown with floating
            point value and rate.
        """
        self.step_finished = False
        if command == 0:
            self.instrument.set_temperature(value,rate)
            while not self.step_finished and not self.should_stop:
                if self.instrument.temperature_status == "Stable":
                    # temperature sweep finished
                    self.step_finished = True
                    break
                sleep(self.check_interval)
        elif command == 1:
            self.instrument.set_field_driven(value,rate)
            while not self.step_finished and not self.should_stop:
                if self.instrument.magnet_status == "Driven mode stable":
                    # field sweep finished
                    self.step_finished = True
                    break
                sleep(self.check_interval)
        elif command == 2:
            self.instrument.set_field_persistent(value,rate)
            while not self.step_finished and not self.should_stop:
                if self.instrument.magnet_status == "Persistent mode stable":
                    # field sweep finished
                    self.step_finished = True
                    break
                sleep(self.check_interval)
        elif command == 3:
            # wait for value minutes
            while not self.step_finished and not self.should_stop:
                sleep(value*60)
                self.step_finished = True
        elif command == 4:
            self.instrument.shutdown_potops()
            while not self.step_finished and not self.should_stop:
                if self.instrument.temperature_status == "Standby":
                    # shutdown finished
                    self.step_finished = True
                    break
                sleep(self.check_interval)
        elif command == 5:
            self.instrument.shutdown_continuous()
            while not self.step_finished and not self.should_stop:
                if self.instrument.temperature_status == "Standby":
                    # shutdown finished
                    self.step_finished = True
                    break
                sleep(self.check_interval)

    @Slot()
    def run_sequence_thread(self):
        """ Put run_sequence function on a different thread than GUI. """
        # Construct worker classes for threadpool
        class JobRunner(QRunnable):
            def __init__(self,fun):
                super().__init__()
                self.is_killed = False
                self.function = fun
    
            @Slot()
            def run(self):
                while not self.is_killed:
                    self.function()
                    self.kill() # stop running after executing function once

            def kill(self):
                self.is_killed = True
        
        self.runner = JobRunner(self.run_sequence)
        self.threadmanager.start(self.runner)

    def run_sequence(self):
        """ Run the sequence currently in treeview. Set the ongoing row background to 
            ongoingbrush
        """
        sequence_length = self.sequencetree.topLevelItemCount()
        # First set all the row background to defaultbrush
        for i in range(sequence_length):
            self.sequencetree.topLevelItem(i).setBackground(0,self.defaultbrush)
            self.sequencetree.topLevelItem(i).setBackground(1,self.defaultbrush)
            self.sequencetree.topLevelItem(i).setBackground(2,self.defaultbrush)

        self.current_step = 0
        self.step_finished = False
        self.should_stop = False
        
        for j in range(sequence_length):
            item = self.sequencetree.topLevelItem(j)
            item.setBackground(0,self.ongoingbrush)
            item.setBackground(1,self.ongoingbrush)
            item.setBackground(2,self.ongoingbrush)
            if j > 0:
                # change previous segment back to finished brush
                self.sequencetree.topLevelItem(j-1).setBackground(0,self.finishedbrush)
                self.sequencetree.topLevelItem(j-1).setBackground(1,self.finishedbrush)
                self.sequencetree.topLevelItem(j-1).setBackground(2,self.finishedbrush)
            self.current_step = j
            command = self.sequence_commands.index(item.text(0))
            value = float(item.text(1))
            rate = float(item.text(2))
            log.info("Running command " + self.sequence_commands[command] + ", end value = " + item.text(1) + ", rate = " + item.text(2))
            self.run_step(command,value,rate)
            if self.should_stop:
                break
        
        # clean up last row when entire sequence finishes
        self.sequencetree.topLevelItem(sequence_length-1).setBackground(0,self.finishedbrush)
        self.sequencetree.topLevelItem(sequence_length-1).setBackground(1,self.finishedbrush)
        self.sequencetree.topLevelItem(sequence_length-1).setBackground(2,self.finishedbrush)
        log.info("Sequence finished.")

    def stop_sequence(self):
        """ Abort current sequence command and stop sequence run, set current step background as stoppedbrush. """
        self.should_stop = True
        self.instrument.abort_sequence()
        self.runner.kill()
        if self.current_step == self.sequencetree.topLevelItemCount()-1 and self.step_finished == True:
            ### we've finished the last step
            log.info("Sequence aborted after finishing.")
        else:
            self.sequencetree.topLevelItem(self.current_step).setBackground(0,self.stoppedbrush)
            self.sequencetree.topLevelItem(self.current_step).setBackground(1,self.stoppedbrush)
            self.sequencetree.topLevelItem(self.current_step).setBackground(2,self.stoppedbrush)
            log.info("Sequence aborted.")


    def preview_widget(self, parent=None):
        """ Return a widget suitable for preview during loading,
        not implemented really
        """
        return PPMSControlWidget("PPMS control preview",
                                        instrument=None,
                                        parent=parent,
                                    )

    def send_command(self):
        """ Send GPIB command to PPMS. """
        command = self.GPIBCommandentry.text()
        self.instrument.write(command)
        log.info("Command " + command + " sent to " + self.name)

    def query_command(self):
        """ Send GPIB command to PPMS and read the response. """
        command = self.GPIBCommandentry.text()
        query = self.instrument.ask(command)
        self.GPIBReturnentry.setText(query)
        log.info("Query " + command + " sent to " + self.name + ", return is " + query)


