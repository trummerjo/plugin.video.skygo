# coding: utf8
import sys
import json
import xbmc
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
    nav.addDir('Filme', url)

    url = common.build_url({'action': 'watchlist', 'list': 'Episode'})
    nav.addDir('Episoden', url)

    url = common.build_url({'action': 'watchlist', 'list': 'Sport'})
    nav.addDir('Sport', url)

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

    nav.listAssets(listitems, isWatchlist=True)
    
def addToWatchlist(asset_id, asset_type):
    skygo.login()
    url = base_url + 'add?assetId=' + asset_id + '&type=' + asset_type + '&version=12354&platform=web&product=SG&catalog=sg'
    r = skygo.session.get(url)
    res = json.loads(r.text[3:len(r.text)-1])
    if res['resultMessage'] == 'OK':
        xbmcgui.Dialog().notification('SkyGo ', asset_type + ' zur Merkliste hinzugefügt', xbmcgui.NOTIFICATION_INFO, 2000, True)
    else:
        xbmcgui.Dialog().notification('SkyGo ', asset_type + ' konnte nicht zur Merkliste hinzugefügt werden', xbmcgui.NOTIFICATION_ERROR, 2000, True)

def deleteFromWatchlist(asset_id):
    url = base_url + 'delete?assetId=' + asset_id + '&version=12354&platform=web&product=SG&catalog=sg'
    r = skygo.session.get(url)
    res = json.loads(r.text[3:len(r.text)-1])
    if res['resultMessage'] == 'OK':
        xbmc.executebuiltin('Container.Refresh')
    else:
        xbmcgui.Dialog().notification('SkyGo', 'Fehler: Merkliste', xbmcgui.NOTIFICATION_ERROR, 2000, True)
