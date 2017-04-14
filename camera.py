import piggyphoto

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