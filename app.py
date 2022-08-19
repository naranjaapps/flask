import base64
import os
import time
import uuid

import json

from bs4 import BeautifulSoup
from flask import Flask
from flask_restful import Resource, Api
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select
from selenium import webdriver
import chromedriver_autoinstaller

from twocaptcha import TwoCaptcha


app = Flask(__name__)
api = Api(app)


def getrandomfilepng():
    return f"{uuid.uuid4()}.png"


def getrandomfile():
    import tempfile
    temp_name = next(tempfile._get_candidate_names())
    return temp_name


def save_screenshot(driver, element= None):


    if element:
        desired_y = (element.size['height'] / 2) + element.location['y']
        current_y = (driver.execute_script('return window.innerHeight') / 2) + driver.execute_script(
            'return window.pageYOffset')
        scroll_y_by = desired_y - current_y
        driver.execute_script("window.scrollBy(0, arguments[0]);", scroll_y_by)

    ENCODING = 'utf-8'
    IMAGE_NAME = 'screen.png'
    JSON_NAME = 'output.json'

    file_name = getrandomfilepng()
    driver.save_screenshot(file_name)

    with open(file_name, "rb") as image_file:
        byte_content = base64.b64encode(image_file.read())

    # second: base64 encode read data
    # result: bytes (again)
    base64_bytes = base64.b64encode(byte_content)

    # third: decode these bytes to text
    # result: string (in utf-8)
    base64_string = base64_bytes.decode(ENCODING)

    # optional: doing stuff with the data
    # result here: some dict
    raw_data = {IMAGE_NAME: base64_string}

    # now: encoding the data to json
    # result: string
    json_data = json.dumps(raw_data, indent=2)

    os.remove(file_name)

    return {"image": json_data}


class JSon():
    pass


def sunarp_event():
    URL = 'https://enlinea.sunarp.gob.pe/sunarpweb/pages/acceso/ingreso.faces'
    driver = None
    SUNARP_USERNAME = "10631860"
    SUNARP_PASSOWRD = "w5745UMbTI"

    CAPTCHA_USERNAME = "juan.chavez"
    CAPTCHA_PASSOWRD = "Xg464pA4"
    results = []
    screenshots = []

    chromedriver_autoinstaller.install()

    try:

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--start-maximized")
        driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), chrome_options=chrome_options)

        driver.set_window_size(1280, 960)
        driver.get(URL)

        username = driver.find_element(by=By.XPATH, value="//input[@name='username']")
        username.send_keys(SUNARP_USERNAME)

        username = driver.find_element(by=By.XPATH, value="//input[@name='password']")
        username.send_keys(SUNARP_PASSOWRD)

        driver.execute_script("ingresarEventoClic();")
        time.sleep(2)

        driver.switch_to.default_content()
        parentFrameset = driver.find_element(By.TAG_NAME, value="frameset")
        parentFrame = parentFrameset.find_elements(By.TAG_NAME, value="frame")[1]
        driver.switch_to.frame(parentFrame)
        childFrameset = driver.find_element(By.TAG_NAME, value="frameset")
        childFrame = childFrameset.find_elements(By.TAG_NAME, value="frame")[2]
        driver.switch_to.frame(childFrame)

        time.sleep(1.5)

        selectPropiedad = Select(
            driver.find_elements(by=By.XPATH, value="//select[contains(@name, 'frmPartidaDirecta')]")[1])
        selectPropiedad.select_by_value("6")

        time.sleep(1.5)

        placa = driver.find_element(by=By.ID, value='frmPartidaDirecta:idTxtPlacas')
        placa.send_keys("ABC123")

        screenshots.append(save_screenshot(driver=driver, element=placa))

        button = driver.find_element(by=By.ID, value="frmPartidaDirecta:btnBuscarVeh")
        button.click()

        time.sleep(2)

        element = driver.find_element(by=By.ID, value="frmResultadoVeh:tblResultPartVeh_head")
        screenshots.append(save_screenshot(driver=driver, element=element))

        buttons = driver.find_elements(by=By.XPATH, value="//button[contains(@id, 'frmResultadoVeh:tblResultPartVeh')]")
        buttons[1].click()
        time.sleep(1)

        size = len(driver.window_handles)
        for h in range(0, size):
            driver.switch_to.window(driver.window_handles[h])
            if "PARTIDA" in driver.title.upper():
                break

        panel = driver.find_element(by=By.ID, value="frmVisualizar:panelAientos")
        tables = panel.find_elements(by=By.TAG_NAME, value="table")
        table_rows = tables[1].find_elements(by=By.TAG_NAME, value="tr")
        last_buy = False
        last_buy_downloaded = False
        link_img = None

        for table_row in table_rows:
            table_cols = table_row.find_elements(by=By.TAG_NAME, value="td")
            for table_col in table_cols:
                links = table_col.find_elements(by=By.TAG_NAME, value="a")
                # [contains( @ id, 'btnCargar')]
                # links_paginas = table_col.find_elements(by=By.XPATH, value="a[contains(@class, 'linkParticipante visualizar1')]")

                for link in links:
                    id = link.get_attribute("id")
                    list_class = link.get_attribute("class")
                    if "btnCargar" in id:
                        link.click()
                        time.sleep(1)
                        screenshots.append(save_screenshot(driver=driver, element=link))

                        soup = BeautifulSoup(driver.page_source, 'html.parser')
                        data = []
                        form = soup.find('form', id="form2")
                        table = form.find('table')
                        table_body = table.find('tbody')
                        rows = table_body.find_all('tr')
                        for row in rows:
                            cols = row.find_all('td')
                            cols = [ele.text.strip() for ele in cols]
                            data.append([ele for ele in cols])


                        event = {}
                        date = data[0][1]
                        event["inscription"] = f"{date[6:10]}-{date[3:5]}-{date[0:2]}"

                        date = data[1][1]
                        event["presentation"] = f"{date[6:10]}-{date[3:5]}-{date[0:2]}"

                        event["heading"] = data[2][1]
                        event["act"] = data[3][1]
                        event["natural"] = data[4][1]
                        event["legal"] = data[5][1]

                        results.append(event)

                        if not last_buy_downloaded and ("TRANSFERENCIA DE PROPIEDAD" in event["act"] or "Inscripción de Vehículo"):
                            last_buy = True

                        close_button = driver.find_element(by=By.XPATH, value="//button[contains(@id, 'form2')]")
                        close_button.click()

                    elif "linkParticipante visualizar9" in list_class and last_buy and not last_buy_downloaded:
                        link_img = link
                        last_buy = False
                        last_buy_downloaded = True

        if link_img:
            link_img.click()
            time.sleep(5)

            img = driver.find_element(by=By.ID, value="frmVisualizar:imagenContent")
            screenshots.append(save_screenshot(driver=driver, element=img))


    except Exception as ex:
        results.append({"errror":str(ex)})

    if driver:
        driver.close()
        driver.quit()

    return {"data": results, "screenshot" : screenshots}


class HelloWorld(Resource):
    def get(self):
        return "<p>Sunarp Servicio</p>"


class GetEvents(Resource):
    def get(self):
        data = sunarp_event()

        return {"resultado": data}

api.add_resource(HelloWorld, '/')
api.add_resource(GetEvents, '/GetEvents')

if __name__ == '__main__':
    app.run(host='0.0.0.0')