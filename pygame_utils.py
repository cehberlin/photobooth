import pygame

DEFAULT_FONT_SIZE = 72

class PyGameEventManager(object):
    """
    Classes caches and simplifies pygame event management
    """

    MOUSE_LEFT = 1
    MOUSE_RIGHT = 3

    def __init__(self):
        self.events = []
        pygame.event.set_allowed(None)
        pygame.event.set_allowed(pygame.MOUSEBUTTONUP)
        pygame.event.set_allowed(pygame.KEYDOWN)
        pygame.event.set_allowed(pygame.QUIT)

    def update_events(self):
        """
        Update method has to be called every cycle in python main loop
        """
        self.events = pygame.event.get()
        pygame.event.pump()

    def key_pressed(self, keys):
        """
        check if a key from the given key list is pressed
        :param keys:
        :return: True if one is pressed
        """
        for event in self.events:
            if event.type == pygame.KEYDOWN and event.key in keys:
                return True
        return False

    def mouse_pressed(self, mouse_key=MOUSE_LEFT):
        """
        Check if a mousekey was pressed
        :param mouse_key: define the mouse key
        :return: True if pressed
        """
        for event in self.events:
            #print(event)
            if event.type == pygame.MOUSEBUTTONUP and event.button == mouse_key:
                return True
        return False

    def quit_pressed(self):
        """
        Check if application termination was requested
        :return True if quit was pressed/requested
        """
        for event in self.events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE \
                or event.type == pygame.QUIT:
                return True

def get_text_mid_position(resolution):
    return (resolution[0]/2,resolution[1]/2)

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