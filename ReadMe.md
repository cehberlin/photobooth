# Dependencies

```sudo apt install python-piggyphoto python-pygame```

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
