#!/bin/sh
#!/usr/bin/python3.9

python3.9 -m pip install -r requirements.txt
python3.9 -m pip install -r requirements-dev.txt
python3.9 -m pytest
python3.9 -m coverage run --source=xbrlassembler -m pytest -v tests && coverage report -m
