import queue
import threading

new_trades = queue.Queue()
trades_to_fix = queue.Queue()
has_fixed_trade = threading.Semaphore(value=0)
has_trade = threading.Semaphore(value=0)
EVENT = threading.Event()