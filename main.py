import sys
import networkx as nx
from pyvis.network import Network
import pickle
import urllib.request
import re
from bs4 import BeautifulSoup

CLEANR = re.compile('<.*?>')

base_link = "https://scp-wiki.wikidot.com"
base_series_link = base_link+"/scp-series"

articles = []
cross_refs = set()


def cleanhtml(raw_html):
  cleantext = re.sub(CLEANR, '', raw_html)
  return cleantext

def remove_trash(raw_html):
	soup = BeautifulSoup(raw_html, "html.parser")
	for div in soup.find_all("div", class_="footer-wikiwalk-nav"): # remove previous and next scp link
		div.decompose()
	for li in soup.find_all("li", class_="rateBox"): # remove everything from the ratebox as it can contain "more from this author" links
		li.decompose()
	for div in soup.find_all("div", class_="list-pages-box"): # remove "more from this author" links
		div.decompose()
	for div in soup.find_all("div", class_="list-pages-item"): # remove "more from this author" links
		div.decompose()
	for table in soup.find_all("table", class_="wiki-content-table"): # remove "more from this author" links
		table.decompose()
	for div in soup.find_all("div", class_="more-by-calibold"): # bro why
		div.decompose()
	return str(soup)

def get_all_scp_articles():
	for i in range(1,11):
		print(i)
		suffix = "" if i == 1 else "-"+str(i)
		page = urllib.request.urlopen(base_series_link+suffix)
		content = page.read().decode(page.headers.get_content_charset())
		#print(content)
		matches = re.findall("<li><a href=\"(.+?)\">SCP-(.+?)</a> - (.+?)</li>", content)
		print(["number: " + m[1] + " - name: " + m[2] + " - link: /" + m[0] + "\n" for m in matches])
		for m in matches:
			articles.append({
				"link": str(m[0]),
				"number": str(m[1]),
				"name": cleanhtml(m[2]),
			})

def build_all_references(articles):
	for a in articles:
		print(f'searching in {a["link"]}')
		try:
			page = urllib.request.urlopen(base_link+a["link"])
		except:
			print('----------')
			print('----------')
			print(f'ERROR WHILE GETTING PAGE {a["link"]}')
			print('----------')
			print('----------')
			continue
		content = page.read().decode(page.headers.get_content_charset())
		# clear footer references
		clean_content = remove_trash(content)
		
		# print(clean_content)
		# print('||||||||||||||||||')
		# print('||||||||||||||||||')
		# print('||||||||||||||||||')
		soup = BeautifulSoup(clean_content, "html.parser")
		matches = soup.find_all("a")
		for m in matches:
			ref = str(m.get("href"))
			if ref != a["link"] and ref in [e["link"] for e in articles]:
				print(f'found reference from SCP-{a["number"]} to SCP-{[e["number"] for e in articles if e["link"] == ref]}')
				cross_refs.add(tuple(sorted((a["link"],ref))))

def generate_graph():
	G = nx.Graph()

	get_all_scp_articles()

	for a in articles:
		G.add_node(a["link"], **{
			"number": a["number"],
			"name": a["name"],
		})
	
	build_all_references(articles)

	G.add_edges_from(cross_refs)

	pickle.dump(G, open('scp.pickle', 'wb'))

	return G

def draw_graph(G):
	net = Network(
		notebook=False,
		height="800px",
		width="100%",
		bgcolor="#222222",
		font_color="white"
	)

	net.barnes_hut(gravity=-25000)
	net.force_atlas_2based()
	net.toggle_physics(True)
	net.from_nx(G)
	for node in net.nodes:
		node['title'] = str(node['number'])
		node['label'] = node['id']


	net.show("graph.html", notebook=False)

def main():
	
	G = generate_graph()
	draw_graph(G)

if __name__ == '__main__':
    sys.exit(main())