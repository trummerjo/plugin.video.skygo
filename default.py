import sys
import urlparse
import resources.lib.vod as vod
import resources.lib.clips as clips
import resources.lib.liveTv as liveTv
from skygo import SkyGo

import navigation as nav
import watchlist

addon_handle = int(sys.argv[1])
plugin_base_url = sys.argv[0]
params = dict(urlparse.parse_qsl(sys.argv[2][1:]))

# Router for all plugin actions
if params:

    print params

    if params['action'] == 'playVod':
        vod.playAsset(params['vod_id'])
    elif params['action'] == 'playClip':
        clips.playClip(params['id'])
    elif params['action'] == 'playLive':
        liveTv.playLiveTv(params['channel_id'])

    elif params['action'] == 'listLiveTvChannels':
        nav.listLiveChannels()

    elif params['action'] == 'watchlist':
        if 'list' in params:
            page = 0
            if 'page' in params:
                page = params['page']
            watchlist.listWatchlist(params['list'], page=page)
        else:
            watchlist.rootDir()
    elif params['action'] == 'watchlistAdd':
        watchlist.addToWatchlist(params['id'], params['assetType'])
    elif params['action'] == 'watchlistDel':
        watchlist.deleteFromWatchlist(params['id'])

    elif params['action'] == 'search':
        nav.search()

    elif params['action'] == 'listPage':
        if 'id' in params:
             nav.listPage(params['id'])
        elif 'path' in params:
            nav.listPath(params['path'])

    elif params['action'] == 'listSeries':
        nav.listSeasonsFromSeries(params['id'])
    elif params['action'] == 'listSeason':
        nav.listEpisodesFromSeason(params['series_id'], params['id'])

else:
    nav.rootDir()
