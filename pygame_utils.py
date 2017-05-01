import pygame

DEFAULT_FONT_SIZE = 72

COLOR_GREEN = (34,139,34)
COLOR_RED = (200,0,0)
COLOR_WHITE = (255, 255, 255)
COLOR_GREY = (220,220,220)
COLOR_YELLOW = (255,255,0)
COLOR_BLUE =(0,0,255)
COLOR_ORANGE = (210,105,30)

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


def draw_rect(screen, pos, size, color=COLOR_GREY):
    pygame.draw.rect(screen, color, (pos[0],pos[1],size[0],size[1]))

def show_text_mid(screen, text, mid_pos, size=DEFAULT_FONT_SIZE, color=COLOR_WHITE):
    """
    Show text using mid position for entire text
    :param screen:
    :param text:
    :param mid_pos:
    :param size:
    :return:
    """
    txt_img = get_text_img(text, size, color)
    screen.blit(txt_img,
                (mid_pos[0] - txt_img.get_width() // 2, mid_pos[1] - txt_img.get_height() // 2))

def show_text_left(screen, text, pos, size=DEFAULT_FONT_SIZE,  color=COLOR_WHITE):
    """
    Show text with left pos reference position
    :param screen:
    :param text:
    :param pos:
    :param size:
    :return:
    """
    txt_img = get_text_img(text, size, color)
    screen.blit(txt_img,pos)