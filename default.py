import sys
import xbmcgui
import xbmcplugin
import urlparse
import requests
import resources.lib.liveTv as liveTv
import resources.lib.common as common
import resources.lib.vod as vod
from resources.lib import movies
from resources.lib import series
from skygo import SkyGo

import xml.etree.ElementTree as ET
import navigation as nav
import watchlist
import resources.lib.clips as clips

addon_handle = int(sys.argv[1])
plugin_base_url = sys.argv[0]
params = dict(urlparse.parse_qsl(sys.argv[2][1:]))


def landing():
    skygo = SkyGo()
    landing_page = skygo.getLandingPage()

    keys = ['box_listing', 'listing']

    for key in keys:
        if key in landing_page:
            for item in landing_page[key]['item']:
                url = common.build_url({'action': 'listing', 'path': item['path']})

                # Skip Sport stuff for now
                if item['title'] == 'Sport':
                    continue

                li = xbmcgui.ListItem(item['title'])
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                            listitem=li, isFolder=True)

    url = common.build_url({'action': 'listLiveTvChannels'})
    li = xbmcgui.ListItem('Live TV')
    li.setProperty('IsPlayable', 'false')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)
       

def rootDir():

    url = common.build_url({'action': 'listPage', 'url': 'http://www.skygo.sky.de/sg/multiplatform/web/json/landingpage/7.json'})
    li = xbmcgui.ListItem('Sport')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)

    url = common.build_url({'action': 'listPage', 'page': 'movies'})
    li = xbmcgui.ListItem('Filme')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)

    url = common.build_url({'action': 'listPage', 'page': 'series'})
    li = xbmcgui.ListItem('Serien')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)

    url = common.build_url({'action': 'listPage', 'url': 'http://www.skygo.sky.de/sg/multiplatform/web/json/landingpage/342.json'})
    li = xbmcgui.ListItem('Sky Arts')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)

    url = common.build_url({'action': 'listPage', 'url': 'http://www.skygo.sky.de/sg/multiplatform/web/json/landingpage/3.json'})
    li = xbmcgui.ListItem('Dokus')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)

    url = common.build_url({'action': 'listPage', 'url': 'http://www.skygo.sky.de/sg/multiplatform/web/json/landingpage/319.json'})
    li = xbmcgui.ListItem('Lifestyle')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)

    url = common.build_url({'action': 'listPage', 'url': 'http://www.skygo.sky.de/sg/multiplatform/web/json/landingpage/4.json'})
    li = xbmcgui.ListItem('Kids')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)

    url = common.build_url({'action': 'listPage', 'url': 'http://www.skygo.sky.de/sg/multiplatform/web/json/landingpage/351.json'})
    li = xbmcgui.ListItem('Sky Box Sets')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)


    url = common.build_url({'action': 'listLiveTvChannels'})
    li = xbmcgui.ListItem('Live TV')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)


    url = common.build_url({'action': 'landing'})
    li = xbmcgui.ListItem('Landing Page')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)


    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)

# Router for all plugin actions
if params:

    print params

    if params['action'] == 'playVod':
        vod.play_vod(params['vod_id'])
    elif params['action'] == 'playClip':
        clips.playClip(params['id'])

    elif params['action'] == 'listLiveTvChannels':
        liveTv.generate_channel_list()
    elif params['action'] == 'watchlist':
        if 'list' in params:
            page = 0
            if 'page' in params:
                page = params['page']
            watchlist.listWatchlist(params['list'], page=page)
        else:
            watchlist.rootDir()
    elif params['action'] == 'search':
        nav.search()

    elif params['action'] == 'landing':
        landing()

    elif params['action'] == 'moviesList':
        if 'letter' in params:
            movies.lexic(params['letter'])
        else:
            movies.all_by_lexic()

    elif params['action'] == 'seriesList':
        if 'letter' in params:
            series.lexic(params['letter'])
        else:
            series.all_by_lexic()
    elif params['action'] == 'list':
        if 'path' in params:
            listJson(params['path'])

    elif params['action'] == 'listPage':
        if 'page' in params:
            if params['page'] == 'movies':
                movies.overview_list()
            elif params['page'] == 'series':
                series.overview_list()
        elif 'id' in params:
             nav.listPage(params['id'])
        elif 'path' in params:
            nav.listPath(params['path'])
        else:
            vod.generateLPageDir(params['url'])
            xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)

    elif params['action'] == 'listSeries':
        nav.listSeasonsFromSeries(params['id'])
    elif params['action'] == 'listSeason':
        nav.listEpisodesFromSeason(params['series_id'], params['id'])

    elif params['action'] == 'playLiveTvChannel':
        liveTv.play_live_tv(params['epg_channel_id'])

    elif params['action'] == 'listing':
        vod.list_dir(params['path'])

    elif params['action'] == 'listSeries':
        vod.list_series(params['series_id'])
else:
#    rootDir()
    nav.rootDir()
