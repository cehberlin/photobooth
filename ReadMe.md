# CEH-Photo.de Photobooth

http://www.ceh-photo.de

This is a modular photobooth software written in Python using pygame, which is suppose to run on a Linux computer (I have used a Raspberry Pi 3) and controls a camera with GPhoto2 interface. I have tested and used it with two Nikon DSLRs (D5100, D7100). Adapating the software to other cameras like Canon cameras should not be a big problem due to the modular code structure. It was developed for my own wedding party and was a great fun and resulted in unforgetable photos.

# Features
- Display Live Preview (automatically enabling, disabling autofocus)
- Photo Countdown
- External Push Buttons, the concept it based on the availability of 4 colorful pushbuttons.
- Applying fancy filters (implemented using Imagemagick), selectable by the user
- Configurable and modular (e.g. you can disable printing, filtering ...)
- Automated printing (current version uses an additional Windows computer for priting interfaced through provided python printing service as my printer did not work well in Linux, Replacing this interface with something based on `lp` is a minor adjustment)
- Multi-Language suppport (currently German and English)
- Slideshow mode
- Support for different Gphoto2 interfaces (gphoto2-cffi, piggyphoto, commandline-based)
- Modes for testing and development that can be used without any camera or buttons

# Requirements and Hints
- Gphoto2 interface is localized in some parts and this has influence on the name of some configuration options etc. This software expects an English interface, hence you should set your Photobooth Linux to the localization English.
- I had big trouble with several memory leak issues in the gphoto2 library and both corresponding Python interfaces (gphoto2-cffi and piggyphoto), for this reason I developed a gphoto2 commandline-based interface using `popen` that does not suffer this problem due to its process-like interface

# Install

```git clone --recursive https://github.com/cehberlin/photobooth.git```

## Dependencies

```sudo apt install python-pygame python-yaml pmount```

### gphoto2-cffi

if available use 

``` sudo apt install python-gphoto2cffi```

but e.g. on raspian you have to build it yourself with following commands.

```
sudo apt-get install python2.7-dev libgphoto2-dev libffi6 libffi-dev python-cffi

git clone https://github.com/jbaiter/gphoto2-cffi.git
cd gphoto2-cffi
python setup.py build
sudo python setup.py install
```

## Setup

Disable the GPhoto2 Volumen Monitor
```disable_gphoto2_gvfs.sh```

### Update localization

1. Extract strings
```
pygettext -d photobooth photobooth.py 

```

2. Open old localization files with poedit

locale/en/LC_MESSAGES/photobooth.po
locale/de/LC_MESSAGES/photobooth.po

3. Select from menu Catalog -> Update from POT and select file in photobooth root.
