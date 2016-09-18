# coding: utf8
import sys
import os
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs
import requests
import urllib2
import json
import xml.etree.ElementTree as ET
import resources.lib.common as common
from skygo import SkyGo
import watchlist

addon_handle = int(sys.argv[1])
icon_file = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')+'/icon.png').decode('utf-8')
skygo = SkyGo()

#Blacklist: diese nav_ids nicht anzeigen
#Sport: Datencenter, NewsSection, Aktuell, Snap
nav_blacklist = [34, 32, 27, 15]
#Force: anzeige dieser nav_ids erzwingen
#Sport: Wiederholungen
nav_force = [35, 36, 37, 161]

xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
 
def getNav():
    feed = urllib2.urlopen('http://www.skygo.sky.de/sg/multiplatform/ipad/json/navigation.xml')
    nav = ET.parse(feed)
    return nav.getroot()
     
def liveChannelsDir():
    url = common.build_url({'action': 'listLiveTvChannels'})
    addDir('Livesender', url)

def watchlistDir():
    url = common.build_url({'action': 'watchlist'})
    addDir('Merkliste', url)

def rootDir():
    print sys.argv
    nav = getNav()
    #Livesender
    liveChannelsDir()
    #Navigation der Ipad App
    for item in nav:
        if item.attrib['hide'] == 'true' or item.tag == 'item':
            continue
        url = common.build_url({'action': 'listPage', 'id': item.attrib['id']})
        addDir(item.attrib['label'], url)
        li = xbmcgui.ListItem(item.attrib['label'])

    #Merkliste
    watchlistDir()
    #Suchfunktion
    url = common.build_url({'action': 'search'})
    addDir('Suche', url)
     
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)

def addDir(label, url, icon=icon_file):
    li = xbmcgui.ListItem(label, iconImage=icon)
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)
    
def getHeroImage(data):
    if 'main_picture' in data:
        for pic in data['main_picture']['picture']:
            if pic['type'] == 'hero_img':
                return skygo.baseUrl + pic['path']+'/'+pic['file']
    if 'item_image' in data:
        return skygo.baseUrl + data['item_image']
    if 'picture' in data:
        return skygo.baseUrl + data['picture']

    return ''

def getPoster(data):
    if 'logo' in data:
        if 'name' in data and xbmcaddon.Addon().getSetting('enable_customlogos') == 'true':
            img = getLocalChannelLogo(data['name'])
            if img:
                return img
        return skygo.baseUrl + data['logo']
    if 'dvd_cover' in data:
        return skygo.baseUrl + data['dvd_cover']['path'] + '/' + data['dvd_cover']['file']
    if 'item_preview_image' in data:
        return skygo.baseUrl + data['item_preview_image']
    if 'picture' in data:
        return skygo.baseUrl + data['picture']

    return ''

def getLocalChannelLogo(channel_name):   
    logo_path = xbmcaddon.Addon().getSetting('logoPath')
    if not logo_path == '' and xbmcvfs.exists(logo_path):
        dirs, files = xbmcvfs.listdir(logo_path)
        for f in files:
            if f.lower().endswith('.png'):
                if channel_name.lower().replace(' ', '') == os.path.basename(f).lower().replace('.png', '').replace(' ', ''):
                    return os.path.join(logo_path, f)

    return None

def search():
    dlg = xbmcgui.Dialog()
    term = dlg.input('Suchbegriff', type=xbmcgui.INPUT_ALPHANUM)
    if term == '':
        return
    term = term.replace(' ', '+')
    url = 'https://www.skygo.sky.de/SILK/services/public/search/web?searchKey=' + term + '&version=12354&platform=web&product=SG'
    r = skygo.session.get(url)
    data = json.loads(r.text[3:len(r.text)-1])
    listitems = []
    for item in data['assetListResult']:
        url = common.build_url({'action': 'playVod', 'vod_id': item['id']}) 
        listitems.append({'type': 'searchresult', 'label': item['title'], 'url': url, 'data': item})

