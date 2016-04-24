import sys

import xbmcaddon
import xbmcgui
import xbmcplugin
import common
from skygo import SkyGo


addon_handle = int(sys.argv[1])
addon = xbmcaddon.Addon()
username = addon.getSetting('email')
password = addon.getSetting('password')
skygo = SkyGo()


def list_dir(path):
    assets = skygo.getListing(path)
    xbmcplugin.setContent(addon_handle, 'movies')

    for asset in assets:
        url = common.build_url({'action': 'playVod', 'vod_id': asset['id']})

        # Try to find a hero img
        heroImg = ''
        videoWallImg = ''
        cover = ''

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
        if asset['type'] == 'Episode':
            if 'season_nr' not in asset:
                asset['season_nr'] = '??'
            label = asset['serie_title'] + ' S'+str(asset['season_nr'])+'E'+str(asset['episode_nr'])
            info = {
                'genre': asset['category']['main']['content'],
                'year': asset['year_of_production'],
                'mpaa': asset['parental_rating']['value'],
                'title': asset['serie_title'] + ' E'+str(asset['episode_nr']),
                'mediatype': 'video',
                'originaltitle': asset['original_title'],
                'plot': asset['synopsis'],
                'episode': asset['episode_nr'],
                'season': asset['season_nr']
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
            url = common.build_url({'action': 'listSeries', 'series_id': asset['id']})

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

        is_dir = False
        if asset['type'] == 'Series':
            is_dir = True
            li.setProperty('IsPlayable', 'false')
        else:
            li.setProperty('IsPlayable', 'true')

        li.setInfo('video', info)

        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li, isFolder=is_dir)

    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)


def list_series(series_id):
    series = skygo.getSeriesInfo(series_id)
    xbmcplugin.setContent(addon_handle, 'movies')

    for season in series['seasons']['season']:
        print season

        for episode in season['episodes']['episode']:
            url = common.build_url({'action': 'playVod', 'vod_id': episode['id']})

            print episode['id']

            # Try to find images
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

            if 'season_nr' not in episode:
                episode['season_nr'] = '??'
            label = episode['serie_title'] + ' S'+str(episode['season_nr'])+'E'+str(episode['episode_nr'])
            info = {
                'genre': episode['category']['main']['content'],
                'mpaa': episode['parental_rating']['value'],
                'title': episode['serie_title'] + ' E'+str(episode['episode_nr']),
                'mediatype': 'movie',
            }
            li = xbmcgui.ListItem(label=label)
            li.setArt({'thumb': cover, 'poster': cover, 'fanart': heroImg})

            li.setProperty('IsPlayable', 'true')

            li.setInfo('video', info)

            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                        listitem=li)

    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)


def play_vod(vod_id):
    login = skygo.login(username, password)

    if login:
        session_id = skygo.sessionId
        # Get the play info via the id of the video
        play_info = skygo.getPlayInfo(id=vod_id)

        apix_id = play_info['apixId']
        manifest = play_info['manifestUrl']
        duration = int(play_info['duration'])*60

        # create init data for licence acquiring
        init_data = skygo.get_init_data(session_id, apix_id)

        # Prepare new ListItem to start playback
        li = xbmcgui.ListItem(path=manifest)
        info = {
            'mediatype': 'movie',
            'duration': duration
        }
        li.setInfo('video', info)

        # Force smoothsteam addon
        li.setProperty('inputstream.smoothstream.license_type', 'com.widevine.alpha')
        li.setProperty('inputstream.smoothstream.license_key', skygo.licence_url)
        li.setProperty('inputstream.smoothstream.license_data', init_data)
        li.setProperty('inputstreamaddon', 'inputstream.smoothstream')

        # Start Playing
        xbmcplugin.setResolvedUrl(addon_handle, True, listitem=li)
    else:
        xbmcgui.Dialog().notification('SkyGo Fehler', 'Fehler bei Login', xbmcgui.NOTIFICATION_ERROR, 2000, True)
        print 'Fehler beim Einloggen'
