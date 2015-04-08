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
import glob
import sys
import datetime

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
		#print output
		resizeImage(Image.open(output), output)
	except Exception as e:
		print "Image resize error"
		print str(e)

def readConfig(file):
	systems=[]
	config = ET.parse(file)
	configroot = config.getroot()
	for child in configroot.findall('system'):

		nameElement = child.find('name')
		pathElement = child.find('path')
		platformElement = child.find('platform')
		extElement = child.find('extension')

		if nameElement is not None and pathElement is not None and platformElement is not None and extElement is not None:
			name = nameElement.text
			path = re.sub('^~', homepath, pathElement.text, 1)
			ext = extElement.text
			platform = platformElement.text
			numfiles = len(glob.glob(path+'/**'))

			if numfiles > 0:
				system=(name,path,ext,platform)
				systems.append(system)


	return systems

def getPlatformId(_platforms):
	platforms = _platforms.split(',')

	for (i, platform) in enumerate(platforms):
		if gamesdb_platforms[platform] is not None: platform = gamesdb_platforms[platform]

	return platform
	#print platforms

def getRomType(filename):
	if "(Proto)" in filename :
		return "Prototype"
	else :
		return "Official"

def getRegion(filename):
	region = re.search('\((.+?)\)', filename)
	if region :
		return region.group(1)
	else:
		return ""

def getPlayers(strplayer):
	players = ['8','7','6','5','4','3','2','1']
	for i,v in enumerate(players):
		if v in strplayer:
			return v


def getDate(date):
	month = ['January','February','March','April','May','June','July','August','September','October','November','Deceber']
	if "/" in date:

		slist = date.split("/")
		if 59 <= int(slist[2]) <= 99:
			year = '19' + slist[2]
		else:
			year = '20' + slist[2]
		formatDate = datetime.date(int(year),int(slist[0]),int(slist[1]))

	elif len(date) is 4:

		formatDate = datetime.date(int(date),1,1)

	else :
		for i,v in enumerate(month):
			if v in date:
				numMonth = i+1
				year = date.replace(v,"").strip()
				formatDate = datetime.date(int(year),numMonth,1)

	ReleaseDate = str(formatDate).replace("-","")+"T000000"
	return ReleaseDate

def getGenre(genre):
	gameDB = [ 'Action',
	'Adventure',
	'Construction and Management Simulation',
    'Role-Playing',
    'Puzzle',
    'Strategy',
    'Racing',
    'Shooter',
    'Life Simulation',
    'Fighting',
    'Sports',
    'Sandbox',
    'Flight Simulator',
    'MMO',
    'Platform',
    'Stealth',
    'Music',
    'Horror']

	for i,v in enumerate(gameDB):
		if v in genre:
			return v

def skipGame(list, filepath):
	for game in list.iter("game"):
		if game.findtext("path") == filepath:
			print "Game \"%s\" already in gamelist. Skipping.." % os.path.basename(filepath)
			return True


def scanFiles(SystemInfo):
	print "System info : " + str(SystemInfo)
	emulatorname = SystemInfo[0]
	folderRoms = SystemInfo[1]
	extension = SystemInfo[2]
	platformname = SystemInfo[3]
	platform = getPlatformId(platformname)



	gamelistExists = False
	existinglist = None


	print "Scanning folder..(%s)" % folderRoms
	gamelist_path = gamelists_path+"%s/gamelist.xml" % emulatorname

	if not os.path.exists(boxart_path + "%s" % platformname):
		print "NOT EXISTS"+boxart_path + platformname
		os.mkdir(boxart_path + "%s" % platformname)

	if os.path.exists(gamelist_path):

		try:
			print "path : " +gamelist_path
			existinglist = ET.parse(gamelist_path)
			gamelistExists=True
		except:
			gamelistExists = False
			print "There was an error parsing the list or file is empty"


	for root, dirs, allfiles in os.walk(folderRoms, followlinks=True):
		extension = ""
		allfiles.sort()
		#limit De recherche

		gamelist = Element('gameList')
		for files in allfiles:

			if extension=="" or files.endswith(tuple(extension.split(' '))):
				try:
					filepath = os.path.abspath(os.path.join(root, files))
					filepath = filepath.replace(folderRoms, ".")
					filename = os.path.splitext(files)[0]
					if gamelistExists:
						if skipGame(existinglist,filepath):
							continue
					print "\nTrying to identify %s.." % files


					gameToScrap = searchGames(filepath,platform)
					#gameDataToXml(scrapGame(str(gameToScrap[1])),gamelist_path,gamelistExists,existinglist,filepath)
					gamelist = gameDataToXml(scrapGame(str(gameToScrap[1]),platformname,filename),filepath,gamelist)


				except KeyboardInterrupt:
					print "Ctrl+C detected. Closing work now..."
					break
				except Exception as e:
					print "Exception caught! %s" % e
		exportList(gamelist, gamelist_path,gamelistExists,existinglist)



