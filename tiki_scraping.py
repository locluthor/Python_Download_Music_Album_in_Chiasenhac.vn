from bs4 import BeautifulSoup
import requests
import re
import urllib
from urllib.request import urlopen                                                                                                                                                            
from urllib.parse import quote
import sqlite3
import os
import pickle
import sys
import traceback

# URL use for scraping
_url = 'https://tiki.vn/nha-sach-tiki'

# hardcode some book info id in html file
_s_publish_date = 'Ngày xuất bản'
_s_author = 'Author'
_s_num_page = 'Số trang'
_s_publisher = 'Nhà xuất bản'
_s_review_url = 'reiews-url'
_s_total_review_point = 'total-review-point'
_s_image_prop = 'image'
_s_product_price = "product_price"
_s_book_name = 'item-name'
_s_book_sku = "product_sku"
_s_product_box_list = "product-box-list"
_s_sub_categories = "list-group-item book-home-catlink"

# Tiki 3 bigs categories
books_categories = [r'/sach-truyen-tieng-viet',
					r'/sach-tieng-anh',
					r'/ebook']
book_url_pickle = 'book.pickle'
book_urls = set()

if  os.path.exists(book_url_pickle):
	with open(book_url_pickle, mode='rb') as f:
		book_urls = pickle.load(f)


def init_database_connection(database_name):
	'Establish connection to database_name file'

	conn = sqlite3.connect(database_name)
	return conn

def close_database_connection(connection):
	'Close database connection after done all the job with it'
	connection.close()

def create_table(connection, table_name):
	'Create table to store book info from tiki'

	create_table_query = 'CREATE TABLE ' + table_name +\
		' (sku TEXT PRIMARY KEY NOT NULL, \
		   name TEXT NOT NULL, \
		   price INT, \
		   author TEXT, \
		   nxb TEXT, \
		   publish_date TEXT, \
		   num_page INT, \
		   image_url BLOB, \
		   rating INT, \
		   num_rate INT, \
		   book_url TEXT)' 

	# try:
	c = connection.cursor()
	c.execute(create_table_query)
	# except:
	# 	print ('Can not create table : ', table_name)


# Globall database connection variable
sqlite_file = 'my_db.sqlite'
table_name = 'book_info'
if not os.path.exists(sqlite_file):
	sqlite_connection = init_database_connection(sqlite_file)
	create_table(sqlite_connection, table_name)
else:
	sqlite_connection = init_database_connection(sqlite_file)



class Book() :
	'Represent info of book in tiki'

	def __init__(self, sku='', name='', price=0, author='', nxb='', publish_date='', num_page=0, image_url='', rating=0, num_rate=0, book_url='') :
		'Init book info'
		self.sku = sku # unique sku id
		self.name = name # name
		self.price = price	# price
		self.author = author # author
		self.nxb = nxb # nha xuat ban
		self.publish_date = publish_date #  ngay xuat ban
		self.num_page = num_page # so trang
		self.image_url = image_url # cover image url
		self.rating = rating # average rating point 
		self.num_rate = num_rate # number of rated from user
		self.book_url = book_url # url to book in tiki



	def print_info(self):
		'Method spoke for itself'
		print ('sku : ', self.sku)
		print ('name : ', self.name)
		print ('author : ', self.author)
		print ('price : ', self.price)
		print ('nxb : ', self.nxb)
		print ('num_page : ', self.num_page)
		print ('image_url : ', self.image_url)
		print ('publish_date : ', self.publish_date)
		print ('rating : ', self.rating)
		print ('num_rate : ', self.num_rate)
		print ('book_url : ', self.book_url)


	def save_to_database(self, connection, table_name):
		'Save book info to database'
		insert_query = 'INSERT INTO ' + table_name + '(sku, name, author, price, nxb, num_page, image_url, publish_date, rating, num_rate, book_url) VALUES (?,?,?,?,?,?,?,?,?,?,?)'
		parameters = [self.sku, self.name, self.author, self.price, self.nxb, self.num_page, self.image_url, self.publish_date, self.rating, self.num_rate, self.book_url]

		try :
			c = connection.cursor()
			c.execute(insert_query, parameters) # Excecute insert query
			connection.commit() # 	Commit changes to database	
		except sqlite3.IntegrityError:
			# If the sku is already exist then we don't need to update
			# Because this book is duplicated
			print ('Duplicate book : ', self.sku)


