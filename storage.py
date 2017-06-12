#! /usr/bin/env python

import subprocess
import shlex


def mount_device(device_name, media_label='images'):
    command = "pmount {device_name} {media_label}".format(device_name=r'"%s"' % device_name,
                                                          media_label=r'"%s"' % media_label)
    execute_process(command=command)

    return '/media/' + media_label


def umount_device(device_name):
    command = "pumount {device_name}".format(device_name=r'"%s"' % device_name)

    execute_process(command=command)

def execute_process(command):
    """
    Execute the command
    :param command: full command string
    """
    cmd = shlex.split(command)

    p = subprocess.Popen(cmd, shell=False, stderr=subprocess.STDOUT)
    p.wait()


if __name__ == '__main__':

    dev = '/dev/sdi1'
    umount_device(dev)
    directory = mount_device(dev)
    #print(directory)