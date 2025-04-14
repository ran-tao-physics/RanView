import logging

from pymeasure.instruments import Instrument, SCPIUnknownMixin
from pymeasure.instruments.lakeshore.lakeshore_base import LakeShoreTemperatureChannel
from pymeasure.instruments import Instrument, Channel
from pymeasure.instruments.validators import strict_discrete_set

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

class LakeShore340LoopChannel(Channel):
    """ Loop output channel on a lakeshore 340 temperature controller. Provides properties to query
    the output power in percent of the max, set the manual output power, heater range, and PID
    temperature setpoint. Here {ch} refers to the loop (1 or 2).
    """

    output = Instrument.measurement(
        'HTR?',
        """Query the heater output in percent of the max."""
    )
    mout = Instrument.control(
        'MOUT? {ch}',
        'MOUT {ch}, %.2f',
        """Manual heater output in percent to 2 d.p.."""
    )
    range = Instrument.control(
        'RANGE?',
        'RANGE %d',
        """Property controlling heater range, returns numerical value of 
        heater resistance, but in setting only takes 0 to 5.""",
        validator=strict_discrete_set,
        values={0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5},
        map_values=True)
    setpoint = Instrument.control(
        'SETP? {ch}', 'SETP {ch},%f',
        """A floating point property that control the setpoint temperature
        in the preferred units of the control loop sensor."""
    )
    ramp = Instrument.control(
        'RAMP? {ch}', 'RAMP {ch},%d,%.1f',
        """A pair of integer and floating point properties that controls whether
        a loop is ramped and the rate in K/min that it is ramped."""
    )
    ### usually don't need to use the following commands
    PID = Instrument.control(
        'PID? {ch}', 'PID {ch},%f,%f,%f',
        """Three floating point properties that controls the PID constants of
        a loop."""
    )
    CMODE = Instrument.control(
        'CMODE? {ch}', 'CMODE {ch},%d',
        """Integer properties that controls the control mode of the loop
        1 = Manual PID, 2 = Zone, 3 = Open Loop, 4 = AutoTune PID, 5 = AutoTune PI, 6 = AutoTune P."""
    )
    CSET = Instrument.control(
        'CSET? {ch}', 'CSET {ch},%s,%d,%d,1',
        """Properties that controls the setup of the loop, consisting of <input> (A or B),
        <units> (1=K, 2=C, 3=sensor units), <off/on> (0=off, 1=on), <powerup enable> (set to 1)"""
    )

class LakeShore340AnalogChannel(Channel):
    """ Analog output channel on a lakeshore 340 temperature controller. Provides properties to query
    the output power in integer percent of 10V for channel 1/2 in manual mode, e.g.
    ANALOG 1 (channel), 0 (bipolar disabled only positive output), 2 (manual mode), , , , ,25.5 (25.5% of 10V output)
    """

    output = Instrument.measurement(
        'AOUT? {ch}',
        """Query the heater output in percent of 10V."""
    )
    mout = Instrument.control(
        'ANALOG? {ch}',
        'ANALOG {ch}, 0, 2,,,,, %.1f',
        """Manual heater output in percent to 1 decimal place."""
    )

class LakeShore340(SCPIUnknownMixin, Instrument):
    """ Represents the Lake Shore 340 Temperature Controller and provides
    a high-level interface for interacting with the instrument. There are
    two to four input channels, one main heater output channel, and two 
    analog output channels.
    This driver makes use of the :ref:`LakeShoreChannels`.

    .. code-block:: python

        controller = LakeShore340("GPIB::1")

        print(controller.loop_1.setpoint)         # Print the current setpoint for loop 1
        controller.loop_1.setpoint = 50           # Change the loop 1 setpoint to 50 K
        controller.loop_1.heater_range = 'low'    # Change the heater range to low.
        controller.input_A.wait_for_temperature()   # Wait for the temperature to stabilize.
        print(controller.input_A.temperature)       # Print the temperature at sensor A.
    """

    output_1 = Instrument.ChannelCreator(LakeShore340AnalogChannel, 1)
    output_2 = Instrument.ChannelCreator(LakeShore340AnalogChannel, 2)
    loop_1 = Instrument.ChannelCreator(LakeShore340LoopChannel,1)
    loop_2 = Instrument.ChannelCreator(LakeShore340LoopChannel,2)

    def __init__(self, adapter, name="Lakeshore Model 336 Temperature Controller", input = 2, **kwargs):
        kwargs.setdefault('read_termination', "\r\n")
        super().__init__(
            adapter,
            name,
            **kwargs
        )
        self.input_channel = input
        if input == 2:
            self.input_A = Instrument.ChannelCreator(LakeShoreTemperatureChannel, 'A')
            self.input_B = Instrument.ChannelCreator(LakeShoreTemperatureChannel, 'B')
        if input == 3:
            self.input_A = Instrument.ChannelCreator(LakeShoreTemperatureChannel, 'A')
            self.input_B = Instrument.ChannelCreator(LakeShoreTemperatureChannel, 'B')
            self.input_C = Instrument.ChannelCreator(LakeShoreTemperatureChannel, 'C')
        if input == 4:
            self.input_A = Instrument.ChannelCreator(LakeShoreTemperatureChannel, 'A')
            self.input_B = Instrument.ChannelCreator(LakeShoreTemperatureChannel, 'B')
            self.input_C = Instrument.ChannelCreator(LakeShoreTemperatureChannel, 'C')
            self.input_D = Instrument.ChannelCreator(LakeShoreTemperatureChannel, 'D')

    ### only loop 1 has settle property for controlling temperature ramp, but usually only ramping in loop 1
    settle = Instrument.control(
        'SETTLE?', 'SETTLE %f ,%f',
        """A paired floating point property that controls the settling parameters of loop 1 (threshold and time in seconds)."""
    )
