#!/usr/bin/env python

from bs4 import BeautifulSoup
import argparse
import urllib
import urllib2
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, tostring
import zlib
import os
import re
from PIL import Image
import time
import random

parser = argparse.ArgumentParser(description='ES-scraper, a scraper for EmulationStation')
parser.add_argument("-n", metavar="gameId", help="game ID", type=int)
parser.add_argument("-r", metavar="rom link", help="game ID", type=str)
args = parser.parse_args()

GAMESDB_BASE  = "http://www.gamefaqs.com/"
GAMESDB_LIST = GAMESDB_BASE + "search/index.html?platform=%s&game=%s"

DEFAULT_WIDTH  = 375
DEFAULT_HEIGHT = 350

gamesdb_platforms = {}

def resizeImage(img, output):  
	if img.size[0] > DEFAULT_WIDTH or img.size[1] > DEFAULT_HEIGHT:
		if img.size[0] > DEFAULT_WIDTH:
      			print "Boxart over %spx (width). Resizing boxart.." % DEFAULT_WIDTH
    		elif img.size[1] > DEFAULT_HEIGHT:
      			print "Boxart over %spx (height). Resizing boxart.." % DEFAULT_HEIGHT
    		img.thumbnail((DEFAULT_WIDTH, DEFAULT_HEIGHT), Image.ANTIALIAS)
    		img.save(output)

			
def downloadBoxart(path, output):
	os.system("wget -q %s --output-document=\"%s\"" % (path,output))
	try:
		print output
		resizeImage(Image.open(output), output)		
	except Exception as e:
		print "Image resize error"
		print str(e)

		
def chooseResult(options):
	if len(options) >0:		
		for i,v in enumerate(options):
			name = v[0]
			region = v[1]
			publisher = v[2]
			date = v[3]
			try:
				print " [%s] (%s) %s %s" % (i,region, name,date)
			except Exception, e:
				"Error ChooseResult : " + str(e)
		choice = raw_input("Select a result :")
		return int(choice)

		
def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
	
	
def exportList(gamelist, gamelist_path):
	indent(gamelist)
	ET.ElementTree(gamelist).write(gamelist_path)
	print "Done! List saved on %s" % gamelist_path

def getPlatforms():
	platforms = ET.parse('./GameFaqsPlatforms.xml')
	platformsroot = platforms.getroot()
	for platform in platformsroot:
		gamesdb_platforms[platform.find('es').text] = platform.find('db').text

def scrapGame(gameId):
	gamereqDesc = urllib2.Request(GAMESDB_BASE+gameId, urllib.urlencode({}),headers={'User-Agent' : "Recalbox Scraper Browser"})
	sleepTime = random.randint(0,random.randint(5,15)) % random.randint(1,random.randint(1,13))
	print "WAIT "+str(sleepTime)+"second...... to avoid blacklisting"
	time.sleep(sleepTime)
	gamereqData = urllib2.Request(GAMESDB_BASE+gameId+"/data", urllib.urlencode({}),headers={'User-Agent' : "Recalbox Scraper Browser"})
	sleepTime = random.randint(0,random.randint(5,15)) % random.randint(1,random.randint(1,13))
	print "WAIT "+str(sleepTime)+"second...... to avoid blacklisting"
	time.sleep(sleepTime)

	try:
		soupDesc = BeautifulSoup( urllib2.urlopen(gamereqDesc))
		soupData = BeautifulSoup( urllib2.urlopen(gamereqData))
		
	except Exception, e:
		print "error soup"+ str(e)
		
	
	try:    
		options = []
		imgSource = soupDesc.find('img',attrs = {'class' : 'boxshot'})["src"].replace("thumb.jpg", "front.jpg")
		print "Downloading boxart..."
		downloadBoxart(imgSource, homepath + "/Documents/downloaded_images/test.jpg")
		descTemp = soupDesc.find('div', {'class': 'desc'}).text
		
		data = soupData.find('div', {'class': 'pod_titledata'}).findAll('dt')
		if data :
			for elem in data:
				
				if elem.text == "Genre:":
					genreTemp = elem.findNext('dd').text
				if elem.text == "Developer:":
					developerTemp = elem.findNext('dd').text		
		
		tableData = soupData.findAll('td',attrs={'class' : 'cbox'})
		if tableData:		
			for elem in tableData:	
				nextTr = elem.findNext('tr')
				nameTemp = elem.findNext('td').text
				regionTemp = nextTr.find('td',attrs={'class' : 'cregion'}).text
				publisherTemp = nextTr.find('td',attrs={'class' : 'datacompany'}).text
				dateTemp = nextTr.find('td',attrs={'class' : 'cdate'}).text			
				options.append((nameTemp,regionTemp,publisherTemp,dateTemp,genreTemp,developerTemp,descTemp))
		
		gameData = options[chooseResult(options)]
		return gameData
		
	except Exception, e:
		print "error"+ str(e)

