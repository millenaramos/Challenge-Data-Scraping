# src/main.py

import os
import requests
import json
import time
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def setup_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")

    prefs = {"download.default_directory": os.getcwd() + "/output/assets"}
    options.add_experimental_option("prefs", prefs)

    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    driver.wait = WebDriverWait(driver, 60)
    return driver

def scroll_into_view(driver, element):
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
    time.sleep(1)

def baixar_arquivo(url, endereco):
    try:
        resposta = requests.get(url, timeout=15)
        if resposta.status_code == 200:
            with open(endereco, 'wb') as f:
                f.write(resposta.content)
            print(f"Download concluído: {endereco}")
        else:
            print(f"Erro ao baixar {url}: status {resposta.status_code}")
    except Exception as e:
        print(f"Erro ao baixar arquivo {url}: {e}")

def coletar_blocos(driver, categoria_url, limite_produtos=5):
    blocos = []
    driver.get(categoria_url)
    time.sleep(5)

    while True:
        try:
            driver.wait.until(
                EC.presence_of_element_located((By.XPATH, '//div[@class="container rounded-corners"]'))
            )
            break
        except TimeoutException:
            print("Demorou para carregar, recarregando...")
            driver.refresh()

    produtos_list = driver.find_elements(By.XPATH, '//div[@class="container rounded-corners"]')

    for produto in produtos_list:
        try:
            nome = produto.find_element(By.CLASS_NAME, "ng-binding.ng-scope").text
            descricao = produto.find_element(By.CLASS_NAME, "description.ng-binding").text
            link = produto.find_element(By.XPATH, './/div[contains(@class, "overview")]/h3/a').get_attribute("href")
            id_produto = link.split("/")[-1]

            specs = {}
            try:
                table_element = produto.find_element(By.XPATH, './/table')
                rows = table_element.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) >= 2:
                        key_raw = cols[0].text.strip().lower()
                        value = cols[1].text.strip()

                        if "output" in key_raw:
                            specs["hp"] = value
                        elif "base speed" in key_raw:
                            specs["rpm"] = value
                        elif "voltage" in key_raw:
                            specs["voltage"] = value
                        elif "frame" in key_raw:
                            specs["frame"] = value
            except Exception as e:
                print(f"Specs não encontradas para o produto: {e}")

            driver.execute_script("window.open(arguments[0]);", link)
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(10)

            try:
                popup = driver.find_element(By.ID, "adroll_reject")
                popup.click()
                time.sleep(2)
            except:
                pass

            bom = coletar_bom(driver)
            assets = coletar_assets(driver, id_produto)

            driver.close()
            driver.switch_to.window(driver.window_handles[0])

            produto_info = {
                "product_id": id_produto,
                "name": nome,
                "description": descricao,
                "specs": specs,
                "bom": bom,
                "assets": assets
            }

            blocos.append(produto_info)

            if len(blocos) >= limite_produtos:
                break

        except Exception as e:
            print(f"Erro ao extrair produto: {e}")
            continue

    return blocos

def coletar_bom(driver):
    bom_list = []
    wait = driver.wait

    try:
        aba_bom = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="catalog-detail"]/div[2]/div/div/div/nav/ul/li[5]')))
        scroll_into_view(driver, aba_bom)
        aba_bom.click()
        time.sleep(2)

        tabela_bom = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="catalog-detail"]/div[2]/div/div/div/div/div[5]')))
        linhas = tabela_bom.find_elements(By.TAG_NAME, 'tr')

        for linha in linhas:
            colunas = linha.find_elements(By.TAG_NAME, 'td')
            if len(colunas) >= 3:
                part_number = colunas[0].text.strip()
                description = colunas[1].text.strip()
                quantity_text = colunas[2].text.strip()

                # Extração numérica robusta
                match = re.search(r'[\d.,]+', quantity_text)
                if match:
                    quantity_str = match.group().replace(",", ".")
                    try:
                        quantity = float(quantity_str) if "." in quantity_str else int(quantity_str)
                    except ValueError:
                        quantity = "N/A"
                else:
                    quantity = "N/A"

                bom_list.append({
                    "part_number": part_number,
                    "description": description,
                    "quantity": quantity
                })

    except Exception as e:
        print(f"BOM não encontrado: {e}")

    return bom_list


