import requests
from bs4 import BeautifulSoup
import csv
import scrape_yahoo_finance
import time


def get_sym_data(curr_company, symbols, sectors):
    """
    calls yahoo finance and merges the data into the sectors, symbols dictionaries

    :param curr_company: dictionary - current symbol and data about the symbol from swingtradebot
    :param symbols: dictionary - previous symbols and their data from swingtradebot
    :param sectors: dictionary - sectors and the symbols within each
    :return: updated versions of (avg_volumes, symbols, sectors)
    """
    SYMBOL_KEY = 'symbol'

    # yahoo finance call, returns a dictionary with information about that symbol
    yahoo_company_info = scrape_yahoo_finance.scrape_and_compile_yahoo(curr_company[SYMBOL_KEY])
    sector = yahoo_company_info['sector']

    # update sectors dictionary with new symbol
    curr_symbols_in_sector = sectors.get(sector, [])
    curr_symbols_in_sector.append(curr_company[SYMBOL_KEY])
    sectors[sector] = curr_symbols_in_sector

    # add current company to symbols
    curr_company.update(yahoo_company_info)
    symbols[curr_company[SYMBOL_KEY]] = curr_company

    return symbols, sectors


def swingtradebot_scraper(max_page_num):
    """
    Processes the main scrape using requests and bs4.
    :param max_page_num: page number to stop at (each swingtradebot.com page has 20 symbols)
    :return: [symbols, message, success]

    symbols is a dictionary full with the data from STB and Yahoo Finance
    message is a text of whether the scrape was successful or if it failed
    success is a bool based on if the scrape was successful or it it failed
    """
    curr_company_swing_trade_keys = ['symbol', 'name', 'close_price', 'volatility', 'avg_volume']
    symbols = dict()  # has full information about symbol
    sectors = dict()  # sectors to symbols
    page_num = 1
    success = True
    VOLUME_KEY = 'avg_volume'

    # continue until the max page number is reached
    while page_num < max_page_num:
        url = f'https://swingtradebot.com/equities?adx_trend=&direction=desc&end_date=2019-11-15&grade=&grade_target' \
              f'=B&include_etfs=0&max_price=99999999999999.0&min_price=0.0&min_vol=0&optionable=false&sort' \
              f'=average_daily_volume&sort_by=average_daily_volume+ASC&trading_date=2019-11-15&weekly_options=false' \
              f'&page={page_num}'

        # get request and see if it is valid. If a 503 or 400 Error comes up, then it will wait 2 seconds and try again
        # if it fails a second time, it will return whatever the program was able to scrape with an unsuccessful message
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if '503 Server Error' in response or '400 Client Error:' in response:
                print('503 Error or 400 Error. Trying again in 2 seconds. If it fails again, program will quit. ')
                time.sleep(2)

                try:
                    response = requests.get(url)
                    response.raise_for_status()
                except requests.exceptions.HTTPError as e:
                    if '503 Server Error' in response or '400 Client Error:' in response:
                        print('503 Error or 400 Error. It failed again, program will quit. ')
                        success = False
                        message = f'Back to back 503 or 400 errors. The page_num was {page_num}. Error was "{e}"'
                        return [symbols, message, success]
                    else:
                        message = f'Unexpected error. The page_num was {page_num}. Error was "{e}"'
                        success = False
                        return [symbols, message, success]
            else:
                message = f'Unexpected error. The page_num was {page_num}. Error was "{e}"'
                success = False
                return [symbols, message, success]

        # once the request is deemed valid, using BS4 to parse the data we want
        soup = BeautifulSoup(response.content, 'lxml')
        table = soup.find('div', {'class': 'table-responsive'})
        data = table.find('tbody')

        for tr in data.find_all('tr'):
            curr_company = dict()

            # put in dummy values of None for each key
            for key in curr_company_swing_trade_keys:
                curr_company[key] = None

            # this loop assumes that the structure of the table is the same for each page.
            for td in tr.find_all('td'):
                a = td.find('a')

                # some data is stored in <a> tags, some is not
                if a is None:
                    # skip if there is no data
                    if len(td.text) == 0:
                        continue
                    else:
                        td_text = td.text.replace(',', '')
                        if curr_company['close_price'] is None:
                            curr_company['close_price'] = float(td_text)
                        elif curr_company['volatility'] is None:
                            curr_company['volatility'] = float(td_text)
                        elif curr_company['avg_volume'] is None:
                            curr_company['avg_volume'] = float(td_text)
                else:
                    if curr_company['symbol'] is None:
                        curr_company['symbol'] = a.text
                    elif curr_company['name'] is None:
                        curr_company['name'] = a.text

            # convert volume to an integer
            curr_company[VOLUME_KEY] = int(curr_company[VOLUME_KEY])

            # get the sector and other important company information.
            # it returns updated symbols, sectors dictionaries
            symbols, sectors = get_sym_data(curr_company, symbols, sectors)

        print(f'Finished scraping symbols from SwingTradeBot/Yahoo Finance for page {page_num}.')
        page_num += 1

    message = 'Successfully scraped SwingTradeBot.com and Yahoo Finance'
    return [symbols, message, success]


def deposit_to_csv(symbols):
    """
    store the symbols and the collected data into a csv called "symbols.csv"
    :param symbols: dictionary that has all the symbols and their information needed.
    :return: Nothing is returned.
    """
    try:
        tmp = open('symbols.csv', 'w', newline='', encoding="utf-8")
        tmp.close()
    except PermissionError as e:
        print(f'File is open or locked. Close the file before rerunning. {e}')
        input('Once you have closed the file, press Enter for the program to resume.')
        ret = deposit_to_csv(symbols)
        return ret
    else:

        with open('symbols.csv', 'w', newline='', encoding="utf-8") as csvfile:
            symbols_writer = csv.writer(csvfile)

            dummy_value = list(symbols.values())[0]
            headers = list(dummy_value.keys())

            # headers
            symbols_writer.writerow(headers)

            # data
            for symbol in symbols.keys():
                s = symbols[symbol].copy()
                row = list()
                for header in headers:
                    row.append(s[header])
                symbols_writer.writerow(row)
        return 'symbols.csv was created or updated.'


def swingtradebot_driver(overwrite, max_page_num):
    """
    calls the swingtradebot functions in order to scrape and generate a CSV file with the data.
    :param overwrite: whether to overwrite current file.
    :param max_page_num: page number to stop at (each swingtradebot.com page has 20 symbols)
    :return: the symbols dictionary is returned
    """
    if max_page_num == 2:
        print('--------\nScraping SwingTradeBot.com and Yahoo Finance. Note: This step will take 1 to 2 minutes to '
              'complete.')
    else:
        print('--------\nScraping SwingTradeBot.com and Yahoo Finance. Note: This step will take 3 to 5 minutes to '
              'complete.')

    # call swingtradebot scraper
    symbols, message, scrape_success = swingtradebot_scraper(max_page_num)

    if scrape_success and overwrite:
        message = deposit_to_csv(symbols)
        print(message)
    elif scrape_success and not overwrite:
        print(message)
    else:
        print(message)
        print('Scraping SwingTradeBot.com and Yahoo Finance was unsuccessful. Please check the error message to see if '
              'there is a internet/HTTP issue')

    return symbols
