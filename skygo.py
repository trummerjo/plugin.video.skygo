import base64
import struct

import requests
import json
import re
import datetime
import time
import pickle
import os
import xml.etree.ElementTree as ET

import xbmc
import xbmcgui
import xbmcaddon

LOGIN_STATUS = { 'SUCCESS': 'T_100',
                  'SESSION_INVALID': 'S_218',
                  'OTHER_SESSION':'T_206' }

licence_url = 'https://wvguard.sky.de/WidevineLicenser/WidevineLicenser|User-Agent=Mozilla%2F5.0%20(X11%3B%20Linux%20x86_64)%20AppleWebKit%2F537.36%20(KHTML%2C%20like%20Gecko)%20Chrome%2F49.0.2623.87%20Safari%2F537.36&Referer=http%3A%2F%2Fwww.skygo.sky.de%2Ffilm%2Fscifi--fantasy%2Fjupiter-ascending%2Fasset%2Ffilmsection%2F144836.html&Content-Type=|{SSM}|'

addon = xbmcaddon.Addon()
autoKillSession = addon.getSetting('autoKillSession')
print autoKillSession
datapath = xbmc.translatePath(addon.getAddonInfo('profile'))
cookiePath = datapath + 'COOKIES'

class SkyGo:
    """Sky Go Class"""

    baseUrl = "https://www.skygo.sky.de"
    entitlements = []


    def __init__(self):
        self.sessionId = ''
        self.cookiePath = cookiePath
        self.licence_url = licence_url

        # Create session with old cookies
        self.session = requests.session()
        self.session.headers.setdefault('User-Agent','Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36')

        if os.path.isfile(cookiePath):
            with open(cookiePath) as f:
                cookies = requests.utils.cookiejar_from_dict(pickle.load(f))
                self.session = requests.session()
                self.session.cookies = cookies
        return


    def getLandingPage(self):
        return self.getPage(self.baseUrl + '/sg/multiplatform/web/json/landingpage/1.json')

    def getPage(self, url):
        r = requests.get(url)
        return r.json()['listing']

    def isLoggedIn(self):
        """Check if User is still logged in with the old cookies"""
        r = self.session.get('https://www.skygo.sky.de/SILK/services/public/user/getdata?product=SG&platform=web&version=12354')
        #Parse json
        response = r.text[3:-1]
        response = json.loads(response)

        print response

        if response['resultMessage'] == 'OK':
            self.sessionId = response['skygoSessionId']
            self.entitlements = response['entitlements']
            print "User still logged in"
            return True
        else:
            print "User not logged in or Session on other device"
            if response['resultCode'] == LOGIN_STATUS['SESSION_INVALID']:
                print 'Session invalid - Customer Code not found in SilkCache'
                return False
        return False



    def killSessions(self):
        # Kill other sessions
        r = self.session.get('https://www.skygo.sky.de/SILK/services/public/session/kill/web?version=12354&platform=web&product=SG')

    def sendLogin(self, username, password):
        # Try to login
        login = "email="+username
        if not re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", username):
        	login = "customerCode="+username
        
        r = self.session.get("https://www.skygo.sky.de/SILK/services/public/session/login?version=1354&platform=web&product=SG&"+login+"&password="+password+"&remMe=true")
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

            # if login is correct but other session is active ask user if other session should be killed
            if response['resultCode'] == 'T_206':
                kill_session = False
                if autoKillSession == 'true':
                    kill_session = True

                if not kill_session:
                    kill_session = xbmcgui.Dialog().yesno('Sie sind bereits eingeloggt!','Sie sind bereits auf einem anderen Geraet oder mit einem anderen Browser eingeloggt. Wollen Sie die bestehende Sitzung beenden und sich jetzt hier neu anmelden?')

                if kill_session:
                    # Kill all Sessions (including ours)
                    self.killSessions()
                    # Session killed so login again
                    self.sendLogin(username, password)
                    # Activate Session
                    self.isLoggedIn()
                    # Save the cookies
                    with open(self.cookiePath, 'w') as f:
                        pickle.dump(requests.utils.dict_from_cookiejar(self.session.cookies), f)
                    return True
                return False
            elif response['resultMessage'] == 'KO':
                xbmcgui.Dialog().notification('Login Fehler', 'Login fehlgeschlagen. Bitte Login Daten ueberpruefen', icon=xbmcgui.NOTIFICATION_ERROR)
                return False
            elif response['resultCode'] == 'T_100':
                # Activate Session with new test if user is logged in
                self.isLoggedIn()
                return True
        else:
            return True

        # If any case is not matched return login failed
        return False

    def getPlayInfo(self, id='', url=''):
        ns = {'media': 'http://search.yahoo.com/mrss/', 'skyde': 'http://sky.de/mrss_extensions/'}

        # If no url is given we assume that the url hast to be build with the id
        if url == '':
            url = self.baseUrl+"/sg/multiplatform/web/xml/player_playlist/asset/" + str(id) + ".xml"

        r = requests.get(url)
        tree = ET.ElementTree(ET.fromstring(r.text.encode('utf-8')))
        root = tree.getroot()
        manifest_url = root.find('channel/item/media:content', ns).attrib['url']
        apix_id = root.find('channel/item/skyde:apixEventId', ns).text
        package_code = root.find('channel/item/skyde:packageCode', ns).text


        return {'manifestUrl': manifest_url, 'apixId': apix_id, 'duration': 0, 'package_code': package_code}

    def getCurrentEvent(self, epg_channel_id):
        # Save date for fure use
        now = datetime.datetime.now()
        current_date = now.strftime("%d.%m.%Y")
        # Get Epg information
        print 'http://www.skygo.sky.de/epgd/sg/web/eventList/'+current_date+'/'+epg_channel_id+'/'
        r = requests.get('http://www.skygo.sky.de/epgd/sg/web/eventList/'+current_date+'/'+epg_channel_id+'/')
        events = r.json()[epg_channel_id]
        for event in events:
            start_date = datetime.datetime(*(time.strptime(event['startDate'] + ' ' + event['startTime'], '%d.%m.%Y %H:%M')[0:6]))
            end_date = datetime.datetime(*(time.strptime(event['endDate'] + ' ' + event['endTime'], '%d.%m.%Y %H:%M')[0:6]))
            # Check if event is running event
            if start_date < now < end_date:
                return event
        # Return False if no current running event
        return False

    def getEventPlayInfo(self, event_id, epg_channel_id):
        # If not Sky news then get details id else use hardcoded playinfo_url
        if epg_channel_id != '17':
            r = requests.get('http://www.skygo.sky.de/epgd/sg/web/eventDetail/'+event_id+'/'+epg_channel_id+'/')
            event_details_link = r.json()['detailPage']
            # Extract id from details link
            p = re.compile('/([0-9]*)\.html', re.IGNORECASE)
            m = re.search(p, event_details_link)
            playlist_id = m.group(1)
            playinfo_url = self.baseUrl+'/sg/multiplatform/web/xml/player_playlist/asset/' + playlist_id + '.xml'
        else:
            playinfo_url = self.baseUrl+'/sg/multiplatform/web/xml/player_playlist/ssn/127.xml'

        return self.getPlayInfo(url=playinfo_url)

    def may_play(self, entitlement):
        return entitlement in self.entitlements

    def getMostWatched(self):
        r = requests.get("http://www.skygo.sky.de/sg/multiplatform/web/json/automatic_listing/film/mostwatched/32.json")
        mostWatchedJson = r.json()
        return mostWatchedJson['listing']['asset_listing']['asset']

    def getListing(self, path):
        r = requests.get(self.baseUrl + path)
        return r.json()['listing']['asset_listing']['asset']


    def getChannels(self):
        r = requests.get("http://www.skygo.sky.de/epgd/sg/web/channelList")
        channels = r.json()['channelList']
        # Filter for channels with mediaurl
        channels = [c for c in channels if c['mediaurl'] != '']

        return channels


    def getSeriesInfo(self, series_id):
        r = requests.get(self.baseUrl + "/sg/multiplatform/web/json/details/series/"+ series_id +"_global.json")
        return r.json()['serieRecap']['serie']

    def get_init_data(self, session_id, apix_id):
        init_data = 'kid={UUID}&sessionId='+session_id+'&apixId='+apix_id+'&platformId=WEB&product=BW&channelId='
        init_data = struct.pack('1B', *[30])+init_data
        init_data = base64.urlsafe_b64encode(init_data)
        return init_data


