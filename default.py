import sys
import xbmcgui
import xbmcplugin
import urlparse
import resources.lib.liveTv as liveTv
import resources.lib.common as common
import resources.lib.vod as vod
from skygo import SkyGo


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


def generateLPageDir(url):
    skygo = SkyGo()
    page = skygo.getPage(url)

    keys = ['box_listing', 'listing']

    for key in keys:
        if key in page:
            for item in page[key]['item']:
                url = common.build_url({'action': 'listing', 'path': item['path']})

                # Skip Sport stuff for now
                if item['title'] == 'Sport':
                    continue

                li = xbmcgui.ListItem(item['title'])
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                            listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)


def rootDir():

    url = common.build_url({'action': 'landing'})
    li = xbmcgui.ListItem('Landing Page')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)

    url = common.build_url({'action': 'listPage', 'url': 'http://www.skygo.sky.de/sg/multiplatform/web/json/landingpage/6.json'})
    li = xbmcgui.ListItem('Filme')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)

    url = common.build_url({'action': 'listPage', 'url': 'http://www.skygo.sky.de/sg/multiplatform/web/json/landingpage/5.json'})
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



    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)

# Router for all plugin actions
if params:
    if params['action'] == 'playVod':
        vod.play_vod(params['vod_id'])

    elif params['action'] == 'listLiveTvChannels':
        liveTv.generate_channel_list()

    elif params['action'] == 'landing':
        landing()

    elif params['action'] == 'listPage':
        generateLPageDir(params['url'])

    elif params['action'] == 'playLiveTvChannel':
        liveTv.play_live_tv(params['epg_channel_id'])

    elif params['action'] == 'listing':
        vod.list_dir(params['path'])

    elif params['action'] == 'listSeries':
        vod.list_series(params['series_id'])
else:
    rootDir()