# XBRL Assembler
[![pipeline status](https://gitlab.com/Reggles44/xbrlassembler/badges/master/pipeline.svg)](https://gitlab.com/Reggles44/xbrlassembler/-/commits/master)
[![coverage report](https://gitlab.com/Reggles44/xbrlassembler/badges/master/coverage.svg)](https://gitlab.com/Reggles44/xbrlassembler/-/commits/master)

``XBRLAssembelr`` is a parsing library for putting xbrldocuments from the sec together into ``pandas.Dataframe``.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install XBRLAssembler.

```bash
pip install xbrlassembler
```

## Usage

```python
from xbrlassembler import XBRLAssembler, FinancialStatement
assembler = XBRLAssembler(xbrlafiles)
income_statement = assembler.get(FinancialStatement.INCOME_STATEMENT)
balance_sheet = assembler.get(FinancialStatement.BALANCE_SHEET)
```
