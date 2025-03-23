#
# This file is modified from part of the PyMeasure package and is a wrapper for multipyvu
# Commands are limited to temperature, field, chamber status, and resistivity channels

import re
import time
from time import sleep
import numpy as np
from enum import IntFlag
from pymeasure.instruments import Instrument
from pymeasure.instruments.validators import strict_discrete_set, \
    truncated_discrete_set, truncated_range, discreteTruncate
import math


class mpvPPMS(Instrument):
    
    delay = 0
    model = "PPMS"
    maxfield = 9 # in Tesla
    maxfieldsweeprate = 1 # in Tesla/min
    maxtemperaturesweeprate = 10 # in K/min

    def __init__(self, adapter, name="PPMS", client=None,
                 **kwargs):
        super().__init__(
            adapter,
            name,
            includeSCPI=False,
            **kwargs
        )
        self.client = client

    @property
    def temperature(self):
        """ Reads the temperature in Kelvin. """
        t, t_status = self.client.get_temperature()
        return t
    
    def set_temperature(self,temp,rate):
        """ Sets the temperature in Kelvin to temp at rate in Kelvin/min in fast settle mode"""
        self.client.set_temperature(temp,
                           rate,
                           self.client.temperature.approach_mode.fast_settle)
        self.client.wait_for(self.delay, 0, self.client.temperature.waitfor) # wait for 0s delay and 0s timeout
    
    @property
    def field(self):
        """ Reads the field in Tesla. """
        f, f_status = self.client.get_field()
        return f/10000
    
    def set_field_driven(self,field,rate):
        """ Sets the field in Tesla to field at rate in Tesla/min in linear approach, driven mode"""
        field_sign = math.copysign(1,field)
        rate_sign = math.copysign(1,rate)
        scaledfield = field_sign*min(field_sign*field,self.maxfield)*10000 # in oersted
        scaledrate = rate_sign*round(min(rate_sign*rate,self.maxfieldsweeprate)*10000/60,2) # in oersted/sec, rounded to 2 d.p.
        self.client.set_field(scaledfield,
                             scaledrate,
                             self.client.field.approach_mode.linear,
                             self.client.field.driven_mode.driven)
    
    def set_field_persistent(self,field,rate):
        """ Sets the field in Tesla to field at rate in Tesla/min in linear approach, persistent mode"""
        field_sign = math.copysign(1,field)
        rate_sign = math.copysign(1,rate)
        scaledfield = field_sign*min(field_sign*field,self.maxfield)*10000 # in oersted
        scaledrate = rate_sign*round(min(rate_sign*rate,self.maxfieldsweeprate)*10000/60,2) # in oersted/sec, rounded to 2 d.p.
        self.client.set_field(scaledfield,
                             scaledrate,
                             self.client.field.approach_mode.linear,
                             self.client.field.driven_mode.persistent)
    
    @property
    def chamber(self):
        """ Get chamber status as a string. """
        return self.client.get_chamber()

    def set_chamber(self,mode):
        """ Sets the chamber status with integer mode. 
            0 = Seal
            1 = Purge and seal
            2 = Vent and seal
            3 = Pump continuously
            4 = Vent continuously
            5 = High vacuum
        """
        if mode == 0:
            self.client.set_chamber(self.client.chamber.mode.seal)
        elif mode == 1:
            self.client.set_chamber(self.client.chamber.mode.purge_seal)
        elif mode == 2:
            self.client.set_chamber(self.client.chamber.mode.vent_seal)
        elif mode == 3:
            self.client.set_chamber(self.client.chamber.mode.pump_continuous)
        elif mode == 4:
            self.client.set_chamber(self.client.chamber.mode.vent_continuous)
        elif mode == 5:
            self.client.set_chamber(self.client.chamber.mode.high_vacuum)
    
    @property
    def bridge1(self):
        """ Read bridge resistance in ohms in channel 1. """
        r, s = self.client_object.resistivity.get_resistance(1) # s is the error which we don't return for now
        return r
    
    @property
    def bridge2(self):
        """ Read bridge resistance in ohms in channel 2. """
        r, s = self.client_object.resistivity.get_resistance(2) # s is the error which we don't return for now
        return r
    
    @property
    def bridge3(self):
        """ Read bridge resistance in ohms in channel 3. """
        r, s = self.client_object.resistivity.get_resistance(3) # s is the error which we don't return for now
        return r
    
    @property
    def bridge4(self):
        """ Read bridge resistance in ohms in channel 4. """
        r, s = self.client_object.resistivity.get_resistance(4) # s is the error which we don't return for now
        return r

    def set_bridge(self,channel,excitation,power):
        """ Set bridge cofiguration for AC excitation in microamps (up to 5000 uA), 
            power limit in microwatts (up to 1000 uW) and standard mode. 
            channel = 1, 2, 3, or 4. 
        """
        self.client.resistivity.bridge_setup(bridge_number=channel,
                                                channel_on=True,
                                                current_limit_uA=excitation,
                                                power_limit_uW=power,
                                                voltage_limit_mV=1000)
    
    @property
    def temperature_status(self):
        """ Get temperature status and return a string descriptor. """
        t, t_status = self.client.get_temperature()
        return t_status

    @property
    def magnet_status(self):
        """ Get magnet status and return a string descriptor. """
        f, f_status = self.client.get_field()
        return f_status
    
    # def abort_sequence(self):
    #     """ Abort any temperature or magetic field sequence commands. """
    #     self.write("SEQCTRL 0")

    # def wait_for(self,query_delay):
    #     """ Wait for some time. Used by ask before reading. This is added because PPMS takes a long time to respond. """
    #     sleep(0.2)