import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pretty_html_table import build_table
import pandas as pd
import config

# input is two dataframes
def send(departures: pd.DataFrame, returns: pd.DataFrame, depart_date: str, return_date: str, filename: str) -> None:

    MAX_RETRIES = 5
    retries = 0
    success = False

    departures = build_table(departures, "blue_light")
    returns = build_table(returns, "blue_light")

    logs = None
    with open(filename, "r") as f:
        logs = f.readlines()

    log_html = "".join(l + "<br>" for l in logs)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Flight Data for {depart_date} and {return_date}"
    msg["From"] = config.EMAIL
    msg["To"] = config.EMAIL

    html = f"""
            <html>
                <head></head>
                <body>
                    <h1>Departures</h1>
                    {departures}
                    <br>
                    <h1>Returns</h1>
                    {returns}
                    <br>
                    <br>
                    {log_html}
                </body>
            </html>
            """

    body = MIMEText(html, "html")
    msg.attach(body)
    msg = msg.as_string()

    while retries < MAX_RETRIES and not success:

        try:
            smtp_server = smtplib.SMTP('smtp.mail.me.com', 587)
            smtp_server.starttls()
            smtp_server.login(config.EMAIL, config.PASSWORD)
            
            # print(code)
            smtp_server.sendmail(from_addr=config.EMAIL, to_addrs=config.EMAIL, msg=msg)
            smtp_server.quit()

            success = True

        except Exception as e:
            retries += 1

    return