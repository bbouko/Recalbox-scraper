#!/usr/bin/env python

from bs4 import BeautifulSoup
import argparse
import urllib
import urllib2
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, tostring
import zlib
import os
from PIL import Image

parser = argparse.ArgumentParser(description='ES-scraper, a scraper for EmulationStation')
parser.add_argument("-n", metavar="gameId", help="game ID", type=int)
args = parser.parse_args()

GAMESDB_BASE_DESC  = "http://www.gamefaqs.com/"+str(args.n)
GAMESDB_BASE_DATA = "http://www.gamefaqs.com/"+str(args.n) +"/data"
DEFAULT_WIDTH  = 375
DEFAULT_HEIGHT = 350

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

		
if os.getuid() == 0:
    username = os.getenv("SUDO_USER")
    homepath = os.path.expanduser('~'+username+'/')
else:
    homepath = os.path.expanduser('~')		
		
gamereqDesc = urllib2.Request(GAMESDB_BASE_DESC, urllib.urlencode({}),headers={'User-Agent' : "Recalbox Scraper Browser"})
gamereqData = urllib2.Request(GAMESDB_BASE_DATA, urllib.urlencode({}),headers={'User-Agent' : "Recalbox Scraper Browser"})

try:
	soupDesc = BeautifulSoup( urllib2.urlopen(gamereqDesc) )
	soupData = BeautifulSoup( urllib2.urlopen(gamereqData) )
	
except Exception, e:
    print "error soup"+ str(e)

lin=0
try:    
	options = []
	imgSource = soupDesc.find('img',attrs = {'class' : 'boxshot'})["src"].replace("thumb.jpg", "front.jpg")
	print "Downloading boxart.."
	downloadBoxart(imgSource, homepath + "/Documents/downloaded_images/test"+str(lin)+".jpg")
	descTemp = soupDesc.find('div', {'class': 'desc'}).text
	
	data = soupData.find('div', {'class': 'pod_titledata'}).findAll('dt')
	if data :
		for elem in data:
			#print elem.text
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
			#print elem.findNext('td').text + " " + nextTr.find('td',attrs={'class' : 'cregion'}).text + " " + nextTr.find('td',attrs={'class' : 'datacompany'}).text + " " + nextTr.find('td',attrs={'class' : 'cdate'}).text
			options.append((nameTemp,regionTemp,publisherTemp,dateTemp,genreTemp,developerTemp,descTemp))
	#choice = chooseResult(options)
	gameData = options[chooseResult(options)]
	#print str(gameData)

	
except Exception, e:
    print "error"+ str(e)
	

	
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

#print str(gameData)
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



	
	
	
	

