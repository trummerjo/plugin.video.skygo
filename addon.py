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
licenseUrl = 'https://wvguard.sky.de/WidevineLicenser/WidevineLicenser|User-Agent=Mozilla%2F5.0%20(X11%3B%20Linux%20x86_64)%20AppleWebKit%2F537.36%20(KHTML%2C%20like%20Gecko)%20Chrome%2F49.0.2623.87%20Safari%2F537.36&Referer=http%3A%2F%2Fwww.skygo.sky.de%2Ffilm%2Fscifi--fantasy%2Fjupiter-ascending%2Fasset%2Ffilmsection%2F144836.html&Content-Type=||'


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
    if params['action'] == 'playLive':
        epg_channel_id = params['id']
        # Get Current running event on channel
        current_event = skygo.getCurrentEvent(epg_channel_id)

        # If there is a running event play it
        if current_event is not False:
            event_id = current_event['id']
            playInfo = skygo.getEventPlayInfo(event_id, epg_channel_id)

            apixId = playInfo['apixId']
            manifestUrl = playInfo['manifestUrl']

            print "#######################################################"
            print "ApixID: " + apixId + " manifestUrl: " + manifestUrl
            print "#######################################################"

            # Login to get session
            login = skygo.login(username, password)
            sessionId = skygo.sessionId

            # create init data for licence acquiring
            initData = 'kid={UUID}&sessionId='+sessionId+'&apixId='+apixId+'&platformId=WEB&product=BW&channelId='
            initData = struct.pack('1B', *[30])+initData
            initData = base64.urlsafe_b64encode(initData)

            # Create list item with inputstream addon
            li = xbmcgui.ListItem(path=manifestUrl)
            info = {
                'mediatype': 'movie',
            }
            li.setInfo('video', info)

            li.setProperty('inputstream.smoothstream.license_type', 'com.widevine.alpha')
            li.setProperty('inputstream.smoothstream.license_key', licenseUrl)
            li.setProperty('inputstream.smoothstream.license_data', initData)
            li.setProperty('inputstreamaddon', 'inputstream.smoothstream')

            xbmcplugin.setResolvedUrl(addon_handle, True, listitem=li)


        else:
            xbmcgui.Dialog().notification('Kein laufendes Event', 'Auf diesem Kanal ist kein laufendes Event vorhanden.', icon=xbmcgui.NOTIFICATION_WARNING)




    if params['action'] == 'playVod':
        id = params['id']
        login = skygo.login(username, password)

        if login:
            sessionId = skygo.sessionId
            # Get the play info via the id of the video
            playInfo = skygo.getPlayInfo(id=id)
            apixId = playInfo['apixId']
            manifestUrl = playInfo['manifestUrl']
            duration = int(playInfo['duration'])*60


            # create init data for licence acquiring
            initData = 'kid={UUID}&sessionId='+sessionId+'&apixId='+apixId+'&platformId=WEB&product=BW&channelId='
            initData = struct.pack('1B', *[30])+initData
            initData = base64.urlsafe_b64encode(initData)
            print initData


            # Prepare new ListItem to start playback
            li = xbmcgui.ListItem(path=manifestUrl)
            info = {
                'mediatype': 'movie',
                'duration': duration
            }
            li.setInfo('video', info)

            # Force smoothsteam addon
            li.setProperty('inputstream.smoothstream.license_type', 'com.widevine.alpha')
            li.setProperty('inputstream.smoothstream.license_key', licenseUrl)
            li.setProperty('inputstream.smoothstream.license_data', initData)
            li.setProperty('inputstreamaddon', 'inputstream.smoothstream')

            # Start Playing
            xbmcplugin.setResolvedUrl(addon_handle, True, listitem=li)
        else:
            xbmcgui.Dialog().notification('SkyGo Fehler', 'Fehler bei Login', xbmcgui.NOTIFICATION_ERROR, 2000, True)
            print 'Fehler beim Einloggen'

    elif params['action'] == 'listing':

        assets = skygo.getListing(params['path'])
        xbmcplugin.setContent(addon_handle, 'movies')


        for asset in assets:
            url = build_url({'action': 'playVod', 'id': asset['id']})

            print asset

            # Try to find a hero img
            heroImg = ''
            videoWallImg = ''
            cover = ''

            print asset['type']


            for image in asset['main_picture']['picture']:
                if image['type'] == 'hero_img':
                    heroImg = skygo.baseUrl + image['path'] + '/' + image['file']
                if image['type'] == 'videowall_home':
                    videoWallImg = skygo.baseUrl + image['path'] + '/' + image['file']
                if image['type'] == 'gallery':
                    cover = skygo.baseUrl + image['path'] + '/' + image['file']

            if asset['dvd_cover']:
                cover = skygo.baseUrl + asset['dvd_cover']['path'] + '/' + asset['dvd_cover']['file']



            info = {}
            label = 'label'
            print asset['type']
            if asset['type'] == 'Episode':
                if 'season_nr' not in asset:
                    asset['season_nr'] = '??'
                label = asset['serie_title'] + ' S'+str(asset['season_nr'])+'E'+str(asset['episode_nr'])
                info = {
                    'genre': asset['category']['main']['content'],
                    'year': asset['year_of_production'],
                    'mpaa': asset['parental_rating']['value'],
                    'title': asset['serie_title'] + ' E'+str(asset['episode_nr']),
                    'mediatype': 'movie',
                    'originaltitle': asset['original_title'],
                    'plot': asset['synopsis'],
                }

            elif asset['type'] == 'Movie' or asset['type'] == 'Film':
                info = {
                    'genre': asset['category']['main']['content'],
                    'year': asset['year_of_production'],
                    'mpaa': asset['parental_rating']['value'],
                    'title': asset['title'],
                    'mediatype': 'movie',
                    'originaltitle': asset['original_title'],
                    'plot': asset['synopsis'],
                }
                label = asset['title']

            elif asset['type'] == 'Series':
                url = build_url({'action': 'listSeries', 'id': asset['id']})
                info = {
                    'genre': asset['category']['main']['content'],
                    'title': asset['title'],
                    'mediatype': 'movie',
                    'originaltitle': asset['original_title'],
                    'plot': asset['synopsis'],
                }
                label = asset['title']

            li = xbmcgui.ListItem(label=label)
            li.setArt({'thumb': cover, 'poster': cover, 'fanart': heroImg})

            li.setProperty('IsPlayable', 'true')

            li.setInfo('video', info)



            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                        listitem=li)

        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)



    elif params['action'] == 'listSeries':

        series = skygo.getSeriesInfo(params['id'])
        xbmcplugin.setContent(addon_handle, 'movies')

        for season in series['seasons']['season']:
            print season

            for episode in season['episodes']:
                url = build_url({'action': 'playVod', 'id': episode['id']})

                print episode

                # Try to find a hero img
                heroImg = ''
                videoWallImg = ''
                cover = ''

                for image in episode['main_picture']['picture']:
                    if image['type'] == 'hero_img':
                        heroImg = skygo.baseUrl + image['path'] + '/' + image['file']
                    if image['type'] == 'videowall_home':
                        videoWallImg = skygo.baseUrl + image['path'] + '/' + image['file']
                    if image['type'] == 'gallery':
                        cover = skygo.baseUrl + image['path'] + '/' + image['file']

                if episode['dvd_cover']:
                    cover = skygo.baseUrl + episode['dvd_cover']['path'] + '/' + episode['dvd_cover']['file']



                info = {}
                label = 'label'
                if episode['type'] == 'Episode':
                    if 'season_nr' not in episode:
                        episode['season_nr'] = '??'
                    label = episode['serie_title'] + ' S'+str(episode['season_nr'])+'E'+str(episode['episode_nr'])
                    info = {
                        'genre': episode['category']['main']['content'],
                        'year': episode['year_of_production'],
                        'mpaa': episode['parental_rating']['value'],
                        'title': episode['serie_title'] + ' E'+str(episode['episode_nr']),
                        'mediatype': 'movie',
                        'originaltitle': episode['original_title'],
                        'plot': episode['synopsis'],
                    }
                li = xbmcgui.ListItem(label=label)
                li.setArt({'thumb': cover, 'poster': cover, 'fanart': heroImg})

                li.setProperty('IsPlayable', 'true')

                li.setInfo('video', info)



                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                            listitem=li)

        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)


    elif params['action'] == 'liveTv':
        channels = skygo.getChannels()
        xbmcplugin.setContent(addon_handle, 'videos')
        for channel in channels:
            url = build_url({'action': 'playLive', 'id': channel['id'], 'liveTv': 'True', 'mediaUrl': channel['mediaurl']})

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
    landing_page = skygo.getLandingPage()

    keys = ['box_listing', 'listing']

    for key in keys:
        if key in landing_page:
            for item in landing_page[key]['item']:
                url = build_url({'action': 'listing', 'path': item['path']})
                li = xbmcgui.ListItem(item['title'])
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                            listitem=li, isFolder=True)


    url = build_url({'action': 'topMovies'})
    li = xbmcgui.ListItem('Top Filme')
    li.setProperty('IsPlayable', 'false')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)

    url = build_url({'action': 'liveTv'})
    li = xbmcgui.ListItem('Live TV')
    li.setProperty('IsPlayable', 'false')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)


    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)