#    if data['assetListResult']['hasNext']:
#        url = common.build_url({'action': 'listPage', 'path': ''}) 
#        listitems.append({'type': 'path', 'label': 'Mehr...', 'url': url})

    listAssets(listitems)

def listLiveChannels():
    listitems = []
    channelid_list = []
    url = 'http://www.skygo.sky.de/epgd/sg/ipad/excerpt/'
    r = requests.get(url)
    data = r.json()
    for tab in data:
        for event in tab['eventList']:
            if event['channel']['msMediaUrl'].startswith('http://'):
                url = common.build_url({'action': 'playLive', 'channel_id': event['channel']['id']})                
                if not event['channel']['id'] in channelid_list:
                    listitems.append({'type': 'live', 'label': event['channel']['name'], 'url': url, 'data': event})
                    channelid_list.append(event['channel']['id'])

    listAssets(listitems)
    

def listEpisodesFromSeason(series_id, season_id):
    url = skygo.baseUrl + '/sg/multiplatform/web/json/details/series/' + str(series_id) + '_global.json'
    r = requests.get(url)
    data = r.json()['serieRecap']['serie']
    xbmcplugin.setContent(addon_handle, 'episodes')
    for season in data['seasons']['season']:
        if str(season['id']) == str(season_id):
            for episode in season['episodes']['episode']:
                url = common.build_url({'action': 'playVod', 'vod_id': episode['id']})
                li = xbmcgui.ListItem()
                li.setProperty('IsPlayable', 'true')
                li.addContextMenuItems(getWatchlistContextItem({'type': 'Episode', 'data': episode}), replaceItems=False)
                info = getInfoLabel('Episode', episode)
                #li.setInfo('video', info)
                li.setLabel('%02d. %s' % (info['episode'], info['title']))
                li.setArt({'poster': skygo.baseUrl + season['path'], 
                           'fanart': getHeroImage(data),
                           'thumb': skygo.baseUrl + episode['webplayer_config']['assetThumbnail']})
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                            listitem=li, isFolder=False)

    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)   

def listSeasonsFromSeries(series_id):
    url = skygo.baseUrl + '/sg/multiplatform/web/json/details/series/' + str(series_id) + '_global.json'
    r = requests.get(url)
    data = r.json()['serieRecap']['serie']
    xbmcplugin.setContent(addon_handle, 'seasons')
    for season in data['seasons']['season']:
        url = common.build_url({'action': 'listSeason', 'id': season['id'], 'series_id': data['id']})
        label = '%s - Staffel %02d' % (data['title'], season['nr'])
        li = xbmcgui.ListItem(label=label)
        li.setProperty('IsPlayable', 'false')
        li.setArt({'poster': skygo.baseUrl + season['path'], 
                   'fanart': getHeroImage(data)})
        li.setInfo('video', {'plot': data['synopsis'].replace('\n', '').strip()})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                        listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)
     
def getAssets(data, key='asset_type'):
    asset_list = []
    for asset in data:
        if asset[key].lower() in ['film', 'episode', 'sport']:
            url = common.build_url({'action': 'playVod', 'vod_id': asset['id']})
            asset_list.append({'type': asset[key], 'label': '', 'url': url, 'data': asset})
        elif asset[key].lower() == 'clip':
            url = common.build_url({'action': 'playClip', 'id': asset['id']})
            asset_list.append({'type': asset[key], 'label': '', 'url': url, 'data': asset})
        elif asset[key].lower() == 'series':
            url = common.build_url({'action': 'listSeries', 'id': asset['id']})
            asset_list.append({'type': asset[key], 'label': asset['title'], 'url': url, 'data': asset})

    return asset_list

def checkForLexic(listing):
    if len(listing) == 2:
        if 'ByLexic' in listing[0]['structureType'] and 'ByYear' in listing[1]['structureType']:
            return True

    return False
        
