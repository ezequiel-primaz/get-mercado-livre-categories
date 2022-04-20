from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import json

from bs4 import BeautifulSoup

jsonFilePath = 'categories.json'

try:
  input_file = open(jsonFilePath)
  categoryList = json.load(input_file)
except:
  categoryList = []

readyCategories = []

for category in categoryList:
  if(len(category['children'] > 0)):
    readyCategories.append(category['id'])

chrome_options = Options()
chrome_options.add_experimental_option("detach", True)

url = 'https://www.mercadolivre.com.br/landing/costos-venta-producto'

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), chrome_options=chrome_options)
driver.get(url)

def getCategoryChildren(category):
  try:
    print(f'category {category["id"]}')
    driver.get(f'https://www.mercadolivre.com.br/landing/costos-venta-producto/api/categories_level/{category["id"]}')
    content = driver.page_source
    content = driver.find_element_by_tag_name('pre').text
    parsed_json = json.loads(content)

    if (len(parsed_json['children_categories']) > 0):
      category['children'] = parsed_json['children_categories']
      for element in category['children']:
        getCategoryChildren(element)
    else:
      catalog_domain = parsed_json['settings']['catalog_domain']
      driver.get(f'https://www.mercadolivre.com.br/landing/costos-venta-producto/api/categories_price/{category["id"]}/MLB/{catalog_domain}')
      content = driver.page_source
      content = driver.find_element_by_tag_name('pre').text
      parsed_json = json.loads(content)
      category['children'] = []
      category['sale_fee_amount'] = {
        'premium': parsed_json[0]['sale_fee_amount'],
        'classic': parsed_json[2]['sale_fee_amount']
      }
  except:
    print('-------------- RETRYING ----------------')
    time.sleep(3)
    getCategoryChildren(category)

if (len(categoryList) == 0):
  soup_level1 = BeautifulSoup(driver.page_source, 'html.parser')

  list = soup_level1.find('ul', attrs={'class': 'andes-list'})

  for row in list.findAll('li', attrs={'class': 'category-selection-lisitem'}):
    name = row.find('span', attrs={'class': 'andes-list__item-primary'}).text
    categoryList.append({
      'id': row['id'],
      'name': name,
      'children': []
    })
  
for category in categoryList:
  if(category['id'] not in readyCategories):
    getCategoryChildren(category)
    with open(jsonFilePath, 'w') as jsonFile:
      jsonFile.write(json.dumps(categoryList, indent=4))
