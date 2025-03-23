##import sys
import logging
import pyqtgraph as pg

##from pymeasure.display.curves import Crosshairs

from pymeasure.display.Qt import QtCore, QtWidgets
#from pyqtgraph.Qt import QtCore, QtWidgets
from pymeasure.display.widgets.tab_widget import TabWidget
##from pymeasure.display.widgets.plot_frame import PlotFrame
import numpy as np
from scipy.optimize import curve_fit
from datetime import datetime
from seabreeze.spectrometers import Spectrometer
from time import sleep
import serial

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

class SpectrumCurve(pg.PlotDataItem):
    """ Creates a curve loaded from the file given by the filename
    """

    def __init__(self, filename, peakmax, wdg=None, **kwargs):
        super().__init__(**kwargs)
        #"C:/Users/rt505/OneDrive - University of Cambridge/Desktop/PhD/MaxView/240112_ambient test in probe ruby 100ms 1 scan binary.txt"
        with open(filename) as f:
            n = len(list(f))
        sp = np.loadtxt(filename,skiprows=17,max_rows=n-17-2)
        sp_l = sp[:,0]
        sp_a = sp[:,1]
        ind_fit=[i for i in range(len(sp_l)) if sp_l[i] < peakmax and sp_l[i] > 690] # lower bound is 690 nm
        sp_a_fit=sp_a[ind_fit]
        sp_l_fit=sp_l[ind_fit]
        self.setData(sp_l_fit, sp_a_fit)

        self.wdg = wdg
        self.pen = kwargs.get('pen', None)
        self.color = self.opts['pen'].color()

    def set_color(self, color):
        self.pen.setColor(color)
        self.color = self.opts['pen'].color()
        self.updateItems(styleUpdate=True)

class SpectrumPlotFrame(QtWidgets.QFrame):
    """ Puts a PyQtGraph Plot into a frame. Modified from
    pymeasure.display.plot_frame
    """

    LABEL_STYLE = {'font-size': '10pt', 'font-family': 'Arial', 'color': '#000000'}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()


    def _setup_ui(self):
        self.setAutoFillBackground(False)
        self.setStyleSheet("background: #fff")
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.setMidLineWidth(1)

        vbox = QtWidgets.QVBoxLayout(self)

        self.plot_widget = pg.PlotWidget(self, background='#ffffff')
        vbox.addWidget(self.plot_widget)
        self.setLayout(vbox)
        self.plot = self.plot_widget.getPlotItem()
        self.plot.setLabel('left','Intensity',units='a.u.')
        self.plot.setLabel('bottom','Wavelength',units='nm')

        # self.crosshairs = Crosshairs(self.plot,
        #                              pen=pg.mkPen(color='#AAAAAA',
        #                                           style=QtCore.Qt.PenStyle.DashLine))
        # self.crosshairs.coordinates.connect(self.update_coordinates)

        # self.timer = QtCore.QTimer(self)
        # self.timer.timeout.connect(self.crosshairs.update)



