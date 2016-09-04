import sys
import json
import time
import base64
import urllib
#cryptopy
from crypto.cipher import aes_cbc
#pycrypto
#from Crypto.Cipher import AES
from skygo import SkyGo
skygo = SkyGo()

secret_key = 'XABD-FHIM-GDFZ-OBDA-URDG-TTRI'
aes_key = ['826cf604accd0e9d61c4aa03b7d7c890', 'da1553b1515bd6f5f48e250a2074d30c']

def getClipToken(content):
    clipType = 'FREE'
    if content == 'ENTITLED USER' or content == 'SUBSCRIBED USER':
        clipType = 'NOTFREE'
    timestamp = str(time.time()).replace('.', '')
    url = 'https://www.skygo.sky.de/SILK/services/public/clipToken?clipType=' + clipType + '&product=SG&platform=web&version=12354=&_' + timestamp
    r = skygo.session.get(url)
    return json.loads(r.text[3:len(r.text)-1])

def buildClipUrl(url, token):
    #pyCrypto
    #dec = AES.new(aes_key[0].decode('hex'), AES.MODE_CBC, aes_key[1].decode('hex'))
    #path = dec.decrypt(base64.b64decode(token['tokenValue']))
    #query = token['tokenName'] + '=' + path2[0:len(path2)-7]
    #
    #cryptopy
    dec = aes_cbc.AES_CBC(key=aes_key[0].decode('hex'), keySize=16)
    path = dec.decrypt(base64.b64decode(token['tokenValue']), iv=aes_key[1].decode('hex'))
    query = token['tokenName'] + '=' + path
    return url + '?' + query

def playClip(clip_id):
    if skygo.login():
        clip_info = skygo.getClipDetails(clip_id)
        token = getClipToken(clip_info['content_subscription'])
        manifest = buildClipUrl(clip_info['videoUrlMSSProtected'], token)
        
        skygo.play(manifest, clip_info['package_code'])


