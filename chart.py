from dateutil import parser
from datetime import timedelta
import requests
from bs4 import BeautifulSoup

def get_date(prompt, date_only = False):
    while True:
        try:
            date = input(f"{prompt}:   ")
            date = parser.parse(date)
            break
        except:
            print("I'm sorry, I couldn't understand that. Please make sure your date is in a valid format (e.g. YYYY-MM-DD)")

    if date_only:
        return date.date()

    return date

def get_chart_source(date):
    url = f"https://www.officialcharts.com/charts/singles-chart/{date:%Y%m%d}/7501/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    chart_elements = soup.find_all("div", class_="chart-item")
    
    for item in chart_elements:
        if "chart-ad" in item["class"]:
            continue

        (title, artist) = parse_chart_item(item)
        print(f"Found {title} by {artist}!")

def parse_chart_item(item):
    description = item.find_all("div", class_="description")[0]
    links = description.find_all("a")
    title = links[0].select("span")[1].text
    artist = links[1].text

    return (title, artist)

date = get_date("Please enter the date you wish to check the charts for", True)
print(f"Searching for charts for week beginning {date}...")
get_chart_source(date)
