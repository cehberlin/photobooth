
import time

import glob
import random
import os

from pygame_utils import *
from user_io import get_user_io_factory, LedState, LedType
from camera import get_camera_factory
import print_utils

#Configuration
DEFAULT_RESOLUTION = [640,424]
START_FULLSCREEN = False

COUNTER_FONT_SIZE = 140
INFO_FONT_SIZE = 36

PHOTO_TIMEOUT = 30
PHOTO_COUNTDOWN = 5
PHOTO_SHOW_TIME = 5
SLIDE_SHOW_TIMEOUT = 5
PHOTO_WAIT_FOR_PRINT_TIMEOUT = 30

PHOTO_DIRECTORY = 'images'

#options 'pygame', 'raspi'
IO_MANAGER_CLASS = 'raspi'

#options 'dummy', 'piggyphoto'
CAMERA_CLASS = 'piggyphoto'

class PhotoBoothState(object):

    def __init__(self, photobooth, next_state, counter_callback=None, counter_callback_args=None, counter=-1):
        self.photobooth = photobooth
        self.next_state = next_state
        self.inital_counter = counter

        self.counter_callback = counter_callback
        self.counter_callback_args = counter_callback_args
        self.counter_sleep_time = 1
        self.reset()

    def reset(self):
        self.counter = self.inital_counter
        self.counter_last_update_time = time.time()

    def set_counter(self, value):
        self.counter_last_update_time = time.time()
        self.counter = value

    def update_callback(self, photobooth):
        pass

    def update(self):
        self.update_callback()
        self.update_counter()

    def update_counter(self):

        if self.counter > 0:
            now = time.time()
            diff = now - self.counter_last_update_time
            if diff >= self.counter_sleep_time:
                self.counter_last_update_time = now
                self.counter-=1
                if self.is_counter_expired():
                    if self.counter_callback:
                        if(self.counter_callback_args):
                            self.counter_callback(*self.counter_callback_args)
                        else:
                            self.counter_callback()

                return True

        return False

    def is_counter_expired(self):
        return self.counter == 0

    def is_counter_enabled(self):
        return self.counter > -1


class PhotoBooth(object):
    def __init__(self, fullscreen=False):

        self.cam = None
        self.screen = None
        self._state = None
        self._last_photo_resized = None
        self._taken_photos = []

        self.fullscreen=fullscreen
        # Detect the screen resolution
        info_object = pygame.display.Info()
        self.screen_resolution = [info_object.current_w, info_object.current_h]

        if self.fullscreen:
            self.screen = pygame.display.set_mode(self.screen_resolution, pygame.FULLSCREEN)
            pygame.mouse.set_visible(False)
        else:
            self.screen = pygame.display.set_mode(DEFAULT_RESOLUTION)

        self.app_resolution = self.screen.get_size()

        self.screen.fill((128, 128, 128))
            
        self.event_manager = PyGameEventManager()

        self.io_manager = get_user_io_factory().create_algorithm(id_class=IO_MANAGER_CLASS, photobooth=self)

        #create photo directory if necessary
        if not os.path.exists(PHOTO_DIRECTORY):
            os.makedirs(PHOTO_DIRECTORY)

    def init_camera(self):
        self.cam = get_camera_factory().create_algorithm(id_class=CAMERA_CLASS, photo_directory=PHOTO_DIRECTORY)
        picture = self.cam.get_preview()
        
        if self.fullscreen:
            self.screen = pygame.display.set_mode(self.screen_resolution, pygame.FULLSCREEN)
            pygame.mouse.set_visible(False)
        else:
            self.screen = pygame.display.set_mode(picture.get_size())

        self.app_resolution = self.screen.get_size()

    def update(self):
        self.event_manager.update_events()
        self.state.update()

    @property
    def last_photo(self):
        return self._last_photo_resized

    @last_photo.setter
    def last_photo(self, value):
        #resize photo to screen
        self._last_photo_resized = (pygame.transform.scale(value[0], self.screen.get_size()), value[1])

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value
        self._state.reset()

#State machine callback functions

