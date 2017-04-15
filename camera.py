import piggyphoto
import pygame

from utils import GenericClassFactory
from shutil import copyfile
from datetime import datetime

from abc import ABCMeta, abstractmethod


class AbstractCamera(object):
    """
    Abstract interface for camera implementations
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def set_memory_capture(self):
        """
        Configure memory capture mode (photos are as well stored on camera memory)
        """
        raise NotImplementedError

    @abstractmethod
    def set_idle(self):
        """
        Set camera to idle mode
        """
        raise NotImplementedError

    @abstractmethod
    def get_preview(self):
        """
        Get a preview image
        :return: preview  pygame.image
        """
        raise NotImplementedError

    @abstractmethod
    def take_photo(self):
        """
        Trigger a photo on the camera
        :return: photo pygame.image
        """
        raise NotImplementedError

# Create singleton factory object
camera_factory = GenericClassFactory(AbstractCamera)


def get_camera_factory():
    """
    Provide external access to the factory instance
    :return: factory instance
    """
    return camera_factory;


class PiggyphotoCamera(AbstractCamera):
    """
    Class wrapping camera access through piggyphoto gphoto2 library
    """

    def __init__(self,  photo_directory, **kwargs):
        """
        :param photobooth: app instance
        :param kwargs:
        """
        self.cam = None
        self.cam = piggyphoto.camera()
        self._photo_directory = photo_directory
        #self.cam.leave_locked() # not sure what would be the effect

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

    def take_photo(self):
        photo_name = self._photo_directory + "/dsc_" + str(datetime.now()) + ".jpg"
        self.cam.capture_image(photo_name)
        return pygame.image.load(photo_name)

    def __del__(self):
        if self.cam:
            self.cam.exit()

camera_factory.register_algorithm("piggyphoto", PiggyphotoCamera)


class DummyCamera(AbstractCamera):
    """
    Dummy camera class that just provides some example images for testing
    """

    def __init__(self, photo_directory, **kwargs):
        # Load some dummy images
        self._photo_directory = photo_directory
        self._previews = [pygame.image.load("dummy_preview00.jpg"), pygame.image.load("dummy_preview01.jpg")]
        self._preview_cnt = 0
        self._photo = pygame.image.load("dummy_snap.jpg")

    def set_memory_capture(self):
        pass

    def set_idle(self):
        pass

    def get_preview(self):
        self._preview_cnt = (self._preview_cnt + 1) % len(self._previews)
        return self._previews[self._preview_cnt]

    def take_photo(self):
        copyfile("dummy_snap.jpg", self._photo_directory + "/dummy_snap_" +str(datetime.now())+ ".jpg")
        return self._photo

    def __del__(self):
        pass

camera_factory.register_algorithm("dummy", DummyCamera)