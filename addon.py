import sys
import xbmcaddon
import xbmcgui
import xbmc
import xbmcplugin
import urllib
import base64
import urlparse
import struct
import requests
import re
import datetime
import time

from skygo import SkyGo

addon_handle = int(sys.argv[1])
plugin_base_url = sys.argv[0]
params = dict(urlparse.parse_qsl(sys.argv[2][1:]))


addon = xbmcaddon.Addon()
__addonname__ = addon.getAddonInfo('name')
username = addon.getSetting('email')
password = addon.getSetting('password')

pluginpath = addon.getAddonInfo('path')
datapath = xbmc.translatePath(addon.getAddonInfo('profile'))
cookiePath = datapath + 'COOKIES'




skygo = SkyGo(cookiePath)

def build_url(query):
    return plugin_base_url + '?' + urllib.urlencode(query)



if params:
    if params['action'] == 'play':
        id = params['id']
        error = False

        # Check if is LiveTV
        liveTv = False
        if 'liveTv' in params:

            now = datetime.datetime.now()
            currentDate = now.strftime("%d.%m.%Y")

            # Get Epg information
            print 'http://www.skygo.sky.de/epgd/sg/web/eventList/'+currentDate+'/'+id+'/'
            r = requests.get('http://www.skygo.sky.de/epgd/sg/web/eventList/'+currentDate+'/'+id+'/')
            # print r.json()
            epgJson = r.json()[id]
            runningProgram = ''
            for entry in epgJson:
                startDateStr = entry['startDate'] + ' ' + entry['startTime']
                endDateStr = entry['endDate'] + ' ' + entry['endTime']
                startDate = datetime.datetime(*(time.strptime(startDateStr, '%d.%m.%Y %H:%M')[0:6]))
                endDate = datetime.datetime(*(time.strptime(endDateStr, '%d.%m.%Y %H:%M')[0:6]))
                # Check if Program is running program
                if startDate < now < endDate:
                    runningProgram = entry
                    break

            if runningProgram is not '':
                entryId = runningProgram['id']
                print 'http://www.skygo.sky.de/epgd/sg/web/eventDetail/'+entryId+'/'+id+'/'
                r = requests.get('http://www.skygo.sky.de/epgd/sg/web/eventDetail/'+entryId+'/'+id+'/')
                eventDetail = r.json()

                # If not live it is a vod - do some magic do get asset id
                if runningProgram['live'] == 0:
                    detailsLink = eventDetail['detailPage']
                    # Extract id from details link
                    p = re.compile('/([0-9]*)\.html', re.IGNORECASE)
                    m = re.search(p, detailsLink)
                    detailId = m.group(1)
                    print 'Detail Id: ' + detailId

                    id = detailId
            else:
                xbmcgui.Dialog().ok('Kein Programm', 'Auf diesem Kanal ist kein aktuelles Programm vorhanden.')
                # Do not play stream
                error = True

            print params['mediaUrl']
            liveTv = True

        if not error:
            login = skygo.login(username, password)
            sessionId = skygo.sessionId
            licenseUrl = 'https://wvguard.sky.de/WidevineLicenser/WidevineLicenser|User-Agent=Mozilla%2F5.0%20(X11%3B%20Linux%20x86_64)%20AppleWebKit%2F537.36%20(KHTML%2C%20like%20Gecko)%20Chrome%2F49.0.2623.87%20Safari%2F537.36&Referer=http%3A%2F%2Fwww.skygo.sky.de%2Ffilm%2Fscifi--fantasy%2Fjupiter-ascending%2Fasset%2Ffilmsection%2F144836.html&Content-Type=||'

            playInfo = ''
            manifestUrl = ''
            if not liveTv:
                playInfo = skygo.getPlayInfo(id)
                apixId = playInfo['apixId']
                manifestUrl = playInfo['manifestUrl']
            else:
                print id
                # Sport News has fixed playinfourl
                playInfoUrl = '/sg/multiplatform/web/xml/player_playlist/ssn/127.xml'
                if id != '17':
                    playInfoUrl = '/sg/multiplatform/web/xml/player_playlist/asset/' + str(id) + '.xml'

                print 'Playinfourl: ' + playInfoUrl

                playInfo = skygo.getLivePlayInfo(playInfoUrl)
                apixId = playInfo['apixId']
                manifestUrl = playInfo['manifestUrl']

            print "#######################################################"
            print "ApixID: " + apixId + " manifestUrl: " + manifestUrl
            print "#######################################################"

            # create init data for licence acquiring
            initData = 'kid={UUID}&sessionId='+sessionId+'&apixId='+apixId+'&platformId=WEB&product=BW&channelId='
            initData = struct.pack('1B', *[30])+initData
            initData = base64.urlsafe_b64encode(initData)
            print initData



            li = xbmcgui.ListItem(path=manifestUrl)
            info = {
                'mediatype': 'movie'
            }
            li.setInfo('video', info)

            li.setProperty('inputstream.smoothstream.license_type', 'com.widevine.alpha')
            li.setProperty('inputstream.smoothstream.license_key', licenseUrl)
            li.setProperty('inputstream.smoothstream.license_data', initData)
            li.setProperty('inputstreamaddon', 'inputstream.smoothstream')

            # Check if the Stream is playable
            playStream = True
            if not login:
                playStream = False

            xbmcplugin.setResolvedUrl(addon_handle, playStream, listitem=li)

    elif params['action'] == 'topMovies':
        mostWatchedMovies = skygo.getMostWatched()
        xbmcplugin.setContent(addon_handle, 'movies')
        for movie in mostWatchedMovies:
            url = build_url({'action': 'play', 'id': movie['id']})

            # Try to find a hero img
            heroImg = ''
            videoWallImg = ''
            cover = ''


            for image in movie['main_picture']['picture']:
                if image['type'] == 'hero_img':
                    heroImg = skygo.baseUrl + image['path'] + '/' + image['file']
                if image['type'] == 'videowall_home':
                    videoWallImg = skygo.baseUrl + image['path'] + '/' + image['file']
                if image['type'] == 'gallery':
                    cover = skygo.baseUrl + image['path'] + '/' + image['file']

            if movie['dvd_cover']:
                cover = skygo.baseUrl + movie['dvd_cover']['path'] + '/' + movie['dvd_cover']['file']

            li = xbmcgui.ListItem(label=movie['title'])
            li.setArt({'thumb': cover, 'poster': cover, 'fanart': heroImg})

            li.setProperty('IsPlayable', 'true')

            info = {
                'genre': movie['category']['main']['content'],
                'year': movie['year_of_production'],
                'mpaa': movie['parental_rating']['value'],
                'title': movie['title'],
                'mediatype': 'movie',
                'originaltitle': movie['original_title'],
                'plot': movie['synopsis']
            }
            li.setInfo('video', info)



            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                        listitem=li)

        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)


    elif params['action'] == 'liveTv':
        channels = skygo.getChannels()
        xbmcplugin.setContent(addon_handle, 'videos')
        for channel in channels:
            url = build_url({'action': 'play', 'id': channel['id'], 'liveTv': 'True', 'mediaUrl': channel['mediaurl']})

            print channel


            li = xbmcgui.ListItem(label=channel['name'])
            li.setProperty('IsPlayable', 'true')
            li.setArt({'thumb': skygo.baseUrl+channel['logo']})
            info = {
                'mediatype': 'video'
            }
            li.setInfo('video', info)
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                        listitem=li, isFolder=False)

        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)



else:

    url = build_url({'action': 'topMovies'})
    li = xbmcgui.ListItem(label='Top Filme')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)

    url = build_url({'action': 'liveTv'})
    li = xbmcgui.ListItem(label='Live TV')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)


    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)
