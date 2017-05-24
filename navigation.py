# coding: utf8
import sys
import os
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs
import requests
import urllib2
import json
import datetime
import time
import xml.etree.ElementTree as ET
import resources.lib.common as common
from skygo import SkyGo
import watchlist
import re
import urllib
import base64
from HTMLParser import HTMLParser

try:
    import StorageServer
except:
    import storageserverdummy as StorageServer

addon = xbmcaddon.Addon()

# Doc for Caching Function: http://kodi.wiki/index.php?title=Add-on:Common_plugin_cache
assetDetailsCache = StorageServer.StorageServer(addon.getAddonInfo('name') + '.assetdetails', 24 * 30)
TMDBCache = StorageServer.StorageServer(addon.getAddonInfo('name') + '.TMDBdata', 24 * 30)

extMediaInfos = addon.getSetting('enable_extended_mediainfos')
addon_handle = int(sys.argv[1])
icon_file = xbmc.translatePath(addon.getAddonInfo('path')+'/icon.png').decode('utf-8')
skygo = SkyGo()
htmlparser = HTMLParser()

#Blacklist: diese nav_ids nicht anzeigen
#Sport: Datencenter, NewsSection, Aktuell, Snap
nav_blacklist = [34, 32, 27, 15]
#Force: anzeige dieser nav_ids erzwingen
#Sport: Wiederholungen
nav_force = [35, 36, 37, 161]

#Jugendschutz
js_showall = xbmcaddon.Addon().getSetting('js_showall')
 
def getNav():
    feed = urllib2.urlopen('http://www.skygo.sky.de/sg/multiplatform/ipad/json/navigation.xml')
    nav = ET.parse(feed)
    return nav.getroot()
     
def liveChannelsDir():
    url = common.build_url({'action': 'listLiveTvChannelDirs'})
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

    xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)

def addDir(label, url, icon=icon_file):
    li = xbmcgui.ListItem(label, iconImage=icon)
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)

def showParentalSettings():
    fsk_list = ['Deaktiviert', '0', '6', '12', '16', '18']
    dlg = xbmcgui.Dialog()
    code = dlg.input('PIN Code', type=xbmcgui.INPUT_NUMERIC)
    if code == xbmcaddon.Addon().getSetting('password'):
        idx = dlg.select('Wähle maximale FSK Alterstufe', fsk_list)
        if idx >= 0:
            fsk_code = fsk_list[idx]
            if fsk_code == 'Deaktiviert':
                xbmcaddon.Addon().setSetting('js_maxrating', '-1')
            else:
                xbmcaddon.Addon().setSetting('js_maxrating', fsk_list[idx])
        if idx > 0:
            if dlg.yesno('Jugendschutz', 'Sollen Inhalte mit einer Alterseinstufung über ', 'FSK ' + fsk_list[idx] + ' angezeigt werden?'):
                xbmcaddon.Addon().setSetting('js_showall', 'true')
            else:
                xbmcaddon.Addon().setSetting('js_showall', 'false')
    else:
        xbmcgui.Dialog().notification('SkyGo - Jugendschutz', 'Fehlerhafte PIN', xbmcgui.NOTIFICATION_ERROR, 2000, True)
    
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
    if 'name' in data and xbmcaddon.Addon().getSetting('enable_customlogos') == 'true':
        img = getLocalChannelLogo(data['name'])
        if img:
            return img
    if data.get('dvd_cover', '') != '':
        return skygo.baseUrl + data['dvd_cover']['path'] + '/' + data['dvd_cover']['file']
    if data.get('item_preview_image', '') != '':
        return skygo.baseUrl + data['item_preview_image']
    if data.get('picture', '') != '':
        return skygo.baseUrl + data['picture']
    if data.get('logo', '') != '':
        return skygo.baseUrl + data['logo']

    return ''

def getChannelLogo(data):
    logopath = ''
    if 'channelLogo' in data:
        basepath = data['channelLogo']['basepath'] + '/'
        size = 0
        for logo in data['channelLogo']['logos']:
            logosize = logo['size'][:logo['size'].find('x')]
            if int(logosize) > size:
                size = int(logosize)
                logopath = skygo.baseUrl + basepath + logo['imageFile']
    return logopath

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

