#!/bin/sh

pip install nose
python setup.py build
nosetests
