from textwrap import dedent
from datetime import datetime

import falcon
import rrdtool
import pandas as pd

import db
import rrd

# define the local time zone
LOCAL_TZ = 'Europe/Stockholm'

# this is the index web page
INDEX_PAGE = dedent('''
    <meta http-equiv="refresh" content="60">

    <body>
        <p><img src="{img}" /></p>
        <p><a href="/?hours=8">8 h</a> <a href="/?hours=24">24 h</a> <a href="/?hours=48">48 h</a> <a href="/?hours=72">72 h</a> <a href="/?hours=168">1 w</a> 
        <p><a href="extract">Export data to TSV</a></p>
    </body>
''')

db.init()

class IndexPageResource:
    def on_get(self, req, resp):
        hours = req.get_param('hours', default=None)  # Get the optional parameter value

        if hours is None:
            # If the parameter is supplied, print its value
            page_content = INDEX_PAGE.format(img="/extract/rrdgraph?hours=72")
        else:
            # If the parameter is not supplied, display a default message
            page_content = INDEX_PAGE.format(img='/extract/rrdgraph?hours=' + hours)

        resp.content_type = 'text/html'
        resp.text = page_content
        resp.status = falcon.HTTP_200


class DataResource:
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = 'text/html'
        resp.text = """
        <html>
        <head><title>Sensor Data Extraction</title></head>
        <body>
            <h1>Sensor Data Extraction</h1>
            <form action="/extract/extract_tsv" method="get">
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
        df = pd.DataFrame(data)

        # replace "U" with empty string in the DataFrame
        df = df.replace('U', '')

        # convert the 'read_time' column to datetime and localize it to the desired timezone
        df['read_time'] = pd.to_datetime(df['read_time'], unit='s').dt.tz_localize(LOCAL_TZ)

        # format the 'read_time' column to human-readable format
        df['read_time'] = df['read_time'].dt.strftime('%Y-%m-%d %H:%M:%S')

        resp.content_type = 'text/tab-separated-values'
        resp.body = df.to_csv(index=False, sep='\t')
        resp.status = falcon.HTTP_200


class RRDGraphResource:
    def on_get(self, req, resp):
        # get the number of hours from the query parameter
        hours = req.get_param_as_int('hours')

        if hours is None or hours <= 0:
            resp.status = falcon.HTTP_400  # Bad Request
            resp.text = "Invalid input. Please provide a positive 'hours' parameter."
            return

        try:
            # Generate the graph and capture it as a binary image
            graph_binary = rrd.custom_rrd_graph(hours)
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
app.add_route('/extract', DataResource()) # url for the web page
app.add_route('/extract/extract_tsv', ExtractDataResource()) # url for the cgi endpoint
app.add_route('/extract/rrdgraph', RRDGraphResource())

if __name__ == '__main__':
    import wsgiref.simple_server
    httpd = wsgiref.simple_server.make_server('', 8000, app)
    httpd.serve_forever()
