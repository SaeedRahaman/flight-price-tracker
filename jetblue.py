from selenium import webdriver
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

from time import sleep
from datetime import datetime
import argparse
import logging as l

from search_html import find_flight_info, write_html
from send_email import send
from save_data import save_csv

from selenium.webdriver.remote.remote_connection import LOGGER
LOGGER.setLevel(l.WARNING)

def browse_flights(l, departure="Orlando, FL (MCO)", destination="Newark, NJ (EWR)", arrive_date="Thu Dec 22", leave_date="Fri Jan 6"):

    browser_options = Options()
    browser_options.add_argument("--no-sandbox")
    # driver = webdriver.Chrome(executable_path="./chromedriver", options=browser_options)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=browser_options)
    driver.set_window_size(1920, 1080)

    driver.get("https://www.jetblue.com/")

    # accept all cookies
    WebDriverWait(driver,10).until(EC.frame_to_be_available_and_switch_to_it((By.CLASS_NAME, 'truste_popframe')))
    WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[8]/div[1]/div/div[3]/a[1]"))).click()

    # switch back to default window context
    driver.switch_to.default_content()

    # wait for browser to load content
    sleep(5)

    # input destination
    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="jb-autocomplete-4-search"]'))).click()
        driver.find_element(By.XPATH, '//*[@id="jb-autocomplete-4-search"]').send_keys(destination)
        driver.find_element(By.XPATH, '//*[@id="jb-autocomplete-4-search"]').send_keys(Keys.ENTER)
        l.info("input destination")
    except TimeoutException:
        l.info("retrying destination")

        # sometimes id's are different
        try:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="jb-autocomplete-2-search"]'))).click()
            driver.find_element(By.XPATH, '//*[@id="jb-autocomplete-2-search"]').send_keys(destination)
            driver.find_element(By.XPATH, '//*[@id="jb-autocomplete-2-search"]').send_keys(Keys.ENTER)
        except Exception as e:
            l.error(f"could not input destination \n{e}")
            return pd.DataFrame(), pd.DataFrame()

    # input arrival date
    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="jb-date-picker-input-id-2"]'))).click()
        driver.find_element(By.XPATH, '//*[@id="jb-date-picker-input-id-2"]').send_keys(arrive_date)
        l.info("input arrival date")
    except TimeoutException:
        l.info("retrying arrival date")

        # sometimes id's are different
        try: 
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="jb-date-picker-input-id-0"]'))).click()
            driver.find_element(By.XPATH, '//*[@id="jb-date-picker-input-id-0"]').send_keys(arrive_date)
        except Exception as e:
            l.error(f"could not input arrival date \n{e}")
            return pd.DataFrame(), pd.DataFrame()

    # input leave date
    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="jb-date-picker-input-id-3"]'))).click()
        driver.find_element(By.XPATH, '//*[@id="jb-date-picker-input-id-3"]').send_keys(leave_date)
        l.info("input leave date")
    except TimeoutException:
        l.info("retrying leave date")

        # sometimes id's are different
        try: 
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="jb-date-picker-input-id-1"]'))).click()
            driver.find_element(By.XPATH, '//*[@id="jb-date-picker-input-id-1"]').send_keys(leave_date)
        except Exception as e:
            l.error(f"could not input leave date \n{e}")
            return pd.DataFrame(), pd.DataFrame()

    # submit search query
    try:
        final_button = "/html/body/jb-app/main/jb-basic-template/jb-renderer-template/jb-section-header-container/div/div[1]/div/jb-section-container/div/div/jb-renderer-template/jb-tab-component-container/div/jb-tabs/section/div/jb-tab-panel[1]/div/jb-renderer-template/dot-booker-air/div/dot-booker-air-v2/form/div/div[2]/div[3]/div/button/span/span"

        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, final_button))).click()
        l.info("search initiated...")

    # error with submitting query
    except Exception as e:
        l.error(f"could not submit query \n{e}")
        return pd.DataFrame(), pd.DataFrame()

    # grab html data for departing flights
    try: 
        # select Blue tier
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="auto-fare-code-1"]'))).click()

        # WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/jb-app/div/jb-fares/div[3]/div[1]/div/div/div[2]/jb-flight-details")))

        l.info("Getting departing flights")

        html = driver.page_source
        write_html(html, "departure.html")
        departures, lowest_index = find_flight_info(html, l)

        jb = driver.find_elements(By.TAG_NAME, "jb-flight-detail-item")
        jb[lowest_index].click()
    
    except Exception as e:
        l.error(f"could not find departing flight information for selected dates \n{e}")
        return pd.DataFrame(), pd.DataFrame()

    sleep(5)

    # get return flights
    try:
        # click on best flight
        driver.find_element(By.XPATH, f'//*[@id="auto-depart-time-{lowest_index}"]').click()

        # WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "/html/body/jb-app/div/jb-fares/div[3]/div[1]/div/div/div[2]/jb-flight-details")))

        l.info("Getting return flights")

        html = driver.page_source
        driver.quit()
        write_html(html, "returns.html")

        returns, lowest_index = find_flight_info(html, l)
    
    except Exception as e:
        l.error(f"could not find return flight information for selected dates \n{e}")
        return pd.DataFrame(), pd.DataFrame()

    l.info("done")
    return departures, returns
    

def flight(depart_date: str, return_date: str) -> None:
    # set logging config
    filename = f"output-{depart_date}-{return_date}.log"
    filename = filename.replace(' ', '-')
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
            departures, returns = browse_flights(l, arrive_date=depart_date, leave_date=return_date)

            # check that flight data was received
            if len(departures) > 0 and len(returns) > 0:
                save_csv(l, departures, returns, depart_date, return_date)
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
    parser.add_argument("-d")
    parser.add_argument("-r")

    # Parse and print the results
    args = parser.parse_args()
    
    flight(args.d, args.r)