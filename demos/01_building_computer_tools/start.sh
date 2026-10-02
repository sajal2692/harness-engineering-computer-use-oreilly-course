#!/bin/bash
# Starts the desktop: the display, the Xfce session, and the viewer. No application is open.
Xvfb :1 -screen 0 2560x1440x24 -nolisten tcp &
until xdotool getdisplaygeometry >/dev/null 2>&1; do sleep 0.1; done
dbus-launch startxfce4 >/dev/null 2>&1 &
xsetroot -cursor_name left_ptr
# -nocursorshape draws the pointer into the picture, so every viewer shows where it is
x11vnc -display :1 -forever -shared -nopw -quiet -rfbport 5900 -cursor most -nocursorshape >/dev/null 2>&1 &
websockify --web /usr/share/novnc 6080 localhost:5900 >/dev/null 2>&1 &
wait
