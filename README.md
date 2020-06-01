# XBRL Assembler
[![pipeline status](https://gitlab.com/Reggles44/xbrlassembler/badges/master/pipeline.svg)](https://gitlab.com/Reggles44/xbrlassembler/-/commits/master)
[![coverage report](https://gitlab.com/Reggles44/xbrlassembler/badges/master/coverage.svg)](https://gitlab.com/Reggles44/xbrlassembler/-/commits/master)
[![Documentation Status](https://readthedocs.org/projects/xbrlassembler/badge/?version=latest)](https://xbrlassembler.readthedocs.io/en/latest/?badge=latest)

``XBRLAssembelr`` is a parsing library for putting xbrldocuments from the sec together into ``pandas.Dataframe``.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install XBRLAssembler.

```bash
pip install xbrlassembler
```

## Usage

```python
from xbrlassembler import XBRLAssembler, FinancialStatement

google_index = "https://www.sec.gov/Archives/edgar/data/1652044/0001652044-20-000021-index.htm"
assembler = XBRLAssembler.from_sec_index(index_url=google_index)
income_statement = assembler.get(FinancialStatement.INCOME_STATEMENT)
balance_sheet = assembler.get(FinancialStatement.BALANCE_SHEET)
```
