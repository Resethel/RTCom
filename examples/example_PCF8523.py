#
#
"""Main function."""

from RTCom import PCF8523
import time


def main():
    """
    Test the code.
    """
    rtc_clock = PCF8523.RTC()

    # Initialize clock date for the 21 october 2015 at 4:29pm
    # Disable the switch_over
    rtc_clock.init((2015, 10, 21, 16, 29, 0, 0, 0), switch_over=False)

    # Sets the weekday to wednesday
    rtc_clock.set_weekday("WED")

    # Display the control bits
    print("Control 1: {:08b}".format(rtc_clock.__read_register(PCF8523._REGISTER_CONTROL_1)))
    print("Control 2: {:08b}".format(rtc_clock.__read_register(PCF8523._REGISTER_CONTROL_2)))
    print("Control 3: {:08b}".format(rtc_clock.__read_register(PCF8523._REGISTER_CONTROL_3)))

    while True:
        # Prints the time as a datetime tuple
        print(rtc_clock.now())

        # Prints the time in a human readable format
        sec = rtc_clock.get_second()
        min = rtc_clock.get_minute()
        hour = rtc_clock.get_hour()
        day = rtc_clock.get_day()
        weekday = rtc_clock.get_weekday(as_str=True)
        month = rtc_clock.get_month(as_str=True)
        year = rtc_clock.get_year()
        print("{}h {}min {}s - {}, {} {} {}".format(hour, min, sec, weekday, month, day, year))

        time.sleep_ms(1000)

# End def main


if __name__ == '__main__':
    main()
