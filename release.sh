#!/bin/sh
#!/usr/bin/python3.9

read -p 'Username: ' uservar
read -s -p "Password: " passvar

python3.9 -m pip install -U twine
python3.9 setup.py sdist
python3.9 -m twine upload dist/*.tar.gz -u $uservar -p $passvar --verbose