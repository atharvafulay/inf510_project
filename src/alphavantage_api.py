import requests
import csv
import json
import time
import pandas as pd
import copy


def alphavantage_deposit(symbol, dictionary, headers, other_headers, tmp_ow):
    """
    creates or adds to the file with historical prices
    :param symbol: string value of symbol (i.e. "AAPL")
    :param dictionary: prices where the keys are the date and teh value is a list of prices / split co-efficient
    :param headers: names of headers that the file should include (from alphavantage)
    :param other_headers: other headers that we have to manually add (symbol and date)
    :param tmp_ow: a bool to determine if we should overwrite the current file.
    :return: updated tmp_ow
    """

    # ensure we can read and write to the file.
    try:
        tmp_append = open('ninety_day_historical_prices.csv', mode='a', newline='', encoding="utf-8")
        tmp_append.close()

        temp_read = open('ninety_day_historical_prices.csv', mode='r', encoding="utf-8")
        read_tmp = csv.reader(temp_read)
        row_count = sum(1 for row in read_tmp)
        temp_read.close()

    except PermissionError as e:
        print(f'The file is locked. Please unlock or close the file before rerunning. {e}')
    else:
        other_headers.extend(headers)

        # if the file is empty, then write to it (create it)
        if row_count == 0 or tmp_ow:
            tmp_ow = not tmp_ow
            with open('ninety_day_historical_prices.csv', mode='w', newline='', encoding="utf-8") as write:
                writer = csv.writer(write)
                writer.writerow(other_headers)

                for key in dictionary.keys():
                    row = [symbol, key]
                    for header in headers:
                        row.append(dictionary[key][header])
                    writer.writerow(row)

        # or else just append to it
        else:
            with open('ninety_day_historical_prices.csv', mode='a', newline='', encoding="utf-8") as append:
                appender = csv.writer(append)

                for key in dictionary.keys():
                    row = [symbol, key]
                    for header in headers:
                        row.append(dictionary[key][header])
                    appender.writerow(row)

    return tmp_ow


def alphavantage_api_call(symbols, api_key, overwrite, max_page_num):
    """
    make the API call to Alphavantage, write to file (if asked), and return pandas df with data from calls
    :param symbols: list of symbols to process
    :param api_key: api key from alphavantage
    :param overwrite: bool to determine if we should overwrite the file
    :param max_page_num: page number to stop at (each swingtradebot.com page has 20 symbols)
    :return: pandas DataFrame containing all information from API calls
    """
    count = 1
    prices_for_all_symbols = pd.DataFrame()
    tmp_ow = copy.copy(overwrite)
    num_symbs = 20 * (max_page_num - 1)

    for symbol in symbols:
        api_link = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}' \
                   f'&apikey={api_key}'

        # default this to true so that it will enter the loop
        error_503 = True
        error_count = 0

        # if we run into the 503 server error, we will try every 12 seconds for 2 minutes and to try to get the value
        # if we still fail, then exit
        while error_503:

            try:
                response = requests.get(api_link)
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:

                if '503 Server Error' in str(e):
                    print(e)
                    print(f'Retrying in 12 seconds. Current symbol is {symbol}')

                    error_count += 1
                else:
                    error_503 = False

                if error_count == 10:
                    print(
                        'Hit 10 consecutive 503 Errors. Ending program. Please check to see if the Alphavantage API is still online.')
                    exit()

            else:
                # this is if response is valid
                error_503 = False
                content = response.content
                historical_prices = json.loads(content)
                key_error = False

                # write to file if user wants to update data
                if overwrite:
                    try:
                        headers = list(list(historical_prices['Time Series (Daily)'].values())[0].keys())
                        tmp_ow = alphavantage_deposit(symbol, historical_prices['Time Series (Daily)'], headers,
                                                      ['symbol', 'date'], tmp_ow)
                    except KeyError:
                        key_error = True
                        print(f'Alphavantage could not process {symbol}. Continuing with the remaining symbols.')

                # update dataframe if no errors from alphavantage API call
                if not key_error:
                    try:
                        curr_historical_prices = pd.DataFrame.from_dict(historical_prices['Time Series (Daily)']).T
                        curr_historical_prices['symbol'] = [symbol] * len(
                            historical_prices['Time Series (Daily)'].keys())
                        curr_historical_prices['date'] = curr_historical_prices.index
                        curr_historical_prices = curr_historical_prices.reset_index()
                        prices_for_all_symbols = prices_for_all_symbols.append(curr_historical_prices)
                    except KeyError:
                        print(f'Alphavantage could not process {symbol}. Continuing with the remaining symbols.')

            # update user on progress
            if count % 10 == 0:
                print(f'Finished API call for {symbol} ({count} of {num_symbs})')

            # alphavantage has limit of 5 calls per minute
            if count != len(symbols):
                time.sleep(12)

            count += 1

    return prices_for_all_symbols.reset_index()


def alphavantage_driver(symbols=None, overwrite=False, max_page_num=11):
    """
    drives the calls, central place for the api key
    :param symbols: list of symbols to process
    :param overwrite: bool of if user wants to overwrite the csv file stored locally
    :param max_page_num: page number to stop at (each swingtradebot.com page has 20 symbols), default to full run
    :return: pandas DataFrame with data from alphavantage API calls
    """
    minutes = (max_page_num - 1) * 4
    print(f'Alphavantage has an API limit of 5 calls a minute. This step will take roughly {minutes} minutes to '
          f'complete.')

    # if the symbols list is empty, then exit program
    if len(symbols) == 0:
        print('Symbols list is empty. File is possibly empty. Ending program. Check file and rerun.')
        exit()

    api_key = 'DU4ISISK6O9TAOZI'
    prices_df = alphavantage_api_call(symbols, api_key, overwrite, max_page_num)

    if overwrite:
        print('ninety_day_historical_prices.csv was created or updated.')

    return prices_df
