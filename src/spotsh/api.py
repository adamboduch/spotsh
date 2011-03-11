
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
import os
import os.path
import uuid
import httplib
import socket
from urllib import urlencode
from urlparse import urljoin

from oauth import oauth
from utils import to_str

OAUTH_GET_REQUEST_TOKEN_PATH    = '/_ah/OAuthGetRequestToken'
OAUTH_AUTHORIZE_TOKEN_PATH      = '/_ah/OAuthAuthorizeToken'
OAUTH_GET_ACCESS_TOKEN_PATH     = '/_ah/OAuthGetAccessToken'

URLENCODED_TYPE = 'application/x-www-form-urlencoded'

is_file = lambda o: hasattr(o, 'read')


def field_generator(boundary, name, value):
    yield '--' + boundary
    yield 'Content-Disposition: form-data; name="%s"' % to_str(name)
    yield ''
    yield to_str(value)

def file_generator(boundary, name, file):
    name = to_str(name)
    filename = to_str(os.path.basename(file.name))
    
    yield '--' + boundary
    yield 'Content-Disposition: form-data; name="%s"; filename="%s"' % (name, filename)
    yield 'Content-Type: application/octet-stream'
    yield ''
    yield file.read()

def multipart_generator(boundary, fields):
    for key, value in fields.items():
        if is_file(value):
            for chunk in file_generator(boundary, key, value):
                yield chunk
        else:
            for chunk in field_generator(boundary, key, value):
                yield chunk
    yield '--' + boundary + '--'
    yield ''

def encode_multipart(data):
    boundary = str(uuid.uuid4())
    body = '\r\n'.join(multipart_generator(boundary, data))
    headers = {
        'Content-Type': 'multipart/form-data; boundary=%s' % boundary,
        'Content-Length': len(body),
    }
    return headers, body


class ClientBase(object):
    
    def __init__(self, host):
        self.connection = httplib.HTTPSConnection(host)
    
    def sign_request(self, method, path, data, body, headers):
        pass
    
    def request(self, method, path, data=None, headers=None):
        body = None
        
        if headers:
            headers = headers.copy() 
        else:
            headers = {}
        
        if data:
            if method in ('GET', 'DELETE'):
                path += '?' + urlencode(data, doseq=True)
            elif method in ('POST', 'PUT'):
                content_headers, body = encode_multipart(data)
                headers.update(content_headers)
            else:
                raise ValueError('%s method is not supported' % method)
        
        self.sign_request(method, path, data, body, headers)
        
        try:
            self.connection.request(method, path, body, headers)
        except socket.gaierror:
            sys.exit('Host connection failed')
            
        response = self.connection.getresponse()
        
        return response
    
    def get(self, path, data=None, headers=None):
        return self.request('GET', path, data, headers)
    
    def post(self, path, data=None, headers=None):
        return self.request('POST', path, data, headers)
    
    def put(self, path, data=None, headers=None):
        return self.request('PUT', path, data, headers)
    
    def delete(self, path, data=None, headers=None):
        return self.request('DELETE', path, data, headers)


class SpotCloud(ClientBase):
    
    def __init__(self, host, consumer, access_token=None):
        
        super(SpotCloud, self).__init__(host)
        
        self.consumer = consumer
        self.request_token = None
        self.access_token = access_token
        self.host = host
    
    def fetch_oauth_request_token(self):
        response = self.get(OAUTH_GET_REQUEST_TOKEN_PATH)
        
        try:
            self.request_token = oauth.OAuthToken.from_string(response.read())
        except KeyError:
            return None
            
        return self.request_token
    
    def get_oauth_authorize_url(self):
        if self.request_token is None:
            raise RuntimeError('You should get request token first')
        
        url = urljoin('https://%s/' % self.host, OAUTH_AUTHORIZE_TOKEN_PATH)
        
        oauth_request = oauth.OAuthRequest.from_token_and_callback(
            token = self.request_token,
            http_url = url,
        )
        return oauth_request.to_url()
    
    def fetch_oauth_access_token(self):
        if self.request_token is None:
            raise RuntimeError('You should get request token first')
        
        response = self.get(OAUTH_GET_ACCESS_TOKEN_PATH)
        self.access_token = oauth.OAuthToken.from_string(response.read())
        return self.access_token
    
    def sign_request(self, method, path, data, body, headers):
        url = urljoin('https://%s/' % self.host, path)
        
        parameters = None
        if body is None or headers.get('Content-Type') == URLENCODED_TYPE:
            parameters = data
        
        signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1()
        
        if self.access_token is not None:
            token = self.access_token
        elif self.request_token is not None:
            token = self.request_token
        else:
            token = None
        
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            oauth_consumer = self.consumer,
            token = token,
            http_url = url,
            http_method = method,
            parameters = parameters,
        )
        oauth_request.sign_request(signature_method, self.consumer, token)
        headers.update(oauth_request.to_header())