def listLiveTvChannelDirs():
    data = getlistLiveChannelData()
    for tab in data:
        url = common.build_url({'action': 'listLiveTvChannels', 'channeldir_name': tab['tabName']})
        li = xbmcgui.ListItem(label=tab['tabName'].title(), iconImage=icon_file)
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)

def listLiveTvChannels(channeldir_name):
    data = getlistLiveChannelData(channeldir_name)
    for tab in data:
        if tab['tabName'].lower() == channeldir_name.lower():
            details = {}
            for event in tab['eventList']:
                if event['event']['detailPage'].startswith("http"):
                    detail = event['event']['detailPage']
                else:
                    detail = str(event['event']['cmsid'])
                if 'assetid' not in event['event']:
                    assetid_match = re.search('\/([0-9]*)\.html', event['event']['detailPage'])
                    if assetid_match:
                        assetid = int(assetid_match.group(1))
                        try:
                            if assetid > 0:
                                mediainfo = getAssetDetailsFromCache(assetid)
                                event['mediainfo'] = mediainfo
                                manifest_url = mediainfo['media_url']
                                if not manifest_url.startswith('http://'):
                                    continue
                        except:
                            continue
                    url = common.build_url({'action': 'playLive', 'manifest_url': manifest_url, 'package_code': event['channel']['mobilepc']})
                elif event['channel']['msMediaUrl'].startswith('http://'):
                    manifest_url = event['channel']['msMediaUrl']
                    url = common.build_url({'action': 'playLive', 'manifest_url': manifest_url, 'package_code': event['channel']['mobilepc']})

                else:                    
                    url = common.build_url({'action': 'playVod', 'vod_id': event['event']['assetid']})
                    try:
                        if event['event']['assetid'] > 0:
                            mediainfo = getAssetDetailsFromCache(event['event']['assetid'])
                            event['mediainfo'] = mediainfo
                    except:
                        pass

                #zeige keine doppelten sender mit gleichem stream - nutze hd falls verfügbar
                if detail != '':
                    if not detail in details.keys():                 
                        details[detail] = {'type': 'live', 'label': event['channel']['name'], 'url': url, 'data': event}
                    elif details[detail]['data']['channel']['hd'] == 0 and event['channel']['hd'] == 1 and event['channel']['name'].find('+') == -1:
                        details[detail] = {'type': 'live', 'label': event['channel']['name'], 'url': url, 'data': event}

            listAssets(sorted(details.values(), key=lambda k:k['data']['channel']['name']))

def getlistLiveChannelData(channel = ''):
    version = 'ipad'
    if channel.lower() == 'bundesliga' or channel.lower() == 'sport':
        version = 'web'
    url = 'http://www.skygo.sky.de/epgd/sg/' + version + '/excerpt/'
    data = requests.get(url).json()
    data = [json for json in data if json['tabName'] != 'welt']
    for tab in data:
        if tab['tabName'] == 'film':
            tab['tabName'] = 'cinema'
        elif tab['tabName'] == 'buli':
            tab['tabName'] = 'bundesliga'
    return sorted(data, key=lambda k: k['tabName'])    

def listEpisodesFromSeason(series_id, season_id):
    url = skygo.baseUrl + '/sg/multiplatform/web/json/details/series/' + str(series_id) + '_global.json'
    r = requests.get(url)
    data = r.json()['serieRecap']['serie']
    xbmcplugin.setContent(addon_handle, 'episodes')
    for season in data['seasons']['season']:
        if str(season['id']) == str(season_id):
            for episode in season['episodes']['episode']:
                #Check Altersfreigabe / Jugendschutzeinstellungen
                if 'parental_rating' in episode:
                    if js_showall == 'false':
                        if not skygo.parentalCheck(episode['parental_rating']['value'], play=False):   
                            continue
                url = common.build_url({'action': 'playVod', 'vod_id': episode['id']})
                li = xbmcgui.ListItem()
                li.setProperty('IsPlayable', 'true')
                li.addContextMenuItems(getWatchlistContextItem({'type': 'Episode', 'data': episode}), replaceItems=False)
                info, episode = getInfoLabel('Episode', episode)
                li.setInfo('video', info)
                li.setLabel('%02d. %s' % (info['episode'], info['title']))
                li.setArt({'poster': skygo.baseUrl + season['path'], 
                           'fanart': getHeroImage(data),
                           'thumb': skygo.baseUrl + episode['webplayer_config']['assetThumbnail']})
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                            listitem=li, isFolder=False)

    xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_EPISODE)
    xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR) 
    xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_DURATION)
    xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
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

    xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR)   
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

