XBRL Assembler
==============
.. image:: https://gitlab.com/Reggles44/xbrlassembler/badges/master/pipeline.svg
    :alt: pipeline status
    :target: https://gitlab.com/Reggles44/xbrlassembler/-/commits/master

.. image:: https://gitlab.com/Reggles44/xbrlassembler/badges/master/coverage.svg
    :alt: coverage report
    :target: https://gitlab.com/Reggles44/xbrlassembler/-/commits/master

.. image:: https://readthedocs.org/projects/xbrlassembler/badge/?version=latest
    :alt: Documentation Status
    :target: https://xbrlassembler.readthedocs.io/

``XBRLAssembelr`` is a parsing library for putting xbrldocuments from the sec together into ``pandas.Dataframe``.

Installation
------------

Use the package manager pip to install XBRLAssembler.

.. code-block::bash

    python -m pip install xbrlassembler

Usage
-----

XBRLAssembler has two main use cases, local file parsing or SEC index parsing.

The first use can be donw as shown given the SEC statement index url.

.. code-block:: python

    from xbrlassembler import XBRLAssembler

    google_index = "https://www.sec.gov/Archives/edgar/data/1652044/0001652044-20-000021-index.htm"
    assembler = XBRLAssembler.from_sec_index(index_url=google_index)


Alternatively local documents from a specific folder can be the basis for the assembler.
This is done by using the from_dir constructor. 

.. code-block:: python

    from xbrlassembler import XBRLAssembler

    assembler = XBRLAssembler.from_dir("C://path/to/files")

To access data from an assembler use the 'get' function.
Search for specific documents but the buildin enum, regex, or string.

.. code-block:: python

    import re
    from xbrlassembler import FinancialStatement

    income_statment = assembler.get(FinancialStatement.INCOME_STATEMENT)
    income_statment = assembler.get(re.compile(r'Income Statment'))
    income_statment = assembler.get('Income Statement')

Get returns an XBRLElement which can be swapped into better forms.
XBRLElement.visualize() will return a multiline string containing all data under that node.
XBRLElement.to_dataframe() creates a pandas.Dataframe out of the tree

.. code-block:: python

    print(income_statement.visualize())
    income_dataframe = income_statement.to_dataframe()

Additional documentation for specific functions and errors can be found at, https://xbrlassembler.rtfd.io.
