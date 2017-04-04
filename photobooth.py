import piggyphoto
import pygame
import time

DEFAULT_RESOLUTION = [640,424]

START_FULLSCREEN = True

DEFAULT_FONT_SIZE = 72

COUNTER_FONT_SIZE = 140

MOUSE_LEFT = 1
MOUSE_RIGHT = 3

PHOTO_TIMEOUT = 10
PHOTO_COUNTDOWN = 5
PHOTO_SHOW_TIME = 5

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

class Camera(object):
    """
    Class wrapping camera access
    """

    def __init__(self):
        self.cam = None
        self.cam = piggyphoto.camera()
        # cam.leave_locked()

    def set_memory_capture(self):
        # set capturetarget to memory card
        cam_config = self.cam.config
        cam_config['main']['settings']['capturetarget'].value = 'Memory card'
        self.cam.config = cam_config

    def set_idle(self):
        cam_config = self.cam.config
        cam_config['main']['actions']['viewfinder'].value = 0
        self.cam.config = cam_config

    def get_preview(self):
        self.cam.capture_preview('preview.jpg')
        picture = pygame.image.load("preview.jpg")
        return picture

    def take_photo(self,app):
        self.cam.capture_image('snap.jpg')
        app.last_photo = pygame.image.load('snap.jpg')
        app.last_photo = pygame.transform.scale(app.last_photo, app.screen.get_size())

    def __del__(self):
        if self.cam:    
            self.cam.exit()


