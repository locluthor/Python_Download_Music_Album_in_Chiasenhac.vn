from BeautifulSoup import *
import urllib
import re
import os
import sys

url = raw_input('Enter Chiasenhac album url : ')
saveDir = raw_input('Enter Save Folder : ')



def reporthook(blocknum, blocksize, totalsize):
    readsofar = blocknum * blocksize
    if totalsize > 0:
        percent = readsofar * 1e2 / totalsize
        s = "\r%5.1f%% %*d / %d" % (
            percent, len(str(totalsize)), readsofar, totalsize)
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
	#remove duplicate link 
	
	# downloadLinks = set(temp)
	
	return downloadLinks
		

def GetAllTagInUrl(url, inputTag):

	listUrl = []
	html = urllib.urlopen(url).read()
	soup = BeautifulSoup(html)
	#Retrieve all of the inputTag tags
	tags = soup(inputTag)
	for tag in tags:
		 listUrl.append(str(tag.get('href', None)))
		 
	return listUrl

def GetDirectLink(url) :
	html = urllib.urlopen(url).read()
	soup = BeautifulSoup(html)
	
	#download link in place inside javascript tab
	tags = soup('script')
	for tag in tags :
		script = str(tag.string)
		links = re.findall('href="(http:.*\[MP3 320kbps\].+?)"', script)
		if len(links) != 0 : 
			return links[0]
	#return only first link, because the second link is provide when adblock is turn on	-> not valid
	return ''
	
def GetMp3AlbumLink(urlList) :
	albumLink = []
	for link in urlList :
		temp = GetDirectLink(link)
		print temp
		albumLink.append( temp )
	return albumLink

def DownloadFile( link ) :
	temp = link.split('/')
	filename = temp[len(temp) - 1]
	filename = filename.replace('%20', ' ')
	print 'downloading ' + saveDir + '/' + filename
	if not os.path.exists(saveDir) :
		os.makedirs(saveDir)
	urllib.urlretrieve( link , saveDir + '/' + filename, reporthook)

def DownloadAlbum( urlList ) :
	for link in urlList :
		DownloadFile(link)
		

song_urls = GetDownloadLinks( GetAllTagInUrl(url, 'a'))
albumLink = GetMp3AlbumLink( song_urls )
DownloadAlbum(albumLink)

