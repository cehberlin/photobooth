#! /usr/bin/env python
import time
import glob
import random
import os
import socket
import gettext
import traceback
import yaml
import sys
from subprocess import check_output

#Own modules
from pygame_utils import *
from user_io import get_user_io_factory, LedState, LedType
from camera import get_camera_factory
from instagram_filters.filters import Gotham,Kelvin,Nashville,Lomo,Toaster,BlackAndWhite
import print_utils
import storage

#Visual Configuration
DEFAULT_RESOLUTION = [640,424]

COUNTER_FONT_SIZE = 140
INFO_FONT_SIZE = 36
INFO_SMALL_FONT_SIZE = 24
INFO_TEXT_Y_POS = 100


def draw_wait_box(screen, text):
    draw_text_box(screen=screen, text=text, pos=(None, None),
                  size=INFO_FONT_SIZE)
    pygame.display.update()

class PhotoBoothState(object):

    def __init__(self, photobooth, next_state, failure_state=None, counter_callback=None, counter_callback_args=None, counter=-1):
        self.photobooth = photobooth
        self.next_state = next_state
        self.inital_counter = counter

        self.failure_state = failure_state

        self.counter_callback = counter_callback
        self.counter_callback_args = counter_callback_args
        self.counter_sleep_time = 1
        self.enabled = False
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
        try:
            self.update_callback()
            self.update_counter()
        except Exception:
            print(traceback.format_exc())
            if self.failure_state:
                self.switch_state(self.failure_state)
            else:
                print('No failure_state defined, trying to switch to last state')
                self.switch_last()
            return

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
    def __init__(self, config):

        self.cam = None
        self.screen = None
        self._state = None
        self._last_state = None
        # tuple of (pygame.image, image path)
        self._last_photo_resized = None
        # tuple of (pygame.image, image path)
        self._last_photo = None
        self._taken_photos = []

        self.config = config

        self.tmp_dir = config['temp_directory']

        self.fullscreen=bool(config['fullscreen'])
        # Detect the screen resolution
        info_object = pygame.display.Info()
        self.screen_resolution = [info_object.current_w, info_object.current_h]

        self.set_fullscreen(self.fullscreen)

        self.app_resolution = self.screen.get_size()

        self.screen.fill((128, 128, 128))
            
        self.event_manager = PyGameEventManager()

        self.io_manager = get_user_io_factory().create_algorithm(id_class=config['io_manager'], photobooth=self)

        self.change_photo_dir(config['photo_directory'])

    def set_fullscreen(self, fullscreen):
        if fullscreen:
            self.screen = pygame.display.set_mode(self.screen_resolution, pygame.FULLSCREEN)
            pygame.mouse.set_visible(False)
        else:
            if self.cam:
                picture = self.cam.get_preview()
                self.screen = pygame.display.set_mode(picture.get_size())
            else:
                self.screen = pygame.display.set_mode(DEFAULT_RESOLUTION)

        self.app_resolution = self.screen.get_size()

    def change_photo_dir(self, new_directory):

        self.photo_directory = new_directory
        # create photo directory if necessary
        if not os.path.exists(self.photo_directory):
            os.makedirs(self.photo_directory)

        self.init_camera()

    def init_camera(self):
        if self.cam:
            self.cam.close()

        self.cam = get_camera_factory().create_algorithm(id_class=self.config['camera_type'], photo_directory=self.photo_directory, tmp_directory=self.tmp_dir)
        self.cam.disable_live_autofocus()
        self.set_fullscreen(self.fullscreen)

    def update(self):
        self.event_manager.update_events()
        self.state.update()
        #order is important here
        self.io_manager.update()

    def close(self):
        if self.cam:
            self.cam.set_idle()
        if self.io_manager:
            self.io_manager.set_all_led(LedState.OFF)
        pygame.quit()

    @property
    def last_photo(self):
        """
        last photo
        :return: tuple of (pygame.image, image path)
        """
        return self._last_photo

    @property
    def last_photo_resized(self):
        """
        last photo already resized to screen
        :return: tuple of (pygame.image, image path)
        """
        return self._last_photo_resized

    @last_photo.setter
    def last_photo(self, value):
        """
        set new photo
        :param value: tuple of (pygame.image, image path)
        """
        self._last_photo = value
        #resize photo to screen
        self._last_photo_resized = (pygame.transform.scale(value[0], self.screen.get_size()), value[1])

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        if not value.enabled:
            self.state = value.next_state
            return

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
            #background color
            draw_rect(self.photobooth.screen, (0, 0), self.photobooth.app_resolution)
            if self.photobooth.io_manager.admin_button_pressed():
                if self.admin_state:
                    self.photobooth.state = self.admin_state
            self.photobooth.init_camera()
            self.switch_next()
        except Exception as e:
            pos = get_text_mid_position(self.photobooth.app_resolution)
            show_text_mid(self.photobooth.screen, _("Camera not connected: ") + str(e), pos,
                           size=INFO_FONT_SIZE, color=COLOR_ORANGE)
            time.sleep(1)


