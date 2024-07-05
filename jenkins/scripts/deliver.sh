#!/bin/bash

# Echoing current working directory
echo "Current working directory:"
pwd

# Echoing contents of target directory
echo "Contents of target directory before delivery:"
ls -l target

# Running the Python application
echo 'The following command runs the Python application'
source venv/bin/activate
python main.py
