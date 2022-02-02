# Server

The Windows host to accept incoming connection and run commands given by
the websocket clients.

A software 'device' captures the incoming messages and acts upon them as expected.
Each Device mounts a purpose, e.g. Mouse, Keyboard, Gamepad etc..
Messages in dictate the message digest however the _actuation_ of a utility occurs
through software choice, allowing the use of non-mouse devices to mount _mouse_
actions, for example a gamepad, or _another devices_ pen.


# Interface

A UI interface baked into the app, but also as a web-viewable, callable for user
preference. This is a special mouse track pad within a HTML webview.

1. A standard relative trcking mouse pad
2. Mouse clicks.
3. Other mouse buttons, scrolls.

Notably the actions occur through "touch" events and should translate to the
correct mounting such as 'click' or 'mouse move'.

# Views

A standard trackpad view with buttons and a scoll bar.

The 'nipple' view for button style mouse motion - with a fancy animation for the
'button' down action.


## Center Scroll

The mouse center wheel is a special scroller, which a middle-click.

1. swipe (hold and wheel direction)
2. delta buttons
3. middle-click
4. double-tap and hold on the second tap-down to wheel click hold and scroll.
5. flyweight mechanism - for gravity throws.
