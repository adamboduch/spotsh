
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

import os
import os.path
import sys
import optparse
import pickle
import httplib

try:
    from json import loads, dumps
except:
    from simplejson import loads, dumps
from oauth import oauth

import model
from api import SpotCloud
from packagebuilder import build_package, PackageConfig, DISK_TYPE_HD,\
                           ExistingImageDisk
from packageuploader import upload_package


ACCESS_TOKEN_PATH = os.path.expanduser('~/.spotcloud_api_token')


class BaseCommand(object):
    
    option_list = [
        optparse.make_option('-z',
                             '--host',
                             default='spotcloud.appspot.com',
                             dest='_host',
                             help='Host')
    ]
    
    def __init__(self, options):
        self.option_list.extend(options)
        self.parser = optparse.OptionParser(usage=self.usage(),
                                            version=self.get_version(),
                                            option_list=self.option_list)
        self.options, self.args = self.parser.parse_args()
        try:
            self.client = self.makeClient()
        except RuntimeError:
            print self.usage()
        
    def makeClient(self):

        loaded = False
        access_token = None
        
        try:
            access_token = pickle.load(open(ACCESS_TOKEN_PATH))
            loaded = True
        except:
            pass
        
        consumer = oauth.OAuthConsumer('anonymous', 'anonymous')

        client = SpotCloud(self.options._host, consumer, access_token=access_token)
        
        if not client.access_token:
            client.fetch_oauth_request_token()
            authorization_url = client.get_oauth_authorize_url()
            print 'Please confirm token on page %s and press Enter' % authorization_url
            try:
                raw_input()
            except KeyboardInterrupt:
                sys.exit(0)
            try:
                client.fetch_oauth_access_token()
            except KeyError:
                sys.exit('Unauthorized')
            access_token = client.access_token
                   
        if not loaded:
            pickle.dump(client.access_token, open(ACCESS_TOKEN_PATH, 'w'))        
            
        return client
        
        
    def check_response(self, response, expected_status=httplib.OK):
        if response.status != expected_status:
            body = response.read()
            if body:
                body = "body: %s" % body
            sys.exit("""status: %s reason: "%s" %s""" % (response.status,
                                                response.reason, body))
        
        
    def parse_response(self, response, expected_status=httplib.OK):
        self.check_response(response, expected_status)
        
        if expected_status != httplib.NO_CONTENT:
            try:
                body = response.read()
                return loads(body)
            except ValueError:
                sys.exit('API error.  Please try again later. Response body: %s' % body)

        # TODO: and return None by default ?
        
        
    def get_version(self):

        return '0.0.1'


class MainCommand(object):
      
    def __init__(self):
           
        commands = {'instance': InstanceCommand,
                    'appliance': ApplianceCommand,
                    'provider': ProviderCommand,
                    'hardware': HardwareCommand,
                    'logout': LogoutCommand,}
        
        if len(sys.argv) >=2 and sys.argv[1] in commands.keys():
            commands[sys.argv[1]]()
            
        else:
            print self.usage()
        
    def usage(self):
        
        return '\nspotsh instance \n'\
               '       appliance \n'\
               '       provider\n'\
               '       hardware\n'\
               '       logout\n'\
        
        
class InstanceCommand(BaseCommand):
    
    command_options = (
        optparse.make_option('-l',
                             '--list',
                             action='store_true',
                             dest='_list',
                             help='List all instances'),
                    
        optparse.make_option('-k',
                             '--key',
                             default=None,
                             dest='_key',
                             help='Retrieve instance by key'),
                    
        optparse.make_option('-d',
                             '--delete',
                             default=None,
                             dest='_delete',
                             help='Delete instance by key'),
                    
        optparse.make_option('-c',
                             '--create',
                             action='store_true',
                             dest='_create',
                             help='Create a new instance using a provider, appliance, and hardware key'),
                             
        optparse.make_option('-p',
                             '--provider',
                             default=None,
                             dest='_provider',
                             help='Provider key used when creating an instance'),
                             
        optparse.make_option('-a',
                             '--appliance',
                             default=None,
                             dest='_appliance',
                             help='Appliance key used when creating an instance'),
                             
        optparse.make_option('-m',
                             '--hardware',
                             default=None,
                             dest='_hardware',
                             help='Hardware key used when creating an instance')
    )
    
    def __init__(self):
        
        super(InstanceCommand, self).__init__(self.command_options)
              
        if self.options._list:
            response = self.client.get('/api/v1/buyer/instances/list')
            instances = self.parse_response(response)
            for instance in instances:
                print model.Instance(instance)
            
        elif self.options._key:
            response = self.client.get('/api/v1/buyer/instance/%s' % self.options._key)
            instance = self.parse_response(response)
            print model.Instance(instance)

        elif self.options._delete:
            response = self.client.delete('/api/v1/buyer/instance/%s' % self.options._delete)
            self.parse_response(response, expected_status=httplib.NO_CONTENT)
            print 'Deleted\n'  
        
        elif self.options._create:
            response = self.client.post('/api/v1/buyer/instances/list',
                                        data = dict(provider=self.options._provider,
                                                    appliance=self.options._appliance,
                                                    hardware=self.options._hardware))
            instance = self.parse_response(response, expected_status=httplib.CREATED)
            print model.Instance(instance)
        
        else:
            self.parser.print_help()
            
    def usage(self):
        return 'spotsh instance \n'
   
   
