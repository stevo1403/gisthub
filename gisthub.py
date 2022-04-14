import argparse
import json
import os
import re
import time
from urllib.parse import urlparse

import github
import phonenumbers
import requests
from bs4 import BeautifulSoup as BS

from web_helpers import (get_protocol, get_url_info, is_domain, is_ip,
                         is_subdomain, is_valid_domain)


def extract_emails(text):
	
	"""
	Todo:
	1) Alter RegEx to match:
		username+alt-name@example.com
		user-name@example.com
		user_name@example.com
	"""

	regex = "((?:[a-zA-Z0-9\.]+(?:_)?[a-zA-Z0-9\.]+)(?:[\+](?:[a-zA-Z0-9\.]+(?:_)?[a-zA-Z0-9\.]+))?\@(?:[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+))"
	pattern = re.compile(regex)
	result = re.findall(pattern, text)
	return list(set(result))

def extract_phonenumbers(text, region=None):
	phone_numbers = set()

	for match in phonenumbers.PhoneNumberMatcher(text, region, leniency=0):
		pn = match.raw_string
		phone_numbers.add(pn)

	return list(phone_numbers)

def extract_urls(text):

	regex = "(?:(?:[a-zA-Z]+):\/\/)?[\w/\-?=%.]+\.[\w/\-?=%.]+"
	pattern = re.compile(regex)
	urls = re.findall(pattern, text)	
	return list(set(urls))

def process_urls(urls):
	_urls = set()

	for url in urls:
		
		if not url:
			continue

		protocol = get_protocol(url)
		url = url.strip().strip('.')
		real_url = url
		# print(url, protocol)

		if protocol or url.startswith('//') or url.startswith('://'):
			url = urlparse(url).hostname

		if '/' in url:
			url = url.split('/', 1)
			url = url[0]


		if is_ip(url):
			_urls.add(real_url)
		elif is_domain(url):
			if is_valid_domain(url):
				_urls.add(real_url)

	return list(_urls)

def canonicalize_urls(urls, default_scheme='http'):
	_urls = set()
	for url in urls:
		if not url:
			continue

		if url.startswith('//'):
			url = default_scheme + ':' + url
		elif url.startswith('://'):
			url = default_scheme + url
		elif urlparse(url).scheme:
			pass
		else:
			url = default_scheme + ':' + '//' + url

		_urls.add(url)

	return list(_urls)

