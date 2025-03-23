#
# This file is modified from the PyMeasure package.

# =============================================================================
# Libraries / modules
# =============================================================================

from dsp_base_ar import DSPBase
from pymeasure.instruments import Instrument
from pymeasure.instruments.validators import strict_range
import logging
from time import sleep

# =============================================================================
# Logging
# =============================================================================

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# =============================================================================
# Instrument file
# =============================================================================


class DSP72XX_ar(DSPBase):
    """Represents the Signal Recovery DSP 72XX lock-in amplifier.

    Class inherits commands from the DSPBase parent class and utilizes dynamic
    properties for various properties and includes additional functionality.

    .. code-block:: python

        lockin72XX = DSP72XX_ar("GPIB0::12::INSTR")
        lockin72XX.imode = "voltage mode"       # Set to measure voltages
        lockin72XX.reference = "internal"       # Use internal oscillator
        lockin72XX.fet = 1                      # Use FET pre-amp
        lockin72XX.shield = 0                   # Ground shields
        lockin72XX.coupling = 0                 # AC input coupling
        lockin72XX.time_constant = 0.10         # Filter time set to 100 ms
        lockin72XX.sensitivity = 2E-3           # Sensitivity set to 2 mV
        lockin72XX.frequency = 100              # Set oscillator frequency to 100 Hz
        lockin72XX.voltage = 1                  # Set oscillator amplitude to 1 V
        lockin72XX.gain = 20                    # Set AC gain to 20 dB
        print(lockin72XX.x)                     # Measure X channel voltage
        lockin72XX.shutdown()                   # Instrument shutdown

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
                  'adc2', 'adc3', 'dac1', 'dac2', 'noise', 'ratio', 'log ratio',
                  'event', 'frequency part 1', 'frequency part 2',
                  # Dual modes
                  'x2', 'y2', 'magnitude2', 'phase2', 'sensitivity2']
    
    model = "DSP72XX"

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Initializer
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, adapter, name="Signal Recovery DSP 72XX", **kwargs):
        super().__init__(
            adapter,
            name,
            **kwargs
        )

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Additional properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    dac3 = Instrument.control(
        "DAC. 3", "DAC. 3 %g",
        """Control the voltage of the DAC3 output on the rear panel.

        Valid values are floating point numbers between -12 to 12 V.
        """,
        validator=strict_range,
        values=[-12, 12]
    )

    dac4 = Instrument.control(
        "DAC. 4", "DAC. 4 %g",
        """Control the voltage of the DAC4 output on the rear panel.

        Valid values are floating point numbers between -12 to 12 V.
        """,
        validator=strict_range,
        values=[-12, 12]
    )

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
                self.write("TC 11")
                current_sen = int(self.ask("SEN"))
                if abs(int(self.ask("MAG"))) > 9000:
                    self.write("SEN %d" % (current_sen + 1))
                elif abs(int(self.ask("MAG"))) < 1000:
                    self.write("SEN %d" % (current_sen - 1))
                sleep(1) # give lock-in 1s to settle before checking again
            self.write("TC %d" % current_tc) ### change back to original time constant
            sleep(5) ### give lock-in 5s to settle before measuring

    def auto_sensitivity(self):
        ### overwrite parent class method
        self.write("AS")

    @property
    def adc3(self):
        """Measure the ADC3 input voltage."""
        # 50,000 for 1V signal over 1 s
        integral = self.values("ADC 3")[0]
        return integral / (50000.0 * self.adc3_time)

    @property
    def adc3_time(self):
        """Control the ADC3 sample time in seconds."""
        # Returns time in seconds
        return self.values("ADC3TIME")[0] / 1000.0

    @adc3_time.setter
    def adc3_time(self, value):
        # Takes time in seconds
        self.write("ADC3TIME %g" % int(1000 * value))
        sleep(value * 1.2)