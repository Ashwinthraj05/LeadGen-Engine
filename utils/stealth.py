import time
import random
from config import REQUEST_DELAY_MIN, REQUEST_DELAY_MAX


def human_delay():
    time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))
