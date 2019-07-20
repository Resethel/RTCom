#
#
"""Docstring."""

from machine import I2C
import struct

# Address of PCF8523
_ADDRESS = 104

# Register addresses for control
_REGISTER_CONTROL_1 = 0x00
_REGISTER_CONTROL_2 = 0x01
_REGISTER_CONTROL_3 = 0x02

# Register addresses for time
_REGISTER_SECOND = 0x03
_REGISTER_MINUTE = 0x04
_REGISTER_HOUR = 0x05
_REGISTER_DAY = 0x06
_REGISTER_WEEKDAY = 0x07
_REGISTER_MONTH = 0x08
_REGISTER_YEAR = 0x09

# Register addresses for alarms

# Constants
DAYS_IN_MONTH = []
WEEKDAY_STR = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
MONTH_STR = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


class RTC():
    """
    RTC class for the PCF8523 module.
    """

    # =====( Constructor and Initalizer)===================================== #

    def __init__(self, _i2c=None):
        """
        Initialize the class.
        """

        # Get the i2c bus
        self.i2c_bus = None
        if _i2c:
            self.i2c_bus = _i2c
        else:
            self.i2c_bus = I2C(0, I2C.MASTER, baudrate=10000)

    # End def __init__

    def init(self, datetime=None, switch_over=True, vbat_interrupt=False):
        """
        Initialize the RTC module.

        datetime -- optional time at initialization
        switch_over -- Activate/Deactivate the switch over of the battery
        vbat_interrupt -- Generate an interrupt when the battery's voltage is low
        """

        if _ADDRESS not in self.i2c_bus.scan():
            raise RuntimeError("PCF8523 module is not detected in the I2C bus")

        # Set the clock in 24 hour mode
        self.__enable_24_mode()

        # Sets battery switch_over
        self.battery_switch_over(switch_over)

        # Sets interrupt on battery low
        self.vbat_interrupt(vbat_interrupt)

        # Finally set the datetime if requested
        if datetime is not None:
            self.set_time(datetime)
    # End def init

    # =====( Controls setters & getters )==================================== #

    def battery_switch_over(self, activate=True):
        """
        Set the clock in 24 hour mode.
        """
        # Get the values of the register control_3
        ctrl3_val = self.__read_register(_REGISTER_CONTROL_3)

        # First we clear the interrupt flag
        # 0bXXXXXXXX & 0b11110111
        ctrl3_val = ctrl3_val & 0xF7  # 0xF7 = 0b11110111

        if activate is True:
            # Sets the 3 first of control_3 to 0
            # 0bXXXXXXXX & 0b00011111
            ctrl3_val = ctrl3_val & 0x1F  # 0x1F = 0b00011111
        elif activate is False:
            # Sets the 3 first bits of control_3 to 1
            # 0bXXXXXXXX | 0b11100000
            ctrl3_val = ctrl3_val | 0xE0  # 0xE0 = 0b11100000
        else:
            raise ValueError("battery_switch_over only takes boolean argument")

        # Write the new control_3 register in memory
        self.__write_register(_REGISTER_CONTROL_3, ctrl3_val)
    # End set_battery_switch_over

    def vbat_interrupt(self, activate=True):
        """
        Activate/Interrupt when battery is low.
        """

        # Get the values of the register control_3
        ctrl3_val = self.__read_register(_REGISTER_CONTROL_3)

        if activate is True:
            # Sets the 1 first bits of control_3 to 1
            # 0bXXXXXXXX | 0b11100000
            ctrl3_val = ctrl3_val | 0x01  # 0x01 = 0b00000001
        elif activate is False:
            # Sets the 1 first of control_3 to 0
            # 0bXXXXXXXX & 0b00011111
            ctrl3_val = ctrl3_val & 0xFE  # 0xFE = 0b11111110
        else:
            raise ValueError("vbat_interrupt only takes boolean argument")

        # Write the new control_3 register in memory
        self.__write_register(_REGISTER_CONTROL_3, ctrl3_val)
    # End set_battery_switch_over

    def battery_low(self):
        """
        Return the state of the battery.

        True if its low and False if the battery voltage is ok
        """
        ctrl3_val = self.__read_register(_REGISTER_CONTROL_3)
        BLF_flag = (ctrl3_val & 0b00000100) >> 2
        if BLF_flag == 1:
            return True
        else:
            return False
    # End battery_low

    # =====( Time Functions )================================================ #

    def now(self):
        """
        Return the current time as a tuple.
        """
        year = self.get_year()
        month = self.get_month()
        day = self.get_day()
        hour = self.get_hour()
        minute = self.get_minute()
        second = self.get_second()

        return (year, month, day, hour, minute, second, 0, 0)
    # End def now

    def set_time(self, datetime):
        """
        Set the time of the RTC.

        datetime -- a tuple in format (year, month, day[, hour[, minute[, second[, microsecond[, tzinfo]]]]])
                    tzinfo and microsecond are ignored.
        """

        self.set_year(datetime[0])
        self.set_month(datetime[1])
        self.set_day(datetime[2])

        # Optional Hour
        if len(datetime) > 3:
            self.set_hour(datetime[3])
        else:
            self.set_hour(0)

        # Optional Minute
        if len(datetime) > 4:
            self.set_minute(datetime[4])
        else:
            self.set_minute(0)

        # Optional Second
        if len(datetime) > 5:
            self.set_second(datetime[5])
        else:
            self.set_second(0)
    # End def set_time

    # =====( Basic time getters )============================================ #

    def get_second(self):
        """
        Get the second of the current time.
        """

        # First we get the 8 bits stored in the second register
        # and translate it to an integer
        second_bcd = self.__read_register(_REGISTER_SECOND)

        # Then we extract the digits
        tens = (second_bcd & 0b01110000) >> 4
        digit = (second_bcd & 0b00001111)

        return 10 * (tens) + digit
    # End def get_second

    def get_minute(self):
        """
        Get the minute of the current time.
        """

        # First we get the first 8 bits stored in the minute register
        # and translate it to an integer
        minute_bcd = self.__read_register(_REGISTER_MINUTE)

        # We separate the tens from the digits

        tens = (minute_bcd & 0x70) >> 4  # 0x70 = 0b01110000
        digit = (minute_bcd & 0x0F)  # 0x0F = 0b00001111

        return 10 * (tens) + digit
    # End def get_minute

    def get_hour(self):
        """
        Get the current hour.
        """
        hour = None
        # First we get the first 8 bits stored in the hour register
        # and translate it to an integer
        hour_bcd = self.__read_register(_REGISTER_HOUR)

        # In case there was an issue with enabling the 14hour mode, we still want
        # to be able to read the hour correctly
        if self.__get_bit_12_24() == 0:  # 24h mode

            tens = (hour_bcd & 0x30) >> 4  # 0x30 = 0b00110000
            digit = (hour_bcd & 0x0F)      # 0x0F = 0b00001111
            hour = 10 * (tens) + digit

        else:  # 12h mode
            am_pm = (hour_bcd & 0x20) >> 5  # 0x20 = 0b00100000
            tens = (hour_bcd & 0x10) >> 4   # 0x10 = 0b00010000
            digit = (hour_bcd & 0x0F)       # 0x0F = 0b00001111
            hour = 12 * am_pm + 10 * (tens) + digit

        return hour
    # End def get hour

    def get_day(self):
        """
        Get the current day.
        """

        # First we get the first 8 bits stored in the day register
        # and translate it to an integer
        day_bcd = self.__read_register(_REGISTER_DAY)

        # Then we extract the digits and the tens
        tens = (day_bcd & 0x30) >> 4  # 0x30 = 0b00110000
        digit = (day_bcd & 0x0F)     # 0x0F = 0b00001111

        # End return the last value
        return 10 * (tens) + digit
    # End def get_day

    def get_weekday(self, as_str=False):
        """
        Get the current dqy of the week.

        By default, "0" corresponds to Sunday and "6" to Saturday
        """

        # First we get the first 8 bits stored in the weekday register
        # and translate it to an integer
        wd_8bits = self.__read_register(_REGISTER_WEEKDAY)

        # Then we extract the weekday and return it
        wd = wd_8bits & 0x07  # 0x07 = 0b00000111

        if as_str is True:   # if we want the weekday's name
            wd = WEEKDAY_STR[wd]

        return wd
    # End def get_weekday

    def get_month(self, as_str=False):
        """
        Get the current month.

        By default, "1" corresponds to January and "12" to December
        """

        # First we get the first 8 bits stored in the month register
        month_bcd = self.__read_register(_REGISTER_MONTH)

        # Then we extract the digits and the tens
        tens = (month_bcd & 0x10) >> 4  # 0x10 = 0b00010000
        digit = (month_bcd & 0x0F)      # 0x0F = 0b00001111

        month = 10 * (tens) + digit

        if as_str is True:  # if we want the month's name
            month = MONTH_STR[month - 1]

        return month
    # End def get_month

    def get_year(self):
        """
        Get the current year.
        """

        # First we get the first 8 bits stored in the yqr register
        year_bcd = self.__read_register(_REGISTER_YEAR)

        # Then we extract the digits and the tens
        tens = (year_bcd & 0xF0) >> 4  # 0xF0 = 0b11110000
        digit = (year_bcd & 0x0F)     # 0x0F = 0b00001111

        # We return year value shifted in range [1970..2129]
        return (10 * (tens) + digit) + 1970
    # End def get_year

    # =====( Basic time setters )============================================ #

    def set_second(self, second):
        """
        Set the current second.

        second -- an int comprised between 0 and 59 included.
        """
        if second not in range(60):
            raise ValueError("Second value must be in range [0..59] but is {}".format(second))

        # First we separate the tens and the digit
        tens, digit = divmod(int(second), 10)

        # Then we add them in a single int
        reg_value = (tens << 4) | digit

        # The we add it to a registory
        self.__write_register(_REGISTER_SECOND, reg_value)
    # End def set_second

    def set_minute(self, minute):
        """
        Set the current minute.

        minute -- an int comprised between 0 and 59 included.
        """
        if minute not in range(60):
            raise ValueError("Second value must be in range [0..59] but is {}".format(minute))

        # First we separate the tens and the digit
        tens, digit = divmod(int(minute), 10)

        # Then we add them in a single int
        reg_value = (tens << 4) | digit

        # The we add it to the register
        self.__write_register(_REGISTER_MINUTE, reg_value)
    # End def set_minute

    def set_hour(self, hour):
        """
        Set the current hour.

        hour -- Hour in range [0..23]. For now only 24h format is accepted
        """
        if hour not in range(24):
            raise ValueError("Hour value for 24h must be in range [1..23] but is {}".format(hour))

        # In case there was an issue with enabling the 14hour mode, we still want
        # to be able to write the hour correctly
        if self.__get_bit_12_24() == 0:
            # First we separate the tens and the digit
            tens, digit = divmod(int(hour), 10)

            # In 24h mode, we add them in a single int
            reg_value = (tens << 4) | digit

        else:  # 12h mode
            # We get the meridien
            if hour <= 12:
                meridien = 0
            else:
                meridien = 1

            # We treat the hour
            if hour == 12:
                tens, digit = divmod(int(12), 10)
            else:
                tens, digit = divmod(int(hour % 12), 10)

            # In 24h mode, we add them in a single int
            reg_value = (meridien << 5) | (tens << 4) | digit

            # Then we print the value to the register
        self.__write_register(_REGISTER_HOUR, reg_value)
    # End def set_minute

    def set_day(self, day):
        """
        Set the current day.

        month -- an int comprised between 0 and 31 included.
                 if the month as less than 31 day and a value in the range is entered
                 then we just clamp it to the month max value
        """
        if day not in range(1, 31):
            raise ValueError("Day value must be in range [1..12] but is {}".format(day))

        # First we separate the tens and the digit
        tens, digit = divmod(int(day), 10)

        # Then we add them in a single int
        reg_value = (tens << 4) | digit

        # The we add it to the register
        self.__write_register(_REGISTER_DAY, reg_value)
    # End def set_month

    def set_weekday(self, weekday):
        """
        Set the weekday.
        """
        # if the sting value of weekday is correct then we transform it into an
        # integer
        if isinstance(weekday, str):
            if weekday in WEEKDAY_STR:
                weekday_int = WEEKDAY_STR.index(weekday)
            else:
                raise ValueError("Weekday as a string can only take the value {}".format(WEEKDAY_STR))
        else:
            weekday_int = weekday

        # Check if weekday int in good range
        if weekday_int not in range(7):
            raise ValueError("Weekday value must be in range [0..6] but is {}".format(weekday_int))

        self.__write_register(_REGISTER_WEEKDAY, weekday_int)
    # End def set_weekday

    def set_month(self, month):
        """
        Set the current month.

        month -- an int comprised between 0 and 12 included.
        """
        # if the sting value of month is correct then we transform it into an
        # integer
        if isinstance(month, str):
            if month in MONTH_STR:
                month_int = MONTH_STR.index(month) + 1
            else:
                raise ValueError("Weekday as a string can only take the value {}".format(MONTH_STR))
        else:
            month_int = month

        # Check if month_int in good range
        if month_int not in range(1, 13):
            raise ValueError("Month value must be in range [1..12] but is {}".format(month_int))

        # First we separate the tens and the digit
        tens, digit = divmod(int(month_int), 10)

        # Then we add them in a single int
        reg_value = (tens << 4) | digit

        # The we add it to the register
        self.__write_register(_REGISTER_MONTH, reg_value)

    # End def set_month

    def set_year(self, year):
        """
        Set the current year.

        year -- an int comprised between 1970 and 2129 included.
                This limitation is due to PCF8523 that can only take 159 year values
        """
        if year not in range(1970, 2120):
            raise ValueError("Year must be in range [1970..2129] but is {}".format(year))

        # First we separate the tens and the digit. We also shift the year to
        # the range [0..159]
        tens, digit = divmod(int(year - 1970), 10)

        # Then we add them in a single int
        reg_value = (tens << 4) | digit

        # The we add it to a registory
        self.__write_register(_REGISTER_YEAR, reg_value)
    # End def set_year

    # =====( Helper Functions )============================================== #

    def __read_register(self, reg_addr):
        # Read a register

        reg_value_bytes = self.i2c_bus.readfrom_mem(_ADDRESS, reg_addr, 1)
        return int(struct.unpack('B', reg_value_bytes)[0])  # We return an integer representing the function
    # End def __get_control_register

    def __write_register(self, reg_addr, value):
        # Write in the register (Erase all previous values)

        value_str = struct.pack('<B', value)
        self.i2c_bus.writeto_mem(_ADDRESS, reg_addr, value_str)
    # End def __write_register

    def __enable_24_mode(self):
        # Set the clock in 24 hour mode.

        ctrl1_val = self.__read_register(_REGISTER_CONTROL_1)
        # 0bXXXXXXXX & 0b11110111
        # Sets the 4th byte to 0
        ctrl1_val1 = ctrl1_val & 0xF7  # 0xF7 = 0b11110111

        # Write the new control_1 register in memory
        self.__write_register(_REGISTER_CONTROL_1, ctrl1_val1)
    # End def __enable_24_mode

    def __get_bit_12_24(self):
        # Tell if the clock is in 12h mode or 24 hour mode.

        ctrl1_val = self.__read_register(_REGISTER_CONTROL_1)
        bit_12_24 = (ctrl1_val & 0x08) >> 3  # 0x08 = 0b00001000

        return bit_12_24
    # End def __get_bit_12_24