def get_cmd_args():

	subcommands = ['user', 'gist', 'search']
	parser = argparse.ArgumentParser()
	subparsers = parser.add_subparsers(title="subcommands", description="The available subcommands are listed below.", metavar=", ".join(subcommands), dest="subcommand")

	#========start user_parser ============
	user_parser = subparsers.add_parser('user', description='This subcommands performs user-related activities.')
	user_parser.add_argument('--username', '-u', action='append', default=[], metavar='USERNAME', dest='usernames', help='specify the username of the users whose gists should be retrieved. Repeat the flag to add multiple usernames.')
	user_parser.add_argument('--username-list', '-L', metavar='USERNAMES_FILE', help='specify the file containing usernames.', dest='username_file')
	user_parser.add_argument('--maximum', '-m', metavar='INTEGER', type=int, dest='maximum', default=100, help='specify the maximum number of gists to retrieve. Default is 100.')
	user_parser.add_argument('--save', '-s', metavar='FILE', dest='save', help='specify the file to save the retrieved gists. Format is JSON.')
	user_parser.add_argument('--save-id', metavar='FILE', dest='save_id', help='specify the file(flat) to save the ids(s) only. Format is TXT')
	user_parser.add_argument('--save-metadata', '-S', metavar='FILE', dest='save_metadata', help='specify the file to save the metadata of the gists. Format is JSON')
	user_parser.add_argument('--verbose','-v',default=0, action='count',help='specify the verbosity of the program.', dest='verbosity')
	#========end user_parser ============
	
	#========start gist_parser ============
	gist_parser = subparsers.add_parser('gist', description='This subcommands performs gist-related activities.')
	gist_parser.add_argument('--gists', '-g', action='append', default=[], metavar='GIST_ID', dest='gists_id', help='specify the gist ids of the gist that should be retrieved. Repeat the flag to add multiple ids.')
	gist_parser.add_argument('--gist-list', '-L', metavar='GISTS_FILE', help='specify the file containing gist ids.', dest='gist_file')
	gist_parser.add_argument('--maximum', '-m', metavar='INTEGER', type=int, default=0, dest='maximum', help='specify the maximum number of gists to retrieve. Default is 0(which means all gists in the user\'s timeline).')
	gist_parser.add_argument('--save', '-s', metavar='FILE', dest='save', help='specify the file to save the retrieved gists. Format is JSON.')
	gist_parser.add_argument('--save-metadata', metavar='FILE', dest='save_metadata', help='specify the file to save the metadata. Format is JSON')
	gist_parser.add_argument('--verbose','-v', default=0, action='count',help='specify the verbosity of the program.',dest='verbosity')
	#========end gist_parser ============

	#========start search_parser ============
	search_parser = subparsers.add_parser('search', description='This subcommands performs search-related activities.')
	search_parser.add_argument('--query', '-q', required=True, metavar='QUERY', dest='query', help='specify the query.')
	search_parser.add_argument('--language', '-l', metavar='LANGUAGE', dest='language', help='specify the language of the gists to return. Values include Markdown,CSV,HTML,JavaScript,JSON,XML,Python,SCSS,Shell,Text.')
	search_parser.add_argument('--page', '-p', metavar='INTEGER', type=int, default=1, dest='page', help='specify the page to start from. Default is 1.')
	search_parser.add_argument('--max-gists', '-m', metavar='INTEGER', type=int, default=100, dest='maximum_gists', help='specify the maximum number of gists to retrieve. Default is 100.')
	search_parser.add_argument('--max-pages', '-M', metavar='INTEGER', type=int, default=100, dest='maximum_pages', help='specify the maximum number of pages to retrieve. Default is 100.')
	search_parser.add_argument('--sort', '-x', metavar='SORT', dest='sort', choices=['stars', 'forks', 'updated'], help='specify the way to sort the result.')
	search_parser.add_argument('--order', '-o', metavar='ORDER', dest='order', choices=['asc', 'desc'], help='specify the order of the sort.')
	search_parser.add_argument('--get-all', '-G', action='store_true', dest='get_all', help='specify that the maximum possible number of gists should be retrieved.')
	search_parser.add_argument('--save', '-s', metavar='FILE', dest='save', help='specify the file to save the retrieved gists. Format is JSON.')
	search_parser.add_argument('--save-usernames', metavar='FILE', dest='save_usernames', help='specify the file(flat) to save the usernames of users who authored the gists. Format is TXT.')
	search_parser.add_argument('--save-metadata', '-S', metavar='FILE', dest='save_metadata', help='specify the file to save the metadata. Format is JSON.')
	search_parser.add_argument('--verbose','-v', default=0, action='count', help='specify the verbosity of the program.',dest='verbosity')
	#========end search_parser ============

	args = parser.parse_args()
	return parser, args

class GGist(github.Gist.Gist):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

