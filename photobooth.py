
import time

import glob
import random
import os
import socket

#Own modules
from pygame_utils import *
from user_io import get_user_io_factory, LedState, LedType
from camera import get_camera_factory
import print_utils

import gettext

#Visual Configuration
DEFAULT_RESOLUTION = [640,424]
START_FULLSCREEN = False

COUNTER_FONT_SIZE = 140
INFO_FONT_SIZE = 36
INFO_SMALL_FONT_SIZE = 24

# Core configurations

PHOTO_TIMEOUT = 30
PHOTO_COUNTDOWN = 5
PHOTO_SHOW_TIME = 5
SLIDE_SHOW_TIMEOUT = 5
PHOTO_WAIT_FOR_PRINT_TIMEOUT = 30

#options 'de', 'en'
LANGUAGE_ID = 'en'

PHOTO_DIRECTORY = 'images'

# Implementation configuration / module selection
#options 'pygame', 'raspi'
IO_MANAGER_CLASS = 'pygame'
#options 'dummy', 'piggyphoto'
CAMERA_CLASS = 'dummy'

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

    def switch_state(self, state):
        self.photobooth.state = state

    def switch_next(self):
        self.switch_state(self.next_state)

    def switch_last(self):
        self.switch_state(self.photobooth.last_state)


class PhotoBooth(object):
    def __init__(self, fullscreen=False):

        self.cam = None
        self.screen = None
        self._state = None
        self._last_state = None
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
        #order is important here
        self.io_manager.update()

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
        self._last_state = self._state
        self._state = value
        self._state.reset()

    @property
    def last_state(self):
        return self._last_state

#State machine callback functions

class StateWaitingForCamera(PhotoBoothState):
    """
    Initial state that waits for the camera becoming available
    This state can also be used to return in failure case
    """
    def __init__(self, photobooth, next_state, admin_state):
        super(StateWaitingForCamera, self).__init__(photobooth=photobooth, next_state=next_state)
        self.admin_state = admin_state

    def update_callback(self):
        # try initialisation again
        try:
            if self.photobooth.io_manager.admin_button_pressed():
                if self.admin_state:
                    self.photobooth.state = self.admin_state
            self.photobooth.init_camera()
            self.switch_next()
        except Exception as e:
            show_text_mid(self.photobooth.screen, _("Camera not connected: ") + str(e),
                          get_text_mid_position(self.photobooth.app_resolution), size=INFO_FONT_SIZE, color=COLOR_ORANGE)
            time.sleep(1)


class StateShowSlideShow(PhotoBoothState):
    """
    State showing already taken photos in a random order slide show
    """
    def __init__(self, photobooth, next_state, counter):
        super(StateShowSlideShow, self).__init__(photobooth=photobooth, next_state=next_state, counter=counter, counter_callback=self._next_photo)
        self._photo_set = []
        self.current_photo = None

    def update_callback(self):
        if self.photobooth.event_manager.mouse_pressed() or self.photobooth.io_manager.any_button_pressed(reset=True):
            self.switch_next()

        if self.current_photo:
            show_cam_picture(self.photobooth.screen, self.current_photo)

        self.photobooth.io_manager.show_led_coutdown(self.counter)
        show_text_left(self.photobooth.screen, _("Slideshow, press any button to continue"), (20, 30), INFO_FONT_SIZE)

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
    """
    State waiting for people initiating the next photo
    """
    def __init__(self, photobooth, next_state, timeout_state = None, admin_state=None,failure_state=None, counter=-1):
        super(StateWaitingForPhotoTrigger, self).__init__(photobooth=photobooth, next_state=next_state, counter=counter, counter_callback=self._switch_timeout_state)
        self.timeout_state = timeout_state
        self.failure_state = failure_state
        self.admin_state = admin_state

    def update_callback(self):
        if self.photobooth.io_manager.admin_button_pressed():
            if self.admin_state:
                self.photobooth.state = self.admin_state
        elif self.photobooth.event_manager.mouse_pressed() or self.photobooth.io_manager.any_button_pressed(reset=True):
            self.switch_next()
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
    """
    Count down photo trigger state
    """
    def __init__(self, photobooth, next_state, failure_state=None, counter=-1):
        super(StatePhotoTrigger, self).__init__(photobooth=photobooth, next_state=next_state, counter=counter, counter_callback=self._take_photo)
        self.failure_state = failure_state
        
    def update_callback(self):
        try:
            preview_img = self.photobooth.cam.get_preview()
            show_cam_picture(self.photobooth.screen, preview_img)
            # Show countdown
            show_text_mid(self.photobooth.screen, str(self.counter), get_text_mid_position(self.photobooth.app_resolution), COUNTER_FONT_SIZE)
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

        self.switch_next()


