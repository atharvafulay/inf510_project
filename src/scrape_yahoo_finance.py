import csv
import requests
from bs4 import BeautifulSoup
import time


def clean_address(info, company_info, fields):
    """
    return cleaned address fields / information
    :param info: HTML <p> tag that has Address of company
    :param company_info: dictionary that has current information about the company
    :param fields: ('phone', 'website', 'city', 'country')
    :return: list of city and country name
    """
    str_info = str(info.text)
    # depending on if there is a phone number / website linked with the company, there is different logic to get the
    # address
    try:
        if len(company_info[fields[0]]) > 0:
            address = str_info.rstrip().strip().split(f'\n{company_info[fields[0]]}')[0]
        elif len(company_info[fields[1]]) > 0:
            address = str_info.rstrip().split(f'\n{company_info[fields[1]]}')[0]
        else:
            address = str_info.rstrip().strip()

    # this is in the case that there is no data at all, so we return an empty string
    except KeyError as ke:
        return [None] * 4

    # this is in the case that the city and country are empty or not available, so we return an empty string
    if len(address) == 0:
        return [None] * 2

    address_split = address.split('\n')
    city_zip = address_split[-2]

    if address_split[-1] == 'United States' or address_split[-1] == 'Brazil' or address_split[-1] == 'Canada':
        city = city_zip.split(',')[0]
    else:
        city = city_zip.rsplit(' ', 1)[0]

    cz_split = [city, address_split[-1]]
    return cz_split


def get_address(soup):
    """
    gets the phone, website, city, and country from yahoo finance html
    :param soup: BeautifulSoup object for the symbol
    :return: company_info - dictionary with company's phone, website, city, and country
    """
    company_info = dict()
    general_info = soup.find('p', {'data-reactid': '8'})
    address_fields = ('phone', 'website', 'city', 'country')

    if general_info is not None:
        # https://stackoverflow.com/questions/12545897/convert-br-to-end-line
        # to edit code if needed
        for br in general_info.find_all('br'):
            if '\n' not in repr(br):
                br.replace_with('\n')

        phone_and_website = general_info.find_all('a')

        # get phone number and website
        for item in phone_and_website:
            len_of_company_info = len(company_info.keys())
            company_info[address_fields[len_of_company_info]] = item.text

        # get city and country
        address_split = clean_address(general_info, company_info, address_fields)

        # return the compiled information
        for item in address_split:
            len_of_company_info = len(company_info.keys())
            company_info[address_fields[len_of_company_info]] = item
    else:
        for k in address_fields:
            company_info[k] = None

    return company_info


def get_sector_industry_fte(soup):
    """
    get the sector, industry, and FTE info for each symbol / company
    :param soup: BeautifulSoup object for the symbol
    :return: return a dictionary containing sector, industry, and FTE
    """

    # sifte is for (s)ector (i)ndustry and (fte)
    sifte_field = ('sector', 'industry', 'fte')
    sifte_dict = dict()
    sifte_box = soup.find('p', {'class': 'D(ib) Va(t)'})

    try:
        sifte = sifte_box.find_all('span', {'class': 'Fw(600)'})
    except AttributeError:
        for field in sifte_field:
            sifte_dict[field] = None
        return sifte_dict

    # fill in dictionary
    for index in range(len(sifte)):
        if len(sifte[index]) == 0:
            sifte_dict[sifte_field[index]] = None
        else:
            sifte_dict[sifte_field[index]] = sifte[index].text

    # want the integer value for FTEs
    if sifte_dict['fte'] is not None:
        sifte_dict['fte'] = int(sifte_dict['fte'].replace(',', ''))

    return sifte_dict


def get_desc(soup):
    """

    get the description for each symbol / company
    :param soup: BeautifulSoup object for the symbol
    :return: return a dictionary containing the description
    """
    field = 'description'
    desc_dict = dict()

    try:
        section = soup.find('section', {'class': 'quote-sub-section Mt(30px)'})
        desc = section.find('p', {'class': 'Mt(15px) Lh(1.6)'})
    except AttributeError:
        desc_dict[field] = None
        return desc_dict
    else:
        desc_dict[field] = desc.text
        return desc_dict


def scrape_and_compile_yahoo(sym):
    """
    scrapes yahoo finance, and returns a variety of information for each company that is assocaited with the given
    symbol
    :param sym:  Symbol of the company
    :return: dictionary of information for that company
    """
    yahoo_link = f'https://finance.yahoo.com/quote/{sym}/profile?p={sym}'

    # ensure the response is valid or exit program.
    try:
        response = requests.get(yahoo_link)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if '503 Server Error' in str(e):
            print(e)
            print(f'Retrying in 2 seconds. If it fails again, program will stop. Current symbol is {sym}')

            time.sleep(2)
            try:
                response = requests.get(yahoo_link)
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print(e)
                exit()
        else:
            print(f'There was an error. This error was not seen before. Error: "{e}". Program has exited. Please '
                  f're-run if it is a network issue.')
            exit()

    # call functions to fill the dictionary and return it
    soup = BeautifulSoup(response.content, 'lxml')
    company_info = get_address(soup)

    sifte = get_sector_industry_fte(soup)
    company_info.update(sifte)

    desc = get_desc(soup)
    company_info.update(desc)

    return company_info
