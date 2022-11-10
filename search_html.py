from bs4 import BeautifulSoup
import pandas as pd
from locale import atof

def find_detail(soup, element, element_id, length):
    l = []

    # price info is wrapped in <ins> tags with no id attributes
    if element == "ins":
        info = soup.find_all(element)
        for tag in info:
            tag = tag.text
            tag = tag.replace('\n', '')
            tag = tag.replace(',', '')
            tag = tag.strip()

            l.append(tag)
        
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


def find_flight_info_helper(flight_info, key, soup, element, element_id, num_flights, l):

    try:
        flight_info[key] = find_detail(soup, element, element_id, num_flights)

    except Exception as e:
        l.error(f"error finding information for {key} and id {element_id} \n{e}")
    
    return flight_info


def write_html(html, filename):
    soup = BeautifulSoup(html, "html.parser")

    with open(filename, "w") as f:
        f.write(soup.prettify())
    return

def print_dict(d):
    for key, val in d.items():
        print(key, val, len(val))
    print()
    return

def find_flight_info(soup, l):

    soup = BeautifulSoup(soup, "html.parser")

    num_flights = len(soup.find_all("jb-flight-detail-item"))

    flight_info = {}

    flight_info = find_flight_info_helper(flight_info, "Depart Time", soup, "div", "auto-depart-time", num_flights, l)
    flight_info = find_flight_info_helper(flight_info, "Depart City", soup, "div", "auto-depart-from", num_flights, l)
    flight_info = find_flight_info_helper(flight_info, "Arrival Time", soup, "div", "auto-arrival-time", num_flights, l)
    flight_info = find_flight_info_helper(flight_info, "Arrival City", soup, "div", "auto-arrive-to", num_flights, l)
    flight_info = find_flight_info_helper(flight_info, "Duration", soup, "div", "auto-flight-duration", num_flights, l)
    flight_info = find_flight_info_helper(flight_info, "Flight Number", soup, "div", "auto-flight-number", num_flights, l)
    flight_info = find_flight_info_helper(flight_info, "Stops", soup, "span", "auto-flight-stops", num_flights, l)
    flight_info = find_flight_info_helper(flight_info, "Price", soup, "ins", None, num_flights, l)
    flight_info = find_flight_info_helper(flight_info, "Tier", soup, "div", "auto-flight-fare-code", num_flights, l)

    # remove $ sign and convert strings to int
    for i, f in enumerate(flight_info["Price"]):
        flight_info["Price"][i] = int(f[1:])

    # print_dict(flight_info)

    flights = pd.DataFrame(flight_info)
    # print(flights.to_string(index=False))
    # print()

    lowest_fare = flights.loc[ (flights["Stops"] == "Nonstop") & (flights["Price"] == flights["Price"].min()) ]
    lowest_fare = lowest_fare.loc[flights["Duration"] == lowest_fare["Duration"].min()]
    # print(lowest_fare)

    return flights, lowest_fare.index[0]