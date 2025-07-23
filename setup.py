from setuptools import setup
import os

APP = ["main.py"]
OPTIONS = {
    'argv_emulation': True,
    'includes': ['pygame'],
}

DATA_FILES = []
for root, dirs, files in os.walk('assets'):
    for file in files:
        DATA_FILES.append((os.path.join(root), [os.path.join(root, file)]))

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    data_files=DATA_FILES,
)