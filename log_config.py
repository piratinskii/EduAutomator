import logging
import os
import time
from logging.handlers import TimedRotatingFileHandler


class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    """
    Custom handler for logging. It creates new log file every midnight and keep 7 last log files
    (you can change this in backupCount parameter). Log file name format is "YYYY-MM-DD.log"
    """
    def __init__(self, dir_name, backupCount=0, encoding=None, delay=False, utc=False, atTime=None):
        # Set log file name to current date
        filename = os.path.join(dir_name, time.strftime("%Y-%m-%d") + ".log")
        # Initialize TimedRotatingFileHandler
        super().__init__(filename, when='midnight', backupCount=backupCount, encoding=encoding, delay=delay, utc=utc, atTime=atTime)

    def doRollover(self):
        # Get current log file name
        new_log_file = os.path.join(os.path.dirname(self.baseFilename), time.strftime("%Y-%m-%d") + ".log")
        # If new log file name is different from current log file name - change it
        if self.baseFilename != new_log_file:
            self.stream.close()
            self.baseFilename = new_log_file
            if self.delay:
                self.stream = None
            else:
                self.stream = self._open()


# Logging
logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d')
"""
Logging settings:
logger.setLevel - logging level (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL)
in handler = TimedRotatingFileHandler you can change also name of the log file (edu_automator.log) and backupCount (7)
- how many log files to keep. By default program create new log file every midnight and keep 7 last log files.
"""
logger.setLevel(logging.INFO)  # Here you can change the logging level

# Settings for logging to file
# Check if logs folder exists, if not - create it
if not os.path.exists('logs'):
    os.makedirs('logs')
handler = CustomTimedRotatingFileHandler("logs", backupCount=7)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Settings for logging to console
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
