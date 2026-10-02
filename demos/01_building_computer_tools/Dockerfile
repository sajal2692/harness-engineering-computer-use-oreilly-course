# The agent's computer: a Debian Linux desktop with no monitor, running in Docker on your machine.
FROM debian:bookworm

# 1. A virtual display (Xvfb), the Xfce desktop and everyday applications, and the programs the tools call:
#    ImageMagick's import for screenshots, xdotool for mouse and keyboard input, wmctrl for windows.
#    x11vnc and noVNC let you watch the desktop in a browser. They are for people, not for the model.
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        xvfb xfce4 xfce4-terminal thunar mousepad ristretto atril firefox-esr \
        dbus-x11 adwaita-icon-theme elementary-xfce-icon-theme fonts-dejavu-core \
        imagemagick xdotool wmctrl \
        x11vnc novnc websockify \
    && rm -rf /var/lib/apt/lists/*

# 2. An ordinary user account, with the task's files in its home folder and Xfce's settings:
#    the default panels, and applications drawn at twice the size, like a high-resolution laptop screen
RUN useradd --create-home --shell /bin/bash agent
COPY --chown=agent:agent receipts/ /home/agent/receipts/
COPY --chown=agent:agent xfce/ /home/agent/.config/xfce4/xfconf/xfce-perchannel-xml/
RUN cp /etc/xdg/xfce4/panel/default.xml /home/agent/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml \
    && mkdir /home/agent/notes /home/agent/Desktop && chown -R agent:agent /home/agent
COPY --chmod=755 start.sh /usr/local/bin/start.sh
# The dock's web browser icon has a mouse pointer drawn on it, which looks like a second pointer; use Firefox's
RUN sed -i 's/^Icon=.*/Icon=firefox-esr/' /usr/share/applications/xfce4-web-browser.desktop

# 3. A 2560 x 1440 display, with a large mouse pointer so it shows in the viewer
ENV DISPLAY=:1 NO_AT_BRIDGE=1 XCURSOR_THEME=Adwaita XCURSOR_SIZE=96
USER agent
WORKDIR /home/agent
EXPOSE 6080
CMD ["start.sh"]
