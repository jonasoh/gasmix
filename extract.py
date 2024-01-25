# extract.py --
#   falcon web app for presenting and exporting data from the gas mixer/logger

from textwrap import dedent
from datetime import datetime

import falcon
import rrdtool
import pandas as pd

import db
import rrd

# define the local time zone
LOCAL_TZ = 'Europe/Stockholm'

# web page for showing graphs
INDEX_PAGE = dedent('''\
    <meta http-equiv="refresh" content="60">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/purecss@3.0.0/build/pure-min.css" integrity="sha384-X38yfunGUhNzHpBaEBsWLO+A0HDYOQi8ufWDkZ0k9e0eXz/tH3II7uKZ9msv++Ls" crossorigin="anonymous">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/purecss@3.0.0/build/grids-responsive-min.css">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <body>
        <div class="pure-g">
            <div class="pure-u-1">
                <div style="display: flex;">
                    <img src="{img}&reactor=0&width=400&height=800" class="pure-img" style="width: 33.33%;" />
                    <img src="{img}&reactor=1&width=400&height=800" class="pure-img" style="width: 33.33%;" />
                    <img src="{img}&reactor=2&width=400&height=800" class="pure-img" style="width: 33.33%;" />
                </div>
            </div>
            <div class="pure-u-1" style="display: flex; justify-content: center; align-items: center;">
                <p>
                    <a href="/?hours=4" class="pure-button">4 h</a>
                    <a href="/?hours=8" class="pure-button">8 h</a>
                    <a href="/?hours=24" class="pure-button">24 h</a>
                    <a href="/?hours=48" class="pure-button">48 h</a>
                    <a href="/?hours=72" class="pure-button">72 h</a>
                    <a href="/?hours=168" class="pure-button">1 w</a>
                    <a href="extract" class="pure-button" style="background: rgb(210, 196, 240)">Export data to TSV</a>
                </p>
            </div>
        </div>
    </body>''')

EXTRACT_PAGE = dedent("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/purecss@3.0.0/build/pure-min.css" integrity="sha384-X38yfunGUhNzHpBaEBsWLO+A0HDYOQi8ufWDkZ0k9e0eXz/tH3II7uKZ9msv++Ls" crossorigin="anonymous">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/purecss@3.0.0/build/grids-responsive-min.css">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Sensor Data Extraction</title>
    <body>
        <div class="pure-g">
        <div class="pure-u-1-5"></div>
        <div class="pure-u-3-5">
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                // Function to format the date in 'YYYY-MM-DDTHH:mm' format
                function formatDate(date) {
                const pad = (n) => n.toString().padStart(2, '0');
                return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
                }

                // Get the current date
                const currentDate = new Date();

                // Prefill end_date with the current date
                document.getElementById('end_date').value = formatDate(currentDate);

                // Calculate date minus 24 hours
                const startDate = new Date(currentDate);
                startDate.setHours(currentDate.getHours() - 24);

                // Prefill end_date with the current date minus 24 hours
                document.getElementById('start_date').value = formatDate(startDate);
            });
        </script>

        <form action="/extract/extract_tsv" method="get" class="pure-form pure-form-aligned" style="margin-top: 40px;">
            <fieldset>
                <legend>Sensor data extraction</legend>
                <div class="pure-control-group">
                    <label for="start_date">Start Date</label><input type="datetime-local" name="start_date" id="start_date">
                </div>
                <div class="pure-control-group">
                    <label for="end_date">End Date</label><input type="datetime-local" name="end_date" id="end_date">
                </div>
                <div class="pure-controls">
                    <button type="submit" class="pure-button pure-button-primary">Extract data</button>
                </div>
            </fieldset>
        </form>
        </div>
        <div class="pure-u-1-5"></div>
        </div>
    </body>
    </html>
    """)

db.init()

class IndexPageResource:
    def on_get(self, req, resp):
        hours = req.get_param_as_int('hours', default=None)
        if hours is None or hours < 0:
            page_content = INDEX_PAGE.format(img="/extract/rrdgraph?hours=4")
        else:
            # If the parameter is not supplied, display a default message
            page_content = INDEX_PAGE.format(img='/extract/rrdgraph?hours=' + str(hours))

        resp.content_type = 'text/html'
        resp.status = falcon.HTTP_200
        resp.text = page_content

class DataResource:
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = 'text/html'
        resp.text = EXTRACT_PAGE

class ExtractDataResource:
    def on_get(self, req, resp):
        start_date = req.get_param('start_date')
        end_date = req.get_param('end_date')

        # Convert dates to Unix timestamps
        start_timestamp = int(datetime.strptime(start_date, '%Y-%m-%dT%H:%M').timestamp())
        end_timestamp = int(datetime.strptime(end_date, '%Y-%m-%dT%H:%M').timestamp())

        # Retrieve data from the database based on the date range
        data = db.queries.extract_data(start_timestamp=start_timestamp, end_timestamp=end_timestamp)
        df = pd.DataFrame(data)

        # convert the 'read_time' column to datetime, localize it to the desired timezone, and format as human-readable
        df['read_time'] = pd.to_datetime(df['read_time'], unit='s').dt.tz_localize(LOCAL_TZ).dt.strftime('%Y-%m-%d %H:%M:%S')

        resp.content_type = 'text/tab-separated-values'
        resp.status = falcon.HTTP_200
        resp.body = df.to_csv(index=False, sep='\t')

class RRDGraphResource:
    def on_get(self, req, resp):
        # make variables from the request parameters to save some space
        req_vars = ['reactor', 'hours', 'width', 'height']
        for var in req_vars:
            globals()[var] = req.get_param_as_int(var)

        try:
            # Generate the graph and capture it as a binary image
            graph_binary = rrd.custom_rrd_graph(
                reactor=reactor if reactor else 0,                          # type: ignore
                duration=hours if hours is not None and hours > 0 else 4,   # type: ignore
                width=width if width else 600,                              # type: ignore
                height=height if height else 400)                           # type: ignore

        except rrdtool.OperationalError as e:
            resp.status = falcon.HTTP_500  # Internal Server Error
            resp.text = f"Error generating RRDtool graph: {str(e)}"
            return

        # Set the response content type to display the image
        resp.content_type = 'image/png'
        resp.data = graph_binary['image']

# create a falcon api instance
app = falcon.App()
app.add_route('/', IndexPageResource())
app.add_route('/extract', DataResource())                       # url for the tsv extractor
app.add_route('/extract/extract_tsv', ExtractDataResource())    # url for the cgi endpoint (sqlite->tsv)
app.add_route('/extract/rrdgraph', RRDGraphResource())          # url for the dynamically generated graph

# allow running from command line
if __name__ == '__main__':
    import wsgiref.simple_server
    httpd = wsgiref.simple_server.make_server('', 8000, app)
    httpd.serve_forever()
