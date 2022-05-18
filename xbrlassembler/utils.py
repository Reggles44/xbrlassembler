import re
from datetime import datetime

DATE_REGEX = {
    '%Y': r'(2[0-2][0-9]{2})',
    '%y': fr'(0[1-9]|1[0-9]|2[0-{str(datetime.now().year)[-1]}])',
    '%m': r'(0[1-9]|1[0-2])',
    '%d': r'(0[1-9]|[1-2][0-9]|30|31)',
    '%b': r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
}

QUARTER_REPLACEMENTS = {
    'Q1': '0331',
    'Q2': '0630',
    'Q3': '0930',
    'Q4': '1231'
}

DATE_FORMATS = (
    '%Y%m%d',
    '%m%d%Y',
    '%d%b%Y',
    '%y%m%d',
    '%b%d%Y'
)


def parse_datetime(value):
    if value is None:
        return

    for qtr, month_day in QUARTER_REPLACEMENTS.items():
        value = value.replace(qtr, month_day)

    for fmt in DATE_FORMATS:
        regex_fmt = ''.join(DATE_REGEX[f'%{c}'] for c in fmt.split('%') if c)
        date_search = re.search(regex_fmt, value)
        if date_search:
            return datetime.strptime(f"{date_search[1]}{date_search[2]}{date_search[3]}", fmt)