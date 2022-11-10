import pandas as pd
from os import listdir

def save_csv(l, departures, returns, ddate, rdate):
    departures['Date'] = ddate
    returns['Date'] = rdate

    files = listdir()

    if "departures.csv" not in files or "returns.csv" not in files:
        departures.to_csv("departures.csv", index=False)
        returns.to_csv("returns.csv", index=False)

    else:
        d = pd.read_csv("departures.csv")
        r = pd.read_csv("returns.csv")

        d = pd.concat([d, departures], axis=0)
        r = pd.concat([r, returns], axis=0)

        d.to_csv("departures.csv", index=False)
        r.to_csv("returns.csv", index=False)

    l.info("data saved")

    return

if __name__ == "__main__":
    save_csv(pd.DataFrame(), pd.DataFrame(), "Mon Dec 22", "Fri Jan 6")