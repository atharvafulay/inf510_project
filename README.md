# inf510_project
USC INF 510 Final Project

This is the final class project for INF 510 at USC. 

What my project does is collects data on stock symbols, groups them by sector and provides a potential return on investment over the last 100 business days. The program scrapes swingtradebot.com and Yahoo Finance as well as calls the Alphavantage API to collect the data. All of the code is in Python (either as .py or .ipynb files). This code uses pandas data frames to model the data, and the data is stored on disk as two CSV files. 

To run the program, you will have to:
  - download all the files in the /src and /data directories.
    - Then you'll have to move all the files into the same directory.
  - Then using the terminal, navigate to the directory where these files are located and run fulay_atharva.py with the following command-line switches:
    - source (required): "remote", "local", or "test". "remote" will scrape SwingTradeBot.com and Yahoo Finance to get symbol data for the top 200 symbols by volume traded. It will also call the Alphavantage API to get historical stock prices (100 business days). "test" will do the same as "remote" except that "test" will be only pull 20 symbols instead of 200. "local" is assuming you have already collected the data (what is in the /data folder), and regenerates the analysis and graph from that. 
	- overwrite (optional): 0 or 1. 1 will overwrite the current files if they exist or create the files if they don't. This includes all files including the CSV and image generated by the analysis. 0 will run the analysis without overwriting or writing to the disk. If the switch is left out, the program defaults to 0. 

Example: $ python fulay_atharva.py -source=local -overwrite=0

This program requires these packages along with python 3.7: pandas, matplotlib.pyplot, argparse, BeautifulSoup (from bs4 import BeautifulSoup), requests, time, csv, copy

The fulay_atharva.ipynb has some of the analysis more broken out and explained. 
