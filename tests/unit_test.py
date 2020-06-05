from xbrlassembler import XBRLAssembler, FinancialStatement


def test_assembler():
    url = "https://www.sec.gov/Archives/edgar/data/1141807/0001141807-20-000011-index.htm"

    xbrl_assembler = XBRLAssembler.from_sec_index(url)
    income_statement = xbrl_assembler.get(FinancialStatement.INCOME_STATEMENT)
    balance_sheet = xbrl_assembler.get(FinancialStatement.BALANCE_SHEET)

    print(income_statement.to_dataframe())
    print(balance_sheet.to_dataframe())