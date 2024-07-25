from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
from geopy.geocoders import Nominatim



timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z')
file_loader = FileSystemLoader('templates')
env = Environment(loader=file_loader)

def get_long_date(timestamp):
  ''' timestamp should be formatted as 1-12-24
  with 1-12-24 being january 12th, 2024''' 
  date_format = '%m-%d-%y'
  parsed_date = datetime.strptime(timestamp, date_format)
  month = parsed_date.strftime("%B")
  year = parsed_date.strftime("%Y")
  day = parsed_date.strftime("%-d")
  long_date = f"{month} {day}, {year}"
  return long_date

def get_pids(name):
  name_list = name.split()
  name_search_string = '%20'.join(name_list)
  search_url = f"https://www.peakbagger.com/search.aspx?tid=M&ss={name_search_string}"
  r = requests.get(search_url)
  soup = BeautifulSoup(r.content, 'html.parser')
  pattern = re.compile(r'pid=(\d{3,})')
  rows = soup.find_all(lambda row: row.name == 'tr' and 'Peak' in row.text)
  pid_values = []
  for row in rows:
    match = pattern.search(str(row))
    if match and match.group(1) not in pid_values:
      pid_values.append(match.group(1))
  return(pid_values)

def lookup_pid(pid):
  peak_url = f"https://www.peakbagger.com/peak.aspx?pid={pid}"
  r = requests.get(peak_url)
  soup = BeautifulSoup(r.content, 'html.parser')
  peak_name = soup.find_all("h1")[0].text
  peak_elevation_feet = re.findall(r"Elevation: ([\d,]+) feet", str(soup.find_all(lambda row: row.name == 'tr' and 'Elevation:' in row.text)[0]))[0]
  peak_prominence_feet = re.findall(r"Prominence: ([\d,]+) ft", str(soup.find_all(lambda row: row.name == 'tr' and 'Prominence:' in row.text)[0]))[0]
  peak_coordinates = re.findall(r'-?\d{1,2}\.\d+, -?\d{1,3}\.\d+', str(soup.find_all(lambda row: row.name == 'tr' and 'Latitude/Longitude' in row.text)[0]))[0]
  #peak_country = re.findall(r"Country\s+(.+)", str(soup.find_all(lambda row: row.name == 'tr' and 'Country' in row.text)[0]))
  geolocator = Nominatim(user_agent="peak_locator")
  peak_location =  location = geolocator.reverse(peak_coordinates)
  peak = {"name": peak_name,
          "elevation_feet": peak_elevation_feet,
          "prominence_feet": peak_prominence_feet,
          "coordinates": peak_coordinates,
          "location": peak_location
         }
  ## todo:
  ## - add values for isolation, country, state, county, ownership
  return peak

print("What is the name of the peak you're looking for?")
peak_name = input()

pids = get_pids(peak_name)
for pid in pids:
  peak_info = lookup_pid(pid)
  name = peak_info["name"]
  elevation_ft = peak_info["elevation_feet"]
  location = peak_info["location"]
  print(f"Is this the peak you're looking for? \n{name}, {elevation_ft}'? \nlocated at: {location} \n \ny or n?")
  response = input()
  if response == "n":
    pass
  elif response == "y":
    selected_peak = pid
    peak_elevation = elevation_ft
    break
print(selected_peak)

print("What date did the trip take place? Use the format `1-22-24` for the date")
short_date = input()

long_date = get_long_date(short_date)

print("paste the text of the trip report now")
report_text = input()


trip_context = {
    'timestamp': timestamp,
    'peak_name': peak_name,
    'short_date': short_date,
    'long_date': long_date,
    'report_text': report_text,
    'peak_elevation': peak_elevation
}
template = env.get_template('trip_report.j2')
trip_output = template.render(trip_context)
peak_name_shortened = peak_name.replace(" ", "-")
with open(f"../content/outdoor trip reports/{ peak_name_shortened }-{ short_date }.md", 'w') as f:
    f.write(trip_output)
template = env.get_template('gallery.j2')
gallery_context = {
    'timestamp': timestamp,
    'long_date': long_date,
    'short_date': short_date,
}

gallery_output = template.render(gallery_context)

with open(f"../content/outdoor trip reports/galleries/{ peak_name_shortened }-gallery.md", 'w') as f:
    f.write(gallery_output)

