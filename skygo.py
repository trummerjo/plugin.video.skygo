import requests
import json
import base64
import re
import cookielib
import xml.etree.ElementTree as ET


# https://www.skygo.sky.de/SILK/services/public/session/kill/web?version=12354&platform=web&product=SG&callback=_jqjsp&_1460245964532=
# => kill old session => dann normales login

class SkyGo:
    """Sky Go Class"""

    baseUrl = "http://www.skygo.sky.de"


    def __init__(self):
        self.sessionId = ''
        self.manifest = ''
        self.customerCode = ''
        #self.login()
        #self.loadMostWatched()
        return

    def login(self, username, password):

        session = requests.Session()




        r = session.get('http://www.skygo.sky.de/film/scifi--fantasy/jupiter-ascending/asset/filmsection/144836.html?sessionAction=login')


        #Try to login
        r = session.get("https://www.skygo.sky.de/SILK/services/public/session/login?version=1354&platform=web&product=SG&email="+username+"&password="+password+"&remMe=true")
        #Parse jsonp
        responseJson = r.text[3:-1]
        print r.request.headers
        print responseJson
        loginJson = json.loads(responseJson)

        if loginJson['skygoSessionId'] == '':
            print 'Login Failed'
            return False
        else:
            self.sessionId = loginJson['skygoSessionId']



            ck = cookielib.Cookie(version=0, name='siss', value=self.sessionId, port=None, port_specified=False, domain='www.skygo.sky.de', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
            session.cookies.set_cookie(ck)

            # r = session.get('http://www.skygo.sky.de/film/scifi--fantasy/jupiter-ascending/asset/filmsection/144836.html?sessionAction=login')


            # Kill other sessions
            print '######################### KILL SESSIONS: '
            r = session.get('https://www.skygo.sky.de/SILK/services/public/session/kill/web?version=12354&platform=web&product=SG')
            print r.request.headers
            print r.text
            print 'END #################################################'


            #Try to login
            r = session.get("https://www.skygo.sky.de/SILK/services/public/session/login?version=1354&platform=web&product=SG&email="+username+"&password="+password+"&remMe=true")
            #Parse jsonp
            responseJson = r.text[3:-1]
            print r.request.headers
            print responseJson
            loginJson = json.loads(responseJson)
            self.sessionId = loginJson['skygoSessionId']


            print '######################################## GET DATA!!!'
            r = session.get('https://www.skygo.sky.de/SILK/services/public/user/getdata?product=SG&platform=web&version=12354')
            print r.request.headers
            print r.text
            for cookie in session.cookies:
                print (cookie.name,cookie.value)
            print 'END ##################################################'



            print self.sessionId
            print 'Login succ'
            return True

    # def cws(self):

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