def parseListing(page, path):
    listitems = []
    curr_page = 1
    page_count = 1
    if 'letters' in page:
        for item in page['letters']['letter']:
            if item['linkable'] is True:
                url = common.build_url({'action': 'listPage', 'path': path.replace('header', str(item['content']) + '_p1')})
                listitems.append({'type': 'path', 'label': str(item['content']), 'url': url})
    elif 'listing' in page:
        if 'isPaginated' in page['listing']:
            curr_page = page['listing']['currPage']
            page_count = page['listing']['pages']
        if 'asset_listing' in page['listing']:
            listitems = getAssets(page['listing']['asset_listing']['asset'])        
        elif 'listing' in page['listing']:
            listing_type = page['listing'].get('type', '')
            #SportClips
            if listing_type == 'ClipsListing':
                listitems = getAssets(page['listing']['listing']['item'], key='type')
            #SportReplays
            elif 'asset' in page['listing']['listing']:
                listitems = getAssets(page['listing']['listing']['asset'])
            elif 'item' in page['listing']['listing']:
                if isinstance(page['listing']['listing']['item'], list):
                    #Zeige nur A-Z Sortierung
                    if checkForLexic(page['listing']['listing']['item']):
                        path = page['listing']['listing']['item'][0]['path'].replace('header.json', 'sort_by_lexic_p1.json')
                        listPath(path)
                        return []
                    for item in page['listing']['listing']['item']:
                        if not 'asset_type' in item and 'path' in item:
                            url = common.build_url({'action': 'listPage', 'path': item['path']})
                            listitems.append({'type': 'listPage', 'label': item['title'], 'url': url})
                else:
                    listPath(page['listing']['listing']['item']['path'])

    if curr_page < page_count:
        url = common.build_url({'action': 'listPage', 'path': path.replace('_p' + str(curr_page), '_p' + str(curr_page+1))})
        listitems.append({'type': 'path', 'label': 'Mehr...', 'url': url})

    return listitems

def getInfoLabel(asset_type, data):    
    info = {}
    info['title'] = data.get('title', '')
    info['originaltitle'] = data.get('original_title', '')
    if not data.get('year_of_production', '') == '':
        info['year'] = data.get('year_of_production', '')
    info['plot'] = data.get('synopsis', '').replace('\n', '').strip()
    print data
    if info['plot'] == '':
        info['plot'] = data.get('description', '').replace('\n', '').strip()
    info['duration'] = data.get('length', 0)*60
    if asset_type == 'Film':
        info['mediatype'] = 'movie'
        info['genre'] = data.get('category', {}).get('main', {}).get('content', '')
    if asset_type == 'Series':
        info['year'] = data.get('year_of_production_start', '')
    if asset_type == 'Episode':
        info['mediatype'] = 'episode'
        info['episode'] = data.get('episode_nr', '')           
        info['season'] = data.get('season_nr', '')
        info['tvshowtitle'] = data.get('serie_title', '')
        if info['title'] == '':
            info['title'] = '%s - S%02dE%02d' % (data.get('serie_title', ''), data.get('season_nr', 0), data.get('episode_nr', 0))
#        else:
#            info['title'] = '%02d - %s' % (info['episode'], info['title'])
    if asset_type == 'Sport':
        pass
    if asset_type == 'Clip':
        info['title'] = data['item_title']
        info['plot'] = data.get('teaser_long', '')
        info['genre'] = data.get('item_category_name', '')
    if asset_type == 'live':
        info['title'] = data['channel']['name']
        info['plot'] = data['event'].get('subtitle', '')
    if asset_type == 'searchresult':
        info['plot'] = data.get('description', '')
        info['year'] = data.get('year', '')
        info['genre'] = data.get('category', '')
   
    return info

