import requests
import json
from bs4 import BeautifulSoup

def get_chart_data(date):
    url = f"https://www.officialcharts.com/charts/singles-chart/{date:%Y%m%d}/7501/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    chart_json = soup.find(id="__NUXT_DATA__")
    chart_json = json.loads(chart_json.text)
    chart_elements = soup.find_all("div", class_="chart-item")
    chart_id = None
    items = []
    
    for item in chart_elements:
        if "chart-ad" in item["class"]:
            continue

        if chart_id is None:
            chart_id = item['data-item'].split('-')[1]

        parsed_chart = parse_chart_item(item)
        chart_item_id = find_chart_id(chart_json, *parsed_chart)
        items.append((*parsed_chart, chart_id, chart_item_id))

    return items

def find_chart_id(haystack, title, artist):
    for i in range(720, len(haystack)):
        if haystack[i] == title: #and haystack[i + 2] == artist:
            try:
                _ = int(haystack[i]) #e.g. Taylor Swift's 22
                if haystack[i + 2] != artist:
                    continue
            except:
                pass #non-numeric title
            return int(haystack[i - 1])

    return None          

def parse_chart_item(item):
    description = item.find_all("div", class_="description")[0]
    links = description.find_all("a")
    title = links[0].select("span")[1].text
    artist = links[1].text

    return (title, artist)

def get_isrc(chart_id, item_id):
    data = requests.get(f"https://backstage.officialcharts.com/ajax/charted-item/chart/{chart_id}/{item_id}").json()
    return data['catNo']
