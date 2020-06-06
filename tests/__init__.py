from datetime import datetime

from xbrlassembler import XBRLElement, FinancialStatement


def assembler_test(xbrl_assembler):
    income_statement = xbrl_assembler.get(FinancialStatement.INCOME_STATEMENT)
    balance_sheet = xbrl_assembler.get(FinancialStatement.BALANCE_SHEET)

    for uri, date in income_statement.references().items():
        print(uri, date)
    print(income_statement.visualize())

    for uri, date in balance_sheet.references().items():
        print(uri, date)
    print(balance_sheet.visualize())

    assert type(income_statement) == type(balance_sheet) == XBRLElement
    assert income_statement._children and balance_sheet._children
    assert type(income_statement.to_dict()) == type(balance_sheet.to_dict()) == dict

    income_ref = income_statement.references()
    balance_ref = balance_sheet.references()

    for ref, date in income_ref.items():
        print(ref, date, type(date[0]))
    for ref, date in balance_ref.items():
        print(ref, date, type(date[0]))

    assert balance_ref and income_ref
    assert all(isinstance(ref[0], datetime) or ref[0] == None for ref in income_ref.values()) and \
           all(isinstance(ref[0], datetime) or ref[0] == None for ref in balance_ref.values())