class SpectrumPlotWidget(TabWidget, QtWidgets.QWidget):
    """ Extends SpectrumPlotFrame to a tab in the GUI
    """
    

    def __init__(self, name, linewidth=2, parent=None):
        super().__init__(name, parent)
        self.linewidth = linewidth
        self._setup_ui()
        self._layout()

    def _setup_ui(self):
        self.delay = 0.1 # delay time in sending serial command
        self.timeout = 10 # 10 second time-out for serial communication

        self.loadButton = QtWidgets.QPushButton(text='Load')
        self.loadButton.clicked.connect(self.loadfilename)
        self.measureButton = QtWidgets.QPushButton(text='Measure')
        self.measureButton.clicked.connect(self.meas_spec)
        self.fitButton = QtWidgets.QPushButton(text='Fit')
        self.fitButton.clicked.connect(self.fit_gaussian)

        self.peakwaveentry = QtWidgets.QLineEdit()
        self.peakwaveentry.setText("694.3")
        self.quickfitButton = QtWidgets.QPushButton(text='Quick fit')
        self.quickfitButton.clicked.connect(self.quick_fit)
        self.pressurelabel = QtWidgets.QLabel(text='p = 0.0000 kbar')
        self.forcelabel = QtWidgets.QLabel(text='F = 0.00 kN')

        self.filelabel = QtWidgets.QLabel(text='File name')
        self.fileentry = QtWidgets.QLineEdit()
        self.filename = ""

        self.specnumlabel = QtWidgets.QLabel(text='Spectrometer serial number')
        self.specnumentry = QtWidgets.QLineEdit()
        self.specnumentry.setText("USB2+H05410")

        self.boxcarlabel = QtWidgets.QLabel(text='Boxcar width')
        self.boxcarentry = QtWidgets.QLineEdit()
        self.boxcarentry.setText("1")

        self.scannumlabel = QtWidgets.QLabel(text='Scans to average')
        self.scannumentry = QtWidgets.QLineEdit()
        self.scannumentry.setText("1")

        self.inttimelabel = QtWidgets.QLabel(text='Integration time (ms)')
        self.inttimeentry = QtWidgets.QLineEdit()
        self.inttimeentry.setText("100")

        self.laserlabel = QtWidgets.QLabel(text='Laser module port')
        self.laserentry = QtWidgets.QLineEdit()
        self.laserentry.setText("COM9") # COM4 on Mott 466 PC

        self.sercomentry = QtWidgets.QLineEdit()
        self.sercomentry.setText("LON")

        self.sercomButton = QtWidgets.QPushButton(text='Write serial command')
        self.sercomButton.clicked.connect(self.write_serial_command)

        self.fitnumlabel = QtWidgets.QLabel(text='Fit points on either side of peak')
        self.fitnumentry = QtWidgets.QLineEdit()
        self.fitnumentry.setText("5")

        self.peakwidthlabel = QtWidgets.QLabel(text='Peak width estimate')
        self.peakwidthentry = QtWidgets.QLineEdit()
        self.peakwidthentry.setText("0.1")

        self.peakheightlabel = QtWidgets.QLabel(text='Peak height estimate')
        self.peakheightentry = QtWidgets.QLineEdit()
        self.peakheightentry.setText("11000")

        self.bkglabel = QtWidgets.QLabel(text='Background estimate')
        self.bkgentry = QtWidgets.QLineEdit()
        self.bkgentry.setText("4000")

        self.maxwavelabel = QtWidgets.QLabel(text='Max wavelength plotted')
        self.maxwaveentry = QtWidgets.QLineEdit()
        self.maxwaveentry.setText("705")

        self.temperaturelabel = QtWidgets.QLabel(text='Temperature')
        self.temperatureentry = QtWidgets.QLineEdit()
        self.temperatureentry.setText("300")

        self.rubycalibration = QtWidgets.QComboBox()
        self.rubycalibration.addItems(['RT calibration','300K calibration','4.5K calibration'])


        self.plot_frame = SpectrumPlotFrame(
            parent=self,
        )
        
        self.plot = self.plot_frame.plot

        self.fitlabel=None

        y_axis=self.plot.getAxis('left')
        y_axis.enableAutoSIPrefix(enable=False) # stop auto converting units from a.u. to 10^3 a.u. for intensity

    def _layout(self):
        vbox = QtWidgets.QVBoxLayout(self)
        vbox.setSpacing(10)

        filebox = QtWidgets.QHBoxLayout()
        filebox.setSpacing(10)
        filebox.setContentsMargins(-1, 6, -1, 6)
        filebox.addWidget(self.filelabel)
        filebox.addWidget(self.fileentry)
        filebox.addWidget(self.loadButton)
        filebox.addWidget(self.measureButton)
        filebox.addWidget(self.fitButton)
        filebox.addWidget(self.peakwaveentry)
        filebox.addWidget(self.quickfitButton)
        filebox.addWidget(self.pressurelabel)
        filebox.addWidget(self.forcelabel)

        serialbox = QtWidgets.QHBoxLayout()
        serialbox.setSpacing(10)
        serialbox.setContentsMargins(-1, 6, -1, 6)
        serialbox.addWidget(self.laserlabel)
        serialbox.addWidget(self.laserentry)
        serialbox.addWidget(self.sercomentry)
        serialbox.addWidget(self.sercomButton)

        spectrometerbox = QtWidgets.QHBoxLayout()
        spectrometerbox.setSpacing(10)
        spectrometerbox.setContentsMargins(-1, 6, -1, 6)
        spectrometerbox.addWidget(self.specnumlabel)
        spectrometerbox.addWidget(self.specnumentry)
        spectrometerbox.addWidget(self.boxcarlabel)
        spectrometerbox.addWidget(self.boxcarentry)
        spectrometerbox.addWidget(self.scannumlabel)
        spectrometerbox.addWidget(self.scannumentry)
        spectrometerbox.addWidget(self.inttimelabel)
        spectrometerbox.addWidget(self.inttimeentry)

        fitspecbox = QtWidgets.QHBoxLayout()
        fitspecbox.setSpacing(10)
        fitspecbox.setContentsMargins(-1, 6, -1, 6)
        fitspecbox.addWidget(self.fitnumlabel)
        fitspecbox.addWidget(self.fitnumentry)
        fitspecbox.addWidget(self.peakwidthlabel)
        fitspecbox.addWidget(self.peakwidthentry)
        fitspecbox.addWidget(self.peakheightlabel)
        fitspecbox.addWidget(self.peakheightentry)
        fitspecbox.addWidget(self.bkglabel)
        fitspecbox.addWidget(self.bkgentry)
        fitspecbox.addWidget(self.temperaturelabel)
        fitspecbox.addWidget(self.temperatureentry)
        fitspecbox.addWidget(self.rubycalibration)

        vbox.addLayout(filebox)
        vbox.addLayout(serialbox)
        vbox.addLayout(spectrometerbox)
        vbox.addLayout(fitspecbox)
        vbox.addWidget(self.plot_frame)
        self.setLayout(vbox)

    def load_cell_calibration(self,V):
        #f = -0.015 + 0.129938*force
        # new calibration with 10V input to load cell instead of 20V
        #f = -0.00525961239506678 + 0.243548554254327*V

        ### calibration with integrated setup, voltage in volts
        f = 0.109774389100682 + 2.31626148365727*V
        return f
    
    def loadfilename(self):
        self.filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Single File', '', 'Spectrum (*.txt);;All Files (*)')
        self.fileentry.setText(str(self.filename))
        log.info("Clearing plot")
        self.clear_widget()
        if self.fitlabel is not None:
            log.info("Removing old fit label")
            self.fitlabel.setText("")
        log.info("Loading spectrum from " + self.filename)
        self.load(self.new_spectrum_curve())

        # parse file name
        s = self.filename
        separator = '_'
        num_sep = [pos for pos, char in enumerate(s) if char == separator]
        len_sep = len(num_sep)
        str_TK = s[(num_sep[len_sep-1]+1):]
        if str_TK[-5] == "K": # "K.txt" at the end
            str_T = s[(num_sep[len_sep-1]+1):(-5)]
            ind_p_T=str_T.find('p')
            if ind_p_T == -1:
                T = str_T
            else:
                T = str_T[0:ind_p] + "." + str_T[(ind_p+1):]
            self.temperatureentry.setText(T)           
            log.info("Loaded spectrum taken at " + T + " K")
    
        str_marker = s[(num_sep[len_sep-2]+1):num_sep[len_sep-1]]
        if str_marker == "up":
            s_f=s[(num_sep[len_sep-3]+1):num_sep[len_sep-2]]
        else:
            s_f=s[(num_sep[len_sep-2]+1):num_sep[len_sep-1]]
        ind_N=s_f.find('N')
        if ind_N == -1:
            ### this is for old files which records the voltage in mV e.g. 23p3
            ind_p=s_f.find('p')
            if ind_p == -1: # integer number
                force = float(s_f)
            else:
                force = float(s_f[0:ind_p]) + float(s_f[(ind_p+1):])/np.power(10,len(s_f)-1-ind_p)
            f = self.load_cell_calibration(force)
            self.forcelabel.setText('F = '+ '{:.2f}'.format(f)+' kN')
        else:
            ### new file names should automatically read the force, e.g. 15p5kN
            s_f = s_f[:-2] # remove the kN at the end
            ind_p=s_f.find('p')
            if ind_p == -1: # integer number
                force = float(s_f)
            else:
                force = float(s_f[0:ind_p]) + float(s_f[(ind_p+1):])/np.power(10,len(s_f)-1-ind_p)
            f = self.load_cell_calibration(force)
            self.forcelabel.setText('F = '+ '{:.2f}'.format(f)+' kN')

        log.info('Loaded spectrum taken at ' + '{:.2f}'.format(f) + ' kN')

    def sizeHint(self):
        return QtCore.QSize(300, 600)

    def new_spectrum_curve(self, color=pg.intColor(0), **kwargs):
        ### draw new spectrum curve, note cannot rename this to new_curve otherwise dock window cannot draw curves
        if 'pen' not in kwargs:
            kwargs['pen'] = pg.mkPen(color=color, width=self.linewidth)
        if 'antialias' not in kwargs:
            kwargs['antialias'] = False
        curve = SpectrumCurve(filename=self.filename,
                              peakmax=float(self.maxwaveentry.text()),
                             wdg=self,
                             **kwargs,
                             )
        curve.setSymbol(None)
        curve.setSymbolBrush(None)
        return curve

    def load(self, curve):
        self.plot.addItem(curve)

    def remove(self, curve):
        self.plot.removeItem(curve)

    def set_color(self, curve, color):
        """ Change the color of the pen of the curve """
        curve.set_color(color)

    def preview_widget(self, parent=None):
        """ Return a widget suitable for preview during loading,
        not implemented really
        """
        return SpectrumPlotWidget("Plot preview",
                          parent=parent,
                          )

    def clear_widget(self):
        self.plot.clear()

    def gaussian(self, x, m, s, A, B): # x must be first independent variable for fitting
        return A*np.exp(-np.power(x-m,2)/2/s/s) + B

    def RT_calibration(self, l):
        # same as 300K calibration but use lambda0=694.3nm measured by Patricia on our rubies
        return 19040/7.665*(np.power((l/694.3),7.665)-1)

    def calibration_with_4p5K_fit(self,l,T):
        R1_peak = 1e7/(14423+4.49e-2*T-4.81e-4*T*T+3.71e-7*T*T*T) # return calibrated wavelength in nm for R1 peak
        return 17620*np.log((l-R1_peak+693.327785)/693.327785)

    def calibration_with_300K_fit(self,l,T):
        R1_peak = 1e7/(14423+4.49e-2*T-4.81e-4*T*T+3.71e-7*T*T*T) # return calibrated wavelength in nm for R1 peak
        R1_peak_300K = 1e7/(14423+4.49e-2*300-4.81e-4*300*300+3.71e-7*300*300*300)
        return 19040/7.665*(np.power(((l-R1_peak+R1_peak_300K)/R1_peak_300K),7.665)-1)
    
    def fit_gaussian(self):
        # Fit background from peak in intenstiy as function of wavelength for fitnumentry points above and below peak
        # to a Gaussian and return the fit function, fit parameters and parameter covariances
        # fit parameter initial guess is peakwaveentry, peakwidthentry, peakheightentry, bkgentry
        # output pressure from calibration function cal, error in pressure (positive and negative)
        N = int(self.fitnumentry.text())
        s = float(self.peakwidthentry.text())
        A = float(self.peakheightentry.text())
        B = float(self.bkgentry.text())
        peakmax = float(self.maxwaveentry.text())
        T = float(self.temperatureentry.text())
        calibration = self.rubycalibration.currentText()
        if calibration == "4.5K calibration":
            cal = lambda x: self.calibration_with_4p5K_fit(x,T)
        elif calibration == "300K calibration":
            cal = lambda x: self.calibration_with_300K_fit(x,T)
        elif calibration == "RT calibration":
            cal = self.RT_calibration

        if len(self.plot.listDataItems()) > 0:
            # use currently plotted data for fit
            log.info("Using currently plotted data for fitting")
            line = self.plot.listDataItems()[0]
            sp_l, sp_a = line.getData()
        else:
            log.info("Loading spectrum from " + self.filename)
            self.fileentry.setText(str(self.filename))
            curve = self.load(self.new_spectrum_curve())
            sp_l, sp_a = curve.getData()

        # ind_fit=[i for i in range(len(sp_l)) if sp_l[i] < peakmax]
        # sp_a_fit=sp_a[ind_fit]
        ind_peak=np.argmax(sp_a)
        peak = sp_l[ind_peak]
        fit_L=sp_l[(ind_peak-N):(ind_peak+N)]
        fit_A=sp_a[(ind_peak-N):(ind_peak+N)]
        popt, pcov = curve_fit(self.gaussian, fit_L, fit_A, p0=[peak,s,A,B])
        fit_fn = lambda x: self.gaussian(x, *popt)

        p=cal(popt[0])
        ppos=cal(popt[0]+np.sqrt(pcov[0,0]))
        pneg=cal(popt[0]-np.sqrt(pcov[0,0]))

        output = "p = " + '{:.4f}'.format(p) + " kbar, [" + '{:.4f}'.format(ppos) + ", " + '{:.4f}'.format(pneg) + "] kbar" + ", Peak = " + '{:.4f}'.format(popt[0]) + " nm, Width = " + '{:.4f}'.format(popt[1])+ ", Height = " + '{:.4f}'.format(popt[2])+ ", Background = " + '{:.4f}'.format(popt[3])
        log.info("Fitted peak with gaussian, obtained following fit parameters: " + output)
        mesh = np.linspace(sp_l[ind_peak-N],sp_l[ind_peak+N],100)
        if len(self.plot.listDataItems()) > 1:
            log.info("Removing old fit")
            self.plot.removeItem(self.plot.listDataItems()[1])
        self.plot.addItem(pg.PlotDataItem(x=mesh,y=fit_fn(mesh),symbol=None,pen=pg.mkPen(color=(0,102,255),width=2)))

        labels = "p = " + '{:.4f}'.format(p) + " kbar<br/>[" + '{:.4f}'.format(ppos) + ", " + '{:.4f}'.format(pneg) + "] kbar" + "<br/>Peak = " + '{:.4f}'.format(popt[0]) + " nm<br/>Width = " + '{:.4f}'.format(popt[1])+ "<br/>Height = " + '{:.4f}'.format(popt[2])+ "<br/>Background = " + '{:.4f}'.format(popt[3])
        
        if self.fitlabel is not None:
            log.info("Removing old fit label")
            self.fitlabel.setText(labels)
        else:
            self.fitlabel = pg.LabelItem(labels,color="#000000")
            self.fitlabel.setParentItem(self.plot)
            self.fitlabel.anchor(itemPos=(0.5, 0.5), parentPos=(0.8, 0.3))

        p_out="p = " + '{:.4f}'.format(p) + " kbar"
        self.pressurelabel.setText(p_out)

    def quick_fit(self):
        # Use peak wavelength entered in peakwaveentry and the temperature in temperatureentry
        # and the fit chosen in the drop down menu to calculate pressure
        # output pressure into text of pressurelabel
        T = float(self.temperatureentry.text())
        calibration = self.rubycalibration.currentText()
        if calibration == "4.5K calibration":
            cal = lambda x: self.calibration_with_4p5K_fit(x,T)
        elif calibration == "300K calibration":
            cal = lambda x: self.calibration_with_300K_fit(x,T)
        elif calibration == "RT calibration":
            cal = lambda x: self.RT_calibration(x)
        lambda_e = float(self.peakwaveentry.text())

        p=cal(lambda_e)
        p_out="p = " + '{:.4f}'.format(p) + " kbar"
        log.info("Quick fit of peak at " + self.peakwaveentry.text() + " nm gives " + p_out)
        self.pressurelabel.setText(p_out)

    def write_serial_command(self):
        serial_port = self.laserentry.text()
        serial_command = self.sercomentry.text()+"\n"
        ser = serial.Serial(serial_port,timeout=self.timeout) # 10 second time-out
        log.info("Communicating with laser module at serial port " + serial_port)
        ser.write(serial_command.encode())
        log.info("Writing to serial port " + self.sercomentry.text() + "\\n")
        sleep(self.delay)
        ser.close()
        log.info("Serial port closed")

    def meas_spec(self):
        log.info("Clearing graph")
        self.clear_widget()
        spec_ser_num=self.specnumentry.text()
        boxcarwidth = int(self.boxcarentry.text())
        scannum = int(self.scannumentry.text())
        peakmax = float(self.maxwaveentry.text())
        inttime = float(self.inttimeentry.text()) # in ms
        serial_port = self.laserentry.text()

        if spec_ser_num != '' and serial_port != '':
            spectrometer = Spectrometer.from_serial_number(spec_ser_num)
            spectrometer.integration_time_micros(inttime*1000)
            sp_l,sp_a=spectrometer.spectrum() # just for initializing sp_l and sp_a
            log.info("Loading spectrometer " + self.specnumentry.text() )
            ser = serial.Serial(serial_port,timeout=self.timeout) # 10 second time-out
            log.info("Communicating with laser module at serial port " + serial_port)
            ser.write('LON\n'.encode())
            log.info("Laser on")
            sleep(self.delay)
            ser.write('CON\n'.encode())
            log.info("Load cell on")
            sleep(self.delay)
            ser.write('READ\n'.encode())
            s=ser.read(6) # voltage in volts
            s=s.decode()[:-2] # get rid of /r at the end
            force = self.load_cell_calibration(float(s))
            log.info("Load cell voltage is " + s + " volts, which is " + str(force) + " kN")
            self.forcelabel.setText('F = '+ '{:.2f}'.format(force)+' kN')
            sleep(self.delay)
            ser.write('COFF\n'.encode())
            log.info("Load cell off")            

            for i in range(scannum):
                log.info("Measuring scan " + str(i+1) + ", integration time is" + self.inttimeentry.text() + " ms, boxcar width is " + self.boxcarentry.text() + ", averaging over " + self.scannumentry.text() + " scans, maximum wavelength plotted is " + self.maxwaveentry.text())
                if i == 1:
                    sp_l,sp_a=spectrometer.spectrum()
                    sp_a_boxcar = np.convolve(np.ones(2*boxcarwidth+1)/(2*boxcarwidth+1),sp_a) 
                    sp_a_boxcar = sp_a_boxcar[boxcarwidth:(boxcarwidth+len(intensity))]
                    # correct for points on edge that have less neighbors to average with
                    for j in range(boxcarwidth):
                        sp_a_boxcar[j] = sp_a_boxcar[j]*(2*boxcarwidth+1)/(boxcarwidth+1+j)
                        sp_a_boxcar[-1-j] = sp_a_boxcar[-1-j]*(2*boxcarwidth+1)/(boxcarwidth+1+j)
                    sp_a = sp_a_boxcar
                else:
                    wavelength, intensity = spectrometer.spectrum()
                    intensity_boxcar = np.convolve(np.ones(2*boxcarwidth+1)/(2*boxcarwidth+1),intensity) 
                    intensity_boxcar = intensity_boxcar[boxcarwidth:(boxcarwidth+len(intensity))]
                    # correct for points on edge that have less neighbors to average with
                    for j in range(boxcarwidth):
                        intensity_boxcar[j] = intensity_boxcar[j]*(2*boxcarwidth+1)/(boxcarwidth+1+j)
                        intensity_boxcar[-1-j] = intensity_boxcar[-1-j]*(2*boxcarwidth+1)/(boxcarwidth+1+j)
                    sp_a = sp_a + intensity_boxcar
            sp_a = sp_a/scannum
            sleep(self.delay)
            spectrometer.close() # close spectrometer to avoid it being occupied for other programs
            log.info("Spectrometer closed")
            ser.write('LOFF\n'.encode())
            log.info("Laser off")
            ser.close()
            log.info("Serial port closed")

        # First plot and fit the spectrum
        
        ind_fit=[i for i in range(len(sp_l)) if sp_l[i] < peakmax and sp_l[i] > 690] # lower bound is 690 nm to avoid divergence problems below 625 nm
        sp_a_fit=sp_a[ind_fit]
        sp_l_fit=sp_l[ind_fit]
        self.plot.addItem(pg.PlotDataItem(x=sp_l_fit,y=sp_a_fit,symbol=None,pen=pg.mkPen(color=pg.intColor(0),width=2)))

        self.fit_gaussian()

        # Then ask if we save entire spectrum
        now = datetime.now()
        now_str = now.strftime("%Y%m%d%H%M")
        temp = round(float(self.temperatureentry.text()))
        force_str = self.forcelabel.text()
        force_str = force_str[4:-3] # remove " kN" at the end and "F = " in front
        ind_p = force_str.find('.')
        if ind_p == -1: # integer number
            spec_name = now_str + '_' + str(int(float(force_str))) + 'kN' + '_' + str(temp) + 'K.txt'
        else:
            spec_name = now_str + '_' + force_str[:ind_p] + 'p' + force_str[(ind_p+1):] + 'kN' + '_' + str(temp) + 'K.txt'
        
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder')
        filename = directory + '/' + spec_name
        self.fileentry.setText(filename)
        self.filename = filename

        with open(filename, "w") as txt_file:
            for i in range(17): # to conform with spectrasuite format
                if i == 1:
                    txt_file.write(now.strftime("%Y-%m-%d %H:%M:%S")+"\n" ) # write timestamp
                elif i == 2:
                    txt_file.write(spec_ser_num+"\n" ) # write serial number
                elif i == 3:
                    txt_file.write("Integration time = " + str(inttime) + " ms"+"\n" ) # Write integration time
                elif i == 4:
                    txt_file.write("Boxcar width = " + str(boxcarwidth)+"\n" ) # Write boxcar width
                elif i == 5:
                    txt_file.write("Number of scans = " + str(scannum)+"\n" ) # Write scan number
                elif i == 6:
                    txt_file.write(str(temp) + " K"+"\n" ) # write temperature
                elif i == 7:
                    txt_file.write(self.forcelabel.text()+"\n" ) # write force applied
                elif i == 8:
                    txt_file.write(self.fitlabel.text+"\n" ) # write fitted pressure parameters in html format
                else:
                    txt_file.write(str(i) + "\n") 
            for line in zip(sp_l,sp_a):
                txt_file.write(format(line[0], '.2f')+ " " + format(line[1], '.2f') + "\n")
            txt_file.write('end' + "\n") # to conform with spectrasuite format add line at the end
        