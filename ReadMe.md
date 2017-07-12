# Dependencies

```sudo apt install python-piggyphoto python-pygame python-yaml pmount```

## gphoto2-cffi

if available use 

``` sudo apt install python-gphoto2cffi```

but e.g. on raspian you have to build it yourself with following commands.

sudo apt-get install python2.7-dev libgphoto2-dev libffi6 libffi-dev python-cffi

git clone https://github.com/jbaiter/gphoto2-cffi.git
cd gphoto2-cffi
python setup.py build
sudo python setup.py install
```

# Setup

Disable the GPhoto2 Volumen Monitor
```disable_gphoto2_gvfs.sh```

# Update localization

1. Extract strings
```
pygettext -d photobooth photobooth.py 

```

2. Open old localization files with poedit

locale/en/LC_MESSAGES/photobooth.po
locale/de/LC_MESSAGES/photobooth.po

3. Select from menu Catalog -> Update from POT and select file in photobooth root.
