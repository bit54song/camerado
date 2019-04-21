# Camerado

This is a GUI for palying around with USB video camera settings using V4L drivers on GNU/Linux.

## Install

You need to have `python3` and `v4l-utils` installed on your system. Assuming you are working on a DEB-based OS like Ubuntu:
```bash
$ sudo apt-get install python3 python3-pip v4l-utils
```
Also, you have to install required python packages listed in `requirements.txt` file. You can use `pip` to install them:
```bash
$ pip3 install --user -r requirements.txt
```

## Usage

This is how the main window looks like:

![](../assets/main.png?raw=true)

On the right panel, there are three groups of controls. The *Device* group contains controls used to open and close a video stream, and to change its resolution. The *Device Settings* are used to save and load video stream settings and to adjust parameters of the current video device:

![](../assets/settings_1.png?raw=true)

The settings controls are discovered using `v4l2-ctl` utility for the current video device dynamically. Some of the controls are dependent on the other ones and may not be rendered as they are not available in the current state. For example, when user turns off the auto mode for exposure and white balance, the corresponded controls will show up after the *Update Controls* button has been pressed:

![](../assets/settings_2.png?raw=true)

The device settings are stored in json format:
```json
{
  "path": "/dev/video1",
  "resolution": [
    1024,
    576
  ],
  "settings": [
    {
      "name": "exposure_absolute",
      "type": "int",
      "min": 3,
      "max": 2047,
      "step": 1,
      "default": 166,
      "value": 664,
      "flags": "inactive"
    },
    {
      "name": "exposure_auto",
      "type": "menu",
      "min": 0,
      "max": 3,
      "default": 3,
      "value": 3,
      "menu": {
        "1": "Manual Mode",
        "3": "Aperture Priority Mode"
      }
    },
    {
      "name": "exposure_auto_priority",
      "type": "bool",
      "default": 0,
      "value": 1
    },
    {
      "name": "focus_absolute",
      "type": "int",
      "min": 0,
      "max": 255,
      "step": 5,
      "default": 60,
      "value": 80,
      "flags": "inactive"
    },
    {
      "name": "focus_auto",
      "type": "bool",
      "default": 1,
      "value": 1
    },
    {
      "name": "pan_absolute",
      "type": "int",
      "min": -36000,
      "max": 36000,
      "step": 3600,
      "default": 0,
      "value": 0
    },
    {
      "name": "tilt_absolute",
      "type": "int",
      "min": -36000,
      "max": 36000,
      "step": 3600,
      "default": 0,
      "value": 0
    },
    {
      "name": "zoom_absolute",
      "type": "int",
      "min": 1,
      "max": 5,
      "step": 1,
      "default": 1,
      "value": 1
    }
  ],
  "roi": [
    [
      0.2688296639629201,
      0.3039039039039039,
      0.7624565469293163,
      0.8114114114114114
    ]
  ]
}
```
You can also add ROIs using controls of the *ROI* group on the main window. The ROI rectangles are stored as lists of relative coordinates of their upper left and bottom right corners *[xmin, ymin, xmax, ymax]*.

