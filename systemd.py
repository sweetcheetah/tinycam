"""
SystemD notifications to allow python apps to have watchdog functionality when
running under systemd.

Usage:
```
import sd_notify

notify = sd_notify.Notifier()
if not notify.enabled():
    # Then it's probably not running is systemd with watchdog enabled
        raise Exception("Watchdog not enabled")

    # Report a status message
    notify.status("Initialising my service...")
    time.sleep(3)

    # Report that the program init is complete
    notify.ready()
    notify.status("Waiting for web requests...")
    time.sleep(3)

    # Report an error to the service manager
    notify.notify_error("An irrecoverable error occured!")
    # The service manager will probably kill the program here
    time.sleep(3)
```
"""
# from https://github.com/stigok/sd-notify/blob/master/sd_notify.py with some changes

import os
import socket

class Notify():
    """Simple class to handle systemd watchdog notifications"""
    def __init__(self):
        self.socket = socket.socket(
            family=socket.AF_UNIX,
            type=socket.SOCK_DGRAM
        )
        self.address = os.getenv("NOTIFY_SOCKET")

    def _send(self, msg):
        """Send string `msg` as bytes on the notification socket"""
        self.socket.sendto(msg.encode(), self.address)

    def enabled(self):
        """Return a boolean stating whether watchdog is enabled"""
        return bool(self.address)

    def ready(self):
        """Report ready service state, i.e. completed initialisation"""
        self._send("READY=1\n")

    def status(self, msg):
        """Set a service status message"""
        self._send(f"STATUS={msg}\n")

    def notify(self):
        """Report a healthy service state"""
        self._send("WATCHDOG=1\n")

    def notify_error(self, msg=None):
        """
        Report a watchdog error. This program will likely be killed by the
        service manager.

        If `msg` is not None, it will be reported as an error message to the
        service manager.
        """
        if msg:
            self.status(msg)

        self._send("WATCHDOG=trigger\n")
