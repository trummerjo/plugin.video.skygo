import sys

import xbmcgui
import xbmcplugin
import requests
from resources.lib import vod
from resources.lib import common


addon_handle = int(sys.argv[1])


def overview_list():
    vod.generateLPageDir('http://www.skygo.sky.de/sg/multiplatform/web/json/landingpage/5.json')
    url = common.build_url({'action': 'seriesList'})
    li = xbmcgui.ListItem('A-Z')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)


def all_by_lexic():
    r = requests.get('http://www.skygo.sky.de/sg/multiplatform/web/json/automatic_listing/series/all/221/header.json')
    header = r.json()
    for letter in header['letters']['letter']:
        if letter['linkable'] is True:
            url = common.build_url({'action': 'seriesList', 'letter': str(letter['content'])})
            li = xbmcgui.ListItem(str(letter['content']))
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                        listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)


def lexic(letter):
    vod.list_dir('/sg/multiplatform/web/json/automatic_listing/series/all/221/'+letter+'_p1.json')

