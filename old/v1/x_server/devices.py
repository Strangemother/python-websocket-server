import asyncio

class Device(object):
    """A mouse receiver, mounting and tracking input events for a mouse inpuyr
    device to actuate on-server changes.

    The stream mounting utility allows thinner message streams from the
    client using simple strings rather than full packages.
    """

    message_key = 'd' # K for keyboard etc.

    def __init__(self):
        print('Device Awake', self.__class__.__name__, self.message_key)

    # async def read_packet(self, packet):
    #     print(f'Read: {self.__class__.__name__}')


    async def read_packet(self, packet):
        """Accept an incoming packet and farm to the attached tasks.
        The _owners_ of the task are first, given the packet['as'].
        Then any run_{as}_hook for each unit.

        """
        if await self.is_mine(packet):
            # info = packet.get_json()
            await self.run_task(packet)

        info = packet.get_json()
        _as = info['as']
        # run other ui capture types
        n = f'run_{_as}_hook'
        if hasattr(self, n):
            await getattr(self, n)(packet)

    async def is_mine(self, packet):
        info = packet.get_json()
        names = (self.message_key, self.__class__.__name__.lower(),)
        return info['as'] in names

    async def run_task(self, packet):
        """Run the task as an event expected for this type.

        """
        info = packet.get_json()
        event = info['event']
        name = f'run_{event}_task'

        print('Run device task')
        if hasattr(self, name):
            await getattr(self, name)(packet)


import ctypes


class Mouse(Device):
    """
     import pyautogui
    >>> import pydirectinput
    >>> pydirectinput.moveTo(100, 150) # Move the mouse to the x, y coordinates 100, 150.
    >>> pydirectinput.click() # Click the mouse at its current location.
    >>> pydirectinput.click(200, 220) # Click the mouse at the x, y coordinates 200, 220.
    >>> pydirectinput.move(None, 10)  # Move mouse 10 pixels down, that is, move the mouse relative to its current position.
    >>> pydirectinput.doubleClick() # Double click the mouse at the
    >>> pydirectinput.press('esc') # Simulate pressing the Escape key.
    >>> pydirectinput.keyDown('shift')
    >>> pydirectinput.keyUp('shift')"""

    message_key = 'm'
    off = False

    async def run_touch_hook(self, packet):
        touch = packet['touches'][0]

        if packet['event'] == 'tap':
            print('\n==tap--\n')
            await self.run_down_task(packet, button=0)
            # await asyncio.sleep(.1)
            return await self.run_up_task(packet, button=0)

        return await self.run_move_task(packet)

    async def run_down_task(self, packet, **extra):
        info = packet.get_json()
        info.update(extra)

        names = ['left', 'middle', 'right', 'x', 'x2']
        name = names[info['button']]
        print('Mouse down', info)
        await self._direct_mouse_down(name)

    async def _ctype_mouse_down(self):
        # see http://msdn.microsoft.com/en-us/library/ms646260(VS.85).aspx for details
        # ctypes.windll.user32.SetCursorPos(100, 20)
        ctypes.windll.user32.mouse_event(2, 0, 0, 0,0) # left down
        ctypes.windll.user32.mouse_event(4, 0, 0, 0,0) # left up

    async def _direct_mouse_down(self, name):
        d_inp.mouseDown(button=name)

    async def run_up_task(self, packet, **extra):
        info = packet.get_json()
        info.update(extra)
        names = ['left', 'middle', 'right', 'x', 'x2']
        name = names[info['button']]
        print('Mouse up', info)
        d_inp.mouseUp(button=name)


    async def run_wheel_task(self, packet, **extra):
        info = packet.get_json()
        dy = info.get('deltaY')
        print('wheel', dy)
        mouse.wheel(dy/100.0)

    async def run_move_task(self, packet, **extra):
        info = packet.get_json()
        info.update(extra)
        # print('move', info)
        x, y = info.get('x', None), info.get('y', None)
        # asyncio.sleep(.0001)
        print('MOVE', x,y)
        if self.off:
            return

        if x is None or y is None:
            return


        mouse.move(x,y, absolute=not info.get('rel', True))

        return
        move_method = d_inp.moveRel if info.get('rel', True) else d_inp.moveTo
        move_method(x,y, _pause=False)

        return

        win32api.mouse_event(
            win32con.MOUSEEVENTF_MOVE, # | win32con.MOUSEEVENTF_ABSOLUTE,
            int(x),
            int(y), )


class Keyboard(Device):

    message_key = 'k'
