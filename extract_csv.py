import os
import csv
from io import StringIO
from datetime import datetime

import pytz
import falcon
import pugsql

import db

# define the local time zone
LOCAL_TZ = pytz.timezone('Europe/Stockholm')

db.init()


class DataResource:
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = 'text/html'
        resp.text = """
        <html>
        <head><title>Sensor Data Extraction</title></head>
        <body>
            <h1>Sensor Data Extraction</h1>
            <form action="/extract/extract_csv" method="get">
                Start Date: <input type="datetime-local" name="start_date"><br>
                End Date: <input type="datetime-local" name="end_date"><br>
                <input type="submit" value="Extract Data">
            </form>
        </body>
        </html>
        """


class ExtractDataResource:
    def on_get(self, req, resp):
        start_date = req.get_param('start_date')
        end_date = req.get_param('end_date')

        # Convert dates to Unix timestamps
        start_timestamp = int(datetime.strptime(start_date, '%Y-%m-%dT%H:%M').timestamp())
        end_timestamp = int(datetime.strptime(end_date, '%Y-%m-%dT%H:%M').timestamp())

        # Retrieve data from the database based on the date range
        data = db.queries.extract_data(start_timestamp=start_timestamp, end_timestamp=end_timestamp)

        # Create a CSV response
        output = StringIO()
        csv_writer = csv.writer(output)
        csv_writer.writerow(['read_time', 'reactor', 'vol', 'h2', 'co2', 'temp', 'pressure', 'humidity', 'comment'])

        # iterate over each row in the data, format "read_time," replace "U" with "", and write it to the csv
        for row in data:
            # Convert Unix timestamp to local time
            local_time = datetime.utcfromtimestamp(row['read_time']).replace(tzinfo=pytz.utc).astimezone(LOCAL_TZ)
            row['read_time'] = local_time.strftime('%Y-%m-%d %H:%M:%S')
            cleaned_row = [str(value).replace("U", "") if value == "U" else value for value in row.values()]
            csv_writer.writerow(cleaned_row)

        resp.content_type = 'text/csv'
        resp.body = output.getvalue()
        resp.status = falcon.HTTP_200


# create a falcon api instance
app = falcon.App()
app.add_route('/extract', DataResource()) # url for the web page
app.add_route('/extract/extract_csv', ExtractDataResource()) # url for the cgi endpoint

if __name__ == '__main__':
    import wsgiref.simple_server
    httpd = wsgiref.simple_server.make_server('', 8000, app)
    httpd.serve_forever()
