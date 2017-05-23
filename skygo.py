import sys
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
import xbmcaddon, xbmcplugin

LOGIN_STATUS = { 'SUCCESS': 'T_100',
                  'SESSION_INVALID': 'S_218',
                  'OTHER_SESSION':'T_206' }

addon = xbmcaddon.Addon()
addon_handle = int(sys.argv[1])
autoKillSession = addon.getSetting('autoKillSession')
username = addon.getSetting('email')
password = addon.getSetting('password')
print autoKillSession
datapath = xbmc.translatePath(addon.getAddonInfo('profile'))
cookiePath = datapath + 'COOKIES'

platform = 0
osAndroid = 1
if xbmc.getCondVisibility('system.platform.android'):
    platform = osAndroid

license_url = 'https://wvguard.sky.de/WidevineLicenser/WidevineLicenser|User-Agent=Mozilla%2F5.0%20(X11%3B%20Linux%20x86_64)%20AppleWebKit%2F537.36%20(KHTML%2C%20like%20Gecko)%20Chrome%2F49.0.2623.87%20Safari%2F537.36&Referer=http%3A%2F%2Fwww.skygo.sky.de%2Ffilm%2Fscifi--fantasy%2Fjupiter-ascending%2Fasset%2Ffilmsection%2F144836.html&Content-Type=|R{SSM}|'
license_type = 'com.widevine.alpha'
android_deviceid = ''
if platform == osAndroid:
    import uuid
    license_url = ''
    license_type = 'com.microsoft.playready'
            
    if addon.getSetting('android_deviceid'):
        android_deviceid = addon.getSetting('android_deviceid')
    else:
        android_deviceid = str(uuid.uuid1())
        addon.setSetting('android_deviceid', android_deviceid)

# Get installed inputstream addon
def getInputstreamAddon():
    r = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1, "method": "Addons.GetAddonDetails", "params": {"addonid":"inputstream.adaptive", "properties": ["enabled"]}}')
    data = json.loads(r)
    if not "error" in data.keys():
        if data["result"]["addon"]["enabled"] == True:
            return True
        
    return None

class SkyGo:
    """Sky Go Class"""

    baseUrl = "https://www.skygo.sky.de"
    entitlements = []


    def __init__(self):
        self.sessionId = ''
        self.cookiePath = cookiePath
        self.license_url = license_url
        self.license_type = license_type
        self.android_deviceId = android_deviceid

        # Create session with old cookies
        self.session = requests.session()
        self.session.headers.setdefault('User-Agent','Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36')

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

        r = self.session.get("https://www.skygo.sky.de/SILK/services/public/session/login?version=12354&platform=web&product=SG&"+login+"&password="+password+"&remMe=true")
        #Parse jsonp
        response = r.text[3:-1]
        response = json.loads(response)
        print response
        return response

    def login(self):

        # If already logged in and active session everything is fine
        if not self.isLoggedIn():
            #remove old cookies
            self.session.cookies.clear_session_cookies()
            response = self.sendLogin(username, password)

            # if login is correct but other session is active ask user if other session should be killed - T_227=SkyGoExtra
            if response['resultCode'] in ['T_206', 'T_227']:
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

    def getAssetDetails(self, asset_id):
        url = 'http://www.skygo.sky.de/sg/multiplatform/web/json/details/asset/' + str(asset_id) + '.json'       
        r = self.session.get(url)
        return r.json()['asset']

    def getClipDetails(self, clip_id):
        url = 'http://www.skygo.sky.de/sg/multiplatform/web/json/details/clip/' + str(clip_id) + '.json'       
        r = self.session.get(url)
        return r.json()['detail']

    def get_init_data(self, session_id, apix_id):
        if platform == osAndroid:
            init_data = 'sessionId='+self.sessionId+'&apixId='+apix_id+'&deviceId=' + self.android_deviceId +'&platformId=AndP&product=BW&version=1.7.1&DeviceFriendlyName=Android'
        else:
            init_data = 'kid={UUID}&sessionId='+session_id+'&apixId='+apix_id+'&platformId=&product=BW&channelId='
            init_data = struct.pack('1B', *[30])+init_data
            init_data = base64.urlsafe_b64encode(init_data)
        return init_data

    def parentalCheck(self, parental_rating, play=False):
        if parental_rating == 0:
            return True

        ask_pin = addon.getSetting('js_askforpin')
        max_rating = addon.getSetting('js_maxrating')
        if max_rating.isdigit():
            if int(max_rating) < 0:
                return True
            if int(max_rating) < parental_rating:
                if ask_pin == 'false' or not play:
                    return False
                else:
                    dlg = xbmcgui.Dialog()
                    code = dlg.input('PIN Code', type=xbmcgui.INPUT_NUMERIC)
                    if code == password:
                        return True
                    else:
                        return False

        return True

    def play(self, manifest_url, package_code, parental_rating=0, info_tag=None, apix_id=None):
        # Inputstream settings
        is_addon = getInputstreamAddon()
        if not is_addon:
            xbmcgui.Dialog().notification('SkyGo Fehler', 'Addon "inputstream.adaptive" fehlt!', xbmcgui.NOTIFICATION_ERROR, 2000, True)
            return False
        
        #Jugendschutz
        if not self.parentalCheck(parental_rating, play=True):
            xbmcgui.Dialog().notification('SkyGo - FSK ' + str(parental_rating), 'Keine Berechtigung zum Abspielen dieses Eintrages', xbmcgui.NOTIFICATION_ERROR, 2000, True)
            return False

        if self.login():
            if self.may_play(package_code):
                init_data = None
                # create init data for license acquiring
                if apix_id:
                    init_data = self.get_init_data(self.sessionId, apix_id)
                # Prepare new ListItem to start playback
                li = xbmcgui.ListItem(path=manifest_url)
                if info_tag:
                    li.setInfo('video', info_tag)

                li.setProperty('inputstream.adaptive.license_type', self.license_type)
                li.setProperty('inputstream.adaptive.manifest_type', 'ism')
                if init_data:
                    li.setProperty('inputstream.adaptive.license_key', self.license_url)
                    li.setProperty('inputstream.adaptive.license_data', init_data)
                li.setProperty('inputstreamaddon', 'inputstream.adaptive')
                # Start Playing
                xbmcplugin.setResolvedUrl(addon_handle, True, listitem=li)
            else:
                xbmcgui.Dialog().notification('SkyGo Fehler', 'Keine Berechtigung zum Abspielen dieses Eintrages', xbmcgui.NOTIFICATION_ERROR, 2000, True)
        else:
            xbmcgui.Dialog().notification('SkyGo Fehler', 'Fehler bei Login', xbmcgui.NOTIFICATION_ERROR, 2000, True)
            print 'Fehler beim Einloggen'