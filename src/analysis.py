import matplotlib.pyplot as plt
import pandas as pd


def calculations(groups, prices_df):
    """
    does the calculations and puts together list of sector performances
    :param groups: dictionary of sectors and the symbols within them
    :param prices_df: pandas DataFrame of prices of stocks within 100 days
    :return: [analysis_dict, dates]

    analysis_dict is the mapping from sector name to a list of its performance within the past 100 days
    dates is a list of dates that were used to measure the prices
    """
    every_n_days = [i for i in range(99, 0, -5)]
    every_n_days.append(0)
    analysis_dict = dict()
    dates_set = set()

    # go through each sector and calculate normalized prices
    for group in list(groups.keys()):
        prices = list()
        normalized_prices = list()
        curr_final_symbs = list()

        num_stock = None

        # want to get shortest list of stocks in case there is an error, missing values, etc.
        for d in every_n_days:
            # narrow to current day's prices
            curr_day_df = prices_df[prices_df['date'] == prices_df.loc[d]['date']]

            curr_price_df = curr_day_df[curr_day_df['symbol'].isin(groups[group])]
            curr_symbols = list(curr_price_df['symbol'])

            if len(curr_final_symbs) == 0 or len(curr_symbols) < len(curr_final_symbs):
                curr_final_symbs = curr_symbols

        for day in every_n_days:

            # narrow to current day's prices
            curr_day_df = prices_df[prices_df['date'] == prices_df.loc[day]['date']]
            dates_set.add(prices_df.loc[day]['date'])
            curr_price_df = curr_day_df[curr_day_df['symbol'].isin(curr_final_symbs)]

            # want to verify that the denominator are of 'int' type
            open_ints = pd.to_numeric(curr_price_df['1. open'], errors='coerce')

            # this gets the coefficient factor (if there is a split or merge)
            coeff = pd.to_numeric(curr_price_df['8. split coefficient'], errors='coerce')

            if num_stock is None:
                # number of stocks for 1000 dollars worth of investments
                num_stock = list(1000 / open_ints)

            curr_total = sum(num_stock * open_ints * coeff)
            prices.append(curr_total)

        # once we have all the prices, want to normalize to percentage to determine performance
        for price in prices:
            try:
                normalized_prices.append(100 * (price / prices[0]) - 100)
            except ZeroDivisionError as e:
                # fill in previous value if exists, or exit.
                if len(normalized_prices) > 0:
                    normalized_prices.append(normalized_prices[-1])
                else:
                    print(f'There was an error while trying to do the analysis. Ending program. {e}')
                    exit()

        analysis_dict[group] = normalized_prices

    # ordered list of dates (for image)
    dates = list(sorted(dates_set))
    return analysis_dict, dates


def generate_image(analysis_dict, dates, ow):
    """
    creates an image with from the analysis of each sector
    :param analysis_dict: the mapping from sector name to a list of its performance within the past 100 days
    :param dates: a list of dates that were used to measure the prices
    :param ow: bool of whether to overwrite the image generated.
    :return: nothing is returned
    """

    # defaults
    curr_max = -100
    sect = 'N/A'

    # image configurations
    fig = plt.figure(num=1, figsize=(10, 6))
    fig.subplots_adjust(top = 0.9, bottom=0.2, left=0.1, right=.75)
    plt.title('Sector Performances Over the Past Quarter')
    plt.xlabel('date')
    plt.ylabel('% gain / loss')
    plt.xticks(rotation=90)

    # plot each sector and store the best performing sector
    for key, value in analysis_dict.items():
        plt.plot(dates, value, label=key)

        if value[-1] > curr_max:
            curr_max = value[-1]
            sect = key

    # plot y = 0, just for reference
    plt.plot(range(0, len(analysis_dict['Utilities'])), [0] * len(analysis_dict['Utilities']), color='black')
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))

    # overwrite the image if user wants.
    # as far as I can tell, I don't get a file error if the image is open and this save operation is run.
    if ow:
        plt.savefig('sector_performances.png')
        print('Image was saved as "sector_performances.png" if you would like to refer to it.')

    plt.show()

    # display to user which sector performed best
    if curr_max >= 0.00:
        print(f'\n------\nThe best performing sector was {sect}, improving by {round(curr_max, 2)} percent over the '
              f'past 100 days.')
    else:
        print(f'\n------\nThe best performing sector was {sect}, only decreasing by {round(curr_max, 2)} '
              f'percent over the past 100 days.')

    return sect


def analysis_driver(symbols_df, prices_df, overwrite):
    """
    calls the appropriate analysis functions based on data and user input
    :param symbols_df: pandas DataFrame that has all symbols and sector data
    :param prices_df: pandas DataFrame that contains prices for symbols over past 100 days
    :param overwrite: bool of whether to overwrite analyzed DataFrame and image
    :return:
    """
    groups = symbols_df.groupby('sector')['symbol'].apply(list)
    analysis_dict, dates = calculations(groups, prices_df)

    if overwrite:
        df = pd.DataFrame.from_dict(analysis_dict).T
        df.columns = dates
        df.to_csv('sector_analysis.csv', encoding='utf-8')
        print('sector_analysis.csv was generated.')

    best_sector = generate_image(analysis_dict, dates, overwrite)
    print(f'Stocks within the {best_sector} sector: {groups[best_sector]}')