class StateWaitingForCamera(PhotoBoothState):
    def __init__(self, photobooth, next_state):
        super(StateWaitingForCamera, self).__init__(photobooth=photobooth, next_state=next_state)

    def update_callback(self):
        # try initialisation again
        try:
            self.photobooth.init_camera()
            self.photobooth.state = self.next_state
        except Exception as e:
            show_text(self.photobooth.screen, "Camera not connected: "+str(e), get_text_mid_position(self.photobooth.app_resolution))
            time.sleep(1)


class StateShowSlideShow(PhotoBoothState):
    def __init__(self, photobooth, next_state, counter):
        super(StateShowSlideShow, self).__init__(photobooth=photobooth, next_state=next_state, counter=counter, counter_callback=self._next_photo)
        self._photo_set = []
        self.current_photo = None

    def update_callback(self):
        if self.photobooth.event_manager.mouse_pressed() or self.photobooth.io_manager.any_button_pressed():
            self.photobooth.state = self.next_state

        if self.current_photo:
            show_cam_picture(self.photobooth.screen, self.current_photo)

        show_text(self.photobooth.screen, "Slideshow, press any button to continue", (100, 30), INFO_FONT_SIZE)

    def _next_photo(self):
        if len(self._photo_set) > 0:
            photo_file = random.choice(self._photo_set)
            print("Next photo: " + photo_file)
            self.current_photo =  pygame.image.load(photo_file)
            super(StateShowSlideShow, self).reset()  # reset counter
        else:
            self._reload_photo_set() # check for new photos

    def _reload_photo_set(self):
        # load all images from directory
        self._photo_set = glob.glob(PHOTO_DIRECTORY + "/*.jpg")

    def reset(self):
        super(StateShowSlideShow, self).reset()
        if self.photobooth.cam:
            self.photobooth.cam.set_idle()
        self._reload_photo_set()
        self._next_photo()
        print("Loading Slideshow images")


class StateWaitingForPhotoTrigger(PhotoBoothState):
    def __init__(self, photobooth, next_state, timeout_state = None, failure_state=None, counter=-1):
        super(StateWaitingForPhotoTrigger, self).__init__(photobooth=photobooth, next_state=next_state, counter=counter, counter_callback=self._switch_timeout_state)
        self.timeout_state = timeout_state
        self.failure_state = failure_state

    def update_callback(self):
        if self.photobooth.event_manager.mouse_pressed() or self.photobooth.io_manager.any_button_pressed():
            self.photobooth.state = self.next_state
        try:
            preview_img = self.photobooth.cam.get_preview()
            show_cam_picture(self.photobooth.screen, preview_img)
        except Exception as e:
            print("Getting preview failed:" + str(e))
            if self.failure_state:
                self.photobooth.state = self.failure_state
        
    def _switch_timeout_state(self):
        if self.timeout_state:
            self.photobooth.state = self.timeout_state
        else:
            self.reset()

    def reset(self):
        super(StateWaitingForPhotoTrigger, self).reset()
        self.photobooth.io_manager.set_all_led(LedState.ON)

class StatePhotoTrigger(PhotoBoothState):
    def __init__(self, photobooth, next_state, failure_state=None, counter=-1):
        super(StatePhotoTrigger, self).__init__(photobooth=photobooth, next_state=next_state, counter=counter, counter_callback=self._take_photo)
        self.failure_state = failure_state
        
    def update_callback(self):
        try:
            preview_img = self.photobooth.cam.get_preview()
            show_cam_picture(self.photobooth.screen, preview_img)
            # Show countdown
            show_text(self.photobooth.screen, str(self.counter), get_text_mid_position(self.photobooth.app_resolution), COUNTER_FONT_SIZE)
            self.photobooth.io_manager.show_led_coutdown(self.counter)
        except Exception as e:
            print("Photo trigger failed:" + str(e))
            if self.failure_state:
                self.photobooth.state = self.failure_state
        
    def _take_photo(self):
        #first update to latest preview
        preview_img = self.photobooth.cam.get_preview()
        show_cam_picture(self.photobooth.screen, preview_img)
        pygame.display.update()
        self.photobooth.io_manager.show_led_coutdown(self.counter)

        #take photo
        self.photobooth.last_photo = self.photobooth.cam.take_photo()

        self.photobooth.io_manager.set_all_led(LedState.ON)

        self.photobooth.state = self.next_state


