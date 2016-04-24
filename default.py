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


# Router for all plugin actions
if params:
    if params['action'] == 'playVod':
        vod.play_vod(params['vod_id'])

    elif params['action'] == 'listLiveTvChannels':
        liveTv.generate_channel_list()

    elif params['action'] == 'playLiveTvChannel':
        liveTv.play_live_tv(params['epg_channel_id'])

    elif params['action'] == 'listing':
        vod.list_dir(params['path'])

    elif params['action'] == 'listSeries':
        vod.list_series(params['series_id'])
else:
    landing()
