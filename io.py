#!/usr/bin/python

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

class ButtonState(object):
    BUTTON_PRESSED = GPIO.LOW
    BUTTON_NOT_PRESSED = GPIO.HIGH

class LedState(object):
    OFF = GPIO.LOW
    ON = GPIO.HIGH

class PushButton(object):

    def __init__(self, color, button_pin, led_pin):
        self.color = color
        self.button_pin = button_pin
        self.led_pin = led_pin

        self.led_state = LedState.OFF
        self.reset_button_state()

        GPIO.setup(self.button_pin, GPIO.IN)

        GPIO.setup(self.led_pin, GPIO.OUT)

        GPIO.output(self.led_pin, GPIO.LOW)

        #TODO add event for both
        GPIO.add_event_detect(self.button_pin, GPIO.FALLING, callback=self._press_callback)
        #GPIO.add_event_detect(self.button_pin, GPIO.RISING, callback=self._release_callback, bouncetime=300)

    def __del__(self):
        GPIO.cleanup(self.button_pin)
        GPIO.cleanup(self.led_pin)

    def _press_callback(self, channel):

        self.button_event_state = ButtonState.BUTTON_PRESSED
        print('_press_callback',self.color)

    def _release_callback(self, channel):

        self.button_event_state = ButtonState.BUTTON_NOT_PRESSED

    def is_pressed(self):
        return GPIO.input(self.button_pin) == GPIO.LOW

    def was_pressed(self):
        result = self.button_event_state == ButtonState.BUTTON_PRESSED
        self.reset_button_state()
        return

    def reset_button_state(self):
        self.button_event_state = ButtonState.BUTTON_NOT_PRESSED

    def led_on(self):
        self.set_led(LedState.ON)

    def led_off(self):
        self.set_led(LedState.OFF)

    def set_led(self, state):
        self.led_state = state
        if self.led_state == LedState.OFF:
            GPIO.output(self.led_pin, GPIO.LOW)
        else:
            GPIO.output(self.led_pin, GPIO.HIGH)

class ButtonRail(object):

    # Adjust configuration if necessary
    push_buttons = [PushButton(color='green',   button_pin=23, led_pin=18),
                    PushButton(color='blue',    button_pin=25, led_pin=24),
                    PushButton(color='yellow',  button_pin=16, led_pin=12),
                    PushButton(color='red',     button_pin=21, led_pin=20)]

    def __init__(self):
        pass

    def any_button_pressed(self):
        """
        Check if any button was pressed
        :return: true if a button was pressed since last call
        """

        result = False
        for button in ButtonRail.push_buttons:
            if button.was_pressed():
                result = True
                #do not break in order to reset all buttons
                #reset is done inside was_pressed()

        return result

    def set_all_led(self, led_state):
        
        for button in ButtonRail.push_buttons:
            button.set_led(led_state)

    def show_led_coutdown(self, counter):
        
        if counter == 4:
            ButtonRail.push_buttons[0].led_off()
        if counter == 3:
            ButtonRail.push_buttons[1].led_off()
        if counter == 2:
            ButtonRail.push_buttons[2].led_off()
        if counter == 1:
            ButtonRail.push_buttons[3].led_off()
        if counter == 0:
            self.set_all_led(LedState.ON)


    def test_routine(self):
        """
        This is a very simple test routine that lights the button that is pressed
        """

        while True: #TODO replace endless loop

            for button in ButtonRail.push_buttons:
                if button.is_pressed():
                    print("pressed: ",button.color)
                    button.led_on()
                else:
                    button.led_off()

        def __del__(self):
            GPIO.cleanup()

if __name__ == '__main__':
    button_rail = ButtonRail()
    button_rail.test_routine()
    
