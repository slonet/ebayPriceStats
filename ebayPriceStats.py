# AUTHOR: Tyler Slone
# 
# wbayPriceStats searches eBay.com with a keyword and gathers price data for active and completed listings.
# It makes a histogram of active listing and completed listing price.
#
# Development Plan:
# 1. grab relevant raw data from ebay.com
# 2. parse the data to get pricing in a data structure
# 3. plot the data in a historgram
#

from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup as BS

def getPage(url):
	try:
		with closing(get(url, stream=True)) as resp:
			if isGoodResp(resp):
				return resp.content
			else:
				return None

	except RequestException as e:
		log_error('Error during request to {0} : {1}'.format(url, str(e)))
		return None


def isGoodResp(resp):
	content_type = resp.headers['Content-Type'].lower()
	return (resp.status_code == 200
			and content_type is not None
			and content_type.find('html') > -1)


def log_error(e):
	fid = open('log.txt', 'w')
	fid.write(e)
	fid.close()

