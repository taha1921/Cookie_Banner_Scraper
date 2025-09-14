## INSTALLATION 

### Requirements

To run this project, you need to have the following installed:

1. Python (>= 3.9). The project is has been tested with and is compatible upto version 3.13
2. Poetry (https://python-poetry.org/) version >= 2.0. The project has been built with version 2.1.4. The website recommends using pipx but it can also be install with `pip install poetry`

The project was built and tested on windows so to avoid unseen errors please use windows to run the project. A small note for linux users is also mentioned in order to run the project successfully but you still may encounter unforseen errors which you will be able to see in the log file. No testing has been done yet on MacOS.

### Steps

1. Clone the repository: git clone https://github.com/taha1921/Cookie_Banner_Scraper.git
2. Shift to the directory: `cd Cookie_Banner_Scraper`
3. To install dependencies, open the terminal and run: `poetry install`
4. You also need to install a chromium for playwright to run the simulator, so run: `poetry run playwright install chromium`
5. You're now good to go, you can proceed to running the application 

#### For Linux users

1. After installing chromium please also run the following command: `poetry run playwright install-deps`
2. Incase Tkinter does not come with your python version, please run: `sudo apt install python3-tk`

## RUNNING THE PROJECT 

1. Shift to the src directory: `cd src`
2. run the program using: `poetry run python file_upload.py`

This will launch a window to upload your csv file with the domains you want to feed into the program. The structure of the csv can be seen in the example.png file as well as in the window of the program.

While the program is running, a log file will be generated to monitor the results of the domains in real time, under `output/logs`. The resulting CSV storing the results for each domain will be generated after a successful completion of the program in the `output/results` folder.

Each run of the program has it's own subfolder inside `output/screenshots` where a screenshot of the domain is saved under any of the following circumstances:
- A domain was resolved using aggressive mode. The resulting screenshot will have `_aggressive.png` in it's name.
- A domain was resolved as not having a reject button. The resulting screenshot will have `_no_reject.png` in it's name.
- No cookie banner could be found for the domain or the website did not load.