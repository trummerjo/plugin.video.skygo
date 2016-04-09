import requests
import json
import base64
import re
import xml.etree.ElementTree as ET


class SkyGo:
    """Sky Go Class"""

    baseUrl = "http://www.skygo.sky.de"


    def __init__(self):
        self.sessionId = ''
        self.manifest = ''
        #self.login()
        #self.loadMostWatched()
        return

    def login(self):
        #Try to login
        password = ''
        mail = 'wurst%40gmx.de'
        r = requests.get("https://www.skygo.sky.de/SILK/services/public/session/login?version=1354&platform=web&product=SG&email="+mail+"&password="+password+"&remMe=false")
        #Parse jsonp
        responseJson = r.text[3:-1]

        loginJson = json.loads(responseJson)
        if loginJson['skygoSessionId'] == '':
            print 'Login Failed'
            return False
        else:
            self.sessionId = loginJson['skygoSessionId']
            print self.sessionId
            print 'Login succ'
            return True

    def getPlayInfo(self, id):
        ns = {'media': 'http://search.yahoo.com/mrss/', 'skyde': 'http://sky.de/mrss_extensions/'}
        url = self.baseUrl+"/sg/multiplatform/web/xml/player_playlist/asset/" + str(id) + ".xml"
        r = requests.get(url)
        tree = ET.ElementTree(ET.fromstring(r.text.encode('utf-8')))
        root = tree.getroot()
        manifestUrl = root.find('channel/item/media:content', ns).attrib['url']
        apixId = root.find('channel/item/skyde:apixEventId',ns).text
        return {'manifestUrl': manifestUrl, 'apixId': apixId}


    def getMostWatched(self):
        r = requests.get("http://www.skygo.sky.de/sg/multiplatform/web/json/automatic_listing/film/mostwatched/32.json")
        mostWatchedJson = r.json()
        return mostWatchedJson['listing']['asset_listing']['asset']


    def getChannels(self):
        r = requests.get("http://www.skygo.sky.de/epgd/sg/web/channelList")
        channels = r.json()['channelList']
        # Filter for channels with mediaurl
        channels = [c for c in channels if c['mediaurl'] != '']
        return channels


    def loadMovieListing(self, id):


        id = 144836 #jupiter ascending

        ns = {'media': 'http://search.yahoo.com/mrss/', 'skyde': 'http://sky.de/mrss_extensions/'}

        url = "http://www.skygo.sky.de/sg/multiplatform/web/xml/player_playlist/asset/" + str(id) + ".xml"
        r = requests.get(url)
        tree = ET.ElementTree(ET.fromstring(r.text.encode('utf-8')))
        root = tree.getroot()
        content = root.find('channel/item/media:content', ns)
        manifestUrl = content.attrib['url']
        self.manifest = SkyGoManifest(manifestUrl)


class SkyGoManifest:
    """Sky Go Manifest Class"""

    def __init__(self, url):
        self.protectionHeader = ''


        self.load(url)
        return

    def load(self, url):
        r = requests.get(url)
        root = ET.fromstring(r.text.encode('utf-8')[4:])
        content = root.find('Protection/ProtectionHeader')

        base64Protection = content.text
        base64Protection = base64Protection.replace(" ", "")

        xml = base64.decodestring(base64Protection)

        p = re.compile('<KID>(.*?)</KID>', re.IGNORECASE)

        m = re.search(p, str(xml).decode('utf-16'))
        print m.group(1)


