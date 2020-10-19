import queue
import threading

new_unprocessed_trades = queue.Queue()
has_unprocessed_trade = threading.Semaphore(value=0)

new_trades = queue.Queue()
has_trade = threading.Semaphore(value=0)

new_discord_trades = queue.Queue()
has_new_discord_trade = threading.Semaphore(value=0)

EVENT = threading.Event()
DEBUG = False