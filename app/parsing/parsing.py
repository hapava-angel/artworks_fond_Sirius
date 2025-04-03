import os
import csv
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Инициализация Selenium
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

output_file = 'app/data/dataset_with_images_full.parquet'
with open(output_file, 'a+', newline='') as f:
    fieldnames =['title','image']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    
output_dir = 'app/data/paintings_data'
count = 0

for path in os.listdir(output_dir):
    if os.path.isfile(os.path.join(output_dir, path)):
        count += 1
print('File count:', count)
    
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

current_page = 104
counter = 0
max_paintings = 1850
while counter < max_paintings:
    base_url = "https://my.tretyakov.ru/app/gallery?ignoreBanner=true&pageNum="
    url = f"{base_url}{current_page}"
    print(f"Accessing URL: {url}")

    driver.get(url)

    time.sleep(3)

    WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.picture-content'))
    )

    paintings = driver.find_elements(By.CSS_SELECTOR, '.picture-content')

    for painting in paintings:
        if counter >= max_paintings:
          break
        try:
            painting_link = painting.find_element(By.CSS_SELECTOR, '.card-image-link').get_attribute('href')
            print(f"Opening painting: {painting_link}")

            driver.get(painting_link)
            time.sleep(3)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'img'))
            )
            image_element = driver.find_element(By.CSS_SELECTOR, 'img')  # CSS селектор для первого изображения
            image_url = image_element.get_attribute('src')
            print(f"Found image URL: {image_url}")

            if 'minkultrf-logo.svg' in image_url:
                print(f"Skipping logo image: {image_url}")
                continue
            
            try:
                author = driver.find_element(By.CSS_SELECTOR, '.discription-author-name span').text
            except Exception as e:
                author = None
            title_full = driver.find_element(By.CSS_SELECTOR, '.discription-masterpiece-name').text.strip()
            title_name, title_years = (title_full.split('\n') + [''])[0:2]
            discription_short = driver.find_element(By.CSS_SELECTOR, '.discription-masterpiece-discr').text
            discription_long = driver.find_element(By.CSS_SELECTOR, '.discription-masterpiece-biography').text
            
            if author:
                filename = f"{title_name}_{author.replace(' ', '_')}.txt"
            else:
                filename = f"{title_name}.txt"
            file_path = os.path.join(output_dir, filename)
            
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(f"Название: {title_name}\n")
                file.write(f"Годы создания: {title_years}\n")
                file.write(f"Автор: {author}\n")
                file.write(f"Характеристики: {discription_short}\n")
                file.write(f"Описание картины: {discription_long}\n")

            with open(output_file, 'a+', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writerow({'title': filename, 'image': image_url})

            driver.back()

            time.sleep(6)

            counter += 1

        except Exception as e:
          print(f"Error finding image on page or a page {current_page}: {e}")
    current_page += 1
    
driver.quit()

