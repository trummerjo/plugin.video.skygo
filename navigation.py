import sys
import xbmcgui
import xbmcplugin
import requests
import json
import resources.lib.liveTv as liveTv
import resources.lib.common as common
import resources.lib.vod as vod
from skygo import SkyGo
import watchlist
import xml.etree.ElementTree as ET

addon_handle = int(sys.argv[1])
plugin_base_url = sys.argv[0]
skygo = SkyGo()

#Blacklist: diese nav_ids nicht anzeigen
#Sport: Datencenter, NewsSection, Aktuell
nav_blacklist = [34, 32, 27]
#Force: anzeige dieser nav_ids erzwingen
#Sport: Wiederholungen
nav_force = [35]

def getNav():
    r = requests.get('http://www.skygo.sky.de/sg/multiplatform/ipad/json/navigation.xml')
    nav = ET.fromstring(r.text.encode('utf-8'))

    return nav

def liveChannelsDir():
    url = common.build_url({'action': 'listLiveTvChannels'})
    li = xbmcgui.ListItem('Livesender')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)

def watchlistDir():
    url = common.build_url({'action': 'watchlist'})
    li = xbmcgui.ListItem('Merkliste')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)

def rootDir():
    nav = getNav()
    #Livesender
    liveChannelsDir()
    #Navigation der Ipad App
    for item in nav:
        if item.attrib['hide'] == 'true' or item.tag == 'item':
            continue
        url = common.build_url({'action': 'listPage', 'id': item.attrib['id']})
        li = xbmcgui.ListItem(item.attrib['label'])
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li, isFolder=True)

    #Merkliste
    watchlistDir()
    #Suchfunktion
    url = common.build_url({'action': 'search'})
    li = xbmcgui.ListItem('Suche')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)     
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)
    
def getHeroImage(data):
    if 'main_picture' in data:
        for pic in data['main_picture']['picture']:
            if pic['type'] == 'hero_img':
                return skygo.baseUrl + pic['path']+'/'+pic['file']
    if 'item_image' in data:
        return skygo.baseUrl + data['item_image']

    return ''

def getPoster(data):
    if 'logo' in data:
        return skygo.baseUrl + data['logo']
    if 'picture' in data:
        return skygo.baseUrl + data['picture']
    if 'dvd_cover' in data:
        return skygo.baseUrl + data['dvd_cover']['path'] + '/' + data['dvd_cover']['file']
    if 'item_preview_image' in data:
        return skygo.baseUrl + data['item_preview_image']

    return ''

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
                url = common.build_url({'action': 'playLive', 'event_id': event['event']['id'], 'manifest': event['channel']['msMediaUrl']})                
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
                url = common.build_url({'action': 'play_vod', 'vod_id': episode['id']})
                li = xbmcgui.ListItem()
                li.setProperty('IsPlayable', 'true')
                info = getInfoLabel('Episode', episode)
                li.setInfo('video', info)
                li.setLabel(info['title'])
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
        label = 'Staffel %02d' % (season['nr'])
        li = xbmcgui.ListItem(label=season['webplayer_config']['assetTitle'])
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
#                        elif 'asset_type' in item:
#                            if item['asset_type'].lower() in ['film', 'clip', 'episode', 'sport']:
#                                if item['asset_type'].lower() == 'clip':
#                                    url = common.build_url({'action': 'playVod', 'vod_id': item['id']})
#                                    listitems.append({'type': 'asset', 'label': '', 'url': url, 'data': item})
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
    if info['plot'] == '':
        info['plot'] = data.get('description', '').replace('\n', '').strip()
    info['genre'] = data.get('category', {}).get('main', {}).get('content', '')
    info['duration'] = data.get('length', 0)*60
    if asset_type == 'Film':
        pass
    if asset_type == 'Series':
        info['year'] = data.get('year_of_production_start', '')
    if asset_type == 'Episode':
        info['episode'] = data.get('episode_nr', '')           
        info['season'] = data.get('season_nr', '')
        if info['title'] == '':
            info['title'] = '%s - S%02dE%02d' % (data.get('serie_title', ''), data.get('season_nr', 0), data.get('episode_nr', 0))
        else:
            info['title'] = '%02d - %s' % (info['episode'], info['title'])
    if asset_type == 'Sport':
        pass
    if asset_type == 'Clip':
        info['title'] = data['item_title']
        info['plot'] = data.get('teaser_long', '')
        info['genre'] = data.get('item_category_name', '')
    if asset_type == 'live':
        info['title'] = data['channel']['name']
        info['plot'] = data['event'].get('subtitle', '')
    
    return info

def listAssets(asset_list):
    for item in asset_list:
        isPlayable = False
        li = xbmcgui.ListItem(label=item['label'])
        if item['type'] in ['Film', 'Episode', 'Sport', 'Clip', 'Series', 'live']:
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
            xbmcplugin.setContent(addon_handle, 'files')
        elif item['type'] == 'live':
            xbmcplugin.setContent(addon_handle, 'movies')
            li.setArt({'poster': getPoster(item['data']['channel']), 'fanart': skygo.baseUrl + item['data']['event']['image']})
            
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
        li = xbmcgui.ListItem(label='[A-Z]')
        url = common.build_url({'action': 'listPage', 'path': path[0:path.index('sort_by_lexic_p')] + 'header.json'})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li, isFolder=True)
    listitems = parseListing(page, path)
    listAssets(listitems)       

def getPageItems(node):
    listitems = []
    for item in node:
        if (item.attrib['hide'] == 'true' or int(item.attrib['id']) in nav_blacklist) and not int(item.attrib['id']) in nav_force:
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
    node = getParentNode(nav, page_id)
    items = getPageItems(node)
    if len(items) == 1:
        if 'path' in items[0].attrib:
            listPath(items[0].attrib['path'])
            return
    for item in items:
        li = xbmcgui.ListItem(item.attrib['label'])
        if item.tag == 'item':
            url = common.build_url({'action': 'listPage', 'path': item.attrib['path']})
        elif item.tag == 'section':
            url = common.build_url({'action': 'listPage', 'id': item.attrib['id']})

        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li, isFolder=True)

    if len(items) > 0:
        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)         