def chooseResult(options):
	if len(options) >0:
		if len(options) == 1:
			return 0
		print "many match found : "
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

def chooseSearchResult(options):
	if len(options) >0:
		if len(options) == 1:
			return 0
		print "choose the version : "
		for i,v in enumerate(options):
			name = v[0]
			gameId = v[1]

			try:
				print " [%s] %s" % (i,name)
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


def exportList(gamelist, gamelist_path,gamelistExists,existinglist):
	if gamelistExists:
		for game in gamelist.iter('game'):
			existinglist.getroot().append(game)
		indent(existinglist.getroot())
		ET.ElementTree(existinglist.getroot()).write(gamelist_path)
		print "Done! List saved on %s" % gamelist_path
	else:
		indent(gamelist)
		ET.ElementTree(gamelist).write(gamelist_path)
		print "Done! List saved on %s" % gamelist_path

def getPlatforms():
	platforms = ET.parse('./GameFaqsPlatforms.xml')
	platformsroot = platforms.getroot()
	for platform in platformsroot:
		gamesdb_platforms[platform.find('es').text] = platform.find('db').text

def scrapGame(gameId,emulatorname,filename):
	gamereqDesc = urllib2.Request(GAMESDB_BASE+gameId, urllib.urlencode({}),headers={'User-Agent' : "Recalbox Scraper Browser"})
	#sleepTime = random.randint(0,random.randint(5,15)) % random.randint(1,random.randint(1,13))
	print "WAIT "+str(2)+" second...... to avoid blacklisting"
	time.sleep(2)
	gamereqData = urllib2.Request(GAMESDB_BASE+gameId+"/data", urllib.urlencode({}),headers={'User-Agent' : "Recalbox Scraper Browser"})
	#sleepTime = random.randint(0,random.randint(5,15)) % random.randint(1,random.randint(1,13))
	print "WAIT "+str(2)+" second...... to avoid blacklisting"
	time.sleep(2)

	try:
		soupDesc = BeautifulSoup( urllib2.urlopen(gamereqDesc))
		soupData = BeautifulSoup( urllib2.urlopen(gamereqData))

	except Exception, e:
		print "error soup"+ str(e)


	try:
		options = []
		imgSource = soupDesc.find('img',attrs = {'class' : 'boxshot'})["src"].replace("thumb.jpg", "front.jpg")
		print "Downloading boxart..."
		imgpath = boxart_path + "%s/%s-image%s" % (emulatorname, filename,os.path.splitext(imgSource)[1])
		downloadBoxart(imgSource, imgpath)
		descTemp = soupDesc.find('div', {'class': 'desc'}).text
		data = soupData.find('div', {'class': 'pod_titledata'}).findAll('dt')

		if data :
			genreTemp = None
			developerTemp = None
			numberofplayerTemp = None
			for elem in data:

				if elem.text == "Genre:":
					genreTemp = elem.findNext('dd').text
				if elem.text == "Developer:":
					developerTemp = elem.findNext('dd').text
				if "Players" in elem.text:
					#print elem.text
					#print "Value" + elem.findNext('dd').text
					numberofplayerTemp = elem.findNext('dd').text



		tableData = soupData.findAll('td',attrs={'class' : 'cbox'})
		if tableData:
			for elem in tableData:
				nextTr = elem.findNext('tr')
				nameTemp = elem.findNext('td').text
				regionTemp = nextTr.find('td',attrs={'class' : 'cregion'}).text
				publisherTemp = nextTr.find('td',attrs={'class' : 'datacompany'}).text
				dateTemp = nextTr.find('td',attrs={'class' : 'cdate'}).text
				options.append((nameTemp,regionTemp,publisherTemp,dateTemp,genreTemp,developerTemp,descTemp,imgpath,filename,gameId,numberofplayerTemp))

		gameData = options[chooseResult(options)]
		return gameData

	except Exception, e:
		print "error: "+ str(e)