class PhotoBooth(object):
    def __init__(self, fullscreen=False):
        self.cam = None
        self.screen = None
        self._state = None

        self.fullscreen=fullscreen
        # Detect the screen resolution
        info_object = pygame.display.Info()
        self.screen_resolution = [info_object.current_w, info_object.current_h]

        if self.fullscreen:
            self.screen = pygame.display.set_mode(self.screen_resolution, pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(DEFAULT_RESOLUTION)

        self.app_resolution = self.screen.get_size()

        self.screen.fill((128, 128, 128))
            
        self.last_photo = None

    def init_camera(self):
        self.cam = Camera()
        picture = self.cam.get_preview()
        
        if self.fullscreen:
            self.screen = pygame.display.set_mode(self.screen_resolution, pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(picture.get_size())

        self.app_resolution = self.screen.get_size()

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value
        self._state.reset()

#helper functions

def get_text_mid_position(resolution):
    return (resolution[0]/2,resolution[1]/2)

def quit_pressed():
    if pygame.event.get(pygame.QUIT):
        return True
    for event in pygame.event.get(pygame.KEYDOWN):
        if event.key == pygame.K_ESCAPE:
            return True
    return False

def mouse_pressed():
    for event in pygame.event.get(pygame.MOUSEBUTTONUP):
        if event.button == MOUSE_LEFT:
            return True
    return False

def show_cam_picture(screen, picture, fullscreen = True):
    if fullscreen:
        img = pygame.transform.scale(picture, screen.get_size())
    else:
        img = picture
    screen.blit(img, (0, 0))

def get_text_img(text, size, color):
    font = pygame.font.Font(None, size)

    return font.render(text, True, color)

def show_text(screen, text, pos, size=DEFAULT_FONT_SIZE):
    txt_img = get_text_img(text, size, (255, 255, 255))
    screen.blit(txt_img,
                (pos[0] - txt_img.get_width() // 2, pos[1] - txt_img.get_height() // 2))

#State machine callback functions

class StateWaitingForCamera(PhotoBoothState):
    def __init__(self, photobooth, next_state):
        super(self.__class__, self).__init__(photobooth=photobooth, next_state=next_state)

    def update_callback(self):
        # try initialisation again
        try:
            self.photobooth.init_camera()
            self.photobooth.state = self.next_state
        except Exception, e:
            show_text(self.photobooth.screen, "Camera not connected: "+str(e), get_text_mid_position(self.photobooth.app_resolution))
            time.sleep(30)


class StateShowSlideShow(PhotoBoothState):
    def __init__(self, photobooth, next_state):
        super(self.__class__, self).__init__(photobooth=photobooth, next_state=next_state)

    def update_callback(self):
        if mouse_pressed():
            self.photobooth.state = self.next_state
        #TODO EXTEND TO REAL SLIDESHOW
        if app.last_photo:
            show_cam_picture(self.photobooth.screen, app.last_photo)

        show_text(self.photobooth.screen, "Slideshow, press any button to continue", (100, 30), 36)

    def reset(self):
        super(self.__class__, self).reset()
        if self.photobooth.cam:
            self.photobooth.cam.set_idle()


class StateWaitingForPhotoTrigger(PhotoBoothState):
    def __init__(self, photobooth, next_state, timeout_state = None, counter=-1):
        super(self.__class__, self).__init__(photobooth=photobooth, next_state=next_state, counter=counter, counter_callback=self._switch_timeout_state)
        self.timeout_state=timeout_state

    def update_callback(self):
        if mouse_pressed():
            self.photobooth.state = self.next_state
        preview_img = self.photobooth.cam.get_preview()
        show_cam_picture(self.photobooth.screen, preview_img)

    def _switch_timeout_state(self):
        if self.timeout_state:
            self.photobooth.state = self.timeout_state
        else:
            self.reset()


class StatePhotoTrigger(PhotoBoothState):
    def __init__(self, photobooth, next_state, counter=-1):
        super(self.__class__, self).__init__(photobooth=photobooth, next_state=next_state, counter=counter, counter_callback=self._take_photo)

    def update_callback(self):

        preview_img = self.photobooth.cam.get_preview()
        show_cam_picture(self.photobooth.screen, preview_img)
        # Show countdown
        show_text(self.photobooth.screen, str(self.counter), get_text_mid_position(self.photobooth.app_resolution), 140)

    def _take_photo(self):
        #first update to latest preview
        preview_img = self.photobooth.cam.get_preview()
        show_cam_picture(self.photobooth.screen, preview_img)
        pygame.display.update()
        #take photo
        self.photobooth.cam.take_photo(self.photobooth)
        self.photobooth.state = self.next_state


class StateShowPhoto(PhotoBoothState):
    def __init__(self, photobooth, next_state, counter=-1):
        super(self.__class__, self).__init__(photobooth=photobooth, next_state=next_state, counter=counter, counter_callback=self._switch_to_next_state)

    def update_callback(self):
        show_cam_picture(self.photobooth.screen, app.last_photo)
        show_text(self.photobooth.screen, "Last Photo:", (70, 30), 36)

    def _switch_to_next_state(self):
        self.photobooth.state = self.next_state


if __name__ == '__main__':
    pygame.init()

    pygame.event.set_allowed(None)
    pygame.event.set_allowed(pygame.MOUSEBUTTONUP)
    pygame.event.set_allowed(pygame.KEYDOWN)
    pygame.event.set_allowed(pygame.QUIT)

    app = PhotoBooth(fullscreen=START_FULLSCREEN)

    # Create all states
    state_show_photo = StateShowPhoto(photobooth=app, next_state=None, counter=PHOTO_SHOW_TIME)

    state_trigger_photo = StatePhotoTrigger(photobooth=app, next_state=state_show_photo, counter=PHOTO_COUNTDOWN)

    timeout_slide_show = StateShowSlideShow(photobooth=app, next_state=None)

    state_waiting_for_photo_trigger = StateWaitingForPhotoTrigger(photobooth=app, next_state=state_trigger_photo, timeout_state=timeout_slide_show, counter=PHOTO_TIMEOUT)

    state_show_photo.next_state = state_waiting_for_photo_trigger
    timeout_slide_show.next_state = state_waiting_for_photo_trigger

    state_waiting_for_camera = StateWaitingForCamera(photobooth=app, next_state=state_waiting_for_photo_trigger)

    app.state = state_waiting_for_camera


    while not quit_pressed():
        
        try:

            app.state.update()

            pygame.event.pump()
            #pygame.event.clear()

        except Exception, e:
            print(e)
            show_text(app.screen, "Error", get_text_mid_position(self.photobooth.app_resolution))
        pygame.display.update()