def buildLiveEventTag(event_info):
    tag = ''
    dayDict = {'Monday': 'Montag', 'Tuesday': 'Dienstag', 'Wednesday': 'Mittwoch', 'Thursday': 'Donnerstag', 'Friday': 'Freitag', 'Saturday': 'Samstag', 'Sunday': 'Sonntag'}
    if event_info != '':  
        now = datetime.datetime.now()

        strStartTime = '%s %s' % (event_info['start_date'], event_info['start_time'])
        strEndTime = '%s %s' % (event_info['end_date'], event_info['end_time'])
        start_time = datetime.datetime.fromtimestamp(time.mktime(time.strptime(strStartTime, "%Y/%m/%d %H:%M")))
        end_time = datetime.datetime.fromtimestamp(time.mktime(time.strptime(strEndTime, "%Y/%m/%d %H:%M")))

        if (now >= start_time) and (now <= end_time):
            tag = '[COLOR red][Live][/COLOR]'
        elif start_time.date() == datetime.datetime.today().date():
            tag = '[COLOR blue][Heute ' + event_info['start_time'] + '][/COLOR]'
        elif start_time.date() == (datetime.datetime.today() + datetime.timedelta(days=1)).date():
            tag = '[COLOR blue][Morgen ' + event_info['start_time'] + '][/COLOR]'
        else:
            day = start_time.strftime('%A')
            if not day in dayDict.values():
                day = day.replace(day, dayDict[day])[0:2]
            tag = '[COLOR blue][' + day + ', ' + start_time.strftime("%d.%m %H:%M]") + '[/COLOR]'
    
    return tag

