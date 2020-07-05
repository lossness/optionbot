import time
from pynput.keyboard import Key, Controller

KEYBOARD = Controller()


def switch_to_mobile(driver):
    time.sleep(1)
    KEYBOARD.press(Key.ctrl)
    KEYBOARD.press(Key.shift)
    KEYBOARD.press('j')
    KEYBOARD.release(Key.ctrl)
    KEYBOARD.release(Key.shift)
    KEYBOARD.release('j')
    time.sleep(1)
    KEYBOARD.press(Key.ctrl)
    KEYBOARD.press(Key.shift)
    KEYBOARD.press('m')
    KEYBOARD.release(Key.ctrl)
    KEYBOARD.release(Key.shift)
    KEYBOARD.release('m')
    driver.refresh()
    driver.get('https://www.instagram.com/marginkings/')
    time.sleep(1)
    KEYBOARD.press(Key.ctrl)
    KEYBOARD.press(Key.shift)
    KEYBOARD.press('j')
    KEYBOARD.release(Key.ctrl)
    KEYBOARD.release(Key.shift)
    KEYBOARD.release('j')