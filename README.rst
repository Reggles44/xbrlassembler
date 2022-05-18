XBRL Assembler
==============

.. image:: https://github.com/Reggles44/xbrl-assembler/workflows/test/badge.svg
    :target: https://github.com/Reggles44/xbrl-assembler/actions?query=workflow%3Atest

.. image:: https://codecov.io/gh/Reggles44/xbrl-assembler/branch/main/graph/badge.svg?token=2YNUXL23DF
    :target: https://codecov.io/gh/Reggles44/xbrl-assembler

.. image:: https://readthedocs.org/projects/xbrlassembler/badge/?version=latest
    :alt: Documentation Status
    :target: https://xbrlassembler.readthedocs.io/

``XBRLAssembelr`` is a parsing library for SEC data in the XBRL format.

Installation
------------

Use the package manager pip to install XBRLAssembler.

.. code-block::bash

    python -m pip install xbrlassembler

Usage
-----

Parse a set of XBRL files and convert it to a single json file.

.. code-block:: python

    import json
    from xbrlassembler import XBRLAssembler

    assembler = XBRLAssembler.parse_dir(PATH_TO_XBRL_FILES)

    with open('/path/to/json/<file_name>.json', 'w') as json_file:
        json.dump(assembler.to_json(), json_file)

Preform complex lookups on specific financial statements using simple matches, regex patterns, or lambda expressions.

.. code-block:: python

    from xbrlassembler import XBRLAssembler, FinancialStatement

    assembler = XBRLAssembler.parse_dir(PATH_TO_XBRL_FILES)

    income_statment = assembler.get(FinancialStatement.INCOME_STATEMENT)
    income_statment = assembler.get(re.compile(r'Income Statment'))
    income_statment = assembler.get('Income Statement')

    revenue = income_statement.find(uri='cash')
    revenue = income_statement.find(uri=re.compile('cash', re.IGNORECASE))
    revenue = income_statement.find(uri='cash', value=lambda value: isinstance(value, int) and value > 100)
