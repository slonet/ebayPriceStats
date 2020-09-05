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


def dumpData(content, file_name):
	data = str(content)
	open(file_name, 'w').write(data)


def getResultPages(keyword):
	n_pages = 1

	prev_top_res = parseTitle(extractItems(getPage(makeUrl(keyword,0,1)))[0])

	while True:
		n_pages += 1
		next_top_res = parseTitle(extractItems(getPage(makeUrl(keyword,0,n_pages)))[0])

		if next_top_res == prev_top_res:
			n_pages -= 1
			break

		prev_top_res = next_top_res

	return n_pages


def extractItems(content):
	content = str(content)

	rslt_start = content.find(results_start)
	rslt_end = content.find(results_end)
	
	content = content[rslt_start:rslt_end].split(item_start)

	raw_items = content[1:len(content)-1] # 1st item is not a listing

	return raw_items


def parseTitle(raw_item):
	title = raw_item.split(title_start)[1]
	title = title[0:title.find(title_end)]

	return title


def parseCond(raw_item):
	try:
		cond = raw_item.split(cond_start)[1]
		cond = cond[0:cond.find(cond_end)]

	except:
		cond = ''

	if " OPEN BOX" in cond.upper():
		cond = 'New - Open Box'

	return cond


def parseAuctType(raw_item):
	try:
		auctType = raw_item.split(auct_start)[1]
		auctType = auctType[0:auctType.find(auct_end)]

	except: # Might be an auction instead of a buy it now
		if bid_start in raw_item:
			auctType = 'Auction'
		
		else:
			auctType = ''

	return auctType


def parsePrice(raw_item):
	try: # this should work for an active listing
		price_str = raw_item.split(price_start)[1]
		price_str = price_str[0:price_str.find(price_end)]
		price = float(price_str.replace(',', ''))
	
	except: # If it is a completed / sold listing the price will be in this format
		price_str = raw_item.split(sold_price_start)[1]
		price_str = price_str[0:price_str.find(sold_price_end)]
		price = float(price_str.replace(',', ''))

	return price


def parseShipCost(raw_item):
	try:
		ship_cost_str = raw_item.split(ship_cost_start)[1]
		ship_cost_str = ship_cost_str[0:ship_cost_str.find(ship_cost_end)]
		ship_cost = float(ship_cost_str.replace(',', ''))

	except:
		ship_cost = 0.0

	return ship_cost


def parseItems(raw_items):
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

		item['Title'] = parseTitle(raw_items[i])
		item['Condition'] = parseCond(raw_items[i])
		item['AuctionType'] = parseAuctType(raw_items[i])
		item['Price'] = parsePrice(raw_items[i])
		item['ShippingCost'] = parseShipCost(raw_items[i])

		items.append(item)

	return items


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

### Main script

#url = makeUrl(keyword, 0, 1)
#content = getPage(url)

#dumpData(content, 'paginationDump.html')

#raw_items = extractItems(content)
#items = parseItems(raw_items)

#print(len(items))
#print('\n' + url)

n_pages = getResultPages(keyword)
print(n_pages)

### DEV NOTES
# Left off at getting the total number of unique result pages. Realized it makes more
# sense to grab the page contents during the process and return all the unique pages.
#
# TODO:
# Get all unique results pages in one operation.
# Iterate over multiple pages and extract the results parameters.
# Post process the results parameters.
#