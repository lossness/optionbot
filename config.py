import queue
import threading

new_unprocessed_trades = queue.Queue()
has_unprocessed_trade = threading.Semaphore(value=0)

new_trades = queue.Queue()
has_trade = threading.Semaphore(value=0)

new_delayed_trades = queue.Queue()
has_delayed_trade = threading.Semaphore(value=0)
cooking_trades = []

new_discord_trades = queue.Queue()
has_new_discord_trade = threading.Semaphore(value=0)

EVENT = threading.Event()
# DEBUG PARAMETERS
# bbs - setup to capture embed messages in discord channel and not post to insta / threaded queue
# bbs_post - same as bbs but goes through all queues and posts to insta
# dev - setup to capture regular messages in channel and not post to insta / threaded queue
# dev_post = same as dev but goes through all queues and posts to insta
# test - setup to loop thru list of messages and see if all return valid / doesn't touch database or threaded queue
DEBUG = False