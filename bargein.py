from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup
from itertools import combinations
from json import loads
from traceback import print_exc


def trail(s, n, ending="..."):
	return s[:n - len(ending)] + (s[n - len(ending):] and ending)


class ListedItem:
	def __init__(self, name, data_pid, price, location, requested_by, search_term, images=()):
		self.name = name
		self.data_pid = data_pid
		self.price = float(price) if price[0] != '$' else float(price[1:])
		self.location = location
		self.requested_by = requested_by
		self.search_term = search_term
		self.images = images

	def get_link(self, config):
		return "https://{}.craigslist.org/sys/{}.html".format(config["location"], self.data_pid)

	def get_report(self, config):
		return "[{:<7} USD] [{:>20}] [{:>25}] {}".format(self.price,
								self.requested_by["name"],
								self.search_term,
								trail(self.get_link(config), 60))


def get_results_for(item, config, search_term):
	r = requests.get("https://{}.craigslist.org/search/{}".format(config["location"], item["section"]), {
		"query": search_term,
		"sort": "rel",
		"srchType": "T",
		"hasPic": config["has_pic"],
		"postedToday": config["posted_today"],
		"bundleDuplicates": 1,
		"search_distance": config["distance"],
		"postal": config["postal"]
	})

	if not r:
		print("[   FAIL] [FETCH] " + trail(r.url, 60))
		return {}
	else:
		print("[SUCCESS] [FETCH] " + trail(r.url, 60))

	results = {}
	get_text = lambda x: x.get_text() if x else None

	for li in BeautifulSoup(r.text, "html.parser").find_all("li", "result-row"):
		data     = li["data-pid"]
		price    = get_text(li.find("span", "result-price"))
		location = get_text(li.find("span", "result-hood"))
		title    = get_text(li.find("a", "result-title"))
		if not price or not title or not data:
			continue
		results[data] = ListedItem(title, data, price, location, item, search_term)

	return results


def get_search_terms_for(item):
	keywords = item["terms"]
	length = len(keywords) if len(keywords) <= 3 else 3

	for i in range(2, length + 1):
		for term in combinations(keywords, r=i):
			yield " ".join(term)


def run(config):
	listings = {}
	for item in config["items"]:
		for term in get_search_terms_for(item):
			listings.update(get_results_for(item, config, term))
	return listings.values()


if __name__ == "__main__":
	with open("config.json") as config_file:
		try:
			config = loads(config_file.read())
			for listing in run(config):
				print(listing.get_report(config))
		except Exception as e:
			print_exc()
