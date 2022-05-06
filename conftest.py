import os
import logging

from tests import XBRL_RESOURCE_FILES, fetch_resource_files
from tests.xbrlassembler_test import BASE_XBRL_URL

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


if len(os.listdir(XBRL_RESOURCE_FILES)) <= 1:
    fetch_resource_files(BASE_XBRL_URL, XBRL_RESOURCE_FILES)



