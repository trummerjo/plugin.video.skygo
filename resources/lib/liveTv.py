import sys

import xbmcaddon
import xbmcgui
import xbmcplugin
import common
from skygo import SkyGo

addon_handle = int(sys.argv[1])
addon = xbmcaddon.Addon()
skygo = SkyGo()

def playLiveTv(manifest_url):
    #hardcoded apixId for live content
    apix_id = 'livechannel_127'

    # Login to get session
    login = skygo.login()
    if login:
        session_id = skygo.sessionId

        # create init data for licence acquiring
        init_data = skygo.get_init_data(session_id, apix_id)

        # Create list item with inputstream addon
        li = xbmcgui.ListItem(path=manifest_url)
        info = {'mediatype': 'movie'}
        li.setInfo('video', info)
        li.setProperty('inputstream.smoothstream.license_type', 'com.widevine.alpha')
        li.setProperty('inputstream.smoothstream.license_key', skygo.licence_url)
        li.setProperty('inputstream.smoothstream.license_data', init_data)
        li.setProperty('inputstreamaddon', 'inputstream.smoothstream')

        xbmcplugin.setResolvedUrl(addon_handle, True, listitem=li)

    else:
        xbmcgui.Dialog().notification('SkyGo Fehler', 'Fehler bei Login', xbmcgui.NOTIFICATION_ERROR, 2000, True)
        print 'Fehler beim Einloggen'


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
        login = skygo.login()
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