class Gist:
	def __init__(self, timeout=10):
		
		self.g = github.Github()
		self.gist_search_url = "https://gist.github.com"
		
		self.session = requests.Session()
		self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'})

		self.timeout = timeout

		self.requester = github.Requester.Requester(None, None, None, "https://api.github.com", 15, "PyGithub/Python", 30, True, None, None)

	def search(self, query=None, page=None, language=None, sort=None, order=None, max_gists=None, max_pages=None, verbosity=0):
		"""
		language:
			Markdown
			CSV
			HTML
			JavaScript
			JSON
			XML
			Python
			SCSS
			Shell
			Text
	
		query:
			filename:.bashrc	Find all gists with a ".bashrc" file.
			cat language:html	Find all cat gists with HTML files.
			join extension:coffee	Find all instances of join in gists with a coffee extension.
			system size:>1000	Find all instances of system in gists containing a file larger than 1000kbs.
			
			cat stars:>100	Find cat gists with greater than 100 stars.
			user:defunkt	Get all gists from the user defunkt.
			cat anon:true	Include anonymous gists in your search for cat-related gists.
			NOT cat	Excludes all results containing cat.
			cat fork:only	Search all forked gists for results containing cat.

		sort:
			stars
			forks
			updated

		order:
			asc
			desc		

		https://gist.github.com/search?p=9&q=zynga.com&ref=searchresults
		"""
		params = {
			'ref':'searchresults',
			'q':query
		}

		endpoint = "/search"
		full_url = self.gist_search_url + endpoint

		if page:
			params['p'] = page

		if language:
			params['l'] = language.capitalize()

		if sort:
			params['s'] = sort
		
		if order and sort:
			params['o'] = order


		gist_links = set()

		total_pages = 0
		error_count = 0
		looped_once = False

		if verbosity > 0:
			print("[+] URL: ", full_url)
			print("[+} Query: ", query)
			print("[+} Page: ", page)
			print("[+} Language: ", language)
			print("[+} Sort: ", sort)
			print("[+} Order: ", order)
			print("[+} Max Pages: ", max_pages)
			print("[+} Max Gists: ", max_gists)
			print()

		t1 = time.time()
		print("[+] Extracting the gists links from search results.")
		print()

		while True:
			gists_returned = 0
			try:
				# self.session.cookies.clear()
				print("[+] Requesting for page %s."%(total_pages + 1))
				with self.session.get(full_url, params=params, timeout=self.timeout) as response:
					if response.status_code == 200:
						html = response.text
						soup = BS(html, features='html.parser')
						info_text = soup.select_one('div.gutter div div h3 div.d-flex h3')

						if info_text:
							info_text = info_text.text
							sections = info_text.strip().split(" ")

							if sections and sections[0].isnumeric():
								num_results = int(sections[0])
								if verbosity and not looped_once:
									print("[+] %s gist(s) was returned."%(num_results))
									print()
									looped_once = True

								gists = soup.select("div main div div.repository-content div.gutter div .gist-snippet")
								if gists:
									gists_returned = len(gists)
									for gist in gists:
										gist_link = gist.select_one("div.gist-snippet-meta ul li.d-inline-block a")
										if gist_link:
											gist_link = gist_link.attrs.get('href')
											if gist_link:
							
												gist_links.add(gist_link)
						else:
							if total_pages > 1:
								print("[*] It seems we have reached the end.")
							else:
								print("[+] The search query returned no results.")

							error_count += 1

					else:
						if verbosity > 0:
							print("[-] Recieved a non-200 status code of %s."%(response.status_code))
						error_count += 1

			except Exception as e:
				print("[-] An error occurred while making request: ", e)
				error_count += 1

			total_pages += 1

			params['p'] = total_pages + 1

			if error_count >= 3:
				if verbosity > 0:
					print("[-] Page iteration stopped due to consecutive errors.")
					break

			if ( max_gists and max_gists >= len(gist_links) ) or (max_pages and max_pages >= total_pages):
				break
			else:
				if max_gists and len(gist_links) >= max_gists:
					break
				elif max_pages and max_pages >= total_pages:
					break

			#uncomment to break when less gists are returned.
			# if gists_returned < 50:
			# 	break

		t2 = time.time()
		print()
		print("[+] %s links were extracted."%(len(gist_links)))
		print("[+] Link extraction took %s seconds before completion."%(t2-t1))

		gist_links = list(gist_links)

		gist_store = {}
		gists_collection = []
		gists_authors = set()

		_gist_links = set()

		t1 = time.time()
		print()
		print("[+] Retrieving gists from the search results.")

		for index, gist_link in enumerate(gist_links, 1):
			
			gist_url = self.gist_search_url + gist_link + '.json'			

			print("[+] Retrieving gist with url '%s'."%(gist_url))

			try:
				with self.session.get(gist_url, timeout=self.timeout) as response:
					if response.status_code == 200:

						data = response.json()
						owner = data.get('owner')
						is_public = data.get('public') or False
						files = data.get('files')

						if not owner in gist_store:
							gist_store[owner] = {
								'owner': owner,
								'url':gist_url,
								'is_public':is_public,
								'files': [],
								'emails': [],
								'phone_numbers': [],
								'urls': [],
							}

						if not gist_link in _gist_links:
							gists_collection.append(data)
							gists_authors.add(owner)

						_gist_links.add(gist_link)

						html = data.get('div')
						soup = BS(html, features='html.parser')

						contents = soup.select("div.gist div.gist-file div.gist-data")
						for content in contents:
							content_data = content.select_one('div.file')
							if content_data:
								content_data = content_data.text
								phone_numbers = extract_phonenumbers(content_data)
								emails = extract_emails(content_data)
								urls = extract_urls(content_data)
								urls = process_urls(urls)
								urls = canonicalize_urls(urls)

								gist_store[owner].get('emails').extend(emails)
								gist_store[owner].get('urls').extend(urls)
								gist_store[owner].get('phone_numbers').extend(phone_numbers)

						metadata = soup.select('div.gist-meta')

						_files = []

						for m in metadata:
							file_link = m.select_one('a')
							if file_link:
								file_link = file_link.attrs.get('href')
								_files.append(file_link)
						
						print("[+] Gist contains %s files."%(len(_files)))
						gist_store[owner]['files'].extend(_files)
			except Exception as e:
				print("[-] An exception occurred while retrieving gist: ", e)

			print()

			if max_gists and max_gists >= index:
				break

		t2 = time.time()
		print("[+] Gists extraction took %s seconds before completion."%(t2-t1))

		return gist_store, gists_collection, list(gists_authors)

	def get_gists(self, username, maximum=1000, page=1, per_page=100):
		endpoint = '/users/%s/gists'%(username)

		url_parameters = {'per_page':per_page, 'page': page}
		results = []
		
		current_page = page

		while True:
			headers, data = self.requester.requestJsonAndCheck("GET", endpoint, parameters=url_parameters)
			for gist in data:
				gg = github.Gist.Gist(self.requester, headers, gist, completed=True)
				results.append(gg)

				if maximum and len( results ) >= maximum:
					break

			if maximum and len( results ) >= maximum:
				break
			
			current_page += 1

			url_parameters['page'] = current_page

		return results

	def get_gist(self, id):
		return self.g.get_gist(id)

