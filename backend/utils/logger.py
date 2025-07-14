import logging
import os

class AppLogger:
    """
    A custom logger class for the application.
    It can be imported into different files and logs messages
    along with the filename where the log call was made.
    """

    def __init__(self, name: str = "my_app", level: int = logging.INFO):
        """
        Initializes the logger.
        Args:
            name (str): The name of the logger (e.g., 'my_app', or __name__ for module-specific).
            level (int): The minimum logging level (e.g., logging.INFO, logging.DEBUG).
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False

        # Create a console handler to output logs to stderr
        console_handler = logging.StreamHandler()

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        console_handler.setFormatter(formatter)

        # Add the console handler to the logger
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)

        self._initialized = True # Mark as initialized

    def get_logger(self) -> logging.Logger:
        """
        Returns the configured logging.Logger instance.
        """
        return self.logger
