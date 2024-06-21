from jinja2 import Environment, FileSystemLoader
import datetime
import argparse



timestamp = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z')
print("Give the trip a name. This can contain spaces")
title = input()


print("give the trip a short name using hyphens and no spaces")
short_name = input()

print("What date did the trip take place? Use the format `1-22-24` for the date")
short_date = input()

print("What date did the trip take place? Use the format `June 12th, 2024` for the date")
long_date = input()

print("paste the text of the trip report now")
report_text = input()


file_loader = FileSystemLoader('templates')
env = Environment(loader=file_loader)
template = env.get_template('trip_report.j2')
trip_context = {
    'timestamp': timestamp,
    'title': title,
    'short_name': short_name,
    'short_date': short_date,
    'long_date': long_date,
    'report_text': report_text,
}

trip_output = template.render(trip_context)

with open(f"../content/outdoor trip reports/{ short_name }-{ short_date }.md", 'w') as f:
    f.write(trip_output)

##############

template = env.get_template('gallery.j2')
gallery_context = {
    'timestamp': timestamp,
    'title': title,
    'long_date': report_text,
}

gallery_output = template.render(gallery_context)

with open(f"../content/outdoor trip reports/galleries/{ short_name }-gallery.md", 'w') as f:
    f.write(gallery_output)
