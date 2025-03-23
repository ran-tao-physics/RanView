# This file is modified from pymeasure library

# =============================================================================
# Libraries / modules
# =============================================================================

import logging
from time import sleep, time
import numpy as np
from pymeasure.instruments import Instrument
from pymeasure.instruments.validators import modular_range_bidirectional
from pymeasure.instruments.validators import strict_discrete_set,truncated_discrete_set
from pymeasure.instruments.validators import strict_range

# =============================================================================
# Logging
# =============================================================================

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())
delay = 0.1

# =============================================================================
# Instrument file
# =============================================================================


class DSP52XXBase(Instrument):
    """This is the base class for the Signal Recovery DSP 52XX lock-in
    amplifiers.

    Do not directly instantiate an object with this class. Use one of the
    DSP 52XX series instrument classes that inherit from this parent
    class. Floating point command mode (i.e., the inclusion of the ``.``
    character in commands) is included for usability.

    Untested commands are noted in docstrings.
    """

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Constants
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    SENSITIVITIES = [
        100.0e-9,
        300.0e-9, 1.0e-6, 3.0e-6, 10.0e-6,
        30.0e-6, 100.0e-6, 300.0e-6, 1.0e-3,
        3.0e-3, 10.0e-3, 30.0e-3, 100.0e-3,
        300.0e-3, 1.0, 3.0
    ]

    TIME_CONSTANTS = [
        1.0e-3, 3.0e-3, 10.0e-3, 30.0e-3, 100.0e-3,
        300.0e-3, 1.0, 3.0, 10.0, 30.0,
        100.0, 300.0, 1.0e3, 3.0e3
    ]
    REFERENCES = ['external','internal']

    CURVE_BITS = ['x', 'y', 'magnitude', 'phase', 'sensitivity', 'adc1',
                  'adc2', 'adc3', 'adc4', 'ratio', 'log ratio',
                  'event', 'frequency part 1', 'frequency part 2'
                  ]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Initializer and important communication methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, adapter, name="Signal Recovery DSP 52XX Base", **kwargs):
        super().__init__(
            adapter,
            name,
            includeSCPI=False,
            **kwargs
        )

    def read(self, **kwargs):
        """Read the response and remove extra unicode character from instrument readings."""
        return super().read(**kwargs).replace('\x00', '')

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    id = Instrument.measurement(
        "ID",
        """Measure the model number of the instrument.

        Returned value is an integer.""",
        cast=int
    )


    slope = Instrument.control(
        "XDB", "XDB %d",
        """Control the low-pass filter roll-off.

        Valid values are the integers 6, 12, which represents the
        slope of the low-pass filter in dB/octave.
        """,
        validator=strict_discrete_set,
        values=[6, 12],
        map_values=True
    )

    time_constant = Instrument.control(
        "TC", "TC %d",
        """Control the filter time constant.

        Valid values are a truncated discrete set of time constants from 1 ms to 3,000 s.
        Returned values are floating point numbers in seconds.
        """,
        validator=truncated_discrete_set,
        values=TIME_CONSTANTS,
        map_values=True
    )

    # voltage = Instrument.control(
    #     "OA", "OA %d",
    #     """Control the oscillator amplitude.

    #     Valid values are integer numbers between 0 to 2000 mV or 5000 mV.
    #     """,
    #     validator=strict_range,
    #     values=[0, 5000]
    # )

    @property
    def voltage(self):
        """Read the signal's measurement oscillator amplitude.

        Values returned are in volts.
        """
        v=float(self.ask("OA"))/1000
        return v

    @voltage.setter
    def voltage(self, value):
        value = strict_range(value, [0,5])
        if value > 3.5:
            value = 5000
        elif value > 2:
            value = 2000
        else:
            value = round(value*1000)
        # Set sensitivity
        self.write("OA %d" % value)

    # frequency = Instrument.control(
    #     "OF", "OF %d %d",
    #     """Control the oscillator frequency.

    #     Valid values are integer numbers n1 n2, where n2 is 0 1 2 3 4 5 controlling 
    #     the frequency band 0.5-2 Hz, 2.0-20Hz, 20-200 Hz, 200-2k Hz, 2k-20k Hz, and
    #     20k-120k Hz and n1 is between 2000 and 20000 (or 5000 to 20000 in lowest band
    #     or 2000 to 12000 in highest band).
    #     """,
    #     validator=lambda x: x, ### not using validator because it is too much work
    #     dynamic=True # i.e. this can be changed during measurement
    # )

    @property
    def frequency(self):
        """Read the oscillator frequency.

        Valid values are integer numbers n1 n2, where n2 is 0 1 2 3 4 5 controlling 
        the frequency band 0.5-2 Hz, 2.0-20Hz, 20-200 Hz, 200-2k Hz, 2k-20k Hz, and
        20k-120k Hz and n1 is between 2000 and 20000 (or 5000 to 20000 in lowest band
        or 2000 to 12000 in highest band).
        """
        re_string=self.ask("OF")
        separator = ','
        num_sep = [pos for pos, char in enumerate(re_string) if char == separator]
        scaled_f = int(re_string[:num_sep[0]])
        f_range = int(re_string[(num_sep[0]+1):])
        if f_range == 0:
            return scaled_f / 10000
        elif f_range == 1:
            return scaled_f / 1000
        elif f_range == 2:
            return scaled_f / 100
        elif f_range == 3:
            return scaled_f / 10
        elif f_range == 4:
            return scaled_f
        else:
            return scaled_f * 10

    @frequency.setter
    def frequency(self, value):
        ### valid range for value is between 0.5 Hz and 120 kHz

        # Check the value
        value = strict_range(value, [0.5,120000])

        if value <= 2:
            scaled_f = round(value*10000)
            f_range = 0
            self.write("OF %d %d" % (scaled_f,f_range))
        elif value <= 20:
            scaled_f = round(value*1000)
            f_range = 1
            self.write("OF %d %d" % (scaled_f,f_range))
        elif value <= 200:
            scaled_f = round(value*100)
            f_range = 2
            self.write("OF %d %d" % (scaled_f,f_range))
        elif value <= 2000:
            scaled_f = round(value*10)
            f_range = 3
            self.write("OF %d %d" % (scaled_f,f_range))
        elif value <= 20000:
            scaled_f = round(value)
            f_range = 4
            self.write("OF %d %d" % (scaled_f,f_range))
        else:
            scaled_f = round(value/10)
            f_range = 5
            self.write("OF %d %d" % (scaled_f,f_range))

    reference = Instrument.control(
        "IE", "IE %d",
        """Control the oscillator reference input mode.

        Valid values are ``external`` or ``internal``.
        """,
        validator=strict_discrete_set,
        values=REFERENCES,
        map_values=True
    )

    harmonic = Instrument.control(
        "F2F", "F2F %d",
        """Control the reference harmonic mode.

        Valid values are ``first`` or ``second``.
        """,
        validator=strict_discrete_set,
        values=['first','second'],
        map_values=True
    )

    reference_phase = Instrument.control(
        "P", "P %d %d",
        """Control the reference absolute phase angle.

        Valid values are integers n1 and n2, n1 is 0 1 2 3 denoting which quadrant
        the phase is in, and n2 is between 0 and 100000 millidegrees with 5 millidegree
        resolution denoting the values in each quadrant.
         """,
        validator=lambda x: x, ### not using validator because it is too much work
        values=[0, 100000]
    )

    dac = Instrument.control(
        "DAC", "DAC %d",
        """Control the voltage of the DAC1 output on the rear panel.

        Valid values are integers between -15000 to 15000 mV.
        """,
        validator=strict_range,
        values=[-15000, 15000]
    )

    @property
    def sensitivity(self):
        """Control the signal's measurement sensitivity range.

        Values returned are in volts.
        """
        i=int(self.ask("SEN"))
        return self.SENSITIVITIES[i]

    @sensitivity.setter
    def sensitivity(self, value):
        # ### valid range for value is an integer from 0 to 15
        # sensitivities_index = range(16)

        # # Check and map the value
        # value = strict_discrete_set(value, sensitivities_index)
        # value = sensitivities_index.index(value)

        value = truncated_discrete_set(value, self.SENSITIVITIES)
        value = self.SENSITIVITIES.index(value)

        # Set sensitivity
        self.write("SEN %d" % value)

    @property
    def x(self):
        """Measure the output signal's X channel in volts."""
        scaled = float(self.ask("X"))
        sleep(delay)
        real = scaled*self.sensitivity/10000
        return real
    
    @property
    def y(self):
        """Measure the output signal's Y channel in volts."""
        scaled = float(self.ask("Y"))
        sleep(delay)
        real = scaled*self.sensitivity/10000
        return real
    
    @property
    def xy(self):
        """Measure the output signal's X channel in volts."""
        scaled = self.ask("XY").replace('\r\n', '')
        separator = ','
        num_sep = [pos for pos, char in enumerate(scaled) if char == separator]
        scaled_x = float(scaled[:num_sep[0]])
        scaled_y = float(scaled[(num_sep[0]+1):])
        sleep(delay)
        scale = self.sensitivity/10000
        real_x = scaled_x*scale
        real_y = scaled_y*scale
        return [real_x, real_y]
    
    @property
    def mag(self):
        """Measure the output signal's magnitude in volts."""
        scaled = float(self.ask("MAG"))
        real = scaled*self.sensitivity/10000
        return real
    
    # x = Instrument.measurement(
    #     "X",
    #     """Measure the output signal's X channel.

    #     Returned value is an integer number, which then needs 
    #     to be mapped to the real value (full range of sensitivity
    #     is 10000).
    #     """) 

    # y = Instrument.measurement(
    #     "Y",
    #     """Measure the output signal's Y channel.

    #     Returned value is an integer number, which then needs 
    #     to be mapped to the real value (full range of sensitivity
    #     is 10000).
    #     """)

    # xy = Instrument.measurement(
    #     "XY",
    #     """Measure both the X and Y channels.

    #     Returned value is an integer number, which then needs 
    #     to be mapped to the real value (full range of sensitivity
    #     is 10000).
    #     """)

    # mag = Instrument.measurement(
    #     "MAG",
    #     """Measure the magnitude of the signal.

    #     Returned value is an integer number, which then needs 
    #     to be mapped to the real value (full range of sensitivity
    #     is 10000).
    #     """)

    phase = Instrument.measurement(
        "PHA",
        """Measure the signal's absolute phase angle.

        Returned value is an integer number in millidegrees,
        which needs to be mapped into degrees.
        """, get_process=lambda x: x/1000)

    adc1 = Instrument.measurement(
        "ADC 1",
        """Measure the voltage of the ADC1 input on the rear panel.

        Returned value is an integer number in millivolts, 
        which needs to be mapped into volts.
        """, get_process=lambda x: x/1000)

    adc2 = Instrument.measurement(
        "ADC 2",
        """Measure the voltage of the ADC2 input on the rear panel.

        Returned value is an integer number in millivolts, 
        which needs to be mapped into volts.
        """, get_process=lambda x: x/1000)
    
    adc3 = Instrument.measurement(
        "ADC 3",
        """Measure the voltage of the ADC3 input on the rear panel.

        Returned value is an integer number in millivolts, 
        which needs to be mapped into volts.
        """, get_process=lambda x: x/1000)
    
    adc4 = Instrument.measurement(
        "ADC 4",
        """Measure the voltage of the ADC4 input on the rear panel.

        Returned value is an integer number in millivolts, 
        which needs to be mapped into volts.
        """, get_process=lambda x: x/1000)

    ratio = Instrument.measurement(
        "RT",
        """Measure the ratio between the X channel and ADC1.

        Returned value is a unitless floating point number equivalent to the
        mathematical expression 1000*X/ADC1, which needs to be mapped to X/ADC1
        """, get_process=lambda x: x/1000)

    log_ratio = Instrument.measurement(
        "LR",
        """
        Measure the log (base 10) of the ratio between the X channel and ADC1.

        Returned value is a unitless floating point number equivalent to the
        mathematical expression 1000*log(X/ADC1), which needs to be mapped to 
        log(X/ADC1)
        """, get_process=lambda x: x/1000)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def auto_sensitivity(self):
        """Adjusts the full-scale sensitivity so signal's magnitude lies
        between 30 - 90 % of full-scale.
        """
        self.write("AS")

    def auto_phase(self):
        """Adjusts the reference absolute phase to maximize the X channel
        output and minimize the Y channel output signals.
        """
        self.write("AQN")

    def wait_for(self,query_delay):
        """ Wait for some time. Used by ask before reading. This is added because no buffer is made and 52XX takes a long time to respond. """
        sleep(0.1)


    def shutdown(self):
        """Safely shutdown the lock-in amplifier.

        Sets oscillator amplitude to 0 V and AC gain to 0 dB.
        """
        log.info("Shutting down %s." % self.name)
        self.voltage = 0.
        self.gain = 0.
        super().shutdown()