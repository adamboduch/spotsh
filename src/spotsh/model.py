
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


from utils import to_str


class Instance(object):
    
    def __init__(self, instance):
        
        self.instance = instance
        
    def __repr__(self):
        
        return '\n'\
               'ID:     %s\n'\
               'Key:    %s\n'\
               'State:  %s\n'\
               'IP:     %s\n'\
               % (self.instance['id'],\
                  self.instance['key'],\
                  self.instance['state'],\
                  self.instance['ip'])        
                 
    def __str__(self):
        
        return self.__repr__()

class Appliance(object):
    
    def __init__(self, appliance):
        
        self.appliance = appliance
        
    def __repr__(self):
        
        return '\n'\
               'Name:   %s\n'\
               'Size:   %s\n'\
               'Key:    %s\n'\
               % (self.appliance['name'],\
                  self.appliance['size'],\
                  self.appliance['key'])        
                 
    def __str__(self):
        
        return self.__repr__()
        
                 
class Provider(object):
    
    def __init__(self, provider):

        self.provider = provider
        
    def __repr__(self):
        
        return to_str(
               '\n'\
               'ID:          %s\n'\
               'Continent:   %s\n'\
               'Country:     %s\n'\
               'City:        %s\n'\
               'Min Cost:    %s\n'\
               'Max Cost:    %s\n'\
               % (self.provider['id'],
                  self.provider['continent'],
                  self.provider['country'],
                  self.provider['city'],
                  self.provider['min_cost'],
                  self.provider['max_cost'])
        )
                 
    def __str__(self):
        return self.__repr__()

class Hardware(object):
    
    def __init__(self, hardware):
        
        self.hardware = hardware
        
    def __repr__(self):
        
        return '\n'\
               'Name:        %s\n'\
               'Cost:        %s\n'\
               'CPU:         %s\n'\
               'Memory:      %s\n'\
               'Max Hours:   %s\n'\
               'Key:         %s\n'\
               % (self.hardware['name'],
                  self.hardware['cost'],
                  self.hardware['cpu'],
                  self.hardware['memory'],
                  self.hardware['max_hours'],
                  self.hardware['key'])        
                 
    def __str__(self):
        
        return self.__repr__()
