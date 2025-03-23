import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

import sys
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem
from time import sleep, time
from datetime import datetime
from pymeasure.log import console_log
from pymeasure.display.Qt import QtWidgets
from managed_dock_window_2plot import ManagedDockWindow_2plot
from pymeasure.experiment import Procedure, Results
from pymeasure.experiment import IntegerParameter, FloatParameter, Parameter
from pymeasure.display.widgets import TableWidget, LogWidget
from PlotSpectrumWidget import SpectrumPlotWidget
from InstrumentControlWidget import InstrumentControltWidget
from PlotDataWidget import PlotDataWidget
from pymeasure.experiment import Procedure, Results, IntegerParameter, FloatParameter, Parameter, BooleanParameter
from dsp72XX_ar import DSP72XX_ar
from sr830_ar import SR830_ar
from dsp52XX_ar import DSP52XX_ar

from pymeasure.display.Qt import QtWidgets

delay = 0.1 # 0.1s delay in taking measurements for communication time

class SetupWindow(QtWidgets.QMainWindow):
    """
    A window for setting up communication ports
    """
    supported_lockins = ['SR830','DSP72XX','DSP52XX']
    # variable for lockin ports
    global lockin_ports, lockin_models, ppms_port, y_axes_labels, lockin_var, data_columns
    lockin_ports = []
    lockin_models = []
    lockin_var = []
    y_axes_labels = []
    data_columns = []

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Experiment setup')
        self.main = QtWidgets.QWidget(self)
        self.setCentralWidget(self.main)

        vbox = QtWidgets.QVBoxLayout()
        vbox.setSpacing(10)

        hbox = QtWidgets.QHBoxLayout()
        hbox.setSpacing(10)
        hbox.setContentsMargins(-1, 6, -1, -1)
        
        hbox2 = QtWidgets.QHBoxLayout()
        hbox2.setSpacing(10)
        hbox2.setContentsMargins(-1, 6, -1, -1)

        self.instrumentmodellabel = QtWidgets.QLabel()
        self.instrumentmodellabel.setText('Instrument model:')

        self.instrumentportlabel = QtWidgets.QLabel()
        self.instrumentportlabel.setText('Instrument port:')

        self.instrumentmodeldropdown = QtWidgets.QComboBox()
        self.instrumentmodeldropdown.addItems(self.supported_lockins)

        self.instrumentportentry = QtWidgets.QLineEdit()
        self.instrumentportentry.setText("GPIB0::21::INSTR")

        self.add_instrument_button = QtWidgets.QPushButton(text='Add instrument')
        self.add_instrument_button.clicked.connect(self.add_instrument)

        self.delete_selected_instrument_button = QtWidgets.QPushButton(text='Delete selected instrument')
        self.delete_selected_instrument_button.clicked.connect(self.delete_selected_instrument)

        self.set_com_settings_button = QtWidgets.QPushButton(text='Set communication ports')
        self.set_com_settings_button.clicked.connect(self.set_com_settings)

        self.tree = QtWidgets.QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Instrument model", "GPIB port"])

        treebox = QtWidgets.QHBoxLayout()
        treebox.setSpacing(10)
        treebox.setContentsMargins(-1, 6, -1, -1)
        treebox.addWidget(self.tree)

        hbox.addWidget(self.instrumentmodellabel)
        hbox.addWidget(self.instrumentmodeldropdown)
        hbox.addWidget(self.instrumentportlabel)
        hbox.addWidget(self.instrumentportentry)
        hbox2.addWidget(self.add_instrument_button)
        hbox2.addWidget(self.delete_selected_instrument_button)
        hbox2.addWidget(self.set_com_settings_button)
        vbox.addLayout(hbox)
        vbox.addLayout(hbox2)
        vbox.addLayout(treebox)
        self.main.setLayout(vbox)

    def set_com_settings(self):
        lockin_ports = []
        lockin_models = []
        lockin_var = []
        ppms_var = None
        y_axes_labels = []
        data_columns = []
        # print(self.tree.topLevelItemCount())
        for row in range(self.tree.topLevelItemCount()):
            # print(self.tree.topLevelItem(row).text(0))
            lockin_models.append(self.tree.topLevelItem(row).text(0))
            lockin_ports.append(self.tree.topLevelItem(row).text(1))
        
        data_columns = ['Elapsed Time (s)', 'Elapsed Time (hr)']
        y_axes_labels = ['Elapsed Time (hr)']
        global widget_list

        widget_list = (SpectrumPlotWidget(name="Spectrum"),)

        lockin_var = [None]*len(lockin_ports)
        
        for i in range(len(lockin_ports)):
            if lockin_models[i] ==  'DSP52XX':
                y_axes_labels.append('Lock-In ' + str(i+1) + ' - X (V)')
                y_axes_labels.append('Lock-In ' + str(i+1) + ' - Y (V)')
            else:
                y_axes_labels.append('Lock-In ' + str(i+1) + ' - X (V)')
                y_axes_labels.append('Lock-In ' + str(i+1) + ' - Y (V)')
                y_axes_labels.append('Lock-In ' + str(i+1) + ' - Frequency (Hz)')
                y_axes_labels.append('Lock-In ' + str(i+1) + ' - Osc Amp (V)')
            if lockin_models[i] == 'SR830':
                    lockin_var[i] = SR830_ar(lockin_ports[i])
            elif lockin_models[i] == 'DSP72XX': 
                    lockin_var[i] = DSP72XX_ar(lockin_ports[i])
            elif lockin_models[i] == 'DSP52XX':
                    lockin_var[i] = DSP52XX_ar(lockin_ports[i],timeout=12000) # use 12000ms timeouts because dsp52XX sometimes take a long time to reply, also add a bit of query delay to allow for time between write and read

            if lockin_models[i] ==  'DSP52XX':
                data_columns.append('Lock-In ' + str(i+1) + ' - X (V)')
                data_columns.append('Lock-In ' + str(i+1) + ' - Y (V)')
            else:
                data_columns.append('Lock-In ' + str(i+1) + ' - X (V)')
                data_columns.append('Lock-In ' + str(i+1) + ' - Y (V)')
                data_columns.append('Lock-In ' + str(i+1) + ' - Frequency (Hz)')
                data_columns.append('Lock-In ' + str(i+1) + ' - Osc Amp (V)')

            widget_list = widget_list + (InstrumentControltWidget(name=lockin_ports[i]+" " + lockin_models[i],instrument=lockin_var[i]),)

        class MainWindow(ManagedDockWindow_2plot):

            def __init__(self):

                class TestProcedure(Procedure):

                    DATA_COLUMNS = data_columns
                    def __init__(self, **kwargs):
                        self.DATA_COLUMNS = data_columns
                        super().__init__(**kwargs)

                    def acquire_data(self,startT):
                        data = {
                            'Elapsed Time (s)': round(time()-startT,3)}
                        data['Elapsed Time (hr)'] = round(time()-startT,3)/3600
                        for i in range(len(lockin_ports)):
                            if lockin_models[i] ==  'DSP52XX':
                                ### Check manually if auto-range is needed
                                ### 52XX is slow in responding so one needs to delay between ask and write

                                if abs(int(lockin_var[i].ask("MAG"))) > 9000 or abs(int(lockin_var[i].ask("MAG"))) < 2000:
                                    ### need to change sensitivity, then change time constant to 0.1s to capture the quick change
                                    current_tc = int(lockin_var[i].ask("TC"))
                                    lockin_var[i].write("TC 4")
                                    while abs(int(lockin_var[i].ask("MAG"))) > 9000 or abs(int(lockin_var[i].ask("MAG"))) < 1000:
                                        current_sen = int(lockin_var[i].ask("SEN"))
                                        if abs(int(lockin_var[i].ask("MAG"))) > 9000:
                                            lockin_var[i].write("SEN %d" % (current_sen + 1))
                                        elif abs(int(lockin_var[i].ask("MAG"))) < 1000:
                                            lockin_var[i].write("SEN %d" % (current_sen - 1))
                                        sleep(1) # give lock-in 1s to respond before checking again
                                    ### change back to measurement TC after we're finished
                                    lockin_var[i].write("TC %d" % current_tc)
                                    sleep(10) ### give lock-in 10s to settle before measuring

                                data['Lock-In ' + str(i+1) + ' - X (V)'] = lockin_var[i].x
                                sleep(delay)
                                data['Lock-In ' + str(i+1) + ' - Y (V)'] = lockin_var[i].y
                                sleep(delay)
                            else:
                                lockin_var[i].auto_range() # auto-range before acquiring data, auto_sensitivity doesn't work due to weird time-out problems
                                data['Lock-In ' + str(i+1) + ' - X (V)'] = lockin_var[i].x
                                data['Lock-In ' + str(i+1) + ' - Y (V)'] = lockin_var[i].y
                                data['Lock-In ' + str(i+1) + ' - Frequency (Hz)'] = lockin_var[i].frequency
                                data['Lock-In ' + str(i+1) + ' - Osc Amp (V)'] = lockin_var[i].voltage
                        self.emit('results', data)
                        # self.emit('progress', 100 * (i + 1) / self.iterations) ### for giving a progress bar
                        log.debug("Emitting results: %s" % data)    
        
                    def startup(self):
                        log.info("Starting measurement interface")

                    def execute(self):
                        startT = time()
        
                        # Default
                        while True:
                            self.acquire_data(startT)
                            sleep(delay)
        
                            if self.should_stop():
                                log.warning("Caught the stop flag in the procedure")
                                break

                super().__init__(
                    procedure_class=TestProcedure,
                    x_axis=['Elapsed Time (s)'],
                    y_axis=y_axes_labels,
                    widget_list=widget_list,
                    sequencer=False,
                )
                self.setWindowTitle('Maxview PPMS')
                self.directory = r'C:\\Users\\rt505\\OneDrive - University of Cambridge\\Desktop\\PhD\\MaxView\\'

            def queue(self, procedure=None):
                directory = self.directory
                timestr = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = directory+timestr+r'.txt'

                if procedure is None:
                    procedure = self.make_procedure()

                results = Results(procedure, filename)
                experiment = self.new_experiment(results)

                self.manager.queue(experiment)
        self.meas_window = MainWindow() 
        self.meas_window.show()

    def add_instrument(self):
        model = self.instrumentmodeldropdown.currentText()
        port = self.instrumentportentry.text()
        item = QtWidgets.QTreeWidgetItem([model,port])
        self.tree.insertTopLevelItem(0, item)

    def delete_selected_instrument(self):
        for item in self.tree.selectedItems():
            i = self.tree.indexOfTopLevelItem(item)
            self.tree.takeTopLevelItem(i)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = SetupWindow()
    #window = MainWindow()
    window.show()
    sys.exit(app.exec()) # start application