class StateShowPhoto(PhotoBoothState):
    """
    State for showing the last taken photo
    """
    def __init__(self, photobooth, next_state, counter=-1):
        super(StateShowPhoto, self).__init__(photobooth=photobooth, next_state=next_state, counter=counter, counter_callback=self.switch_next)

    def update_callback(self):
        show_cam_picture(self.photobooth.screen, app.last_photo[0])
        show_text_left(self.photobooth.screen, _("Last Photo:"), (20, 30), INFO_FONT_SIZE)

class StatePrinting(PhotoBoothState):
    """
    State for selecting print out
    """
    def __init__(self, photobooth, next_state, counter=-1):
        super(StatePrinting, self).__init__(photobooth=photobooth, next_state=next_state, counter=counter, counter_callback=self.switch_next)
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

        show_text_left(self.photobooth.screen, _("Print photo?"), (20, 30), INFO_FONT_SIZE)
        show_text_left(self.photobooth.screen, _("Press GREEN for printing - RED for canceling"), (20, 60), INFO_FONT_SIZE)
        self.photobooth.io_manager.set_led(led_type=LedType.GREEN,led_state=LedState.ON)
        self.photobooth.io_manager.set_led(led_type=LedType.RED, led_state=LedState.ON)
        self.photobooth.io_manager.set_led(led_type=LedType.BLUE, led_state=LedState.OFF)
        self.photobooth.io_manager.set_led(led_type=LedType.YELLOW, led_state=LedState.OFF)

        if self._error_txt:
            show_text_left(self.photobooth.screen, _("Print failure:"), (20, 360), size=INFO_FONT_SIZE, color=COLOR_ORANGE)
            show_text_left(self.photobooth.screen, self._error_txt, (20, 390), size=INFO_FONT_SIZE, color=COLOR_ORANGE)

        if self.photobooth.event_manager.mouse_pressed() or self.photobooth.io_manager.accept_button_pressed():
            if self.print_photo(app.last_photo[1]):
                self.switch_next()
                self._error_txt = None
            else: # failure
                self.reset()  # reset timeout counter
        elif self.photobooth.io_manager.cancel_button_pressed():
            self.switch_next()


