i3-quickterm
=============

[![Packaging status](https://repology.org/badge/vertical-allrepos/python:i3-quickterm.svg)](https://repology.org/project/python:i3-quickterm/versions)

A small drop-down terminal for [i3wm](https://i3wm.org/) and [sway](https://swaywm.org/)

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
bindsym $mod+p exec i3-quickterm
# always pop standard shell, without the menu
bindsym $mod+b exec i3-quickterm shell
```

Configuration
-------------

The configuration is read from `~/.config/i3/i3-quickterm.json`.

* `menu`: the dmenu-compatible application used to select the shell
* `term`: the terminal emulator of choice
* `history`: a file to save the last-used shells order, last-used ordering
  is disabled if set to null
* `ratio`: the percentage of the screen height to use
* `pos`: where to pop the terminal (`top` or `bottom`)
* `shells`: registered shells (`{ name: command }`)

`term` can be either:
- a format string, like this one: `urxvt -t {title} -e {expanded}` with
  the correct arguments format of your terminal. Some terminals, like
  xfce4-terminal need the command argument to be passed as a string. In
  this case, replace `{expanded}` by `{string}`
- a terminal name from the hardcoded list, which should work out of the box.
  Right now, the only reference for the list is the source code
  (search for `TERMS =`).
  If you'd like to add another terminal (or correct an error), please open
  a pull request.

`menu`, `term`, `history` and `shell` can contain placeholders for environment
variables: `{$var}`.

Unspecified keys are inherited from the defaults:

```
{
    "menu": "rofi -dmenu -p 'quickterm: ' -no-custom -auto-select",
    "term": "urxvt",
    "history": "{$HOME}/.cache/i3/i3-quickterm.order",
    "ratio": 0.25,
    "pos": "top",
    "shells": {
        "haskell": "ghci",
        "js": "node",
        "python": "ipython3 --no-banner",
        "shell": "{$SHELL}"
    }
}
```

Requirements
------------

* python >= 3.4
* i3 >= v3.11 or sway >= 1.2
* [i3ipc-python](https://i3ipc-python.readthedocs.io/en/latest/) >= v2.0.1
* dmenu or rofi (optional)