def getInfoLabel(asset_type, item_data):
    data = item_data
    if 'mediainfo' in data:
        data = data['mediainfo']
    elif extMediaInfos and extMediaInfos == 'true':
            try:
                data = getAssetDetailsFromCache(data['id'])
            except:
                pass 
    info = {}
    info['title'] = data.get('title', '')
    info['originaltitle'] = data.get('original_title', '')
    if not data.get('year_of_production', '') == '':
        info['year'] = data.get('year_of_production', '')
    info['plot'] = data.get('synopsis', '').replace('\n', '').strip()
    if info['plot'] == '':
        info['plot'] = data.get('description', '').replace('\n', '').strip()
    info['duration'] = data.get('lenght', 0) * 60
    if data.get('main_trailer', {}).get('trailer', {}).get('url', '') != '':
        info['trailer'] = data.get('main_trailer', {}).get('trailer', {}).get('url', '')
    if data.get('cast_list', {}).get('cast', {}) != '':
        cast_list = []
        castandrole_list = []
        for cast in data.get('cast_list', {}).get('cast', {}):
            if cast['type'] == 'Darsteller':
                if cast['character'] != '':
                    char = re.search('(.*)\(', cast['content']).group(1).strip() if re.search('(.*)\(', cast['content']) else ''
                    castandrole_list.append((char, cast['character']))
                else:
                    cast_list.append(cast['content'])
            elif cast['type'] == 'Regie':
                info['director'] = cast['content']
        if len(castandrole_list) > 0:
            info['castandrole'] = castandrole_list
        else:
            info['cast'] = cast_list
    if data.get('genre', {}) != '':
        category_list = []
        for category in data.get('genre', {}):
            if 'content' in data.get('genre', {}).get(category, {}) and not data.get('genre', {}).get(category, {}).get('content', {}) in category_list:
                category_list.append(data.get('genre', {}).get(category, {}).get('content', {}))
        info['genre'] = ", ".join(category_list)

    if asset_type == 'Sport':
        if data.get('current_type', '') == 'Live':
            #LivePlanner listing
            info['title'] = buildLiveEventTag(data['technical_event']['on_air']) + ' ' + info['title']
    if asset_type == 'Clip':
        info['title'] = data['item_title']
        info['plot'] = data.get('teaser_long', '')
        info['genre'] = data.get('item_category_name', '')
    if asset_type == 'live':
        item_data['event']['subtitle'] = htmlparser.unescape(item_data['event'].get('subtitle', ''))
        info['title'] = item_data['event'].get('subtitle', '')
        info['plot'] = data.get('synopsis', '').replace('\n', '').strip() if data.get('synopsis', '') != '' else item_data['event'].get('subtitle', '')
        if 'assetid' in item_data['event'] and not item_data['channel']['msMediaUrl'].startswith('http://'):
            if 'mediainfo' in item_data:
                info['title'] = data.get('title', '')
                info['plot'] = data.get('synopsis', '').replace('\n', '').strip()
            else:
                info['plot'] = 'Folge: ' + item_data.get('event', '').get('subtitle', '')
                info['title'] = item_data.get('event', '').get('title', '')
                info['duration'] = item_data.get('event', '').get('length', 0) * 60
            if data.get('type', {}) == 'Film':
                asset_type = 'Film'
            elif data.get('type', {}) == 'Episode':
                asset_type = 'Episode'
                info['plot'] = 'Folge: ' + data.get('title', '') + '\n\n' + data.get('synopsis', '').replace('\n', '').strip()
                info['title'] = '%1dx%02d. %s' % (data.get('season_nr', ''), data.get('episode_nr', ''), data.get('serie_title', ''))
        if xbmcaddon.Addon().getSetting('channel_name_first') == 'true':
            channel = '[COLOR blue]' + item_data['channel']['name'] + ' | [/COLOR]'
            info['title'] = channel + info['title']
        else:
            channel = '[COLOR blue] | ' + item_data['channel']['name'] + '[/COLOR]'
            info['title'] += channel               
    if asset_type == 'searchresult':
        info['plot'] = data.get('description', '')
        info['year'] = data.get('year', '')
        info['genre'] = data.get('category', '')
    if asset_type == 'Film':
        info['mediatype'] = 'movie'
        if xbmcaddon.Addon().getSetting('lookup_tmdb_data') == 'true' and not data.get('title', '') == '': 
            title = data.get('title', '').encode("utf-8") 
            xbmc.log('Searching Rating and better Poster for %s at tmdb.com' % title.upper())
            if not data.get('year_of_production', '') == '':
                TMDb_Data = getTMDBDataFromCache(title, info['year'])
            else:
                TMDb_Data = getTMDBDataFromCache(title)
            # xbmc.log('Debug-Info: TMDb_Data: %s' % TMDb_Data)
            if TMDb_Data['rating'] is not None:
                info['rating'] = str(TMDb_Data['rating'])
                info['plot'] = 'User-Rating: '+ info['rating'] + ' / 10 (from TMDb) \n\n' + info['plot']
                xbmc.log( "Result of get Rating: %s" % (TMDb_Data['rating']) )  
            if TMDb_Data['poster_path'] is not None:
                item_data['TMDb_poster_path'] = TMDb_Data['poster_path']            
                xbmc.log( "Path to TMDb Picture: %s" % (TMDb_Data['poster_path']) )                 
    if asset_type == 'Series':
        info['year'] = data.get('year_of_production_start', '')
    if asset_type == 'Episode':
        info['mediatype'] = 'episode'
        info['episode'] = data.get('episode_nr', '')           
        info['season'] = data.get('season_nr', '')
        info['tvshowtitle'] = data.get('serie_title', '')
        if info['title'] == '':
            info['title'] = '%s - S%02dE%02d' % (data.get('serie_title', ''), data.get('season_nr', 0), data.get('episode_nr', 0))
    # xbmc.log( "Debug_Info Current info Element: %s" % (info) ) 
    return info, item_data

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
        if item['type'] in ['Film', 'Episode', 'Sport', 'Clip', 'Series', 'live', 'searchresult']:
            isPlayable = True
            #Check Altersfreigabe / Jugendschutzeinstellungen
            if 'parental_rating' in item['data']:
                if js_showall == 'false':
                    if not skygo.parentalCheck(item['data']['parental_rating']['value'], play=False):   
                        continue
            info, item['data'] = getInfoLabel(item['type'], item['data'])
            # xbmc.log( "Debug_Info Current item Element: %s" % (item) ) 
            li.setInfo('video', info)
            li.setLabel(info['title'])         
            li.setArt({'poster': getPoster(item['data']), 'fanart': getHeroImage(item['data'])})           
        if item['type'] in ['Film']:
            xbmcplugin.setContent(addon_handle, 'movies')
            if xbmcaddon.Addon().getSetting('lookup_tmdb_data') == 'true' and 'TMDb_poster_path' in item['data']:
                poster_path = item['data']['TMDb_poster_path'] 
            else:
                poster_path = getPoster(item['data'])
            # xbmc.log('Debug-Info: Current Poster in item: %s' % getPoster(item['data']) ) 
            # xbmc.log('Debug-Info: Current Poster in info: %s' % item['data']['TMDb_poster_path'] )    
            li.setArt({'poster': poster_path})
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
        elif item['type'] == ('live'):
            xbmcplugin.setContent(addon_handle, 'files')
            if 'TMDb_poster_path' in item['data']:
                poster = item['data']['TMDb_poster_path']
            elif 'mediainfo' in item['data']:
                poster = getPoster(item['data']['mediainfo'])
            else:
                poster = getPoster(item['data']['channel'])
            fanart = skygo.baseUrl + item['data']['event']['image'] if item['data']['channel']['name'].find('News') == -1 else skygo.baseUrl + '/bin/Picture/817/C_1_Picture_7179_content_4.jpg'
            thumb = skygo.baseUrl + item['data']['event']['image'] if item['data']['channel']['name'].find('News') == -1 else getChannelLogo(item['data']['channel'])
            li.setArt({'poster': poster, 'fanart': fanart, 'thumb': thumb})

        #add contextmenu item for watchlist to playable content - not for live and clip content
        if isPlayable and not item['type'] in ['live', 'Clip']:
            li.addContextMenuItems(getWatchlistContextItem(item, isWatchlist), replaceItems=False)
        li.setProperty('IsPlayable', str(isPlayable).lower())
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=item['url'],
                                    listitem=li, isFolder=(not isPlayable))

    xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_DURATION)
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
        xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)         

