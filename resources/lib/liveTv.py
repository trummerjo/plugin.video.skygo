import sys

import xbmcaddon
import xbmcgui
import xbmcplugin
import common
from skygo import SkyGo


addon_handle = int(sys.argv[1])
addon = xbmcaddon.Addon()
username = addon.getSetting('email')
password = addon.getSetting('password')
skygo = SkyGo()


def generate_channel_list():
    channels = skygo.getChannels()
    xbmcplugin.setContent(addon_handle, 'videos')
    for channel in channels:
        url = common.build_url({'action': 'playLiveTvChannel', 'epg_channel_id': channel['id'], 'mediaUrl': channel['mediaurl']})
        li = xbmcgui.ListItem(label=channel['name'])
        li.setProperty('IsPlayable', 'true')
        li.setArt({'thumb': skygo.baseUrl+channel['logo']})
        info = {
            'mediatype': 'video'
        }
        li.setInfo('video', info)
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li, isFolder=False)

    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)


def play_live_tv(epg_channel_id):
    # Get Current running event on channel
    current_event = skygo.getCurrentEvent(epg_channel_id)

    # If there is a running event play it
    if current_event is not False:
        event_id = current_event['id']
        playInfo = skygo.getEventPlayInfo(event_id, epg_channel_id)

        apix_id = playInfo['apixId']
        manifest_url = playInfo['manifestUrl']

        # Login to get session
        login = skygo.login(username, password)
        session_id = skygo.sessionId

        # create init data for licence acquiring
        init_data = skygo.get_init_data(session_id, apix_id)

        # Create list item with inputstream addon
        li = xbmcgui.ListItem(path=manifest_url)
        info = {
            'mediatype': 'movie',
        }
        li.setInfo('video', info)
        li.setProperty('inputstream.smoothstream.license_type', 'com.widevine.alpha')
        li.setProperty('inputstream.smoothstream.license_key', skygo.licence_url)
        li.setProperty('inputstream.smoothstream.license_data', init_data)
        li.setProperty('inputstreamaddon', 'inputstream.smoothstream')

        xbmcplugin.setResolvedUrl(addon_handle, True, listitem=li)


    else:
        xbmcgui.Dialog().notification('Kein laufendes Event', 'Auf diesem Kanal ist kein laufendes Event vorhanden.', icon=xbmcgui.NOTIFICATION_WARNING)

