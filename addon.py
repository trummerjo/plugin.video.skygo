import sys
import xbmcaddon
import xbmcgui
import xbmc
import xbmcplugin
import urllib
import base64
import urlparse
import struct
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


xbmcplugin.setContent(addon_handle, 'movies')


skygo = SkyGo(cookiePath)

def build_url(query):
    return plugin_base_url + '?' + urllib.urlencode(query)



if params:
    if params['action'] == 'play':
        id = params['id']
        xbmc.log('Play SkyGo Movie with id: ' + id)


        playStream = skygo.login(username, password)

        sessionId = skygo.sessionId


        licenseUrl = 'https://wvguard.sky.de/WidevineLicenser/WidevineLicenser|User-Agent=Mozilla%2F5.0%20(X11%3B%20Linux%20x86_64)%20AppleWebKit%2F537.36%20(KHTML%2C%20like%20Gecko)%20Chrome%2F49.0.2623.87%20Safari%2F537.36&Referer=http%3A%2F%2Fwww.skygo.sky.de%2Ffilm%2Fscifi--fantasy%2Fjupiter-ascending%2Fasset%2Ffilmsection%2F144836.html&Content-Type=||'


        playInfo = skygo.getPlayInfo(id)
        initData = 'kid={UUID}&sessionId='+sessionId+'&apixId='+playInfo['apixId']+'&platformId=WEB&product=BW&channelId='
        initData = struct.pack('1B', *[30])+initData
        initData = base64.urlsafe_b64encode(initData)
        print initData

        li = xbmcgui.ListItem(path=playInfo['manifestUrl'])
        info = {
            'mediatype': 'movie'
        }
        li.setInfo('video', info)

        li.setProperty('inputstream.smoothstream.license_type', 'com.widevine.alpha')
        li.setProperty('inputstream.smoothstream.license_key', licenseUrl)
        li.setProperty('inputstream.smoothstream.license_data', initData)
        li.setProperty('inputstreamaddon', 'inputstream.smoothstream')

        xbmcplugin.setResolvedUrl(addon_handle, playStream, listitem=li)

    elif params['action'] == 'topMovies':
        mostWatchedMovies = skygo.getMostWatched()
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


            xbmc.log("Hro image: " + heroImg, xbmc.LOGDEBUG)


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

        xbmcplugin.endOfDirectory(addon_handle, updateListing=True, cacheToDisc=False)


    elif params['action'] == 'liveTv':
        channels = skygo.getChannels()
        for channel in channels:
            url = build_url({'action': 'playTv', 'id': channel['id']})


            li = xbmcgui.ListItem(label=channel['name'])
            li.setArt({'poster': skygo.baseUrl+channel['logo']})

            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                        listitem=li, isFolder=False)

        xbmcplugin.endOfDirectory(addon_handle, updateListing=True, cacheToDisc=False)



else:

    url = build_url({'action': 'topMovies'})
    li = xbmcgui.ListItem(label='Top Filme')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                        listitem=li, isFolder=True)

    url = build_url({'action': 'liveTv'})
    li = xbmcgui.ListItem(label='Live TV')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                        listitem=li, isFolder=True)


    xbmcplugin.endOfDirectory(addon_handle, updateListing=True, cacheToDisc=False)
