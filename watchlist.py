import sys
import json
import xbmcaddon
import xbmcgui
import xbmcplugin
import resources.lib.common as common
from skygo import SkyGo
import navigation as nav
skygo = SkyGo()

addon_handle = int(sys.argv[1])
base_url = 'https://www.skygo.sky.de/SILK/services/public/watchlist/'

def rootDir():
    url = common.build_url({'action': 'watchlist', 'list': 'Film'})
    li = xbmcgui.ListItem('Filme')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li, isFolder=True)
    url = common.build_url({'action': 'watchlist', 'list': 'Episode'})
    li = xbmcgui.ListItem('Episoden')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li, isFolder=True)
    url = common.build_url({'action': 'watchlist', 'list': 'Sport'})
    li = xbmcgui.ListItem('Sport')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)    

def listWatchlist(asset_type, page=0):
    skygo.login()
    url = base_url + 'get?type=' + asset_type + '&page=' + str(page) + '&pageSize=8'
    r = skygo.session.get(url)
    data = json.loads(r.text[3:len(r.text)-1])
    if not 'watchlist' in data:
        return
    listitems = []    
    for item in data['watchlist']:
        asset = skygo.getAssetDetails(item['assetId'])        
        for asset_details in nav.getAssets([asset]):
            listitems.append(asset_details)
    
    if data['hasNext']:
        url = common.build_url({'action': 'watchlist', 'list': asset_type, 'page': page+1})    
        listitems.append({'type': 'path', 'label': 'Mehr...', 'url': url})

    nav.listAssets(listitems)

def addToWatchlist(asset_id):
    url = base_url + 'add?assetId=' + asset_id
    #todo    

def deleteFromWatchlist(asset_id):
    url = base_url + 'add?assetId=' + asset_id
    #todo
