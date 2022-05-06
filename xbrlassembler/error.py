class XBRLError(Exception):
    """Base XBRLAssembler Exception"""


class XBRLAssemblerFromDirectoryError(XBRLError):
    """Raised when an XBRLAssembler can not be created from the specified directory"""


class XBRLAssemblerFromJSONError(XBRLError):
    """Raised when an XBRLAssembler can not be created from the specified directory"""