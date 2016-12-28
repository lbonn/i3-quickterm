i3-quickterm
=============

A small drop-down terminal for [i3wm](https://i3wm.org/)

Features
--------

* use your favourite terminal emulator
* can select a shell with [dmenu](http://tools.suckless.org/dmenu/) /
  [rofi](https://github.com/DaveDavenport/rofi)
* adapt to screen width
* multi-monitor aware

Usage
-----

When launched, it will minimize the quickterm on the current screen if there is
one.  Otherwise, it will either prompt the user for the shell to open or use the
one supplied in argument.

If the requested shell is already opened on another screen, it will be moved on
the current screen.

It is recommended to map it to an i3 binding:

```
# with prompt
bindsym $mod+p exec i3_quickterm
# always pop bash, without the menu
bindsym $mod+b exec i3_quickterm bash
```

Configuration
-------------

The configuration is done directly in the source for the moment:

* `MENU`: the dmenu-compatible application used to select the shell
* `TERM`: the terminal emulator of choice
* `RATIO`: the percentage of the screen height to use
* `POS`: where to pop the terminal (`top` or `bottom`)
* `SHELLS`: registered shells

The defaults are:

```
MENU = ['rofi', '-dmenu', '-p', 'quickterm: ', '-no-custom', '-auto-select']
TERM = ['urxvt']
RATIO = 0.25
POS = 'top'
SHELLS = {
    'haskell': 'ghci',
    'js': 'node',
    'python': 'ipython3 --no-banner',
    'shell': os.environ.get('SHELL', 'bash'),
    }
```

Requirements
------------

* python 3
* i3 >= v3.11
* [i3ipc-python](https://i3ipc-python.readthedocs.io/en/latest/)
* dmenu or rofi (optional)