def get_gists_id(args):
	"""
	TODO:
	Optimize for streaming.
	"""
	gists_id = set(args.gists_id)

	if args.gist_file:
		with open(args.gist_file, 'rt', encoding='utf-8') as f:
			while True:
				while len(gists_id) >= 100:
					gists_id = list(gists_id)
					yield gists_id[:100]
					gists_id = set(gists_id[100:])

				line = f.readline()
				line = line.strip()
				if not line:
					break

				if line and not (line.startswith('#') or line.startswith("//")):
					gists_id.add(line)

	yield gists_id

def get_usernames(args):
	"""
	TODO:
	Optimize for streaming.
	"""
	usernames = set(args.usernames)


	if args.username_file:
		with open(args.username_file, 'rt', encoding='utf-8') as f:
			while True:
				while len(usernames) >= 100:
					usernames = list(usernames)
					yield usernames[:100]
					usernames = set(usernames[100:])

				line = f.readline()
				line = line.strip()
				if not line:
					break

				if line and not (line.startswith('#') or line.startswith("//")):
					usernames.add(line)

	yield usernames

def get_files(files, session, strict=True):
	content = []

	for file in files:
		ftype = file.type
		raw_url = file.raw_url
		if strict:
			if ftype and 'plain' in ftype:
				with session.get(raw_url) as response:
					if response.status_code == 200:
						content.append(response.text)

	return content

