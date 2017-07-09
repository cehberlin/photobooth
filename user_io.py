#!/usr/bin/python

from abc import ABCMeta, abstractmethod
from utils import GenericClassFactory

from pygame_utils import *

import imp

class ButtonState(object):
    BUTTON_PRESSED = 0
    BUTTON_NOT_PRESSED = 1

class LedState(object):
    OFF = 0
    ON = 1

class LedType(object):
    RED = 0
    BLUE = 1
    YELLOW = 2
    GREEN = 3

class AbstractUserIo(object):
    """
    Abstract interface for all additional hardware user interfaces buttons, leds ...
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def update(self):
        raise NotImplementedError

    @abstractmethod
    def reset_button_states(self):
        raise NotImplementedError

    @abstractmethod
    def any_button_pressed(self, reset = False):
        raise NotImplementedError

    @abstractmethod
    def button_idx_pressed(self, idx):
        raise NotImplementedError

    @abstractmethod
    def accept_button_pressed(self):
        raise NotImplementedError

    @abstractmethod
    def cancel_button_pressed(self):
        raise NotImplementedError

    @abstractmethod
    def admin_button_pressed(self):
        raise NotImplementedError

    @abstractmethod
    def next_button_pressed(self):
        raise NotImplementedError

    @abstractmethod
    def prev_button_pressed(self):
        raise NotImplementedError

    @abstractmethod
    def set_all_led(self, led_state):
        """
        Set state for all leds
        :param led_state: new state
        :type led_state: LedState
        """
        raise NotImplementedError

    @abstractmethod
    def set_led(self, led_type, led_state):
        """
        Set led state for a led of a particular type
        :param led_type: selected led type
        :type led_type: LedType
        :param led_state: new state
        :type led_state: LedState
        :return:
        """
        raise NotImplementedError

    @abstractmethod
    def show_led_coutdown(self, counter):
        raise NotImplementedError

# Create singleton factory object
user_io_factory = GenericClassFactory(AbstractUserIo)

def get_user_io_factory():
    """
    Provide external access to the factory instance
    :return: factory instance
    """
    return user_io_factory;

class PyGameUserIo(AbstractUserIo):
    def __init__(self, photobooth, **kwargs):
        self._photobooth = photobooth
        pass

    def update(self):
        pass

    def reset_button_states(self):
        pass

    def accept_button_pressed(self, reset = True):
        return self._photobooth.event_manager.key_pressed([pygame.K_4])

    def cancel_button_pressed(self, reset = True):
        return self._photobooth.event_manager.key_pressed([pygame.K_1])

    def admin_button_pressed(self, reset = False):
        return self._photobooth.event_manager.key_pressed([pygame.K_a])

    def next_button_pressed(self, reset = True):
        return self._photobooth.event_manager.key_pressed([pygame.K_3])

    def prev_button_pressed(self, reset = True):
        return self._photobooth.event_manager.key_pressed([pygame.K_2])

    def button_idx_pressed(self, idx):
        if idx == 0:
            return self._photobooth.event_manager.key_pressed([pygame.K_1])
        if idx == 1:
            return self._photobooth.event_manager.key_pressed([pygame.K_2])
        if idx == 2:
            return self._photobooth.event_manager.key_pressed([pygame.K_3])
        if idx == 3:
            return self._photobooth.event_manager.key_pressed([pygame.K_4])

    def any_button_pressed(self, reset = False):
        keys = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]
        return self._photobooth.event_manager.key_pressed(keys)

    def set_led(self, led_type, led_state):
        #print('set led type' + str(led_type) + ' state' + str(led_state))
        pass
    def set_all_led(self, led_state):
        #print('set all led:', led_state)
        pass

    def show_led_coutdown(self, counter):
        #print('led countdown:', counter)
        pass

#Register the PyGameUserIo implementation
user_io_factory.register_algorithm(id_class='pygame', class_obj=PyGameUserIo)

#following implementation is only activated if RPi (probably on a raspberry pi is available
try:
    imp.find_module('RPi')
    found_rpi_module = True
except ImportError:
    found_rpi_module = False
    print("Couldn't find RPi module, proceeding without")

if found_rpi_module:

    import RPi.GPIO as GPIO

    GPIO.setmode(GPIO.BCM)


    class RaspiPushButton(object):

        def __init__(self, color, button_pin, led_pin):
            self.color = color
            self.button_pin = button_pin
            self.led_pin = led_pin

            self.led_state = LedState.OFF
            self.reset_button_state()

            GPIO.setup(self.button_pin, GPIO.IN)

            GPIO.setup(self.led_pin, GPIO.OUT)

            GPIO.output(self.led_pin, GPIO.LOW)

            GPIO.add_event_detect(self.button_pin, GPIO.FALLING, callback=self._press_callback, bouncetime=300)
            
        def __del__(self):
            GPIO.cleanup(self.button_pin)
            GPIO.cleanup(self.led_pin)

        def _press_callback(self, channel):

            self.button_event_state = ButtonState.BUTTON_PRESSED
            #print('_press_callback', self.color)

        def is_pressed(self):
            return GPIO.input(self.button_pin) == GPIO.LOW

        def was_pressed(self, reset=True):
            result = self.button_event_state == ButtonState.BUTTON_PRESSED
            if reset:
                self.reset_button_state()
            return result

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
            elif self.led_state == LedState.ON:
                GPIO.output(self.led_pin, GPIO.HIGH)


    class ButtonRail(AbstractUserIo):

        # Adjust configuration if necessary
        push_buttons = {LedType.GREEN:RaspiPushButton(color='green', button_pin=23, led_pin=18),
                        LedType.BLUE:RaspiPushButton(color='blue', button_pin=25, led_pin=24),
                        LedType.YELLOW:RaspiPushButton(color='yellow', button_pin=16, led_pin=12),
                        LedType.RED:RaspiPushButton(color='red', button_pin=21, led_pin=20)}

        def __init__(self, **kwargs):
            pass

        def update(self):
            pass

        def reset_button_states(self):
            for _, button in ButtonRail.push_buttons.iteritems():
                button.reset_button_state()
        
        def any_button_pressed(self, reset = False):
            """
            Check if any button was pressed
            :return: true if a button was pressed since last call
            """

            result = False
            for key, button in ButtonRail.push_buttons.iteritems():
                if button.was_pressed(reset=reset):
                    result = True                    

            return result

        def button_idx_pressed(self, idx):
            if idx == 0:
                return self.push_buttons[LedType.RED].was_pressed(reset=True)
            if idx == 1:
                return self.push_buttons[LedType.BLUE].was_pressed(reset=True)
            if idx == 2:
                return self.push_buttons[LedType.YELLOW].was_pressed(reset=True)
            if idx == 3:
                return self.push_buttons[LedType.GREEN].was_pressed(reset=True)

        def accept_button_pressed(self, reset = True):
            return self.push_buttons[LedType.GREEN].was_pressed(reset=reset)

        def cancel_button_pressed(self, reset = True):
            return self.push_buttons[LedType.RED].was_pressed(reset=reset)

        def admin_button_pressed(self, reset = False):
            return self.push_buttons[LedType.GREEN].was_pressed(reset=reset) and \
                   self.push_buttons[LedType.RED].was_pressed(reset=reset)

        def next_button_pressed(self, reset = True):
            return self.push_buttons[LedType.YELLOW].was_pressed(reset=reset)

        def prev_button_pressed(self, reset = True):
            return self.push_buttons[LedType.BLUE].was_pressed(reset=reset)

        def set_all_led(self, led_state):

            for key, button in ButtonRail.push_buttons.iteritems():
                button.set_led(led_state)

        def set_led(self, led_type, led_state):
            self.push_buttons[led_type].set_led(led_state)

        def show_led_coutdown(self, counter):

            counter = counter % 5

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

            while True:  # TODO replace endless loop

                for key, button in ButtonRail.push_buttons.iteritems():
                    if button.is_pressed():
                        print("pressed: ", button.color)
                        button.led_on()
                    else:
                        button.led_off()

        def __del__(self):
            GPIO.cleanup()

    user_io_factory.register_algorithm(id_class='raspi', class_obj=ButtonRail)

    if __name__ == '__main__':
        button_rail = ButtonRail()
        button_rail.test_routine()
