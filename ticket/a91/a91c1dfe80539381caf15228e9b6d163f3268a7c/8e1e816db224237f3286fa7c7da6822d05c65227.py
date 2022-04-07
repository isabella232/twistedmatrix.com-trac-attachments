def formatError(errorcode):
    """
    Returns the string associated with a Windows error message,
    such as the ones found in socket.error.
    
    Attempts direct lookup against the win32 API via ctypes and then
    pywin32 (if available), then in the error table in the socket
    module, then finally defaulting to os.strerror.
    
    @param errorcode: The (integer) Windows error code
    
    @return: The error message string
    
    """
    def lookupErrorCode(errorcode):
        try:
            from socket import errorTab
            return socker.errorTab.get(errorcode, os.strerror(errorcode))
        except ImportError:
            return os.strerror(errorcode)
    try:
        from ctypes import WinError
        lookupErrorCode = lambda err: WinError(errorcode)[1]
    except ImportError:
        try:
            import win32api
            lookupErrorCode = win32api.FormatMessage
        except ImportError:
            pass
    return lookupErrorCode(errorcode)