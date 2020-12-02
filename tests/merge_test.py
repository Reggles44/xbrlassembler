from tests import assembler_test, mkass


def test_merge():
    urls = ["https://www.sec.gov/Archives/edgar/data/1084869/0001437749-20-002005-index.htm",
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-19-018360-index.htm",
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-19-022111-index.htm",
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-19-009426-index.htm,"
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-20-019622-index.htm",
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-20-009975-index.htm",
            "https://www.sec.gov/Archives/edgar/data/1084869/0001437749-19-002107-index.htm"]

    assemblers = [mkass(url) for url in urls]

    main = assemblers[0]
    main.merge(*assemblers[1:])

    assembler_test(main)