def searchGames(file,platform):
	options = []
	title = re.sub(r'\[.*?\]|\(.*?\)', '', os.path.splitext(os.path.basename(file))[0]).strip()

	gamereqList = urllib2.Request(GAMESDB_LIST % (platform,title.replace (" ", "%20")), urllib.urlencode({}),headers={'User-Agent' : "Recalbox Scraper Browser"})
	#gamereqList = urllib2.Request(GAMESDB_LIST % (63, "mario"), urllib.urlencode({}),headers={'User-Agent' : "Recalbox Scraper Browser"})
	#sleepTime = random.randint(0,random.randint(5,15)) % random.randint(1,random.randint(1,13))
	print "WAIT "+str(2)+" second...... to avoid blacklisting"
	time.sleep(2)

	try:
		soupList = BeautifulSoup( urllib2.urlopen(gamereqList))
		scrapData = soupList.find_all('div', {'class': 'pod'})
		for elem in scrapData :
			if elem.findNext('div').text ==  "Best Matches":
				gameTitles = elem.find_all('td', attrs={'class' : 'rtitle'})

				for gameTitle in gameTitles :
					#get link + remove first /
					gameLink = gameTitle.find('a')['href'][1:]
					gameId = gameLink[gameLink.find("/")+1:gameLink.find("-")]
					options.append((gameTitle.text.strip(),gameId))

		gameChoice = options[chooseSearchResult(options)]

		return gameChoice


	except Exception, e:
		print "error soup"+ str(e)


def gameDataToXml(gameData,filepath,gamelist):



	#gamelist = Element('gameList')
	game = SubElement(gamelist, 'game',{'id' : str(gameData[9]), 'source' : "gamefaqs.com" })
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


	if filepath is not None:
		path.text = str(filepath)
	if gameData[8] is not None:
		name.text = str(gameData[8])
	if gameData[6] is not None:
		desc.text = str(gameData[6])
	if gameData[7] is not None:
		image.text = str(gameData[7])
		romtype.text = getRomType(str(gameData[7]))
	if gameData[3] is not None:
		releasedate.text = getDate(str(gameData[3]))
	if gameData[2] is not None:
		publisher.text = str(gameData[2])
	if gameData[5] is not None:
		developer.text = str(gameData[5])
	if gameData[10] is not None:
		players.text = getPlayers(str(gameData[10]))
	if gameData[4] is not None:
		genres.text = getGenre(str(gameData[4]))
	if gameData[8] is not None:
		region.text = getRegion(str(gameData[8]))



	#exportList(gamelist, gamelist_path,gamelistExists,existinglist)
	return gamelist


if os.getuid() == 0:
	username = os.getenv("SUDO_USER")
	homepath = os.path.expanduser('~'+username+'/')
else:
	homepath = os.path.expanduser('~')

essettings_path = homepath + "/Documents/Recalbox-scraper/es_systems.cfg"
gamelists_path = homepath + "/Documents/Recalbox-scraper/gamelists/"
boxart_path = homepath + "/Documents/Recalbox-scraper/downloaded_images/"

getPlatforms()
#print gamesdb_platforms
#gameDataToXml(scrapGame(str(args.n)),homepath)
#searchGames(args.r)

if not os.path.exists(essettings_path):
	essettings_path = "/etc/emulationstation/es_systems.cfg"

	try:
		print "try to open : " + essettings_path
		config=open(essettings_path)
	except IOError as e:
		sys.exit("Error when reading config file: %s \nExiting.." % e.strerror)

ES_systems = readConfig(open(essettings_path))
print "config" + ES_systems
for i,v in enumerate(ES_systems):
	print "[%s] %s" % (i,v[0])
try:
	var = int(raw_input("System ID: "))
	print "choix : " + var
	scanFiles(ES_systems[var])
except:
		print "erreur choix"
		sys.exit()
