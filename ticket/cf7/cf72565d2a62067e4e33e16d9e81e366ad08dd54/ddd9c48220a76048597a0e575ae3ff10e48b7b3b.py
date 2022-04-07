import warnings

def deprecated_property(warning_text, getter=None, setter=None, deller=None, doc=None):
    """Create a property that uses the given getter/setter/deller/doc,
    but wraps them with a deprecation warning of the given text.

    Note that setters/dellers are only usable with new-style classes."""
    getattr_with_deprecation = setattr_with_deprecation = detattr_with_deprecation = None
    if getter:
        def getattr_with_deprecation(self):
            warnings.warn(warning_text, DeprecationWarning, stacklevel=2)
            return getter(self)
    if setter:
        def setattr_with_deprecation(self, new_value):
            warnings.warn(warning_text, DeprecationWarning, stacklevel=2)
            setter(self, new_value)
    if deller:
        def detattr_with_deprecation(self):
            warnings.warn(warning_text, DeprecationWarning, stacklevel=2)
            deller(self)
    return property(getattr_with_deprecation,
                    setattr_with_deprecation,
                    detattr_with_deprecation, doc)

def deprecated_attribute(warning_text, name, getter=False, setter=False, deller=False, doc=None):
    getattr_by_name = setattr_by_name = delattr_by_name = None
    if getter:
        def getattr_by_name(self):
            return getattr(self, name)
    if setter:
        def setattr_by_name(self, value):
            setattr(self, name, value)
    if deller:
        def delattr_by_name(self):
            delattr(self, name)
    return deprecated_property(warning_text,
                               getattr_by_name,
                               setattr_by_name,
                               delattr_by_name,
                               doc)
