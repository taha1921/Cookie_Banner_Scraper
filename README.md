#### INSTALLATION ####
To run this project, you need:

Python >=3.9,<3.14 (tested with 3.9 and 3.13)

Poetry (https://python-poetry.org/) >=1.5: can be installed with pip install poetry

Step 1: Clone the repository
git clone https://github.com/taha1921/GR.git
cd GR

Step 2: Install dependency
run: poetry install

Step 3: Install chromium browser for playwright
run: poetry run playwright install chromium

You should now be good to go

#### RUNNING THE PROJECT ####
cd src

run: poetry run python file_upload.py

This will launch a window to upload your csv file with the domains you want to feed into the program.

Structure your domains csv like the following:

Domain
https://pullandbear.com
https://doctolib.fr
https://meetup.com
https://klarna.com

The results will be saved in the output/results directory.
