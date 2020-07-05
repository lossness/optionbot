import logging


def consumer(queue, event):
    """Pretend we're saving a number in the database."""
    while not event.is_set() or not queue.empty():
        message = queue.get()
        logging.info("Consumer storing message: %s (size=%d)", message,
                     queue.qsize())

    logging.info("Consumer received event. Exiting")