class ApplianceCommand(BaseCommand):
    
    command_options = (
        optparse.make_option('-l',
                             '--list',
                             action='store_true',
                             dest='_list',
                             help='List all appliances'),
                    
        optparse.make_option('-k',
                             '--key',
                             default=None,
                             dest='_key',
                             help='Retrieve appliance by key'),
                    
        optparse.make_option('-d',
                             '--delete',
                             default=None,
                             dest='_delete',
                             help='Delete appliance by key'),
                    
        optparse.make_option('-b',
                             '--build',
                             default=None,
                             dest='_build',
                             help='Build a SpotCloud appliance from a raw disk'),
                             
        optparse.make_option('-n',
                             '--name',
                             default='New Appliance',
                             dest='_name',
                             help='Name used when building a new appliance'),
                             
        optparse.make_option('-u',
                             '--upload',
                             default=None,
                             dest='_upload',
                             help='Upload an XVM2 appliance')
    )
    
    def __init__(self):
        
        super(ApplianceCommand, self).__init__(self.command_options)
        
        if self.options._list:
            response = self.client.get('/api/v1/buyer/appliances/list')
            appliances = self.parse_response(response)
            for appliance in appliances:
                print model.Appliance(appliance)
                                   
        elif self.options._key:
            response = self.client.get('/api/v1/buyer/appliance/%s' % self.options._key)
            appliance = self.parse_response(response)
            print model.Appliance(appliance)
                                 
        elif self.options._delete:
            response = self.client.delete('/api/v1/buyer/appliance/%s' % self.options._delete)
            self.parse_response(response, expected_status=httplib.NO_CONTENT)
            print 'Deleted\n'  
                     
        elif self.options._build:
            if not self.options._build.endswith('.img'):
                sys.exit('Invalid image type - expecting .img')
            if not os.path.exists(self.options._build):
                sys.exit('Invalid image path')
            print 'Building...'
            # TODO: unused "disk" variable 
            disk = ExistingImageDisk(DISK_TYPE_HD, self.options._build)
            print build_package(self.options._name, self.options._build)
                                        
        elif self.options._upload:
            print upload_package(self.client, self.options._upload)['edit_url']
            
        else:
            self.parser.print_help()
                    
    def usage(self):
        
        return 'spotsh appliance \n'
        
        
class ProviderCommand(BaseCommand):
    
    command_options = (
        optparse.make_option('-l',
                             '--list',
                             action='store_true',
                             dest='_list',
                             help='List all providers'),
                    
        optparse.make_option('-k',
                             '--key',
                             default=None,
                             dest='_key',
                             help='Retrieve provider by key'),
    )
    
    def __init__(self):
        
        super(ProviderCommand, self).__init__(self.command_options)
        
        if self.options._list:
            response = self.client.get('/api/v1/buyer/providers/list')
            providers = self.parse_response(response)
            for provider in providers:
                print model.Provider(provider)
            
        elif self.options._key:
            response = self.client.get('/api/v1/buyer/provider/%s' % self.options._key)
            provider = self.parse_response(response)
            print model.Provider(provider)
            
        else:
            self.parser.print_help()
                    
    def usage(self):
        return 'spotsh provider \n'


class HardwareCommand(BaseCommand):
    
    command_options = (
        optparse.make_option('-p',
                             '--provider',
                             default=None,
                             dest='_provider',
                             help='List hardware for the specified provider'),
                             
        optparse.make_option('-l',
                             '--list',
                             action='store_true',
                             default=None,
                             dest='_list',
                             help='List hardware profiles'),
        
        optparse.make_option('-u',
                             '--update',
                             default=None,
                             dest='_hardware',
                             help='Update hardware profile'),

        optparse.make_option('-c',
                             '--cost',
                             default=None,
                             dest='_cost',
                             help='Hardware profile cost'),

        optparse.make_option('-m',
                             '--max_hours',
                             default=None,
                             dest='_max_hours',
                             help='Hardware profile max_hours'),
    )
    
    def __init__(self):
        
        super(HardwareCommand, self).__init__(self.command_options)
            
        # buyer part 

        if self.options._provider:
            response = self.client.get('/api/v1/buyer/provider/%s' % 
                                                    self.options._provider)
            provider = self.parse_response(response)
            for hardware in provider['hardware']:
                print model.Hardware(hardware)
                
        # provider part 
        # TODO: separate
                
        elif self.options._list:
            response = self.client.get('/api/v1/provider/hardware/list')
            hardwares = self.parse_response(response)
            for hardware in hardwares:
                print model.Hardware(hardware)
            
        elif self.options._hardware:
            if not (self.options._cost and self.options._max_hours):
                print "No data for update"
                self.parser.print_help()
                return                
            
            data = {'cost': self.options._cost,
                        'max_hours': self.options._max_hours}
                        
            response = self.client.put('/api/v1/provider/hardware/%s' %
                                       self.options._hardware, data = data)
            self.check_response(response)
            print "Success"
        
        else:
            self.parser.print_help()
                    
    def usage(self):
        return 'spotsh hardware \n'


class LogoutCommand(BaseCommand):
    
    def __init__(self):
        if os.path.exists(ACCESS_TOKEN_PATH):
            os.remove(ACCESS_TOKEN_PATH)
            print "Success"
        else:
            print "Not logged"
    
def main():
    
    MainCommand()
