from bs4 import BeautifulSoup
import pandas as pd
import logging
from typing import Tuple

def find_detail(soup: str, element: str, element_id: Tuple[str, None], length: int) -> list:
    l = []

    # price info is wrapped in <span> tags with no id attributes
    if element_id == None:
        info = soup.find_all(element)
        for tag in info:
            
            tag = tag.text
            tag = tag.strip()

            try:
                tag = int(tag)
                l.append(tag)
            except Exception as e:
                pass
        
        return l

    for i in range(length):

        # find all elements with id
        # for arrival html, the 0 index includes flight information that was selected
        info = soup.find_all(element, {"id": f"{element_id}-{i}"})

        for data_point in info:

            # data is inside a single div
            if len(data_point.contents) == 1:
                data_point = data_point.contents[0]

            # some data is wrapped in a span tag; need to get span contents
            elif len(data_point.contents) > 1:
                data_point = data_point.contents[0].contents[0]

            data_point = data_point.strip()
            l.append(data_point)

    return l


def find_flight_info_helper(flight_info: dict, key: str, soup: str, element: str, element_id: Tuple[str, None], num_flights: int, l: logging.Logger) -> dict:

    try:
        flight_info[key] = find_detail(soup, element, element_id, num_flights)

    except Exception as e:
        l.error(f"error finding information for {key} and id {element_id} \n{e}")
    
    return flight_info


def write_html(html: str, filename: str) -> None:
    soup = BeautifulSoup(html, "html.parser")

    with open(filename, "w") as f:
        f.write(soup.prettify())
    return

def print_dict(d: dict, l: logging.Logger) -> None:
    for key, val in d.items():
        l.info(f"{key}, {val}, {len(val)}")
    l.info("\n")
    return

def find_flight_info(soup: BeautifulSoup, l: logging.Logger) -> Tuple[pd.DataFrame, pd.DataFrame]:

    soup = BeautifulSoup(soup, "html.parser")

    num_flights = len(soup.find_all("jb-flight-detail-item"))

    flight_info = {}

    flight_info = find_flight_info_helper(flight_info, "Depart Time", soup, "div", "auto-depart-time", num_flights, l)
    flight_info = find_flight_info_helper(flight_info, "Depart City", soup, "div", "auto-depart-from", num_flights, l)
    flight_info = find_flight_info_helper(flight_info, "Arrival Time", soup, "div", "auto-arrival-time", num_flights, l)
    flight_info = find_flight_info_helper(flight_info, "Arrival City", soup, "div", "auto-arrive-to", num_flights, l)
    flight_info = find_flight_info_helper(flight_info, "Duration", soup, "div", "auto-flight-duration", num_flights, l)
    flight_info = find_flight_info_helper(flight_info, "Stops", soup, "span", "auto-flight-stops", num_flights, l)
    flight_info = find_flight_info_helper(flight_info, "Price", soup, "label", None, num_flights, l)

    # this scenario happens on return flights
    # ignore the first value in other arrays
    if len(flight_info["Price"]) != len(flight_info["Depart Time"]):
        for key, value in flight_info.items():
            if key != "Price":
                flight_info[key] = value[1:]

    # print_dict(flight_info, l)

    # flight prices are on basic tier
    # add 30$ to price to simulate blue tier
    # blue tier is worth the extra cost for value
    flight_info["Price"] = [price + 30 for price in flight_info["Price"]]

    # print_dict(flight_info, l)

    flights = pd.DataFrame(flight_info)
    # print(flights.to_string(index=False))

    # only keep non stop flights
    flights = flights.loc[flights["Stops"] == "Nonstop"].copy()

    lowest_fare = flights.loc[flights["Price"] == flights["Price"].min()]
    lowest_fare = lowest_fare.loc[flights["Duration"] == lowest_fare["Duration"].min()]

    return flights, lowest_fare.index[0]

if __name__ == "__main__":
    with open("returns.html", "r") as f:
        html = f.read()
        logging.basicConfig(filename="test.log", level=logging.INFO, filemode="w")
        departures, index = find_flight_info(html, logging)

        departures.to_csv("depatures.csv", index=False)
        print(f"index = {index}")