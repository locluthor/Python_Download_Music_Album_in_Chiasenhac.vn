from bs4 import BeautifulSoup
import requests
import re
import urllib
from urllib.request import urlopen                                                                                                                                                            
from urllib.parse import quote    
# URL use for scraping
_url = 'https://tiki.vn/nha-sach-tiki'

# Tiki 3 bigs categories
books_categories = [r'/sach-truyen-tieng-viet',
					r'/sach-tieng-anh',
					r'/ebook']

# Store all tiki books in here
books = set()


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
		tags = soup.findAll("div", { "class" : "list-group-item book-home-catlink" })
		
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
def is_last_page(page) :

	# lpage = 'https://tiki.vn/fiction-literature/c9?page=20'

	with requests.Session() as session :

		html = session.get(page)
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

			divs = soup.findAll("div", { "class" : "product-box-list" })

			# print (str(divs[0]).encode('utf-8', 'ignore'))

			for div in divs :
				# print (divs.a['href'])
				strs = str(divs).encode('utf-8', 'ignore')

				hrefs = re.findall(b'href="(.*?)"', strs)

				for href in hrefs :
					print ('Extracting .... book : ', href.decode('utf-8'))
					yield href.decode('utf-8')
					# books.add(href.decode('utf-8'))

			print ('last page : ', category, ' ', page)

			# print ('Number of books : ', len(books))

			if is_last_page(page_url) :
		
				break

			page += 1


	# return books

# Get books metadata
def get_book_info(book_url) :

	# url = 'https://tiki.vn/bi-mat-dotcom-p269389.html?ref=c316.c846.c848.c7498.'

	with requests.Session() as session :
		# Get html and parse it 
		html = session.get( book_url )
		soup = BeautifulSoup(html.content, 'html.parser')

		# Get book sku id in <input id="product_sku
		_input = soup.find("input", { "id" : "product_sku" })
		book_sku_id = _input['value']

		# Get book name  <h1 class="item-name"
		h1 = soup.find('h1', {'class' : 'item-name'})
		book_name =  h1.string
		# Get book price  <input id="product_price
		_input = soup.find("input", { "id" : "product_price" })
		book_price = _input['value']

		# Get book cover image
		img = soup.find('img', {'itemprop' : 'image'})
		image_url = img['src']

		# Handle url with unicode character
		# We must not encode the ':' character
		sString = image_url.split(':')
		sString[1] = quote(sString[1])	
		# Join 2 String together with ':' in between
		image_url = sString[0] + ':' + sString[1]
		# Download book cover and save it with name is it's sku_id
		urllib.request.urlretrieve(image_url, book_sku_id + '.jpg')
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
			index_nxb = infos.index('Nhà xuất bản')
			nxb = infos[index_nxb + 1] # nxb value is next to nxb index
		except ValueError : # except that nhaxuatban info is missing
			nxb = ''
		# print (index_nxb)

		# Find tác giả
		try : 
			index_author = infos.index('Author') # Author value is next to Author index
			author = infos[index_author + 1]
		except ValueError : # except that nhaxuatban info is missing
			author = ''		

		# print (index_author)

		# # Find số trang
		try : 
			index_num_page= infos.index('Số trang') # Số trang value is next to Số trang index
			num_page = infos[index_num_page + 1]
		except ValueError : # except that nhaxuatban info is missing
			num_page = 0				

		# print (index_num_page)

		# Find Ngày xuất bản
		try : 
			index_publish_date= infos.index('Ngày xuất bản') # Ngày xuất bản value is next to Ngày xuất bản index
			publish_date = infos[index_publish_date + 1]
		except ValueError : # except that nhaxuatban info is missing
			publish_date = ''				

		# print (index_publish_date)

		# with open('out.txt', mode='w', encoding='utf-8') as f:
		# 	f.write(nxb + '\n')
		# 	f.write(author + '\n')
		# 	f.write(num_page + '\n')
		# 	f.write(publish_date + '\n')





if __name__ == '__main__' :

	sub_categories = get_sub_categories(_url)

	# print ('\n'.join(sub_categories))

	# get_book_info('')

	for category in sub_categories :
		for book in get_books(category) :
			get_book_info(book)

	# print ('Number of books : ', len(books))

	# print ( '\n'.join(books) )



