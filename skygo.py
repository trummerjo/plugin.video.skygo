import requests
import json
import base64
import re
import pickle
import os
import xml.etree.ElementTree as ET
import xbmcgui

LOGIN_STATUS = { 'SUCCESS': 'T_100',
                  'SESSION_INVALID': 'S_218',
                  'OTHER_SESSION':'T_206' }


# https://www.skygo.sky.de/SILK/services/public/session/kill/web?version=12354&platform=web&product=SG&callback=_jqjsp&_1460245964532=
# => kill old session => dann normales login

class SkyGo:
    """Sky Go Class"""

    baseUrl = "http://www.skygo.sky.de"


    def __init__(self, cookiePath):
        self.sessionId = ''
        self.cookiePath = cookiePath

        # Create session with old cookies
        self.session = requests.session()

        if os.path.isfile(cookiePath):
            with open(cookiePath) as f:
                cookies = requests.utils.cookiejar_from_dict(pickle.load(f))
                self.session = requests.session()
                self.session.cookies = cookies


        return

    def isLoggedIn(self):
        """Check if User is still logged in with the old cookies"""
        r = self.session.get('https://www.skygo.sky.de/SILK/services/public/user/getdata?product=SG&platform=web&version=12354')
        #Parse json
        response = r.text[3:-1]
        response = json.loads(response)

        print response

        if response['resultMessage'] == 'OK':
            self.sessionId = response['skygoSessionId']
            print "User still logged in"
            return True
        else:
            print "User not logged in or Session on other device"
            if response['resultCode'] == LOGIN_STATUS['SESSION_INVALID']:
                print 'Session invalid - Customer Code not found in SilkCache'
                return False



    def killSessions(self):
        # Kill other sessions
        r = self.session.get('https://www.skygo.sky.de/SILK/services/public/session/kill/web?version=12354&platform=web&product=SG')
        print r.text

    def sendLogin(self, username, password):
        # Try to login
        r = self.session.get("https://www.skygo.sky.de/SILK/services/public/session/login?version=1354&platform=web&product=SG&email="+username+"&password="+password+"&remMe=true")
        #Parse jsonp
        response = r.text[3:-1]
        response = json.loads(response)
        return response

    def login(self, username, password):

        # If already logged in and active session everything is fine
        if not self.isLoggedIn():

            #remove old cookies
            self.session.cookies.clear_session_cookies()
            response = self.sendLogin(username, password)
            print response

            # if login is correct but other session is active ask user if other session should be killed
            if response['resultCode'] == 'T_206':
                killSession = xbmcgui.Dialog().yesno('Sie sind bereits eingeloggt!','Sie sind bereits auf einem anderen Geraet oder mit einem anderen Browser eingeloggt. Wollen Sie die bestehende Sitzung beenden und sich jetzt hier neu anmelden?')
                if killSession:
                    self.killSessions()
                    self.sendLogin(username, password)
                    self.isLoggedIn()
                    # Save the cookies
                    with open(self.cookiePath, 'w') as f:
                        pickle.dump(requests.utils.dict_from_cookiejar(self.session.cookies), f)
                    return True
                return False
            elif response['resultMessage'] == 'KO':
                xbmcgui.Dialog().ok('Login Fehler', 'Login fehlgeschlagen. Bitte Login Daten ueberpruefen'.encode('utf-8'))
                return False

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


