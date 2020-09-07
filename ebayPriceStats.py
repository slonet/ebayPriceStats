# AUTHOR: Tyler Slone
# 
# ebayPriceStats searches eBay.com with a keyword and gathers price data for active and completed listings.
# It makes a histogram of active listing and completed listing price.
#
#

import sys
from requests import get
from requests.exceptions import RequestException
from contextlib import closing

# Parse command line arguments
keyword = str(sys.argv[1])

# Global Variables

results_start = "<ul class=\"srp-results srp-list clearfix\">"
results_end = "class=\"srp-river-answer srp-river-answer--Basic_PAGINATION_V2\">"

item_start = "<li class=\"s-item"

title_start = "href=https://www.ebay.com/itm/"
title_end = "/"

cond_start = "class=SECONDARY_INFO>"
cond_end = "</span>"

auct_start = "class=s-item__purchase-options-with-icon aria-label>"
auct_end = "</span>"

bid_start = "s-item__bidCount\">"
bid_stop = " bids</span>"

price_start = "class=s-item__price>$"
price_end = "</span>"

sold_price_start = ">$"
sold_price_end = "</span>"

ship_cost_start = "s-item__logisticsCost\">+$"
ship_cost_end = " shipping</span>"

url_a = "https://www.ebay.com/sch/i.html?_from=R40&_"
url_b = "trksid=m570.l1313&_nkw="
url_b_mod = "nkw="
url_sold_mod = "&_sacat=0&rt=nc&LH_Sold=1&LH_Complete=1"
url_n_results = "&_ipg=100" # Pre-set to 100 items per page


### getPage(url) returns the raw HTML from an address.
#
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


### isGoodResp(resp) checks the response of the web server for successful query or failure
#
def isGoodResp(resp):
	content_type = resp.headers['Content-Type'].lower()
	return (resp.status_code == 200
			and content_type is not None
			and content_type.find('html') > -1)


### log_error(e) generic error logging function
#
def log_error(e):
	fid = open('log.txt', 'w')
	fid.write(e)
	fid.close()


### dumpData(content, file_name) takes generic data, converts to a string and writes it
# into the specified file.
#
def dumpData(content, file_name):
	data = str(content)
	open(file_name, 'w').write(data)


### getItems(content) takes the raw HTML data and separates it into ebay item classes.
# It returns a list of items it was able to parse from the raw page data. The items are
# formatted as strings and still raw data.
#
def getItems(content):
	content = str(content)

	rslt_start = content.find(results_start)
	rslt_end = content.find(results_end)
	
	content = content[rslt_start:rslt_end].split(item_start)

	raw_items = content[1:len(content)-1] # 1st item is not a listing

	return raw_items


### getTitle(raw_item) takes a raw item parsed out of a results page and parses the item
# title. The item title is returned as a string.
#
def getTitle(raw_item):
	title = raw_item.split(title_start)[1]
	title = title[0:title.find(title_end)]

	return title


### getCond(raw_item) takes a raw item parsed out of a results page and parses the item
# condition. The item condition is returned as a string.
#
def getCond(raw_item):
	try:
		cond = raw_item.split(cond_start)[1]
		cond = cond[0:cond.find(cond_end)]

	except:
		cond = ''

	if " OPEN BOX" in cond.upper():
		cond = 'New - Open Box'

	return cond


### getAuctType(raw_item) takes a raw item parsed out of a results page and parses the item
# auction type. The item auction type is returned as a string.
#
def getAuctType(raw_item):
	try:
		auctType = raw_item.split(auct_start)[1]
		auctType = auctType[0:auctType.find(auct_end)]

	except: # Might be an auction instead of a buy it now
		if bid_start in raw_item:
			auctType = 'Auction'
		
		else:
			auctType = ''

	return auctType


### getPrice(raw_item) takes a raw item parsed out of a results page and parses the item
# price. The item price is returned as a float.
#
def getPrice(raw_item):
	try: # this should work for an active listing
		price_str = raw_item.split(price_start)[1]
		price_str = price_str[0:price_str.find(price_end)]
		price = float(price_str.replace(',', ''))
	
	except: # If it is a completed / sold listing the price will be in this format
		price_str = raw_item.split(sold_price_start)[1]
		price_str = price_str[0:price_str.find(sold_price_end)]
		price = float(price_str.replace(',', ''))

	return price


### getShipCost(raw_item) takes a raw item parsed out of a results page and parses the item
# shipping cost. The item shipping cost is returned as a float. If the item has free shipping
# the shipping cost returned is 0.0
#
def getShipCost(raw_item):
	try:
		ship_cost_str = raw_item.split(ship_cost_start)[1]
		ship_cost_str = ship_cost_str[0:ship_cost_str.find(ship_cost_end)]
		ship_cost = float(ship_cost_str.replace(',', ''))

	except:
		ship_cost = 0.0

	return ship_cost


### getParameters(raw_items) takes the list of raw items parsed from a reults page, iterates through
# the list, and gathers all parameters for all items on the page. Each item has a dictionary of paramters.
#
def getParameters(raw_items):
	N = len(raw_items)

	items = []

	for i in range(N):

		item = {
			'Title': '',
			'Condition': '',
			'AuctionType': '',
			'Price': -1.0,
			'ShippingCost': -1.0,
		}

		item['Title'] = getTitle(raw_items[i])
		item['Condition'] = getCond(raw_items[i])
		item['AuctionType'] = getAuctType(raw_items[i])
		item['Price'] = getPrice(raw_items[i])
		item['ShippingCost'] = getShipCost(raw_items[i])

		items.append(item)

	return items


### makeUrl(keyword, sold, page_no) takes a keyword, a set of search filters, and the desired results page
# it generates a valid eBay URL that can be used to grab the desired page data. The URL is returned as a string.
#
def makeUrl(keyword, sold, page_no):
	# replace spaces in keyword with '+'
	url = ''
	keyword = keyword.replace(' ', '+')
	page_str = "&_pgn=" + str(page_no)

	if sold:
		url = url_a + url_b_mod + keyword + url_sold_mod + url_n_results + page_str

	else:
		url = url_a + url_b + keyword + url_n_results + page_str

	return url


### getResultPages(keyword) takes a keyword and collects all the unique results pages for the keyword.
# 0. Set the n_pages counter to 1
# 1. Get the 1st page and store it in the pages list
# 2. Get the 1st result from the 1st page and store it in prev res
# 3. Begin the loop
# 4. Increment the n_pages counter
# 5. Get the next page and store it in a temporary variable
# 6. Get the top result from the next page
# 7. Compare the prev result to the next result
# 8. If they are equal: break from the loop
# 9. If they are not equal append the next page temporary variable to the pages list
# 10. Repeat loop

def getResultPages(keyword):


	return [n_pages, raw_pages]


### Main script

url = makeUrl(keyword, 0, 1)
content = getPage(url)


### DEV NOTES
# Left off at getting the total number of unique result pages. Realized it makes more
# sense to grab the page contents during the process and return all the unique pages.
#
### Data Hierarchy
#
# Keyword:
# 	Results Pages
#		Results Page
#			Items
#				Item
#					Item Parameters
#						Parameter
#
# TODO:
# Get all unique results pages in one operation.
# Iterate over multiple pages and extract the results parameters.
# Post process the results parameters.
#