def getWatchlistContextItem(item, delete=False):
    label = 'Zur Merkliste hinzufügen'
    action = 'watchlistAdd'
    asset_type = item['type']
    if delete:
        label = 'Von Merkliste entfernen'
        action = 'watchlistDel'
    if asset_type == 'searchresult':
        asset_type = item['data']['contentType']
    url = common.build_url({'action': action, 'id': item['data']['id'], 'assetType': asset_type})
    return [(label, 'RunPlugin(' + url + ')')]

def listAssets(asset_list, isWatchlist=False):
    for item in asset_list:
        isPlayable = False
        li = xbmcgui.ListItem(label=item['label'], iconImage=icon_file)
        print item
        if item['type'] in ['Film', 'Episode', 'Sport', 'Clip', 'Series', 'live', 'searchresult']:
            isPlayable = True
            info = getInfoLabel(item['type'], item['data'])
            li.setInfo('video', info)
            li.setLabel(info['title'])
            li.setArt({'poster': getPoster(item['data']), 'fanart': getHeroImage(item['data'])})       
        if item['type'] in ['Film']:
            xbmcplugin.setContent(addon_handle, 'movies')
        elif item['type'] in ['Series']:
            xbmcplugin.setContent(addon_handle, 'tvshows')
            isPlayable = False
        elif item['type'] in ['Episode']:
            xbmcplugin.setContent(addon_handle, 'episodes')
        elif item['type'] in ['Sport', 'Clip']:
            xbmcplugin.setContent(addon_handle, 'files')
            li.setArt({'thumb': getHeroImage(item['data'])})
        elif item['type'] == 'searchresult':          
            xbmcplugin.setContent(addon_handle, 'movies')
        elif item['type'] == 'live':
            xbmcplugin.setContent(addon_handle, 'movies')
            li.setArt({'poster': getPoster(item['data']['channel']), 'fanart': skygo.baseUrl + item['data']['event']['image']})

        #add contextmenu item for watchlist to playable content - not for live and clip content
        if isPlayable and not item['type'] in ['live', 'Clip']:
            li.addContextMenuItems(getWatchlistContextItem(item, isWatchlist), replaceItems=False)
        li.setProperty('IsPlayable', str(isPlayable).lower())
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=item['url'],
                                    listitem=li, isFolder=(not isPlayable))

    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)
    
    
def listPath(path):
    page = {}
    path = path.replace('ipad', 'web')
    r = requests.get(skygo.baseUrl + path)
    if r.status_code != 404:
        page = r.json()
    else:
        return False
    if 'sort_by_lexic_p' in path:
        url = common.build_url({'action': 'listPage', 'path': path[0:path.index('sort_by_lexic_p')] + 'header.json'})
        addDir('[A-Z]', url)

    listitems = parseListing(page, path)
    listAssets(listitems)       

def getPageItems(nodes, page_id):
    listitems = []
    for section in nodes.iter('section'):
        if section.attrib['id'] == page_id:
            for item in section:
                #if (item.attrib['hide'] == 'true' or int(item.attrib['id']) in nav_blacklist) and not int(item.attrib['id']) in nav_force:
                if int(item.attrib['id']) in nav_blacklist:
                    continue
                listitems.append(item)

    return listitems

def getParentNode(nodes, page_id):
    for item in nodes.iter('section'):
        if item.attrib['id'] == page_id:
            return item
    return None

def listPage(page_id):
    nav = getNav()
    items = getPageItems(nav, page_id)
    if len(items) == 1:
        if 'path' in items[0].attrib:
            listPath(items[0].attrib['path'])
            return
    for item in items:
        url = ''
        if item.tag == 'item':
            url = common.build_url({'action': 'listPage', 'path': item.attrib['path']})
        elif item.tag == 'section':
            url = common.build_url({'action': 'listPage', 'id': item.attrib['id']})

        addDir(item.attrib['label'], url)

    if len(items) > 0:
        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)         


