import logging
from threading import Thread

logger = logging.getLogger(__name__)

class ThreadBase(Thread):

    def __init__(self, func=None):
        super().__init__()
        self.alive = True
        self.func = func

    def stop(self):
        self.alive = False

    def run(self) -> None:
        try:
            self.func()
        finally:
            self.cleanup()

    def cleanup(self):
        # Add any necessary cleanup code here
        logger.info("Performing cleanup operations...")

        # Register any additional cleanup functions here
        self.register_cleanup()

    def register_cleanup(self):
        # Register any necessary cleanup functions using appropriate mechanisms
        logger.info("Registering cleanup functions...")
        # Example: atexit.register(self.cleanup_function)
        # Replace self.cleanup_function with your actual cleanup function

    def cleanup_function(self):
        # Implement your cleanup function logic here
        logger.info("Executing cleanup function...")
        # Replace with your actual cleanup code