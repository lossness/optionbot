import queue
import threading

new_trades = queue.Queue()
has_trade = threading.Semaphore(value=0)
last_message = None