def getAssetDetailsFromCache(asset_id):
    return assetDetailsCache.cacheFunction(skygo.getAssetDetails, asset_id)

def getTMDBDataFromCache(title, year = None, attempt = 1, content='movie'):
    return TMDBCache.cacheFunction(getTMDBData, title, year, attempt, content)

def getTMDBData(title, year=None, attempt = 1, content='movie'):
    #This product uses the TMDb API but is not endorsed or certified by TMDb.
    rating = None
    poster_path = None
    tmdb_id = None
    splitter = [' - ', ': ', ', ']
    tmdb_api = base64.b64decode('YTAwYzUzOTU0M2JlMGIwODE4YmMxOTRhN2JkOTVlYTU=') # ApiKey Linkinsoldier
    Language = 'de'
    str_year = '&year=' + str(year) if year else ''
    movie = urllib.quote_plus(title)
    
    try:
        #Define the moviedb Link zu download the json
        host = 'http://api.themoviedb.org/3/search/%s?api_key=%s&language=%s&query=%s%s' % (content, tmdb_api, Language, movie, str_year)
        #Download and load the corresponding json
        data = json.load(urllib2.urlopen(host))
         
        if data['total_results'] > 0:
            result = data['results'][0]
            if result['vote_average']:
                rating = float(result['vote_average'])
            if result['poster_path']:
                poster_path = 'https://image.tmdb.org/t/p/w640' + str(result['poster_path'])
            tmdb_id = result['id']
        elif year is not None:
            attempt += 1
            xbmc.log('Try again - without release year - to find Title: %s' % title )
            return getTMDBData(title, None, attempt)
        else:
            xbmc.log('No movie found with Title: %s' % title )
        
    except (urllib2.URLError), e:
        xbmc.log('Error reason: %s' % e )
        
        if '429' or 'timed out' in e:
            attempt += 1
            xbmc.log('Attempt #%s - Too many requests - Pause 5 sec' % attempt)
            xbmc.sleep(5000)
            if attempt < 4:
                return getTMDBData(title, year, attempt)
        return {'tmdb_id': tmdb_id, 'title': title, 'rating': rating , 'poster_path': poster_path}
    return {'tmdb_id': tmdb_id, 'title': title, 'rating': rating , 'poster_path': poster_path}