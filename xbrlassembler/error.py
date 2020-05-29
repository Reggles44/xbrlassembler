class XBRLError(Exception):
    name = "Error"
    """Base XBRLAssembler Exception"""
    def __init__(self, info):
        super().__init__(f"Error parsing {self.name} for {info}\n\tThis could be an error with the specific "
                         f"document.\n\tIf you believe this is an error with the code report it to:\n\t"
                         f"https://gitlab.com/Reggles44/xbrlassembler/-/issues/new")


class XBRLSchemaError(XBRLError):
    name = "Cchema"
    """Exception raised when there is an error with an XBRL schema document"""


class XBRLLabelError(XBRLError):
    name = "Label"
    """Exception raised when there is an error with an XBRL label document"""


class XBRLCellsError(XBRLError):
    name = "Cells"
    """Exception raised when there is an error with an XBRL cells document"""


class XBRLRefDocError(XBRLError):
    name = "Reference Document"
    """Exception raised when there is an error with an XBRL reference document"""


class XBRLIndexError(XBRLError):
    name = "Index"
    """Exception raised when there is an error with parsing an Index to get XBRL Documents"""


class XBRLDirectoryError(XBRLError):
    name = "Directory"
    """Exception raised when there is an error with parsing a directory to get XBRL Documents"""
