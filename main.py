import os
import time
import urllib.parse

import pyshorteners
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

from telegram_notifier import send_message

TRIGGER_PRICE = 520


def solve_captcha(driver):
    # solve captcha using buster
    # driver.get("https://www.google.com/recaptcha/api2/demo")

    print("Clicking on the captcha...")
    WebDriverWait(driver, 20).until(
        EC.frame_to_be_available_and_switch_to_it(
            (
                By.XPATH,
                "//iframe[starts-with(@src, 'https://www.google.com/recaptcha/api2/anchor')]",
            )
        )
    )
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//div[@class='recaptcha-checkbox-border']")
        )
    ).click()

    # wiat 130s with progress bar
    n = 121
    with tqdm(total=n, desc="Waiting for captcha to be solved") as pbar:
        for _ in range(n):
            time.sleep(1)
            pbar.update(1)

    driver.switch_to.default_content()

    # # Click at position 500,500
    ac = ActionChains(driver)
    ac.move_by_offset(500, 500).click().perform()
    time.sleep(1)

    WebDriverWait(driver, 20).until(
        EC.frame_to_be_available_and_switch_to_it(
            (
                By.XPATH,
                "//iframe[starts-with(@src, 'https://www.google.com/recaptcha/api2/anchor')]",
            )
        )
    )
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//div[@class='recaptcha-checkbox-border']")
        )
    ).click()
    driver.switch_to.default_content()
    WebDriverWait(driver, 10).until(
        EC.frame_to_be_available_and_switch_to_it(
            (
                By.XPATH,
                "//iframe[starts-with(@src, 'https://www.google.com/recaptcha/api2/bframe')]",
            )
        )
    )
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "solver-button"))
    ).click()

    time.sleep(2)
    if (
        "Your computer or network may be sending automated queries"
        in driver.page_source
    ):
        print("Captcha not solved :(. Automated queries detected")
        return
    driver.switch_to.default_content()
    time.sleep(2)

    if "captcha" in driver.page_source:
        print("Captcha not solved :(, captcha still there")


def defer_captcha(driver):
    # Extract what is after the "https://www.google.com/recaptcha/api2/anchor" and before the "?k=" in the src
    url = driver.find_element(
        By.XPATH,
        "//iframe[starts-with(@src, 'https://www.google.com/recaptcha/api2/anchor"
        "')]",
    ).get_attribute("src")
    print(f"{url=}")
    parsed_url = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    k_value = query_params.get("k", [""])[0]
    print(f"{k_value=}")


def main(driver):
    link = (
        "https://www.rentalcars.com/search-results?coordinates=44.825893%2C-0.556612&doDay=5&doHour=16&doMinute=0"
        "&doMonth=7&doYear=2024&driversAge=30&dropCoordinates=44.825893%2C-0.556612&dropFtsType=&dropLocation=-1"
        "&dropLocationIata=&dropLocationName=Gare%20de%20Bordeaux-Saint-Jean&ftsType=A&location=-1&locationIata"
        "=&locationName=Gare%20de%20Bordeaux-Saint-Jean&puDay=22&puHour=16&puMinute=0&puMonth=6&puYear=2024"
        "&filterCriteria_transmission=MANUAL&filterCriteria_depotLocationType=TRAINSTATION"
        "&filterCriteria_minimumFourDoors=true&filterCriteria_sortBy=PRICE&filterCriteria_sortAscending=true"
    )

    print("Loading page...")
    driver.get(link)
    print("Page loaded")
    time.sleep(10)
    if "captcha" in driver.page_source:
        print("Captcha detected, solving it...")
        solve_captcha(driver)
    elif "voitures disponibles" not in driver.page_source:
        print("No captcha but page not loaded idk what to do bro")
        return
    else:
        print("Page loaded successfully (no captcha)")
    page_source = driver.page_source

    soup = BeautifulSoup(page_source, "html.parser")

    car_div = "SM_f06d4876 SM_fa53da49 SM_aa802929 SM_471a28d9 SM_c47e926c SM_a0d97ebd SM_9cff3157 SM_69509825"
    price_div = "SM_3e7a1efe SM_a81e959c"

    alll = soup.find_all("div", class_=car_div)
    if not alll:
        send_message("Probable bug in the program, found no cars. Check the website.")
        return

    prices: list = []
    # find price in each div
    for div in alll:
        string_amount = div.find("div", class_=price_div).text
        string_amount = string_amount.replace(",", ".").replace("\u202f", "")
        float_amount = float(string_amount[:-2])
        if float_amount < TRIGGER_PRICE:
            prices.append(div)

    n_cars = len(prices)

    shortlink = pyshorteners.Shortener().tinyurl.short(link)
    if n_cars > 0:
        send_message(
            f"Found {n_cars} cars under {TRIGGER_PRICE}€ @times42"
            f"The cheapest one costs {prices[0].find('div', class_=price_div).text}"
            f"\n{shortlink}"
        )
    else:
        send_message(f"No cars found under {TRIGGER_PRICE}€")


if __name__ == "__main__":
    options = uc.ChromeOptions()
    # start maximized
    options.add_argument(f"--load-extension={os.path.abspath('buster')}")
    # add user agent

    with uc.Chrome(options=options) as driver:
        driver.maximize_window()
        # solve_captcha(driver)
        main(driver)
