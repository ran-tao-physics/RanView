#
# This file is modified from the PyMeasure package.

# =============================================================================
# Libraries / modules
# =============================================================================

import logging
from time import sleep, time
import numpy as np
from pymeasure.instruments import Instrument
from pymeasure.instruments.validators import modular_range_bidirectional
from pymeasure.instruments.validators import strict_discrete_set
from pymeasure.instruments.validators import strict_range
from dsp52XXbase import DSP52XXBase


# =============================================================================
# Logging
# =============================================================================

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())
delay = 0.1

# =============================================================================
# Instrument file
# =============================================================================


class DSP52XX_ar(DSP52XXBase):
    """Represents the Signal Recovery DSP 52XX lock-in amplifier.

    Class inherits commands from the DSPBase parent class and utilizes dynamic
    properties for various properties and includes additional functionality.

    .. code-block:: python

        lockin52XX = DSP52XX_ar("GPIB0::12::INSTR")
        lockin52XX.imode = "voltage mode"       # Set to measure voltages
        lockin52XX.reference = "internal"       # Use internal oscillator
        lockin52XX.fet = 1                      # Use FET pre-amp
        lockin52XX.shield = 0                   # Ground shields
        lockin52XX.coupling = 0                 # AC input coupling
        lockin52XX.time_constant = 0.10         # Filter time set to 100 ms
        lockin52XX.sensitivity = 2E-3           # Sensitivity set to 2 mV
        lockin52XX.frequency = 100              # Set oscillator frequency to 100 Hz
        lockin52XX.voltage = 1                  # Set oscillator amplitude to 1 V
        lockin52XX.gain = 20                    # Set AC gain to 20 dB
        print(lockin52XX.x)                     # Measure X channel voltage
        lockin52XX.shutdown()                   # Instrument shutdown

    """

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Dynamic values - Override base class validator values
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    frequency_values = [0.001, 2.5e5]
    harmonic_values = [1, 65535]
    curve_buffer_bit_values = [1, 2097151]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Constants
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    CURVE_BITS = ['x', 'y', 'magnitude', 'phase', 'sensitivity', 'adc1',
                  'adc2', 'adc3', 'adc4', 'ratio', 'log ratio',
                  'event', 'frequency part 1', 'frequency part 2'
                  ]
    
    model = "DSP52XX"

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Initializer
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, adapter, name="Signal Recovery DSP 52XX", **kwargs):
        super().__init__(
            adapter,
            name,
            **kwargs
        )

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Additional properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def auto_range(self):
        ### increase or decrease sensitivity by one step when magnitude of signal is out of 0.1-0.9 of current sensitivity scale
        # sensitivity = self.sensitivity
        # if abs(self.mag) > 0.9*sensitivity:
        #     while abs(self.mag) > 0.9*sensitivity:
        #         self.write("SEN %d" % (int(self.ask("SEN")) + 1))
        #         sensitivity = self.sensitivity
        # elif abs(self.mag) < 0.1*sensitivity:
        #     while abs(self.mag) < 0.1*sensitivity:
        #         self.write("SEN %d" % (int(self.ask("SEN")) - 1))
        #         sensitivity = self.sensitivity 
        if abs(int(self.ask("MAG"))) > 9000 or abs(int(self.ask("MAG"))) < 1000:
            while abs(int(self.ask("MAG"))) > 9000 or abs(int(self.ask("MAG"))) < 1000:
                ### need to change sensitivity, then change time constant to 0.1s to capture the quick change
                current_tc = int(self.ask("TC"))
                self.write("TC 4")
                sleep(delay)
                current_sen = int(self.ask("SEN"))
                if abs(int(self.ask("MAG"))) > 9000:
                    self.write("SEN %d" % (current_sen + 1))
                elif abs(int(self.ask("MAG"))) < 1000:
                    self.write("SEN %d" % (current_sen - 1))
                sleep(1) # give lock-in 1s to settle before checking again
            self.write("TC %d" % current_tc) ### change back to original time constant
            sleep(10) ### give lock-in 10s to settle before measuring
