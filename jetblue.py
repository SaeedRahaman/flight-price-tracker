from selenium import webdriver
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from time import sleep

from datetime import datetime
import argparse
from typing import Tuple
import logging as l

from search_html import find_flight_info, write_html
from send_email import send
from save_data import save_csv
import config

from selenium.webdriver.remote.remote_connection import LOGGER
LOGGER.setLevel(l.WARNING)

def search_flights(l: l.Logger, departure: str, destination: str, depart_date: str, return_date: str) -> Tuple[pd.DataFrame, pd.DataFrame]:

    url = f"https://www.jetblue.com/booking/flights?from={departure}&to={destination}&depart={depart_date}&return={return_date}&isMultiCity=false&noOfRoute=1&lang=en&adults=1&children=0&infants=0&sharedMarket=false&roundTripFaresFlag=false&usePoints=false"

    s = Service("./chromedriver")
    driver = webdriver.Chrome(service=s)
    driver.set_window_size(1920, 1080)

    driver.get(url)

    # accept all cookies
    WebDriverWait(driver,10).until(EC.frame_to_be_available_and_switch_to_it((By.CLASS_NAME, 'truste_popframe')))
    WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[8]/div[1]/div/div[3]/a[1]"))).click()
    
    l.info("getting departing flights")
    sleep(20)

    try:
        html = driver.page_source
        write_html(html, "departure.html")
        departures, lowest_index = find_flight_info(html, l)

        xpath = f" /html/body/jb-app/div/jb-fares/div[3]/div[1]/div/div[1]/div/jb-flight-details/div[2]/div[2]/jb-flight-detail-item[{lowest_index}]/div[1]/div/jb-itinerary-panel/div/div/div/div/div/div[3]/div/jb-fare-class-card/div/div/jb-offer-block/button"

        # click on button
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()

        # click on fare type
        fare_xpath = f"/html/body/jb-app/div/jb-fares/div[3]/div[1]/div/div[1]/div/jb-flight-details/div[2]/div[2]/jb-flight-detail-item[{lowest_index}]/div[1]/div/jb-itinerary-panel/jb-expandable-container/div/jb-expandable-section/div/jb-fare-type-tiles-panel/div/div[2]/jb-fare-type-tile/div/div[1]"
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, fare_xpath))).click()

    except Exception as e:
        l.error(f"could not click on departing flight selection \n{e}")
        return pd.DataFrame(), pd.DataFrame()

    l.info("getting return flights")
    sleep(10)

    try:
        html = driver.page_source
        write_html(html, "returns.html")

        returns, lowest_index = find_flight_info(html, l)
    
    except Exception as e:
        l.error(f"could not find return flight information for selected date \n{e}")
        return pd.DataFrame(), pd.DataFrame()

    driver.quit()
    l.info("done")
    return departures, returns


def flight(depart_code: str, return_code: str, depart_date: str, return_date: str) -> bool:
    # set logging config
    filename = f"output-{depart_date}-{return_date}.log"
    l.basicConfig(filename=filename, level=l.INFO, filemode="w")

    MAX_RETRIES = 1
    retries = 0
    l.info(f"running at time = {datetime.now()}")
    l.info(f"depart date = {depart_date} and return date = {return_date}")

    # retry logic
    while retries < MAX_RETRIES:

        # try to get flight data
        departures, returns = search_flights(l, depart_code, return_code, depart_date, return_date)

        # check that flight data was received
        if len(departures) > 0 and len(returns) > 0:
            save_csv(departures, depart_date, "departures.csv")
            save_csv(returns, return_date, "returns.csv")
            l.info("data saved")

            l.info("Sending Email...")
            send(departures, returns, depart_date, return_date, filename)
            return True
        
        else:
            l.error(f"a dataframe is emtpy. retry #{retries} \n")
            retries += 1
                

    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-depart_date", help="depart date")
    parser.add_argument("-return_date", help="return date")
    parser.add_argument("-depart_code", help="airport code for departure")
    parser.add_argument("-return_code", help="airport code for return")

    args = parser.parse_args()
    flight(args.depart_code, args.return_code, args.depart_date, args.return_date)