class StateAdmin(PhotoBoothState):
    """
    Administration info and command option state
    """
    def __init__(self, photobooth, next_state, counter=-1):
        super(StateAdmin, self).__init__(photobooth=photobooth, next_state=next_state, counter=counter, counter_callback=self.switch_next)

        self._options = [
            ("Return",self.switch_next),
            ("Close photobooth",self.close_app),
            ("Shutdown all",self.shutdown_all),
            ("Start printer",self.start_printer),
            ("Stop printer",self.stop_printer)
        ]

    def get_free_space(self):
        """
        Determine free space in current directory
        :return: free space in MB
        """
        st = os.statvfs('.')
        free_mb = st.f_bsize * st.f_bavail // 1024 // 1024
        return free_mb

    def get_ip_address(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]

    def get_number_taken_photos(self):
        return len(glob.glob(PHOTO_DIRECTORY + "/*.jpg"))

    def update_callback(self):
        # Background
        draw_rect(self.photobooth.screen,(10,10),(self.photobooth.app_resolution[0]-20, self.photobooth.app_resolution[1]-20))

        # Caption
        show_text_left(self.photobooth.screen, _("Administration"), (20, 30), INFO_FONT_SIZE)

        #Infos
        show_text_left(self.photobooth.screen, _("Free space: ") + str(self._free_space) + "MB", (20, 60), INFO_SMALL_FONT_SIZE)
        show_text_left(self.photobooth.screen, _("IP: ") + str(self._ip_address), (20, 90), INFO_SMALL_FONT_SIZE)
        show_text_left(self.photobooth.screen, _("Printer available: ") + str(self._printer_state), (20, 120), INFO_SMALL_FONT_SIZE)
        show_text_left(self.photobooth.screen, _("Taken photos: ") + str(self._taken_photos), (20, 150), INFO_SMALL_FONT_SIZE)

        show_text_left(self.photobooth.screen, _("Select option:"), (20, 190), INFO_FONT_SIZE)
        # Current selected option
        show_text_left(self.photobooth.screen, self._options[self._current_option_idx][0], (20, 220), size=INFO_FONT_SIZE, color=COLOR_GREEN)
        show_text_left(self.photobooth.screen, _("Green=Select, Red=Return, Yellow=Next, Blue=Previous"), (20, 250), INFO_SMALL_FONT_SIZE)

        #Confirmation request
        if self._request_confirmation:
            show_text_left(self.photobooth.screen, "Please confirm selection: " + self._options[self._current_option_idx][0], (20, 280), INFO_SMALL_FONT_SIZE)
            show_text_left(self.photobooth.screen, "Green=Accept, Red=Cancel", (20, 310),INFO_SMALL_FONT_SIZE)

        #Error
        show_text_left(self.photobooth.screen, self._error_text, (20, 280),
                       size=INFO_FONT_SIZE, color=COLOR_ORANGE)

        #Input handling
        if self._option_confirmed:
            try:
                self._options[self._current_option_idx][1]()
                self._error_text = ""
            except Exception as e:
                self._error_text = str(e)
            self._option_confirmed = False
            self._request_confirmation = False

        if self.photobooth.io_manager.accept_button_pressed():
            if self._request_confirmation:
                self._option_confirmed = True
                self._request_confirmation = False
            else:
                self._request_confirmation = True
        elif self.photobooth.io_manager.cancel_button_pressed():
            if self._request_confirmation:
                self._request_confirmation = False
            else:
                self.switch_last()
        elif self.photobooth.io_manager.next_button_pressed():
            self._current_option_idx += 1
            self._current_option_idx = self._current_option_idx % (len(self._options))
        elif self.photobooth.io_manager.prev_button_pressed():
            self._current_option_idx -= 1
            self._current_option_idx = self._current_option_idx % (len(self._options))

    def close_app(self):
        pygame.quit()

    def start_printer(self):
        print_utils.start_printer()

    def stop_printer(self):
        print_utils.stop_printer()

    def shutdown_all(self):
        print_utils.stop_printer()
        os.system('systemctl poweroff')

    def reset(self):
        super(StateAdmin, self).reset()
        self._free_space = self.get_free_space()
        self._ip_address = self.get_ip_address()
        self._printer_state = print_utils.printer_available()
        self._taken_photos = self.get_number_taken_photos()
        self._current_option_idx = 0
        self._option_confirmed = False
        self._request_confirmation = False
        self._error_text = ""

if __name__ == '__main__':

    #localize application
    language = gettext.translation('photobooth', localedir='locale', languages=[LANGUAGE_ID])
    language.install(unicode=True)

    pygame.init()

    # create app
    app = PhotoBooth(fullscreen=START_FULLSCREEN)

    # Create all states
    #state_show_photo = StateShowPhoto(photobooth=app, next_state=None, counter=PHOTO_SHOW_TIME) # enable this state to use without printing
    state_show_photo = StatePrinting(photobooth=app, next_state=None, counter=PHOTO_WAIT_FOR_PRINT_TIMEOUT)

    state_admin = StateAdmin(photobooth=app, next_state=None)

    state_trigger_photo = StatePhotoTrigger(photobooth=app, next_state=state_show_photo, counter=PHOTO_COUNTDOWN)

    timeout_slide_show = StateShowSlideShow(photobooth=app, next_state=None, counter=SLIDE_SHOW_TIMEOUT)

    state_waiting_for_photo_trigger = StateWaitingForPhotoTrigger(photobooth=app, next_state=state_trigger_photo,
                                                                  admin_state=state_admin, timeout_state=timeout_slide_show,
                                                                  counter=PHOTO_TIMEOUT)

    state_show_photo.next_state = state_waiting_for_photo_trigger
    timeout_slide_show.next_state = state_waiting_for_photo_trigger

    state_waiting_for_camera = StateWaitingForCamera(photobooth=app, next_state=state_waiting_for_photo_trigger, admin_state=state_admin)
    state_waiting_for_photo_trigger.failure_state = state_waiting_for_camera
    state_trigger_photo.failure_state = state_waiting_for_camera
    state_admin.next_state = state_waiting_for_camera

    #initial app state
    app.state = state_waiting_for_camera


    # Main program loop
    while not app.event_manager.quit_pressed():
        
        try:
            app.update()

        except Exception as e:
            print(e)
            show_text_mid(app.screen, _("Error"), get_text_mid_position(app.app_resolution))
        pygame.display.update()