if __name__ == '__main__':
	parser, args = get_cmd_args()
	
	defined_subcommands = ["user", "gist", 'search']
	
	g = Gist()

	try:
		if args.subcommand == 'user':

			verbosity = args.verbosity

			usernames = args.usernames
			username_file = args.username_file

			maximum = args.maximum
			save = args.save
			save_id = args.save_id
			save_metadata = args.save_metadata

			session = requests.Session()

			if verbosity > 0:
				print("[+] Retrieving the gists of user's that match any of the specified username(s) from gist.gisthub.")
				print()

			if not usernames and not username_file:
				parser.error("either of the following arguments are required: --username/-u, --username-list/-L")

			if username_file and not (os.path.exists(username_file) and os.path.isfile(username_file)):
				exit("[-] Username file '%s' does not exists."%(username_file))

			usernames = get_usernames(args) 

			gists_id = set()

			gists_store = {}
			gists_collection = []

			for _usernames in usernames:
				for username in _usernames:
					print("[+] Retrieving gists for user '%s'."%(username))
					print()
					try:
						gists = g.get_gists(username, maximum)
					except Exception as e:
						print("[-] An exception occurred while retrieving gists: ", e)
						if hasattr(e, 'status') and e.status == 404:
							print("[-] The username '%s' probably doesn't exist."%(username))
						
						continue

					print("[+] Retrieved %s tweets."%(len(gists)))
					print()
					for gist in gists:
						print("[+] Got gist: Gist(owner'=%s' id=%s created_at=%s, files='%s')"%(gist.owner.login, gist.id, gist.created_at, '|'.join(gist.files.keys())))
						
						if not username in gists_store:
							gists_store[username] = []

						if not gist.id in gists_id:
							gists_collection.append(gist.raw_data)

						gists_id.add(gist.id)

						owner = gist.owner
						gist_url = "https://gist.github.com" + "/" + owner.login + "/" + gist.id
						is_public = gist.public
						files = gist.files

						try:
							contents = get_files(files.values(), session)
						except Exception as e:
							print("[-] An exception occurred while retrieving gist files: ", e)

						urls = set()
						emails = set()
						phone_numbers = set()

						for content in contents:
							content_data = content
							phone_numbers.update( extract_phonenumbers(content_data) )
							emails.update( extract_emails(content_data) )
							urls.update( extract_urls(content_data) )
							urls.update( process_urls(urls) )
							urls.update( canonicalize_urls(urls) )

						gists_store[username].append({
							'id':gist.id,
							'owner': owner,
							'url':gist_url,
							'is_public':is_public,
							'files': [file for file in files],
							'emails': list(emails),
							'phone_numbers': list(phone_numbers),
							'urls': list(urls),
						})

			gists_id = set(gists_id)
			if save_id:
				try:
					print("[+] Saving Gist IDs to file '%s'."%(save_ids))
					with open(save_id, 'wt', encoding='utf-8') as f:
						for _id in gists_id:
							f.write(str(_id)+'\n')
					print("[+] Gist IDs successfully saved to file '%s'."%(save_ids))
					print()
				except Exception as e:
					print("[-] An exception occurred while writing gist ids to file: ", e)

			if save_metadata:
				try:
					print("[+] Saving metadata to file '%s'."%(save_metadata))
					with open(save_metadata, 'wt', encoding='utf-8') as f:
						json.dump(gists_store, f, indent=2)
					print("[+] Gist Metadata successfully saved to file '%s'."%(save_metadata))
					print()
				except Exception as e:
					print("[-] An exception occurred while writing the metadata to file: ", e)

			if save:
				try:
					print("[+] Saving gist to file '%s'."%(save))
					with open(save, 'wt', encoding='utf-8') as f:
						json.dump(gists_collection, f, indent=2)
					print("[+] Gist successfully saved to file '%s'."%(save))
					print()
				except Exception as e:
					print("[-] An exception occurred while writing gists to file: ", e)

			if verbosity >= 2:
				print("[+] Metadata: ")
				print()
				print(json.dumps(gists_store, indent=2))

		elif args.subcommand == 'gist':

			verbosity = args.verbosity

			gists_id = args.gists_id
			gist_file = args.gist_file

			maximum = args.maximum
			save = args.save
			save_metadata = args.save_metadata

			session = requests.Session()

			if verbosity > 0:
				print("[+] Retrieving the specified gists.")
				print()

			if not gists_id and not gist_file:
				parser.error("either of the following arguments are required: --gist/-g, --gist-list/-L")

			if gist_file and not (os.path.exists(gist_file) and os.path.isfile(gist_file)):
				exit("[-] Gist file '%s' does not exists."%(gist_file))

			gists_id = get_gists_id(args) 
			gists_store = {}

			gists_ids = set()

			gists_collection = []

			for _gists_id in gists_id:
				for gist_id in _gists_id:
					_gist_id = gist_id
					print("[+] Retrieving gist with id '%s'."%(_gist_id))
					
					try:
						gist = g.get_gist(_gist_id)
					except Exception as e:
						print("[-] An exception occurred while retrieving gist: ", e)
						if hasattr(e, 'status') and e.status == 404:
							print("[-] The gist with id '%s' probably doesn't exist."%(_gist_id))

						print()
						continue

					print("[+] Got gist: Gist(owner'=%s' id=%s created_at=%s, files='%s')"%(gist.owner.login, gist.id, gist.created_at, '|'.join(gist.files.keys())))

					if not gist.id in gists_ids:
						gists_collection.append(gist.raw_data)

					gists_ids.add(gist.id)

					owner = gist.owner
					gist_url = "https://gist.github.com" + "/" + owner.login + "/" + gist.id
					is_public = gist.public
					files = gist.files

					contents = get_files(files.values(), session)

					urls = set()
					emails = set()
					phone_numbers = set()

					for content in contents:
						content_data = content
						phone_numbers.update( extract_phonenumbers(content_data) )
						emails.update( extract_emails(content_data) )
						urls.update( extract_urls(content_data) )
						urls.update( process_urls(urls) )
						urls.update( canonicalize_urls(urls) )

					gists_store[str(_gist_id)] = {
						'id':gist.id,
						'owner': owner,
						'url':gist_url,
						'is_public':is_public,
						'files': [file for file in files],
						'emails': list(emails),
						'phone_numbers': list(phone_numbers),
						'urls': list(urls),
					}

					print()

			if save_metadata:
				try:
					print("[+] Saving metadata to file '%s'."%(save_metadata))
					with open(save_metadata, 'wt', encoding='utf-8') as f:
						json.dump(gists_store, f, indent=2)
					print("[+] Gist Metadata successfully saved to file '%s'."%(save_metadata))
					print()
				except Exception as e:
					print("[-] An exception occurred while writing the metadata to file: ", e)

			if save:
				try:
					print("[+] Saving gist to file '%s'."%(save))
					with open(save, 'wt', encoding='utf-8') as f:
						json.dump(gists_collection, f, indent=2)
					print("[+] Gist successfully saved to file '%s'."%(save))
					print()
				except Exception as e:
					print("[-] An exception occurred while writing gists to file: ", e)

			if verbosity >= 2:
				print("[+] Metadata: ")
				print(json.dumps(gists_store, indent=2))

		elif args.subcommand == 'search':
			verbosity = args.verbosity
			
			query = args.query
			language = args.language
			page = args.page
			order = args.order
			sort = args.sort
			
			max_gists = args.maximum_gists
			max_pages = args.maximum_pages

			get_all = args.get_all

			if get_all:
				max_gists = None
				max_pages = None
			
			gists_store, gists_collection, gists_authors = g.search(query, page, language, sort, order, max_gists, max_pages, verbosity)


			save = args.save
			save_metadata = args.save_metadata
			save_usernames = args.save_usernames

			if save_metadata:
				try:
					print("[+] Saving metadata to file '%s'."%(save_metadata))
					with open(save_metadata, 'wt', encoding='utf-8') as f:
						json.dump(gists_store, f, indent=2)
					print("[+] Gist Metadata successfully saved to file '%s'."%(save_metadata))
					print()
				except Exception as e:
					print("[-] An exception occurred while writing the metadata to file: ", e)

			if save_usernames:
				try:
					print("[+] Saving username(s) to file '%s'."%(save_usernames))
					with open(save_usernames, 'wt', encoding='utf-8') as f:
						for username in gists_authors:
							f.write(username + '\n')
					print("[+] %s username(s) written successfully to file '%s'."%(len(gists_authors), save_usernames))
					print()
				except Exception as e:
					print("[-] An exception occurred while saving usernames to file: ", e)
			if save:
				try:
					print("[+] Saving gist(s) to file '%s'."%(save))
					with open(save, 'wt', encoding='utf-8') as f:
						json.dump(gists_collection, f, indent=2)
					print("[+] Gist(s) successfully saved to file '%s'."%(save))
					print()
				except Exception as e:
					print("[-] An exception occurred while writing gists to file: ", e)

			if verbosity >= 2:
				print("[+] Metadata: ")
				print(json.dumps(gists_store, indent=2))

		else:
			parser.print_usage()

	except Exception as e:
		print("[-] An exception occurred: ", e)
	except KeyboardInterrupt:
			print()
			print("[+] Exiting now.")