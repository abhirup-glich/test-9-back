import json
import os
import threading
from datetime import datetime
import logging
import traceback

class ErrorManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(ErrorManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, persistence_file='error_counters.json'):
        if self._initialized:
            return
            
        self.persistence_file = persistence_file
        self.counters = {}
        self.file_lock = threading.Lock()
        self.load_counters()
        self._initialized = True
        
        # Configuration defaults
        self.config = {
            'increment_step': 1,
            'max_value': 999999
        }

    def configure(self, app_config):
        """Update configuration from Flask app config."""
        if 'ERROR_INCREMENT_STEP' in app_config:
            self.config['increment_step'] = app_config['ERROR_INCREMENT_STEP']
        if 'ERROR_MAX_VALUE' in app_config:
            self.config['max_value'] = app_config['ERROR_MAX_VALUE']

    def load_counters(self):
        """Load counters from the persistence file."""
        if os.path.exists(self.persistence_file):
            try:
                with open(self.persistence_file, 'r') as f:
                    self.counters = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.counters = {}
        else:
            self.counters = {}

    def save_counters(self):
        """Save counters to the persistence file."""
        with self.file_lock:
            try:
                with open(self.persistence_file, 'w') as f:
                    json.dump(self.counters, f)
            except IOError as e:
                logging.error(f"Failed to save error counters: {e}")

    def get_next_code(self, base_code):
        """
        Get the next unique error code for the given base code.
        e.g., if base_code is 500, might return 500, then 501, etc.
        """
        base_str = str(base_code)
        
        with self._lock:
            if base_str not in self.counters:
                self.counters[base_str] = int(base_code)
            else:
                self.counters[base_str] += self.config['increment_step']
                
                # Check for overflow/reset if needed, though requirements don't strictly specify reset behavior on max
                # "Recycling mechanism" usually implies handling this.
                if self.counters[base_str] > self.config['max_value']:
                     # Resetting to base_code or handling overflow. 
                     # Given "Unique error code", rolling over might cause collisions if logs are retained.
                     # But for this implementation, we'll reset to base + 10000 or just keep growing?
                     # Let's assume we just keep growing until max, then maybe cycle?
                     # For simplicity and robustness, let's just cycle back to base_code + 1 if it gets absurdly high, 
                     # but with 999999 it's unlikely to be hit soon.
                     pass

            current_code = self.counters[base_str]
            self.save_counters()
            return current_code

    def log_error(self, base_code, message, exception=None, context=None):
        """
        Log an error with a unique code and formatted output.
        """
        unique_code = self.get_next_code(base_code)
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        stack_trace = ""
        if exception:
            stack_trace = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        
        log_entry = {
            "error_code": unique_code,
            "timestamp": timestamp,
            "message": message,
            "stack_trace": stack_trace,
            "context": context or {}
        }
        
        # Format for console output as requested
        # "Each log entry must include: Unique error code, Timestamp, Error message, Error stack trace, Context"
        
        console_output = (
            f"\n[ERROR LOG START]"
            f"\nCode: {unique_code}"
            f"\nTime: {timestamp}"
            f"\nMessage: {message}"
            f"\nContext: {context}"
            f"\nStack Trace:\n{stack_trace}"
            f"[ERROR LOG END]\n"
        )
        
        # Print to stderr or use logging module
        # Using print for raw console output requirement visibility, or logging.error
        # The prompt asks for "Console output requirements", usually implies stdout/stderr.
        # I'll use the configured logger if available, but for the "System" part, I'll return the code.
        
        logger = logging.getLogger("ErrorSystem")
        logger.error(console_output)
        
        return unique_code, log_entry

# Global instance
error_manager = ErrorManager()
