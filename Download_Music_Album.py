from bs4 import BeautifulSoup
# from BeautifulSoup import *
import urllib
import re
import os
import sys
import requests
import getopt

_url = '' # album url to download
_format = 'MP3 320kbps' # [m4a, flac, mp3]
_savedir = 'D:/Music/Download'#save folder

def MapTypeToFormat(type) :
	'''
	#hardcode to follow chiasenhac format
	'''
	if type == 'm4a' :
		return 'M4A 500kbps' 
	if type == 'flac' :
		return 'FLAC Lossless'
	return 'MP3 320kbps' #default download mp3
	

def GetArguments(argv) :
	'''
	Parse arguments for cmd to variable
	'''
	try :
		#	getopt take 3 arguments 
		# 	argv : arguments list for cmd
		#	2nd str : short flag (h : -h, u: must follow by value)
		#	3rd str : long flag according short flag (-h <--> --help)
		opts, args = getopt.getopt(argv, "hu:f:s:", ["help", "url=", 'format=', 'savedir='])
	except getopt.GetoptError :
		# usage() #todo Unix rule
		sys.exit(2)

	for opt, arg in opts :
		if opt in ("-h", "--help") :	
			sys.exit()
		elif opt in ("-u", "--url") :
			global _url
			_url = arg
		elif opt in ('-f', '--format') :
			global _format
			_format = MapTypeToFormat(arg)
		elif opt in ('-s', '--savedir') :
			global _savedir
			_savedir = arg

#temporary hard code username and password
username = 'loc.luthor' 
password = 'haydoiday'


def LoginChiasenhac(username, password) :
	#POST 4 pramater to login chiasenhac
	logindata = {'username':username, 'password':password, 'redirect':'', 'login':'%C4%90%C4%83ng+nh%E1%BA%ADp'}
	loginSession = requests.Session()
	loginurl = 'http://chiasenhac.vn/login.php'
	loginSession.post(loginurl, data = logindata)
	return loginSession

loginSession  = LoginChiasenhac(username, password)#use this logined sesstion to download high quality music


def reporthook(blocknum, blocksize, totalsize):
    readsofar = blocknum * blocksize
    if totalsize > 0:
        percent = readsofar * 1e2 / totalsize
        s = "\r%5.1f%% %*dMB / %dMB" % (
            percent, len(str(totalsize)), readsofar / (1024**2), totalsize / (1024**2))
        sys.stderr.write(s)
        if readsofar >= totalsize: # near the end
            sys.stderr.write("\n")
    else: # total size is unknown
        sys.stderr.write("read %d\n" % (readsofar,))



def GetDownloadLinks(urlList) :
	# temp = []
	downloadLinks = set() #using set to remove duplicate links
	#Extract all download link in urlList
	for link in urlList :
		#find download link with regular expression
		tempLink = re.findall('[\S]+_download.html', link)
		if len(tempLink) != 0:
			downloadLinks.add(tempLink[0])
	
	return downloadLinks
		

def GetAllTagInUrl(url, inputTag):
	# loginSession  = LoginChiasenhac(username, password)
	listUrl = []
	html = loginSession.get(url)
	soup = BeautifulSoup(html.content, "html.parser")
	#Retrieve all of the inputTag tags
	tags = soup(inputTag)
	for tag in tags:
		 listUrl.append(str(tag.get('href', None)))
		 
	return listUrl

def GetDirectLink(url) :
	# loginSession  = LoginChiasenhac(username, password)
	html = loginSession.get(url)

	soup = BeautifulSoup(html.content, "html.parser")
	
	#download link in place inside javascript tab
	tags = soup('script')
	# os.system('pause')
	# print tags
	for tag in tags :
		script = str(tag.string)
		# print script
		# print ('format : ', _format)
		links = re.findall(r'href="(http:.*\[' + _format + '\].+?)"', script)
		if len(links) != 0 : 
			return links[0]
	#return only first link, because the second link is provide when adblock is turn on	-> not valid
	return ''
	
def GetMp3AlbumLink(urlList) :
	albumLink = []
	for link in urlList :
		temp = GetDirectLink(link)
		print (temp)
		albumLink.append( temp )
	return albumLink

def DownloadFile( link,  saveDir) :
	temp = link.split('/')
	filename = temp[len(temp) - 1]
	filename = filename.replace('%20', ' ')
	print ('downloading ' , saveDir , '/' , filename)
	if not os.path.exists(saveDir) :
		os.makedirs(saveDir)
	urllib.request.urlretrieve( link , saveDir + '/' + filename, reporthook)

def DownloadAlbum( urlList , _savedir) :
	for link in urlList :
		DownloadFile(link, _savedir)
		

if __name__ == '__main__' :
	
	GetArguments(sys.argv[1:]) # argv[0] is the name of script itself
	song_urls = GetDownloadLinks( GetAllTagInUrl(_url, 'a'))
	albumLink = GetMp3AlbumLink( song_urls )
	DownloadAlbum(albumLink, _savedir)

