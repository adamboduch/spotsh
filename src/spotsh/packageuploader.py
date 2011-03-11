
#    spotsh - The SpotCloud command-line utility.
#    Copyright (C) 2011  Enomaly
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
from urlparse import urljoin, urlparse, urlsplit
import urllib2
import os.path
import socket
from email.Generator import _make_boundary

try:
    from json import loads, dumps
except:
    from simplejson import loads, dumps
    
def upload_package(client, pkg_path):
    
    upload_url = get_upload_url(client)
    result = upload(client, upload_url, pkg_path)
    return result

def get_upload_url(client):

    upload_url = client.get('/api/package/upload').read()
    return upload_url

def upload(client, upload_url, pkg_path):
    
    content_type, prefix, suffix = build_headers(os.path.basename(pkg_path))
    body_length = os.path.getsize(pkg_path)
    content_length = len(prefix) + body_length + len(suffix)

    url_parts = urlsplit(upload_url)    
    
    client.connection.putrequest('POST', url_parts[2])
    client.connection.putheader('Content-Type', content_type)
    client.connection.putheader('Content-Length', content_length)
    client.connection.endheaders()

    client.connection.send(prefix)
    
    body_file = open(pkg_path)
    try:
        blocksize=1024
        data=body_file.read(blocksize)
        while data:
            print '\rUploading: %2d%%...' % ((body_file.tell()*100)/body_length),
            sys.stdout.flush() 
            client.connection.sock.sendall(data)
            data=body_file.read(blocksize)
    except socket.error, v:
        if v.args[0] == 32:
            client.connection.close()
        raise
    print "\rUpload completed.        "

    client.connection.send(suffix)
    response = client.connection.getresponse() 
    
    if response.status == 200:
        return loads(response.read())
    if response.status in (302, 303):            
        location = response.getheader('Location')
        return loads(urllib2.urlopen(location).read())
        
    raise Exception('Unknown return status: %s %s' % (response.status, response.reason))

def build_headers(filename, key_name='file'):
    
    boundary = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    PREFIX = []
    PREFIX.append('--' + boundary)
    PREFIX.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key_name, filename))
    PREFIX.append('Content-Type: %s' % 'application/octet-stream')
    PREFIX.append('')
    PREFIX.append('')
    
    SUFFIX = ['']
    SUFFIX.append('--' + boundary + '--')
    SUFFIX.append('')
    
    content_type = 'multipart/form-data; boundary=%s' % boundary
    
    return content_type, CRLF.join(PREFIX), CRLF.join(SUFFIX)
