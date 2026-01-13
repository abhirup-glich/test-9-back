import logging
import sys
import traceback
import os
from datetime import datetime

class ErrorManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ErrorManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.setup_logging()

    def setup_logging(self):
        """Configure the logging system to match requirements."""
        # Create a custom logger
        self.logger = logging.getLogger("GlobalErrorHandler")
        self.logger.setLevel(logging.ERROR)
        
        # Clear existing handlers to avoid duplicates
        if self.logger.handlers:
            self.logger.handlers.clear()
            
        # Console handler
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(logging.ERROR)
        
        # We will handle formatting manually in log_error to ensure exact compliance with:
        # "[ERROR] [ ${timestamp} ] ${filename} : ${line_number} - ${detailed_error_message} "
        # But for standard logging calls, we can set a formatter too.
        formatter = logging.Formatter('[ERROR] [ %(asctime)s ] %(pathname)s : %(lineno)d - %(message)s', datefmt='%Y-%m-%dT%H:%M:%S.%fZ')
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)

    def configure(self, app_config):
        # No longer needed for counters, but kept for interface compatibility if needed
        pass

    def log_error(self, message, exception=None, context=None):
        """
        Log an error with the specified format.
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        filename = "unknown"
        line_number = 0
        detailed_message = message

        if exception:
            # Extract traceback info
            tb = traceback.extract_tb(exception.__traceback__)
            if tb:
                # Get the last frame (where the error occurred)
                last_frame = tb[-1]
                filename = last_frame.filename
                line_number = last_frame.lineno
            else:
                # If no traceback (e.g. manually raised without raise), try to get caller info
                try:
                    frame = sys._getframe(1)
                    filename = frame.f_code.co_filename
                    line_number = frame.f_lineno
                except ValueError:
                    pass
            
            detailed_message = f"{message} | Exception: {str(exception)}"
        else:
            # If no exception, get caller info
            try:
                frame = sys._getframe(1)
                filename = frame.f_code.co_filename
                line_number = frame.f_lineno
            except ValueError:
                pass

        # Format: "[ERROR] [ ${timestamp} ] ${filename} : ${line_number} - ${detailed_error_message} "
        formatted_log = f"[ERROR] [ {timestamp} ] {filename} : {line_number} - {detailed_message}"
        
        # Print directly to stderr to ensure it appears in terminal as requested
        print(formatted_log, file=sys.stderr)
        
        # Also log context if present (optional, but good for debugging)
        if context:
            print(f"Context: {context}", file=sys.stderr)

        if exception:
             traceback.print_exc()

        # Return a unique identifier (timestamp based) instead of a counter
        return timestamp

# Global instance
error_manager = ErrorManager()
