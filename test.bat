cd tests
python -m pip install --upgrade pytest coverage requests
pytest
coverage run --source=xbrlassembler -m pytest
coverage report -m
cd ..
