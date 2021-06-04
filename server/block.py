from ctypes import *

ok = windll.user32.BlockInput(True) #enable block
print('Disabled block', ok)
#or
import time
time.sleep(5)

ok = windll.user32.BlockInput(False) #disable block

