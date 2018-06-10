# find_a_trail

Try to analyze gpx files and send the result.
Put all required info in environment variable:
```
scrapy_out = os.environ['GPX_FOLDER']
password = os.environ['MY_GMAIL_PASSWORD']
fromaddr = os.environ['MY_GMAIL_ADDRESS']
toaddr = os.environ['MY_WORK_EMAIL']
url = os.environ['GOOGLE_MAP_API_URL']
origin = os.environ['START_POINT'] # for example, P7
API_KEY = os.environ['MY_GCP_API_KEY']
```