def coletar_assets(driver, id_produto):
    assets = {"manual": None, "cad": None, "image": None}
    wait = driver.wait
    pasta = f"output/assets/{id_produto}"
    os.makedirs(pasta, exist_ok=True)

    # Manual (PDF)
    try:
        print("Coletando manual (PDF)...")
        manual = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="infoPacket"]')))
        scroll_into_view(driver, manual)
        manual_url = manual.get_attribute("href")
        print(f"Link do manual: {manual_url}")

        if manual_url:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/pdf",
                "Referer": "https://www.baldor.com/",
            }

            manual_path = f"{pasta}/manual.pdf"
            response = requests.get(manual_url, headers=headers, timeout=60)
            if response.status_code == 200:
                with open(manual_path, "wb") as file:
                    file.write(response.content)
                print(f"Manual salvo em {manual_path}")
                assets["manual"] = manual_path
            else:
                print(f"Erro ao baixar manual: {response.status_code}")
        else:
            print("URL do manual não encontrada ou inválida.")

    except (TimeoutException, NoSuchElementException, Exception) as e:
        print(f"Erro ao coletar manual: {e}")

    try:
        print("Coletando imagem...")
        imagem = wait.until(EC.presence_of_element_located((By.XPATH, "//img[@class='product-image']")))
        scroll_into_view(driver, imagem)
        imagem_url = imagem.get_attribute("src")
        print(f"Link da imagem: {imagem_url}")

        if imagem_url:
            # Forçar headers de navegador
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                "Referer": "https://www.baldor.com/",
            }

            image_path = f"{pasta}/img.jpg"
            response = requests.get(imagem_url, headers=headers, timeout=10)
            if response.status_code == 200:
                with open(image_path, "wb") as file:
                    file.write(response.content)
                print(f"Imagem salva em {image_path}")
                assets["image"] = image_path
            else:
                print(f"Erro ao baixar imagem: {response.status_code}")
        else:
            print("URL da imagem não encontrada ou inválida.")

    except (TimeoutException, NoSuchElementException, Exception) as e:
        print(f"Erro ao coletar imagem: {e}")

    # CAD (DWG)
    try:
        aba_cad = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="catalog-detail"]/div[2]/div/div/div/nav/ul/li[2]')))
        scroll_into_view(driver, aba_cad)
        aba_cad.click()
        time.sleep(2)

        menu_cad = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="drawings"]/div[1]/div[3]/div[3]')))
        scroll_into_view(driver, menu_cad)
        menu_cad.click()
        time.sleep(3)

        opcao_dwg = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div/ul/li[2]')))
        scroll_into_view(driver, opcao_dwg)
        opcao_dwg.click()
        time.sleep(2)

        download_botao = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="cadDownload"]/span')))
        download_botao.click()
        print(f"Download do CAD iniciado para {id_produto}.")
        assets["cad"] = f"{pasta}/cad.dwg"
    except:
        print(f"CAD não encontrado para {id_produto}.")

    return assets

def salvar_produto(produto):
    id_produto = produto["product_id"]
    caminho_json = f"output/{id_produto}.json"
    os.makedirs(os.path.dirname(caminho_json), exist_ok=True)
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(produto, f, indent=4, ensure_ascii=False)

def main():
    driver = setup_driver()

    urls = [
        "https://www.baldor.com/catalog#category=110",
        "https://www.baldor.com/catalog#category=4",
        "https://www.baldor.com/catalog#category=6"
    ]

    todos_produtos = []

    try:
        for url in urls:
            produtos = coletar_blocos(driver, url, limite_produtos=5)
            todos_produtos.extend(produtos)

        for produto in todos_produtos:
            salvar_produto(produto)
            print(f"Produto {produto['product_id']} salvo.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