def searchGames(file,platforms):
	title = re.sub(r'\[.*?\]|\(.*?\)', '', os.path.splitext(os.path.basename(file))[0]).strip()
	#print title		
	gamereqList = urllib2.Request(GAMESDB_LIST % (59,title.replace (" ", "%20")), urllib.urlencode({}),headers={'User-Agent' : "Recalbox Scraper Browser"})
	sleepTime = random.randint(0,random.randint(5,15)) % random.randint(1,random.randint(1,13))
	print "WAIT "+str(sleepTime)+"second...... to avoid blacklisting"
	time.sleep(sleepTime)
	
	try:
		soupList = BeautifulSoup( urllib2.urlopen(gamereqList))
		scrapData = soupList.find_all('div', {'class': 'pod'})
		for elem in scrapData :
			if elem.findNext('div').text ==  "Best Matches":
				print elem
				#print elem.findNext('a', attrs={'class':'sevent_40'})['href']
			
	
	except Exception, e:
		print "error soup"+ str(e)
	
		
def gameDataToXml(gameData,homepath):

	gamelist = Element('gameList')
	game = SubElement(gamelist, 'game',{'id' : str(args.n), 'source' : "gamefaqs.com" })
	path = SubElement(game, 'path')
	name = SubElement(game, 'name')
	desc = SubElement(game, 'desc')
	image = SubElement(game, 'image')
	releasedate = SubElement(game, 'releasedate')
	publisher = SubElement(game, 'publisher')
	developer = SubElement(game, 'developer')
	rating = SubElement(game, 'rating')
	players = SubElement(game, 'players')
	genres = SubElement(game, 'genres')
	region = SubElement(game, 'region')
	romtype = SubElement(game, 'romtype')


	path.text = "testPath"
	name.text = str(gameData[0])
	desc.text = str(gameData[6])
	image.text = "testImage"
	releasedate.text = str(gameData[3])
	publisher.text = str(gameData[2])
	developer.text = str(gameData[5])
	rating.text = "testRating"
	players.text = "testPlayers"
	genres.text = str(gameData[4])
	region.text = str(gameData[1])
	romtype.text = "testRomType"

	exportList(gamelist, homepath + "/Documents/gamelist.xml")
	
if os.getuid() == 0:
    username = os.getenv("SUDO_USER")
    homepath = os.path.expanduser('~'+username+'/')
else:
    homepath = os.path.expanduser('~')	

getPlatforms()
#print gamesdb_platforms	
#gameDataToXml(scrapGame(str(args.n)),homepath)
#searchGames(args.r)


for root, dirs, allfiles in os.walk(args.r, followlinks=True):
	extension = ""
	allfiles.sort()
	#limit De recherche
	limit = 10
	i = 0
	for files in allfiles:
		if extension=="" or files.endswith(tuple(extension.split(' '))):
			try:
			
				filepath = os.path.abspath(os.path.join(root, files))
				filepath = filepath.replace(args.r, ".")
				filename = os.path.splitext(files)[0]
				if limit > i :
					searchGames(filepath,gamesdb_platforms)
				i +=1
				
			except Exception, e:
				print "error"+ str(e)



	
	




	
	
	
	

