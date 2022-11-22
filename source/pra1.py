import psutil
import requests
import pandas as pd
from tqdm import tqdm
from bs4 import BeautifulSoup

def load_prettify_page(url, headers):
    """
    Returns a webpage as a BeautifulShop object
    :param url: url of the page
    :param headers: headers for the request
    :return: BeautifulShop object
    """
    page = requests.get(url, headers= headers)
    return BeautifulSoup(page.content)


def get_books_urls(catalog_url, headers):
    """
    Loads the list of the books in the catalog
    :param catalog_url: url of the catalog xml page
    :param headers: headers for the request
    :return: list with the url of each book webpage
    """
    page = load_prettify_page(catalog_url, headers)
    books = page.find_all("url")
    urls = []
    for book in books:
        urls.append(book.loc.text)
    return urls


def get_classification_info(book_webpage):
    """
    Gets the page of a book and extracts the information of the classification of the book
    :param book_webpage: BeautifulSoup object of the page
    :return: dictionary with te genre, subgenre and name of the book
    """
    classification_info = {
        "generos": list(set([genero.text for genero in book_webpage.find_all("a", {"class": "tag_lvl2"})])),
        "temáticas": list(set([tematica.text for tematica in book_webpage.find_all("a", {"class": "tag_lvl3"})])),
        "titulo": book_webpage.find("h1", {"class": "h1 page-title"}).text
    }
    return classification_info


def get_other_info(book_webpage):
    """
    Gets the rest of the info provided by the publisher. This will vary on each book.
    :param book_webpage: BeautifulSoup object of the page
    :return: dictionary with all the info with a key-value structure
    """
    book_info = book_webpage.find("dl", {"class": "caracteristicas-prod data-sheet"})
    keys = book_info.find_all("dt", {"class":"name"})
    values = book_info.find_all("dd", {"class":"value"})
    book_info = {}
    for key, value in zip(keys, values):
        book_info[key.string] = value.string

    return book_info


def get_publisher_and_date(book_webpage):
    """
    Gets the info of the editorial and the publishing date .
    :param book_webpage: BeautifulSoup object of the page
    :return: dictionary with the info of the publisher and the date
    """
    info = book_webpage.find("div", {"class": "product-category-name-editorial text-muted"})
    editorial, fecha = None, None
    if info != None:
        editorial = info.text.split(",")[0]
        fecha = info.text.split(",")[1]
    return {
        "Editorial": editorial,
        "Fecha": fecha
    }


def get_description(book_webpage):
    """
    Gets the description of the book
    :param book_webpage: BeautifulSoup object of the page
    :return: dictionary with the description of the book
    """
    description = ""
    paragraphs = book_webpage.find("div", {"class":"p_leer_mas p_leer_mas_prod"}).find_all("p")
    for paragraph in paragraphs:
        description += paragraph.text + "\n"
    return {"description": description}


def get_book_price(book_webpage):
    """
    Gets the price of the book
    :param book_webpage: BeautifulSoup object of the page
    :return: dictionary with the price of the book
    """
    price = {"price": book_webpage.find("span", {"itemprop": "price", "class": "product-price"}).text}
    return price


def get_other_info(book_webpage):
    """
    Gets the rest of the info provided by the publisher. This will vary on each book.
    :param book_webpage: BeautifulSoup object of the page
    :return: dictionary with all the info with a key-value structure
    """
    book_info = book_webpage.find("dl", {"class": "caracteristicas-prod data-sheet"})
    keys = book_info.find_all("dt", {"class":"name"})
    values = book_info.find_all("dd", {"class":"value"})
    book_info = {}
    for key, value in zip(keys, values):
        book_info[key.string] = value.string

    return book_info


def scrape_book_info(url, headers):
    """
    Scrapes all the info of a book
    :param url: url of the page of the book
    :return: dictionary with all the info of the book
    """
    # Load the book as a BeautifulSoup object:
    page = requests.get(url, headers=headers)
    book_webpage = BeautifulSoup(page.content)
    publisher = get_publisher_and_date(book_webpage)
    classification_info = get_classification_info(book_webpage)
    description = get_description(book_webpage)
    other_info = get_other_info(book_webpage)
    price = get_book_price(book_webpage)
    info_dict = publisher | classification_info | other_info | description | price
    return info_dict


if __name__ == '__main__':
    XML_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36",
        "features":"xml"
    }
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
    }
    CATALOGS_URLS = {
        "esp": "https://www.penguinlibros.com/sitemap-products-1-es.xml",
        "cat": "https://www.penguinlibros.com/sitemap-products-22-ca.xml"
    }

    # Loads the webpages of each book of the desired catalog
    books = get_books_urls(CATALOGS_URLS["esp"], XML_HEADERS)

    # Loads the info from each book
    books_info = []
    i = 0
    max_i = len(books)
    while (psutil.virtual_memory()[2] < 99):
        print(f"\rBook  {i}/{max_i}. Memory {psutil.virtual_memory()[2]}%", end='')
        i += 1
        books_info.append(scrape_book_info(books[i], HEADERS))

    # Saves the results into a .csv file
    books_df = pd.DataFrame(books_info)
    books_df.to_csv("penguinlibros_esp_catalog.csv")