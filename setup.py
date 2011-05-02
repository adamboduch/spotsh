
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

from setuptools import setup, find_packages

setup(name="spotsh",
      version='0.0.2',
      # python 2.6+ already has json module
      install_requires = ['simplejson', 'oauth'],
      zip_safe=False,
      packages = find_packages('src'),
      package_dir = {'':'src'},
      author = "Enomaly",
      author_email = "adam@enomaly.com",
      license = "GPL V3",
      url = "http://www.enomaly.com/",
      entry_points = {'console_scripts': ['spotsh = spotsh:main']})
