# Importamos las diferentes librerías que deberemos usar para
# realizar el ejercicio de web scraping:

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import pandas as pd
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import locale

# Iniciamos el controlador de Chrome para hacer web scraping:

s = Service('/usr/local/bin/chromedriver')
driver = webdriver.Chrome(service=s)

# Definimos la URL base y los parámetros de búsqueda
base_url = 'https://www.normacomics.com'
params = '/comics/comic-americano/marvel-comics.html?p='

# Creamos una lista de URLs completas de cada página de resultados
urls = [base_url + params + str(page) + '&product_list_limit=72' for page in range(1, 23)]

# Hacemos las peticiones HTTP y extraemos el contenido HTML
soups = []
for url in urls:
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.item.product.product-item")))
    soups.append(BeautifulSoup(driver.page_source, 'html.parser'))

# Extraemos los enlaces de cada cómic
comic_links = []
for soup in soups:
    comics = soup.find_all('li', class_='item product product-item')
    for comic in comics:
        link = comic.find('a', class_='product-item-link')['href']
        comic_links.append(link)

# Hacemos las peticiones HTTP de cada enlace y extraemos su contenido HTML
soups2 = []
for link in comic_links:
    driver.get(link)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td.col.data")))
    soups2.append(BeautifulSoup(driver.page_source, 'html.parser'))

# Extraemos las características de cada cómic en la página correspondiente
comic_names = [soup2.find('span', class_='base').text.strip() for soup2 in soups2]
comic_prices = [soup2.find('span', class_='price').text.strip() for soup2 in soups2]
comic_authors = [soup2.find('td', class_='col data').text.strip() for soup2 in soups2]
comic_editorials = [soup2.find('td', attrs={'data-th': 'Editorial'}).text.strip() for soup2 in soups2]
comic_isbns = [soup2.find('td', attrs={'data-th': 'ISBN'}).text.strip() for soup2 in soups2]

# Para no tener problemas con la configuración regional española:
locale.setlocale(locale.LC_TIME, 'es_ES')

# Para la fecha de lanzamiento haremos uso de datetime
# ya que en la página web sale en un formato "incómodo":
date_without_format = [soup2.find('td', attrs={'data-th': 'Fecha de venta'}).text.strip() for soup2 in soups2]

# Convertimos las fechas en formato de string a datetime:
release_dates = []
for date in date_without_format:
    try:
        release_date = datetime.strptime(date, '%d %b %Y')
    except ValueError:
        release_date = None
    release_dates.append(release_date)

# Formateamos las fechas y les asignamos un nombre:
comic_releases = [release_date.strftime('%d/%m/%Y') if release_date else None for release_date in release_dates]

comic_formats = [soup2.find('td', attrs={'data-th': 'Formato'}).text.strip() if soup2.find('td', attrs={'data-th': 'Formato'}) else '' for soup2 in soups2]
comic_pages = [soup2.find('td', attrs={'data-th': 'Num páginas'}).text.strip() if soup2.find('td', attrs={'data-th': 'Num páginas'}) else '' for soup2 in soups2]
comic_stocks = ['En stock' if soup2.find('span', class_='label-availability').find_next_sibling('span').text.strip() == 'En stock' else 'Agotado' for soup2 in soups2]

# Creamos un dataframe con las características de cada cómic
df = pd.DataFrame({
'Nombre': comic_names,
'Autor': comic_authors,
'Editorial': comic_editorials,
'ISBN': comic_isbns,
'Precio': comic_prices,
'Fecha de lanzamiento': comic_releases,
'Formato': comic_formats,
'Páginas': comic_pages,
'Disponibilidad': comic_stocks
})

#Guardamos el dataframe como un archivo CSV
df.to_csv('comics_marvel.csv', index=False)

driver.quit()