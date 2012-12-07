"""
Star Links Retriever for GReader.
Inspiration:
    http://eamann.com/tech/google-reader-api-a-brief-tutorial/
    http://code.google.com/p/pyrfeed/wiki/GoogleReaderAPI
"""
import sys
import urllib
import urllib2
try:
    import simplejson as json
except ImportError:
    import json

BASE_URL = 'https://www.google.com'
BASE_ATOM = '/reader/atom/'
ITEMS_PER_REQUEST = 100

class StarLinksRetriever:

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.sid = None
        self.auth = None
        self.token = None
        self.headers = {}

    def perform_request(self, url, method='GET', headers=None, data=None):
        opener = urllib2.build_opener()
        request = urllib2.Request(url, data=data)
        request.get_method = lambda: method
        for k, v in headers.iteritems():
            request.add_header(k, v)
        try:
            response = opener.open(request)
            return response.read()
        except urllib2.HTTPError, e:
            print 'HTTP error: {0}.'.format(e.code)
        except urllib2.URLError, e:
            print 'Network error: ({0})'.format(e.reason.args[1])
        return None

    def perform_google_request(self, path):
        url = BASE_URL + path
        return self.perform_request(url, method='GET', headers=self.headers, data=None)

    def parse_login(self, text):
        result = False
        isid = text.find('SID=')
        ilsid = text.find('LSID=')
        iauth = text.find('Auth=')
        if isid != -1 and ilsid != -1 and iauth != -1:
            self.sid = text[isid + 4:ilsid]
            self.auth = text[iauth + 5:]
            result = True
        return result

    def get_sid(self):
        url_parameters = {'service': 'reader',
                          'Email': self.username,
                          'Passwd': self.password}
        url = '/accounts/ClientLogin?' + urllib.urlencode(url_parameters)
        body = self.perform_google_request(url)
        if self.parse_login(body):
            self.headers['Content-type'] = 'application/x-www-form-urlencoded'
            self.headers['Authorization'] = 'GoogleLogin auth=' + self.auth
        return self.sid is not None and self.auth is not None

    def get_token(self):
        url = '/reader/api/0/token'
        body = self.perform_google_request(url)
        if body is not None:
            self.token = body
        return self.token is not None

    def connect(self):
        result = False
        if self.get_sid():
            if self.get_token():
                result = True
        return result

    def reading_list(self, continuation):
        url_parameters = {'n':ITEMS_PER_REQUEST}
        if continuation is not None:
            url_parameters['continuation'] = continuation
        url = '/reader/api/0/stream/contents/user/-/state/com.google/reading-list?' + urllib.urlencode(url_parameters)
        return self.perform_google_request(url)

    def starred(self, continuation):
        url_parameters = {'n':ITEMS_PER_REQUEST}
        if continuation is not None:
            url_parameters['continuation'] = continuation
        url = '/reader/api/0/stream/contents/user/-/state/com.google/starred?' + urllib.urlencode(url_parameters)
        return self.perform_google_request(url)


def get_url_list(json_data):
    result = []
    for item in json_data['items']:
        try:
            result.append(item['canonical'][0]['href'])
        except:
            result.append(item['alternate'][0]['href'])
    return result

def main(args):
    # Get parameters.
    try:
        username = args[1]
        password = args[2]
        filename = args[3]
    except:
        print 'Use: {0} <username> <password> <filename>'.format(args[0])
        sys.exit(0)
    # Create retriever.
    retriever = StarLinksRetriever(username, password)
    # Connect to API.
    if retriever.connect():
        print 'Connected.'
        # Open file.
        with open(filename, "w") as f:
            continuation = None
            # End when continuation is not available in returned info.
            while not continuation or continuation is not '':
                # Retrieve starred urls.
                data = retriever.starred(continuation)
                # Load JSON data.
                json_data = json.loads(data)
                # Get url list from data.
                url_list = get_url_list(json_data)
                # Write urls to file.
                for url in url_list:
                    f.write(url + '\n')
                # Get continuation parameter.
                continuation = json_data.get('continuation', '')
                # Display number of retrieved urls.
                print 'Retrieved: {0}'.format(len(url_list))

if __name__ == "__main__":
    main(sys.argv)
