import piggyphoto.piggyphoto as piggyphoto
import pygame
import time
import imp
from fcntl import fcntl, F_GETFL, F_SETFL
from os import O_NONBLOCK, read

import subprocess
import shlex

from utils import GenericClassFactory
from shutil import copy
from datetime import datetime

from abc import ABCMeta, abstractmethod
from subprocess import Popen, PIPE


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
        :return: (photo pygame.image,PATH_TO_PHOTO)
        """
        raise NotImplementedError

    @abstractmethod
    def enable_live_autofocus(self):
        """
        enable camera autofocus in preview mode
        """
        raise NotImplementedError

    @abstractmethod
    def disable_live_autofocus(self):
        """
        disable camera autofocus in preview mode
        """
        raise NotImplementedError

    def close(self):
        """
        optional closing method
        """
        pass


# Create singleton factory object
camera_factory = GenericClassFactory(AbstractCamera)


def get_camera_factory():
    """
    Provide external access to the factory instance
    :return: factory instance
    """
    return camera_factory


class PiggyphotoCamera(AbstractCamera):
    """
    Class wrapping camera access through piggyphoto gphoto2 library for Nikon DSLR, you probably have to adjust it
    for other camera brands
    """

    def __init__(self,  photo_directory, tmp_directory, **kwargs):
        """
        :param photobooth: app instance
        :param kwargs:
        """
        self.cam = None
        self.cam = piggyphoto.Camera(auto_init=True)
        self._photo_directory = photo_directory
        self._tmp_directory = tmp_directory

    def set_memory_capture(self):
        # set capturetarget to memory card
        config_value = self.cam.config.get_child_by_name("capturetarget")
        config_value.value = 'Memory card'

    def set_idle(self):
        self.disable_liveview()

    def disable_liveview(self):
        config_value = self.cam.config.get_child_by_name("viewfinder")
        config_value.value = 0

    def get_preview(self):
        file = self._tmp_directory +'/preview.jpg'
        cfile = self.cam.capture_preview(destpath=file)
        cfile.clean()
        picture = pygame.image.load(file)
        return picture

    def enable_live_autofocus(self):
        config_value = self.cam.config.get_child_by_name("liveviewaffocus")
        config_value.value = 'Full-time-servo AF'

    def disable_live_autofocus(self):
        config_value = self.cam.config.get_child_by_name("liveviewaffocus")
        config_value.value = 'Single-servo AF'

    def take_photo(self):
        """
        Trigger photo capture
        TODO it seems like capture_image of the library has a memory leak
        :return:  tuple of pygame image and path to file
        """
        #disable liveview to use better internal autofocus of camera
        self.disable_liveview()
        file = self._photo_directory + "/dsc_" + str(datetime.now()).replace(':','-') + ".jpg"
        self.cam.capture_image(destpath=file)
        return pygame.image.load(file), file

    def close(self):
        if self.cam:
            self.set_idle()
            self.cam.close()
            self.cam = None

    def __del__(self):
        self.close()

camera_factory.register_algorithm("piggyphoto", PiggyphotoCamera)

#following implementation is optional and only acivated if requirements are fulfilled
try:
    imp.find_module('gphoto2cffi')
    found_gphoto2_cffi_module = True
except ImportError:
    found_gphoto2_cffi_module = False
    print("Couldn't find gphoto2cffi module, proceeding without")

if found_gphoto2_cffi_module:
    import gphoto2cffi as gp

    class GPhoto2CffiCamera(AbstractCamera):
        """
        Class wrapping camera access through gphoto2cffi library for Nikon DSLR, you probably have to adjust it
        for other camera brands
        """

        def __init__(self,  photo_directory, tmp_directory, **kwargs):
            """
            :param photobooth: app instance
            :param kwargs:
            """
            self.cam = gp.Camera()
            self._photo_directory = photo_directory
            self._tmp_directory = tmp_directory

        def _save_picture(self, filename, data):
            f = open(filename, 'wb')
            f.write(data)
            f.close()

        def set_memory_capture(self):
            # set capturetarget to memory card
            self.cam.config['settings']['capturetarget'].set('Memory card')

        def set_idle(self):
            self.disable_liveview()

        def disable_liveview(self):
            try:
                self.cam.config['actions']['viewfinder'].set(False)
            except:
                print("disable liveview failed")

        def get_preview(self):
            file = self._tmp_directory +'/preview.jpg'
            preview = self.cam.get_preview()
            self._save_picture(filename=file, data=preview)
            picture = pygame.image.load(file)
            return picture

        def enable_live_autofocus(self):            
            try:
                self.cam.config['capturesettings']['liveviewaffocus'].set('Full-time-servo AF')
            except:
                print('could not change liveview AF settings, please enable AF on lens')

        def disable_live_autofocus(self):
            try:
                self.cam.config['capturesettings']['liveviewaffocus'].set('Single-servo AF')
            except:
                print('could not change liveview AF settings, please enable AF on lens')

        def take_photo(self):
            """
            Trigger photo capture
            :return:  tuple of pygame image and path to file
            """
            #disable liveview to use better internal autofocus of camera
            self.disable_liveview()
            file = self._photo_directory + "/dsc_" + str(datetime.now()).replace(':','-') + ".jpg"
            photo = self.cam.capture()
            self._save_picture(filename=file, data=photo)
            return pygame.image.load(file), file

        def close(self):
            pass

        def __del__(self):
            self.close()

    camera_factory.register_algorithm("gphoto2cffi", GPhoto2CffiCamera)

class DummyCamera(AbstractCamera):
    """
    Dummy camera class that just provides some example images for testing
    """

    def __init__(self, photo_directory, tmp_directory, **kwargs):
        # Load some dummy images
        self._photo_directory = photo_directory
        self._preview_cnt = 0
        if tmp_directory:
            self._tmp_directory = tmp_directory + '/'
        else:
            self._tmp_directory = ""

        self._previews = [pygame.image.load(self._tmp_directory + "dummy_preview00.jpg"), pygame.image.load(self._tmp_directory + "dummy_preview01.jpg")]
        self._photo = pygame.image.load(self._tmp_directory + "dummy_snap.jpg")

    def set_memory_capture(self):
        pass

    def set_idle(self):
        pass

    def enable_live_autofocus(self):
        pass

    def disable_live_autofocus(self):
        pass

    def get_preview(self):
        self._preview_cnt = (self._preview_cnt + 1) % len(self._previews)
        return self._previews[self._preview_cnt]

    def take_photo(self):
        photo_file = self._photo_directory + "/dummy_snap_" +str(datetime.now()).replace(':','-')+ ".jpg"
        copy(self._tmp_directory + "dummy_snap.jpg", photo_file)
        return self._photo, photo_file

    def __del__(self):
        pass

camera_factory.register_algorithm("dummy", DummyCamera)

class GPhotoCMDCamera(AbstractCamera):
    """
    Class wrapping camera access through piggyphoto gphoto2 library for Nikon DSLR, you probably have to adjust it
    for other camera brands
    """

    def __init__(self,  photo_directory, tmp_directory, **kwargs):
        """
        :param photobooth: app instance
        :param kwargs:
        """
        self._photo_directory = photo_directory
        self._tmp_directory = tmp_directory
        self._shell_p = None

    def set_memory_capture(self):
        # set capturetarget to memory card
        # self._set_config('/main/settings/capturetarget', 'Memory card')
        self._set_config_by_index('/main/settings/capturetarget', 1)

    def set_idle(self):
        self._disable_shell()

    def disable_liveview(self):
        self._set_config('/main/actions/viewfinder', 0)

    def enable_liveview(self):
        self._set_config('/main/actions/viewfinder', 1)

    def get_preview(self):
        """
        get a camera preview
        :return: pygame image
        """
        preview_picture = None
        try:
            if not self._shell_p:
                self._enable_shell()

            command = "capture-preview "
            self._input_shell(command)
            file = 'capture_preview.jpg'
            preview_picture = pygame.image.load(file)
            if not preview_picture:
                self._disable_shell()
        except Exception as e :
            print(e)
            pass

        return preview_picture

    def enable_live_autofocus(self):
        try:
            # self._set_config('/main/capturesettings/liveviewaffocus', 'Full-time-servo AF')
            self._set_config_by_index('/main/capturesettings/liveviewaffocus', 1)
        except:
            print('could not change liveview AF settings, please enable AF on lens')

    def disable_live_autofocus(self):
        try:
            # self._set_config('/main/capturesettings/liveviewaffocus', 'Single-servo AF')
            self._set_config_by_index('/main/capturesettings/liveviewaffocus', 0)
        except:
            print('could not change liveview AF settings, please enable AF on lens')

    def take_photo(self):
        """
        Trigger photo capture
        :return:  tuple of pygame image and path to file
        """
        # disable liveview to use better internal autofocus of camera by disabling shell mode
        self._disable_shell()

        file = self._photo_directory + "/dsc_" + str(datetime.now()).replace(':','-') + ".jpg"
        command = "gphoto2  --capture-image-and-download --filename {filename}".format(filename=r'"%s"' % file)
        self._execute_process(command)

        return pygame.image.load(file), file

    def _set_config_by_index(self, key, value):
        """
        set a gphoto2 config value using the option index in order to avoid language problems
        function automatically handles non-shell and shell mode
        :param key: config key
        :param value: config value
        """
        value = int(value)

        if not self._shell_p:
            command = "gphoto2 --set-config-index {key}={value}".format(key=key, value=value)
            self._execute_process(command)
        else:

            command = "set-config-index {key}={value}".format(key=key, value=value)
            self._input_shell(command)

    def _set_config(self, key, value):
        """
        set a gphoto2 config value
        function automatically handles non-shell and shell mode
        :param key: config key
        :param value: config value
        """

        if not self._shell_p:
            if isinstance(value, basestring):
                command = "gphoto2  --set-config {key}={value}".format(key=key, value=r'"%s"' % value)
            else:
                command = "gphoto2  --set-config {key}={value}".format(key=key, value=value)
            self._execute_process(command)
        else:
            if isinstance(value, basestring):
                command = "set-config {key}={value}".format(key=key, value=value)
            else:
                command = "set-config {key}={value}".format(key=key, value=value)

            self._input_shell(command)

    def _execute_process(self, command):
        """
        Execute a process command
        :param command: full command string
        """
        cmd = shlex.split(command)

        p = subprocess.Popen(cmd, shell=False, stderr=subprocess.STDOUT)
        p.wait()

    def _enable_shell(self):
        """
        enable gphoto2 interactive shell mode
        """
        command = 'gphoto2 --shell --force-overwrite'

        cmd = shlex.split(command)

        if self._shell_p:
            self._disable_shell()

        self._shell_p = subprocess.Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        # set the O_NONBLOCK flag of p.stdout file descriptor:
        flags = fcntl(self._shell_p.stderr, F_GETFL)  # get current p.stdout flags
        fcntl(self._shell_p.stderr, F_SETFL, flags | O_NONBLOCK)
        time.sleep(0.5)
        if self._shell_p.poll():
            raise Exception("Gphoto2 shell failed ")


    def _disable_shell(self):
        """
        disable gphoto2 interactive shell mode
        check if it was started at all
        """
        if self._shell_p:
            try:
                self._shell_p.stdin.write('exit\n')
                self._shell_p.wait()
                self._shell_p = None
            except Exception as e:
                print("Failed closing shell mode: "+ str(e))

    def _input_shell(self, cmd):
        """
        send a command to a running interactive gphoto shell
        :param cmd: the gphoto2 command
        """
        if self._shell_p and self._shell_p.poll() is None:
            self._shell_p.stdin.write(cmd + '\n')
            self._shell_p.stdin.flush()
            while True:
                try:
                    res = self._shell_p.stderr.readline()
                except Exception as e:
                    if e.errno == 11: # corresponds to "Resource temporarily unavailable" and indicates we do not have more data
                        break
                    else:
                        raise e
                if 'Error' in res: # this is unfortunately language specific
                    self._disable_shell()
                    raise Exception("Shell cmd failed: " + res)
        else:
            self._shell_p = None
            raise Exception("Gphoto2 shell mode not running")

    def close(self):
        if self._shell_p:
            self.set_idle()

    def __del__(self):
        self.close()

camera_factory.register_algorithm("gphotocmd", GPhotoCMDCamera)

if __name__ == '__main__':

    cam = GPhotoCMDCamera('images', 'tmp')
    #cam = PiggyphotoCamera('images', 'tmp')
    preview = cam.get_preview()
    cam.enable_live_autofocus()

    cnt = 0
    while True:
        #photo = cam.take_photo()
        preview = cam.get_preview()
        cnt +=1
        #print(cnt)
