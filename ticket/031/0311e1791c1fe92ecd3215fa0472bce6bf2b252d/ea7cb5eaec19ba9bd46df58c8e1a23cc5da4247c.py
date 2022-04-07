import logging

class PythonLoggingObserver:
    """Output twisted messages as debugging messages.

    Used for Zope 3's event log.
    """
    
    def __init__(self): 
        # Twisted gets it's own system
        self.logger = logging.getLogger("twisted") 

    def __call__(self, log_entry):
        """Receive a twisted log entry, format it and bridge it to python."""
        message = log_entry['message']
        if not message:
            if log_entry['isError'] and log_entry.has_key('failure'):
                text = log_entry['failure'].getTraceback()
            elif log_entry.has_key('format'):
                try:
                    text = log_entry['format'] % eventDict
                except KeyboardInterrupt:
                    raise
                except:
                    try:
                        text = ('Invalid format string in log message: %s'
                                % log_entry)
                    except:
                        text = 'UNFORMATTABLE OBJECT WRITTEN TO LOG, MESSAGE LOST'
            else:
                # we don't know how to log this
                return
        else:
            text = '\n\t'.join(map(str, message))
        self.logger.debug(text)

