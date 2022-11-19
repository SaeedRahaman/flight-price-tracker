import pandas as pd
from os import listdir

def save_csv(csv: pd.DataFrame, date: str, filename: str) -> None:
    csv['Date'] = date

    files = listdir()

    if filename not in files:
        csv.to_csv(filename, index=False)
    
    else:
        df = pd.read_csv(filename)
        df = pd.concat([df, csv], axis=0)
        df.to_csv(filename, index=False)

    return