# Get all book sub categories at tiki.vn
def get_sub_categories(url) :
	'''
	Return list of all book categories from target url
	Input : string : url
	Output : set : catogories 
	'''

	catogories = []

	with requests.Session() as session : 
		# Get html and parse it 
		html = session.get(url)
		
		# Parse Html
		soup = BeautifulSoup(html.content, "html.parser")

		# Get all div tags with attribute class="list-group-item book-home-catlink"
		tags = soup.findAll("div", { "class" : _s_sub_categories })
		
		for tag in tags :
			strs = str(tag).encode('utf-8', 'ignore')
				
			# Only choose real book categoryssss 
			if tag.a['href'] in books_categories :

				# Because strs is bytes string we have to use b prefix before regular expression
				hrefs = re.findall(b'href="(.*?)"', strs) 
				
				for href in hrefs :
					# Decode href from byte to utf-8
					catogories.append(href.decode('utf-8'))

		# We don't need recommend catogories
		# catogories.remove('/sach-hay-tiki-khuyen-doc/c835')


		return catogories

# Check is page is last page in category
def is_last_page(html) :

	# lpage = 'https://tiki.vn/fiction-literature/c9?page=20'

	# with requests.Session() as session :

	# html = session.get(page)
	soup = BeautifulSoup(html.content, 'html.parser')

	links = soup.findAll('link', {'rel' : 'next'})

	# if html contain link tag with attribute rel="next"
	# then it ain't last page
	if len(links) > 0 : 
		return False

	return True
 

# Get all books available in sub categories
def get_books(category) :
	'''
	Get all books in given category
	'''

	url = 'https://tiki.vn' + category + '?page='

	page = 1 # begin with page 1 of category
	
	with requests.Session() as session :

		# Loop until meet last page
		while True : 

			page_url = url + str(page)

			# Get html and parse it 
			html = session.get( page_url )
			soup = BeautifulSoup(html.content, 'html.parser')

			divs = soup.findAll("div", { "class" : _s_product_box_list })

			# print (str(divs[0]).encode('utf-8', 'ignore'))

			for div in divs :
				# print (divs.a['href'])
				strs = str(divs).encode('utf-8', 'ignore')

				hrefs = re.findall(b'href="(.*?)"', strs)

				for href in hrefs :
					
					bookurl = href.decode('utf-8')
					if not bookurl in  book_urls:
						print ('Extracting .... book : ', href.decode('utf-8'))
						yield href.decode('utf-8')
					book_urls.add(bookurl)
					# books.add(href.decode('utf-8'))

			print ('last page : ', category, ' ', page)

			# print ('Number of books : ', len(books))

			if is_last_page(html) :
		
				break

			page += 1


	# return books

