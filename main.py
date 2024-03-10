import pyshorteners
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from telegram_notifier import send_message
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

TRIGGER_PRICE = 520


def main():
    # initialize an instance of the chrome driver (browser)

    # visit your target site
    link = "https://www.rentalcars.com/search-results?coordinates=44.825893%2C-0.556612&doDay=5&doHour=16&doMinute=0&doMonth=7&doYear=2024&driversAge=30&dropCoordinates=44.825893%2C-0.556612&dropFtsType=&dropLocation=-1&dropLocationIata=&dropLocationName=Gare%20de%20Bordeaux-Saint-Jean&ftsType=A&location=-1&locationIata=&locationName=Gare%20de%20Bordeaux-Saint-Jean&puDay=22&puHour=16&puMinute=0&puMonth=6&puYear=2024&filterCriteria_transmission=MANUAL&filterCriteria_depotLocationType=TRAINSTATION&filterCriteria_minimumFourDoors=true&filterCriteria_sortBy=PRICE&filterCriteria_sortAscending=true"

    with uc.Chrome() as driver:
        driver.get(link)
        print("Waiting for page to load")
        WebDriverWait(driver, 20).until(
            EC.text_to_be_present_in_element((By.CLASS_NAME, 'SM_3e7a1efe'), 'voitures disponibles'))
        print("Page loaded or to")
        page_source = driver.page_source

    soup = BeautifulSoup(page_source, "html.parser")

    car_div = "SM_f06d4876 SM_fa53da49 SM_aa802929 SM_471a28d9 SM_c47e926c SM_a0d97ebd SM_9cff3157 SM_69509825"
    price_div = "SM_3e7a1efe SM_a81e959c"

    alll = soup.find_all("div", class_=car_div)
    if not alll:
        send_message("Probable bug in the program, found no cars. Check the website.")
        return

    cheap_cars: list = []
    # find price in each div
    for div in alll:
        string_amount = div.find("div", class_=price_div).text
        string_amount = string_amount.replace(",", ".").replace("\u202f", "")
        float_amount = float(string_amount[:-2])
        if float_amount < TRIGGER_PRICE:
            cheap_cars.append(div)

    n_cars = len(cheap_cars)

    shortlink = pyshorteners.Shortener().tinyurl.short(link)
    if n_cars > 0:
        send_message(f"Found {n_cars} cars under {TRIGGER_PRICE}€ @times42"
                     f"\n{shortlink}")
    else:
        send_message(f"No cars found under {TRIGGER_PRICE}€")


if __name__ == "__main__":
    main()
