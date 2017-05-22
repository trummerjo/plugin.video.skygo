import sys
from skygo import SkyGo
import navigation as nav

skygo = SkyGo()

def playAsset(asset_id):
    #get asset details and build infotag from it
    asset_info = skygo.getAssetDetails(asset_id)
    info_tag, asset_info = nav.getInfoLabel(asset_info.get('type', ''), asset_info)
    manifest_url = asset_info['media_url']
    if 'ms_media_url' in asset_info:
        manifest_url = asset_info['ms_media_url']

    skygo.play(manifest_url, package_code=asset_info['package_code'], info_tag=info_tag, apix_id=str(asset_info['event_id']))