class StateShowSlideShow(PhotoBoothState):
    """
    State showing already taken photos in a random order slide show
    """
    def __init__(self, photobooth, next_state, counter):
        super(StateShowSlideShow, self).__init__(photobooth=photobooth, next_state=next_state, counter=counter, counter_callback=self._next_photo)
        self._photo_set = []
        self.current_photo = None

        logo = self.photobooth.config['logo']
        if logo:
            self._logo_img = pygame.image.load(logo)
        else:
            self._logo_img = None

    def update_callback(self):
        if self.photobooth.event_manager.mouse_pressed() or self.photobooth.io_manager.any_button_pressed(reset=True):
            self.switch_next()

        if self.current_photo:
            show_cam_picture(self.photobooth.screen, self.current_photo)
            if self._logo_img:
                self.draw_logo(self._logo_img)

        self.photobooth.io_manager.show_led_coutdown(self.counter)

        draw_text_box(screen=self.photobooth.screen, text=_("Slideshow, press any button to continue"), pos=(None, self.photobooth.app_resolution[1]-80), size=INFO_FONT_SIZE)

    def draw_logo(self, logo):
        offset = 15
        img_size = logo.get_size()
        pos = (self.photobooth.app_resolution[0] - img_size[0] - offset, offset)
        self.photobooth.screen.blit(logo, pos)

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
        self._photo_set = glob.glob(self.photobooth.photo_directory + "/*.jpg")

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
    def __init__(self, photobooth, next_state, timeout_state = None, admin_state=None, failure_state=None, counter=-1):
        super(StateWaitingForPhotoTrigger, self).__init__(photobooth=photobooth, next_state=next_state,
                                                          failure_state=failure_state, counter=counter,
                                                          counter_callback=self._switch_timeout_state)
        self.timeout_state = timeout_state
        self.admin_state = admin_state

    def update_callback(self):
        if self.photobooth.io_manager.admin_button_pressed():
            if self.admin_state:
                self.photobooth.state = self.admin_state
        elif self.photobooth.event_manager.mouse_pressed() or self.photobooth.io_manager.any_button_pressed(reset=True):
            self.switch_next()
        preview_img = self.photobooth.cam.get_preview()
        show_cam_picture(self.photobooth.screen, preview_img)

        draw_button_bar(self.photobooth.screen, text=[_("Photo"),_("Photo"),_("Photo"),_("Photo")], pos=(None,self.photobooth.app_resolution[1]-60))
        self.photobooth.io_manager.set_all_led(LedState.ON) #TODO maybe not necessary, but needs to be tested

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
        super(StatePhotoTrigger, self).__init__(photobooth=photobooth, next_state=next_state,
                                                failure_state=failure_state, counter=counter,
                                                counter_callback=self._take_photo)
        self._arrow_img = pygame.image.load('res/arrow.png')
        self._mid_position = get_text_mid_position(self.photobooth.app_resolution)

    def update_callback(self):

        self.photobooth.io_manager.show_led_coutdown(self.counter)

        if self.counter == 1:
            self.photobooth.cam.disable_live_autofocus()
            self.show_final_view()
        else:
            preview_img = self.photobooth.cam.get_preview()
            show_cam_picture(self.photobooth.screen, preview_img)

            # Show countdown
            show_text_mid(self.photobooth.screen, str(self.counter), self._mid_position, COUNTER_FONT_SIZE)

        #cancel photo if necessary
        draw_button_bar(self.photobooth.screen, text=[_("Cancel"), "", "", ""],
                        pos=(None, self.photobooth.app_resolution[1] - 60))
        if self.photobooth.io_manager.cancel_button_pressed():
            self.photobooth.cam.disable_live_autofocus()
            self.switch_last()

    def show_final_view(self):
        arrow_size = self._arrow_img.get_size()
        offset = 50
        pos = (self._mid_position[0] - (arrow_size[0] // 2), offset)
        draw_rect(self.photobooth.screen, (0, 0),
                  (self.photobooth.app_resolution[0], self.photobooth.app_resolution[1]))
        self.photobooth.screen.blit(self._arrow_img, pos)
        show_text_mid(self.photobooth.screen, _("Smile :-)"), (self._mid_position[0], arrow_size[1]+50 + offset),
                      COUNTER_FONT_SIZE, color=COLOR_DARK_GREY)

    def reset(self):
        super(StatePhotoTrigger, self).reset()
        self._mid_position = get_text_mid_position(self.photobooth.app_resolution) # update in case resolution changed
        if self.photobooth.cam:
            self.photobooth.cam.enable_live_autofocus()
        
    def _take_photo(self):

        self.photobooth.io_manager.show_led_coutdown(self.counter)

        # take photo
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
        show_cam_picture(self.photobooth.screen, self.photobooth.last_photo_resized[0])

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
        show_cam_picture(self.photobooth.screen, self.photobooth.last_photo_resized[0])

        self.photobooth.io_manager.set_led(led_type=LedType.GREEN,led_state=LedState.ON)
        self.photobooth.io_manager.set_led(led_type=LedType.RED, led_state=LedState.ON)
        self.photobooth.io_manager.set_led(led_type=LedType.BLUE, led_state=LedState.OFF)
        self.photobooth.io_manager.set_led(led_type=LedType.YELLOW, led_state=LedState.OFF)

        if self._error_txt:
            show_text_left(self.photobooth.screen, _("Print failure:"), (20, 240), size=INFO_FONT_SIZE, color=COLOR_ORANGE)
            show_text_left(self.photobooth.screen, self._error_txt, (20, 270), size=INFO_FONT_SIZE, color=COLOR_ORANGE)

        if self.photobooth.event_manager.mouse_pressed() or self.photobooth.io_manager.accept_button_pressed():
            draw_wait_box(screen=self.photobooth.screen, text=_("Please wait, printing ..."))
            if self.print_photo(self.photobooth.last_photo[1]):
                self.switch_next()
                self._error_txt = None
            else: # failure
                self.reset()  # reset timeout counter
        elif self.photobooth.io_manager.cancel_button_pressed():
            self.switch_next()

        draw_text_box(screen=self.photobooth.screen, text=_("Print photo?"), pos=(None, INFO_TEXT_Y_POS), size=INFO_FONT_SIZE)
        draw_button_bar(self.photobooth.screen, text=[_("Cancel"), "", "", _("Print")], pos=(None, self.photobooth.app_resolution[1] - 60))


class StateFilter(PhotoBoothState):
    """
    State for providing several filter options of the photo
    """
    def __init__(self, photobooth, next_state, counter=-1):
        super(StateFilter, self).__init__(photobooth=photobooth, next_state=next_state, counter=counter, counter_callback=self.switch_next)

        self.filter_photos = []
        self._picture_size = ()
        self._current_filter_idx = 0
        self._filter_count = 4

    def filter_photo_fullsize(self, photo, idx, dest):
        """
        filter photo in full resolution
        :param photo: tuple (pygame.image, path)
        :param idx: filter_idx to apply
        :param dest: destination path of photo
        :return: tuple (pygame.image,path) of new photo
        """
        filter_file = dest

        width = photo[0].get_size()[0]
        height =photo[0].get_size()[1]

        if self.apply_photo_filter(input_file=photo[1], idx=idx, output_file=dest, width=width, height=height):

            photo_obj = pygame.image.load(filter_file)

            photo_obj = pygame.transform.scale(photo_obj, self.photobooth.screen.get_size())

            return photo_obj, filter_file
        else:
            return photo

    def filter_photo_preview(self, photo, idx):
        """
        create a small preview filter img
        :param photo: tuple (pygame.image,path)
        :param idx: filter_idx to apply
        :return: tuple (pygame.image,path) of new photo
        """

        filter_file = self.photobooth.tmp_dir + "/filter" + str(idx) + ".jpg"

        pygame.image.save(photo[0], filter_file)

        if self.apply_photo_filter(filter_file, idx):

            photo_obj = pygame.image.load(filter_file)

            return photo_obj, filter_file

        else:
            return photo

    def apply_photo_filter(self, input_file, idx, output_file=None, width=None, height=None):
        """
        apply a photo filter
        :param input_file: the photo file to filter
        :param idx: the idx of the filter to use
        :param output_file: the created file
        :param width: optional width of image to save some image loading
        :param height: optional height of image to save some image loading
        :return: True if a filter was applied
        """

        fil = None
        if idx == 1:
            fil = Nashville(filename=input_file, output_filename=output_file, width=width, height=height)
        if idx == 2:
            fil = Toaster(filename=input_file, output_filename=output_file, width=width, height=height)
        if idx == 3:
            fil = BlackAndWhite(filename=input_file, output_filename=output_file, width=width, height=height)

        if fil:
            fil.apply()
            fil.close_image()
            return True
        else:
            return False

    def create_filtered_photo_collection(self):
        """
        Create small thumbnail preview filtered photos
        """
        last_photo = self.photobooth.last_photo_resized
        scaled_original_photo = (pygame.transform.scale(last_photo[0], self._picture_size), last_photo[1])

        self.filter_photos = [
            scaled_original_photo,
            self.filter_photo_preview(photo=scaled_original_photo, idx=1),
            self.filter_photo_preview(photo=scaled_original_photo, idx=2),
            self.filter_photo_preview(photo=scaled_original_photo, idx=3)
        ]

    def draw_filtered_photos(self):
        """
        draw filter previews to screen
        """
        if len(self.filter_photos) > 0:
            image_pos = (0, 0)
            rect_pos = image_pos
            self.photobooth.screen.blit(self.filter_photos[0][0], image_pos)
            if self._current_filter_idx == 0:
                rect_pos = image_pos
            image_pos = (self._picture_size[0], 0)
            self.photobooth.screen.blit(self.filter_photos[1][0], image_pos)
            if self._current_filter_idx == 1:
                rect_pos = image_pos
            image_pos = ( 0, self._picture_size[1])
            self.photobooth.screen.blit(self.filter_photos[2][0], image_pos)
            if self._current_filter_idx == 2:
                rect_pos = image_pos
            image_pos = self._picture_size
            self.photobooth.screen.blit(self.filter_photos[3][0], image_pos)
            if self._current_filter_idx == 3:
                rect_pos = image_pos
            draw_rect(self.photobooth.screen, rect_pos, self._picture_size, color=None, color_border=COLOR_ORANGE,
                      size_border=8)
            text_margin = 10
            selected_image_text_pos = (rect_pos[0] + text_margin,rect_pos[1]+ text_margin)
            draw_text_box(screen=self.photobooth.screen, text=_("Selected"), pos= selected_image_text_pos,
                          size=INFO_FONT_SIZE, box_color=None, border_color=COLOR_ORANGE, size_border=5, text_color=COLOR_ORANGE)

    def draw_selected(self):
        pass

    def update_callback(self):

        self.draw_filtered_photos()

        # handle filter selection
        if self.photobooth.io_manager.next_button_pressed():
            self._current_filter_idx += 1
            self.set_counter(self.inital_counter)
        if self.photobooth.io_manager.prev_button_pressed():
            self._current_filter_idx -= 1
            self.set_counter(self.inital_counter)

        self._current_filter_idx = self._current_filter_idx % self._filter_count

        if self.photobooth.io_manager.cancel_button_pressed():
            self.switch_state(self.failure_state)
            return

        if self.photobooth.io_manager.accept_button_pressed():

            # create final file name
            path, ext = os.path.splitext(self.photobooth.last_photo[1])

            filter_file = path + '_filtered' + ext
            draw_wait_box(self.photobooth.screen, _("Please wait, processing ..."))
            # redo filtering on full image resolution
            self.photobooth.last_photo = self.filter_photo_fullsize(photo=self.photobooth.last_photo, idx=self._current_filter_idx, dest=filter_file)

            self.switch_next()
            return

        draw_text_box(screen=self.photobooth.screen, text=_("Select photo?"), pos=(None, INFO_TEXT_Y_POS), size=INFO_FONT_SIZE)

        draw_button_bar(self.photobooth.screen, text=[_("Cancel"), _("Prev"), _("Next"), _("Select")], pos=(None,self.photobooth.app_resolution[1]-60))

    def reset(self):
        super(StateFilter, self).reset()

        draw_wait_box(self.photobooth.screen, _("Please wait, processing ..."))
        self._current_filter_idx = 0
        self.photobooth.io_manager.set_led(led_type=LedType.GREEN,led_state=LedState.ON)
        self.photobooth.io_manager.set_led(led_type=LedType.RED, led_state=LedState.ON)
        self.photobooth.io_manager.set_led(led_type=LedType.BLUE, led_state=LedState.ON)
        self.photobooth.io_manager.set_led(led_type=LedType.YELLOW, led_state=LedState.ON)

        self._picture_size = (self.photobooth.screen.get_size()[0] // 2, self.photobooth.screen.get_size()[1] // 2)

        if self.photobooth.last_photo_resized:
            self.create_filtered_photo_collection()


class StateAdmin(PhotoBoothState):
    """
    Administration info and command option state
    """
    def __init__(self, photobooth, next_state, counter=2, state_showphoto=None, state_filter=None, state_printing=None):
        super(StateAdmin, self).__init__(photobooth=photobooth, next_state=next_state, counter=counter, counter_callback=self.enable_input)

        self.state_showphoto = state_showphoto
        self.state_filter = state_filter
        self.state_printing = state_printing

        # we wait some seconds to handle button input to avoid missclicks due required button combo for enabling this mode
        self.input_handling = False

        self._options = [
            (_("Return"), self.switch_next),
            (_("Toggle fullscreen"), self.toggle_fullscreen),
            (_("Enable/Disable state ShowPhoto"), self.toggle_state_showphoto),
            (_("Enable/Disable state Filter"), self.toggle_state_filter),
            (_("Enable/Disable state Printing"), self.toggle_state_printing),
            (_("Close photobooth"), self.photobooth.close),
            (_("Shutdown all"), self.shutdown_all),
            (_("Start printer"), self.start_printer),
            (_("Stop printer"), self.stop_printer),
            (_("Mount/Umount USB storage"), self.toggle_usb_storage),
        ]

    def enable_input(self):
        self.input_handling = True

    def toggle_state_showphoto(self):
        """
        Enable/Disable show_photo state
        """
        if self.state_showphoto:
            self.state_showphoto.enabled = not self.state_showphoto.enabled

    def toggle_state_filter(self):
        """
        Enable/Disable filter state
        :return:
        """
        if self.state_filter:
            self.state_filter.enabled = not self.state_filter.enabled

    def toggle_fullscreen(self):
        """
        Toggle app fullscreen mode
        """
        self.photobooth.fullscreen = not self.photobooth.fullscreen
        self.photobooth.set_fullscreen(self.photobooth.fullscreen)

    def toggle_state_printing(self):
        """
        Enable/Disable printing state
        """
        if self.state_printing:
            self.state_printing.enabled = not self.state_printing.enabled

    def toggle_usb_storage(self):
        if self.photobooth.photo_directory == self.photobooth.config['photo_directory']:
            storage.umount_device(self.photobooth.config['usb_device'])
            self.photobooth.change_photo_dir(storage.mount_device(self.photobooth.config['usb_device']))
        else:
            storage.umount_device(self.photobooth.config['usb_device'])
            self.photobooth.change_photo_dir(self.photobooth.config['photo_directory'])

        self.refresh_information()

    def get_free_space(self):
        """
        Determine free space in current directory
        :return: free space in MB
        """
        free_mb = 0

        try:
            st = os.statvfs(self.photobooth.photo_directory)
            free_mb = st.f_bsize * st.f_bavail // 1024 // 1024
        except:
            print(traceback.format_exc())

        return free_mb

    def get_ip_address(self):
        socket_name = _("WiFi not found")
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            socket_name = s.getsockname()[0]

        except:
            print(traceback.format_exc())

        return socket_name

    def get_network_name(self):

        ssid = _("WiFi not found")
        try:
            scanoutput = check_output(["iwconfig", "wlan0"])
            for line in scanoutput.split():
                line = line.decode("utf-8")
                if line[:5] == "ESSID":
                    ssid = line.split('"')[1]
        except:
            print(traceback.format_exc())

        return ssid

    def get_number_taken_photos(self):
        return len(glob.glob(self.photobooth.photo_directory + "/*.jpg"))

    def update_callback(self):
        # Background
        draw_rect(self.photobooth.screen,(10,10),(self.photobooth.app_resolution[0]-20, self.photobooth.app_resolution[1]-20))

        x_pos = 20
        y_pos= INFO_TEXT_Y_POS

        # Caption
        show_text_left(self.photobooth.screen, _("Administration"), (x_pos, y_pos), INFO_FONT_SIZE)
        y_pos+=30
        #Infos
        show_text_left(self.photobooth.screen, _("Fullscreen: ") + str(self.photobooth.fullscreen), (x_pos, y_pos),
                       INFO_SMALL_FONT_SIZE, color=COLOR_DARK_GREY)
        y_pos += 30
        show_text_left(self.photobooth.screen, _("Free space: ") + str(self._free_space) + "MB", (x_pos, y_pos), INFO_SMALL_FONT_SIZE, color=COLOR_DARK_GREY)
        y_pos += 30
        show_text_left(self.photobooth.screen, _("Network: ") + str(self._network), (x_pos, y_pos), INFO_SMALL_FONT_SIZE,
                       color=COLOR_DARK_GREY)
        y_pos += 30
        show_text_left(self.photobooth.screen, _("IP: ") + str(self._ip_address), (x_pos, y_pos), INFO_SMALL_FONT_SIZE, color=COLOR_DARK_GREY)
        y_pos += 30
        show_text_left(self.photobooth.screen, _("Printer available: ") + str(self._printer_state), (x_pos, y_pos), INFO_SMALL_FONT_SIZE, color=COLOR_DARK_GREY)
        y_pos += 30
        show_text_left(self.photobooth.screen, _("Photo directory: ") + str(self.photobooth.photo_directory), (x_pos, y_pos),
                       INFO_SMALL_FONT_SIZE, color=COLOR_DARK_GREY)
        y_pos += 30
        show_text_left(self.photobooth.screen, _("Taken photos: ") + str(self._taken_photos), (x_pos, y_pos), INFO_SMALL_FONT_SIZE, color=COLOR_DARK_GREY)
        y_pos += 30
        if self.state_showphoto:
            show_text_left(self.photobooth.screen, _("State 'ShowPhotos' enabled: ") + str(self.state_showphoto.enabled), (x_pos, y_pos),
                           INFO_SMALL_FONT_SIZE, color=COLOR_DARK_GREY)
            y_pos += 30
        if self.state_filter:
            show_text_left(self.photobooth.screen, _("State 'Filter' enabled: ") + str(self.state_filter.enabled),
                           (x_pos, y_pos),
                           INFO_SMALL_FONT_SIZE, color=COLOR_DARK_GREY)
            y_pos += 30
        if self.state_printing:
            show_text_left(self.photobooth.screen, _("State 'Printing' enabled: ") + str(self.state_printing.enabled),
                           (x_pos, y_pos),
                           INFO_SMALL_FONT_SIZE, color=COLOR_DARK_GREY)
            y_pos += 30

        show_text_left(self.photobooth.screen, _("Select option:"), (x_pos, y_pos), INFO_FONT_SIZE, color=COLOR_WHITE)
        y_pos += 30
        # Current selected option
        show_text_left(self.photobooth.screen, self._options[self._current_option_idx][0], (x_pos, y_pos), size=INFO_FONT_SIZE, color=COLOR_GREEN)

        if not self._request_confirmation:
            draw_button_bar(self.photobooth.screen, text=[_("Back"), _("Prev"), _("Next"), _("Select")], pos=(None,self.photobooth.app_resolution[1]-60))
        y_pos += 60
        #Confirmation request
        if self._request_confirmation:
            show_text_left(self.photobooth.screen, "Please confirm selection: " + self._options[self._current_option_idx][0],
                           (x_pos, y_pos), INFO_SMALL_FONT_SIZE, color=COLOR_DARK_GREY)
            draw_button_bar(self.photobooth.screen, text=[_("Cancel"), "", "", _("Accept")], pos=(None,self.photobooth.app_resolution[1]-60))

        #Error
        show_text_left(self.photobooth.screen, self._error_text, (x_pos, y_pos),
                       size=INFO_FONT_SIZE, color=COLOR_ORANGE)

        if(not self.input_handling):
            return

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

    def start_printer(self):
        print_utils.start_printer()

    def stop_printer(self):
        print_utils.stop_printer()

    def shutdown_all(self):
        print_utils.stop_printer()
        os.system('systemctl poweroff')

    def reset(self):
        super(StateAdmin, self).reset()
        self.refresh_information()
        self._current_option_idx = 0
        self._option_confirmed = False
        self._request_confirmation = False
        self._error_text = ""

    def refresh_information(self):
        self._free_space = self.get_free_space()
        self._network = self.get_network_name()
        self._ip_address = self.get_ip_address()
        self._printer_state = print_utils.printer_available()
        self._taken_photos = self.get_number_taken_photos()


def read_configuration():
    # load configuration
    if len(sys.argv) < 2:
        config_file = 'test.cfg'
    else:
        config_file = sys.argv[1]
    with open(config_file, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    return cfg


if __name__ == '__main__':

    pygame.init()

    cfg = read_configuration()

    read_configuration()# localize application
    language = gettext.translation('photobooth', localedir='locale', languages=[cfg['language']])
    language.install(unicode=True)

        # create app
    app = PhotoBooth(config=cfg)

    # Create all states

    state_printing = StatePrinting(photobooth=app, next_state=None, counter=cfg['wait_for_print_timeout'])

    state_filter_photo = StateFilter(photobooth=app, next_state=state_printing, counter=cfg['wait_for_print_timeout'])

    state_show_photo = StateShowPhoto(photobooth=app, next_state=state_filter_photo, counter=cfg['photo_show_time']) # enable this state to use without printing

    state_admin = StateAdmin(photobooth=app, next_state=None, state_showphoto=state_show_photo, state_filter=state_filter_photo, state_printing=state_printing)

    state_trigger_photo = StatePhotoTrigger(photobooth=app, next_state=state_show_photo, counter=cfg['photo_countdown'])

    state_timeout_slide_show = StateShowSlideShow(photobooth=app, next_state=None, counter=cfg['slide_show_timeout'])

    state_waiting_for_photo_trigger = StateWaitingForPhotoTrigger(photobooth=app, next_state=state_trigger_photo,
                                                                  admin_state=state_admin, timeout_state=state_timeout_slide_show,
                                                                  counter=cfg['photo_timeout'])

    state_printing.next_state = state_waiting_for_photo_trigger
    state_timeout_slide_show.next_state = state_waiting_for_photo_trigger

    state_waiting_for_camera = StateWaitingForCamera(photobooth=app, next_state=state_waiting_for_photo_trigger, admin_state=state_admin)

    state_admin.next_state = state_waiting_for_camera

    state_waiting_for_photo_trigger.failure_state = state_waiting_for_camera
    state_trigger_photo.failure_state = state_waiting_for_camera
    state_printing.failure_state = state_waiting_for_photo_trigger
    state_filter_photo.failure_state = state_waiting_for_camera #state_waiting_for_photo_trigger
    state_show_photo.failure_state = state_waiting_for_photo_trigger

    #Enable the states we want to use
    state_waiting_for_camera.enabled = True
    state_waiting_for_photo_trigger.enabled = True
    state_trigger_photo.enabled = True
    state_admin.enabled = True
    state_timeout_slide_show.enabled = True
    state_printing.enabled = True
    state_show_photo.enabled = True
    state_filter_photo.enabled = True
    state_printing.enabled = True

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

    app.close()