# Get books metadata
def get_book_info(book_url) :

	# book_url = 'https://tiki.vn/huyen-thoai-mo-dat-p75409.html?ref=c316.c393.c839.c3130.c3259.c4968.c5374.c845.c854.c2766.c3133.c3327.c3377.c3452.c4291.c4697.c4699.c4971.c5234.c5300.c5377.c5571.c2288.c3141.c3328.c3387.c3535.c4972.c4985.c5178.c5807.c3504.c5572.c7498.'

	with requests.Session() as session :
		# Get html and parse it
		html = ''
		try: 
			html = session.get( book_url )
		except:
			print ('URL is not valid')
			return
		soup = BeautifulSoup(html.content, 'html.parser')

		# Get book sku id in <input id="product_sku
		_input = soup.find("input", { "id" : _s_book_sku })
		book_sku_id = _input['value']

		# Get book name  <h1 class="item-name"
		h1 = soup.find('h1', {'class' : _s_book_name})
		book_name =  h1.string.strip()
		# Get book price  <input id="product_price
		_input = soup.find("input", { "id" : _s_product_price })
		book_price = _input['value']

		# Get book cover image
		img = soup.find('img', {'itemprop' : _s_image_prop})
		image_url = img['src']

		# Get book rating
		rating_p = soup.find('p', {'class' : _s_total_review_point})
		rating = rating_p.string.strip()
		rating = eval(rating)

		# Get number of user  had rate this book
		if rating > 0:
			num_rate_tag = soup.find('a', {'id' : _s_review_url})
			num_rate = re.findall(b'\((\d*)', str(num_rate_tag).encode('utf-8')) # Extract so nguoi danh gia
			num_rate = (num_rate[0].decode('utf-8'))
		else:
			num_rate = 0


		# Handle url with unicode character
		# We must not encode the ':' character
		sString = image_url.split(':')
		sString[1] = quote(sString[1])	
		# Join 2 String together with ':' in between
		image_url = sString[0] + ':' + sString[1]
		# Download book cover and save it with name is it's sku_id
		# urllib.request.urlretrieve(image_url, book_sku_id + '.jpg')
		image_bin = urllib.request.urlopen(image_url)
		
		# print ('image_url : ', image_url)


		# Get product details 
		tds = soup.findAll('td')

		# Temporary hack, come back with better solution later
		# List content infomation of book
		infos = []

		# with open('out.txt', mode='w', encoding='utf-8') as f:
		for td in tds :
			if td.string is not None :
				infos.append(td.string.strip())
				# f.write(td.string.strip() + '\n')
			else :
				for child in td.children :
					if (child.string is not None):
						if (child.string.strip() != '') :
							infos.append(child.string.strip())
							# f.write(child.string.strip() + '\n')

		# Find nhà xuất bản
		try : 
			index_nxb = infos.index(_s_publisher)
			nxb = infos[index_nxb + 1] # nxb value is next to nxb index
		except ValueError : # except that nhaxuatban info is missing
			nxb = ''
		# print (index_nxb)

		# Find tác giả
		try : 
			index_author = infos.index(_s_author) # Author value is next to Author index
			author = infos[index_author + 1]
		except ValueError : # except that nhaxuatban info is missing
			author = ''		

		# print (index_author)

		# # Find số trang
		try : 
			index_num_page= infos.index(_s_num_page) # Số trang value is next to Số trang index
			num_page = infos[index_num_page + 1]
		except ValueError : # except that nhaxuatban info is missing
			num_page = 0				

		# print (index_num_page)

		# Find Ngày xuất bản
		try : 
			index_publish_date= infos.index(_s_publish_date) # Ngày xuất bản value is next to Ngày xuất bản index
			publish_date = infos[index_publish_date + 1]
		except ValueError : # except that nhaxuatban info is missing
			publish_date = ''

		# Save book info to database				
		book_info = Book(sku=book_sku_id, name=book_name, price=book_price, author=author, nxb=nxb, publish_date=publish_date,num_page=num_page, image_url=sqlite3.Binary(image_bin.read()), rating=rating, num_rate=num_rate, book_url=book_url)
		book_info.save_to_database(sqlite_connection, table_name)
		image_bin.close()

def main() :
	# Get book sub-category in tiki.vn

	try :
		sub_categories = get_sub_categories(_url)

		# Retrieve all book in all sub-categories
		for category in sub_categories:
			for book in get_books(category):
				get_book_info(book)
	except:
		traceback.print_exc(file=sys.stdout)

	finally:
		print ('Save book url')
		with open(book_url_pickle, mode='wb') as f:
			pickle.dump(book_urls, f)
		# Close connection when ending session
		close_database_connection(sqlite_connection)

if __name__ == '__main__' :

	main()
	