class StateShowPhoto(PhotoBoothState):
    def __init__(self, photobooth, next_state, counter=-1):
        super(StateShowPhoto, self).__init__(photobooth=photobooth, next_state=next_state, counter=counter, counter_callback=self._switch_to_next_state)

    def update_callback(self):
        show_cam_picture(self.photobooth.screen, app.last_photo[0])
        show_text(self.photobooth.screen, "Last Photo:", (70, 30), INFO_FONT_SIZE)

    def _switch_to_next_state(self):
        self.photobooth.state = self.next_state

class StatePrinting(PhotoBoothState):
    def __init__(self, photobooth, next_state, counter=-1):
        super(StatePrinting, self).__init__(photobooth=photobooth, next_state=next_state, counter=counter, counter_callback=self._switch_to_next_state)
        self._error_txt = None

    def print_photo(self, photo_file):

        try:
            print_utils.print_photo(photo_file=photo_file)
            return True
        except Exception as e:
            self._error_txt = str(e)
            return False

    def update_callback(self):
        show_cam_picture(self.photobooth.screen, app.last_photo[0])

        show_text(self.photobooth.screen, "Print photo?", (95, 30), 36)
        show_text(self.photobooth.screen, "Press GREEN for printing - RED for canceling", (285, 60), 36)
        self.photobooth.io_manager.set_led(led_type=LedType.GREEN,led_state=LedState.ON)
        self.photobooth.io_manager.set_led(led_type=LedType.RED, led_state=LedState.ON)
        self.photobooth.io_manager.set_led(led_type=LedType.BLUE, led_state=LedState.OFF)
        self.photobooth.io_manager.set_led(led_type=LedType.YELLOW, led_state=LedState.OFF)

        if self._error_txt:
            show_text(self.photobooth.screen, "Print failure:", (100, 360), 36)
            show_text(self.photobooth.screen, self._error_txt, (210, 390), 36)

        if self.photobooth.event_manager.mouse_pressed() or self.photobooth.io_manager.accept_button_pressed():
            if self.print_photo(app.last_photo[1]):
                self.photobooth.state = self.next_state
                self._error_txt = None
            else: # failure
                self.reset()  # reset timeout counter
        elif self.photobooth.io_manager.cancel_button_pressed():
            self.photobooth.state = self.next_state

    def _switch_to_next_state(self):
        """
        This is just a timeout behaviour
        """
        self.photobooth.state = self.next_state


if __name__ == '__main__':

    pygame.init()

    # create app
    app = PhotoBooth(fullscreen=START_FULLSCREEN)

    # Create all states
    #state_show_photo = StateShowPhoto(photobooth=app, next_state=None, counter=PHOTO_SHOW_TIME)
    state_show_photo = StatePrinting(photobooth=app, next_state=None, counter=PHOTO_WAIT_FOR_PRINT_TIMEOUT)

    state_trigger_photo = StatePhotoTrigger(photobooth=app, next_state=state_show_photo, counter=PHOTO_COUNTDOWN)

    timeout_slide_show = StateShowSlideShow(photobooth=app, next_state=None, counter=SLIDE_SHOW_TIMEOUT)

    state_waiting_for_photo_trigger = StateWaitingForPhotoTrigger(photobooth=app, next_state=state_trigger_photo, timeout_state=timeout_slide_show, counter=PHOTO_TIMEOUT)

    state_show_photo.next_state = state_waiting_for_photo_trigger
    timeout_slide_show.next_state = state_waiting_for_photo_trigger

    state_waiting_for_camera = StateWaitingForCamera(photobooth=app, next_state=state_waiting_for_photo_trigger)
    state_waiting_for_photo_trigger.failure_state = state_waiting_for_camera
    state_trigger_photo.failure_state = state_waiting_for_camera

    #initial app state
    app.state = state_waiting_for_camera


    # Main program loop
    while not app.event_manager.quit_pressed():
        
        try:
            app.update()

        except Exception as e:
            print(e)
            show_text(app.screen, "Error", get_text_mid_position(app.app_resolution))
        pygame.display.update()
