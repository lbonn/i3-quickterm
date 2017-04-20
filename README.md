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
# always pop standard shell, without the menu
bindsym $mod+b exec i3_quickterm shell
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

`menu`, `term`, `history` and `shell` can contain placeholders for environment
variables: `{$var}`. `term` can also contain the `{title}` placeholder to set
the window title of the terminal.

Unspecified keys are inherited from the defaults:

```
{
    "menu": "rofi -dmenu -p 'quickterm: ' -no-custom -auto-select",
    "term": "urxvt -title '{title}'",
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
* i3 >= v3.11
* [i3ipc-python](https://i3ipc-python.readthedocs.io/en/latest/)
* dmenu or rofi (optional)
