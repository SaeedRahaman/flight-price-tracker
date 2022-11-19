from selenium import webdriver
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

from datetime import datetime
import argparse
from typing import Tuple
import logging as l

from search_html import find_flight_info, write_html
from send_email import send
from save_data import save_csv

from selenium.webdriver.remote.remote_connection import LOGGER
LOGGER.setLevel(l.WARNING)

def search_flights(l: l.Logger, departure: str, destination: str, depart_date: str, return_date: str) -> Tuple[pd.DataFrame, pd.DataFrame]:

    url = f"https://www.jetblue.com/booking/flights?from={departure}&to={destination}&depart={depart_date}&return={return_date}&isMultiCity=false&noOfRoute=1&lang=en&adults=1&children=0&infants=0&sharedMarket=false&roundTripFaresFlag=false&usePoints=false"
    browser_options = Options()
    browser_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=browser_options)
    driver.set_window_size(1920, 1080)

    driver.get(url)

     # accept all cookies
    WebDriverWait(driver,10).until(EC.frame_to_be_available_and_switch_to_it((By.CLASS_NAME, 'truste_popframe')))
    WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[8]/div[1]/div/div[3]/a[1]"))).click()

    # grab html data for departing flights
    try: 
        # select Blue tier
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="auto-fare-code-1"]'))).click()

        # select stop drop down
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '/html/body/jb-app/div/jb-fares/div[3]/div[1]/div/div/div[2]/jb-flight-details/div[2]/div[1]/div[3]/div[1]/div[1]/jb-flights-filter/jb-filters-group/div/div/div/jb-filters-collapsible/div/jb-filters-wrapper[1]/div/div/jb-filters-button/button'))).click()

        # select nonstop
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '/html/body/jb-app/div/jb-fares/div[3]/div[1]/div/div/div[2]/jb-flight-details/div[2]/div[1]/div[3]/div[1]/div[1]/jb-flights-filter/jb-filters-group/div/div/div/jb-filters-collapsible/div/jb-filters-wrapper[1]/div/jb-flyout-inner/jb-filters-content/div/div[2]/div[2]/div[1]/jb-checkbox/label/div/span[2]'))).click()

        # select apply
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '/html/body/jb-app/div/jb-fares/div[3]/div[1]/div/div/div[2]/jb-flight-details/div[2]/div[1]/div[3]/div[1]/div[1]/jb-flights-filter/jb-filters-group/div/div/div/jb-filters-collapsible/div/jb-filters-wrapper[1]/div/jb-flyout-inner/jb-filters-content/div/div[3]/jb-button-mobile-sticky/button/div/div'))).click()

    except Exception as e:
        l.error("could not select non stop flights")
        return pd.DataFrame(), pd.DataFrame()
    
    l.info("getting departing flights")

    try:
        html = driver.page_source
        write_html(html, "departure.html")
        departures, lowest_index = find_flight_info(html, l)

        jb = driver.find_elements(By.TAG_NAME, "jb-flight-detail-item")
        jb[lowest_index].click()
    
    except Exception as e:
        l.error(f"could not find departing flight information for selected date \n{e}")
        return pd.DataFrame(), pd.DataFrame()

    # get return flights
    try:
        # click on best flight
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, f'//*[@id="auto-depart-time-{lowest_index}"]'))).click()
    
    except Exception as e:
        l.error("could not click to get return flights")
        return pd.DataFrame(), pd.DataFrame()

    l.info("getting return flights")

    try:
        html = driver.page_source
        driver.quit()
        write_html(html, "returns.html")

        returns, lowest_index = find_flight_info(html, l)
    
    except Exception as e:
        l.error(f"could not find return flight information for selected date \n{e}")
        return pd.DataFrame(), pd.DataFrame()

    l.info("done")
    return departures, returns


def flight(depart_code: str, return_code: str, depart_date: str, return_date: str) -> None:
    # set logging config
    filename = f"output-{depart_date}-{return_date}.log"
    l.basicConfig(filename=filename, level=l.INFO, filemode="w")

    MAX_RETRIES = 5  
    success = False
    retries = 0
    l.info(f"running at time = {datetime.now()}")
    l.info(f"depart date = {depart_date} and return date = {return_date}")

    # retry logic
    while not success and retries < MAX_RETRIES:

        # try to get flight data
        try:
            departures, returns = search_flights(l, depart_code, return_code, depart_date, return_date)

            # check that flight data was received
            if len(departures) > 0 and len(returns) > 0:
                save_csv(departures, depart_date, "departures.csv")
                save_csv(returns, return_date, "returns.csv")
                l.info("data saved")

                l.info("Sending Email...")
                # l.shutdown()
                send(departures, returns, depart_date, return_date, filename)
                success = True
            
            else:
                l.error(f"DataFrames are empty. Retry #{retries} \n")
                retries += 1
                
        # accept exception and increment retry count
        except Exception as e:
            l.error(f"Error getting data. Retry #{retries} \n{e}")
            retries += 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-depart_date", help="depart date")
    parser.add_argument("-return_date", help="return date")
    parser.add_argument("-depart_code", help="airport code for departure")
    parser.add_argument("-return_code", help="airport code for return")

    args = parser.parse_args()
    flight(args.depart_code, args.return_code, args.depart_date, args.return_date)