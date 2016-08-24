import sys

import xbmcaddon
import xbmcgui
import xbmcplugin
import common
from skygo import SkyGo

addon_handle = int(sys.argv[1])
addon = xbmcaddon.Addon()
skygo = SkyGo()

def play_vod(vod_id):
    login = skygo.login()

    if login:
        session_id = skygo.sessionId
        # Get the play info via the id of the video
        play_info = skygo.getPlayInfo(id=vod_id)

        if skygo.may_play(play_info['package_code']):
            apix_id = play_info['apixId']
            manifest = play_info['manifestUrl']
            duration = int(play_info['duration'])*60

            # create init data for licence acquiring
            init_data = skygo.get_init_data(session_id, apix_id)

            # Prepare new ListItem to start playback
            li = xbmcgui.ListItem(path=manifest)
            info = {
                'mediatype': 'movie',
                'duration': duration
            }
            li.setInfo('video', info)

            # Force smoothsteam addon
            li.setProperty('inputstream.smoothstream.license_type', 'com.widevine.alpha')
            li.setProperty('inputstream.smoothstream.license_key', skygo.licence_url)
            li.setProperty('inputstream.smoothstream.license_data', init_data)
            li.setProperty('inputstreamaddon', 'inputstream.smoothstream')

            # Start Playing
            xbmcplugin.setResolvedUrl(addon_handle, True, listitem=li)

        else:
            xbmcgui.Dialog().notification('SkyGo Fehler', 'Keine Berechtigung zum Abspielen dieses Eintrages', xbmcgui.NOTIFICATION_ERROR, 2000, True)
            li = xbmcgui.ListItem()
            xbmcplugin.setResolvedUrl(addon_handle, False, listitem=li)
    else:
        xbmcgui.Dialog().notification('SkyGo Fehler', 'Fehler bei Login', xbmcgui.NOTIFICATION_ERROR, 2000, True)
        print 'Fehler beim Einloggen'
