
import logging
logger = logging.getLogger(__name__)

from concurrent.futures import ThreadPoolExecutor

test_executor = ThreadPoolExecutor(
    max_workers=4, 
    thread_name_prefix="test_executor",
    initializer=lambda: logger.info("test worker initialized")
)