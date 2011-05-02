
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
import re
import string
import tempfile
import tarfile
import subprocess
import shutil
import sys
from cStringIO import StringIO
from subprocess import call
from gzip import GzipFile

try:
    from hashlib import md5
except ImportError:
    from md5 import new as md5

try:
    import xml.etree.ElementTree as ET # in python >=2.5
except ImportError:
    try:
        import cElementTree as ET # effbot's C module
    except ImportError:
        try:
            import elementtree.ElementTree as ET # effbot's pure Python module
        except ImportError:
            try:
                import lxml.etree as ET # ElementTree API using libxml2
            except ImportError:
                import warnings
                warnings.warn("could not import ElementTree "
                              "(http://effbot.org/zone/element-index.htm)")
                raise
try:
    import uuid
    def gen_uuid():
        return str(uuid.uuid1())
except ImportError:
    import subprocess
    def gen_uuid():
        p = subprocess.Popen('uuidgen', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        data, _ = p.communicate()        
        if p.wait() != 0:
            raise ImportError('Please install python uuid module (http://pypi.python.org/pypi/uuid/) or uuidgen utility')
        return data.strip()

DISK_TYPE_HD = 'hd'
DISK_TYPE_CDROM = 'cdrom'

MB = 1024*1024

class BaseDisk(object):
    type = None
    image_type = None
    internal_name = None
    def __str__(self):
        return str(self.__unicode__())
    
class ExistingImageDisk(BaseDisk):
    def __init__(self, type, path):
        self.type = type
        self.path = path
        
        self.size = os.path.getsize(path)
        self.image_type = os.path.splitext(path)[1][1:]
        
        self.gzipped_path = None
        
    def get_gzipped_path(self):
        if not self.gzipped_path:
            self.gzipped_path = gzip_file(self.path)
        return self.gzipped_path        
    
    def get_hash(self):
        return calculate_hash(self.path)
    
    def get_size(self):
        return self.size
    
    def cleanup(self):
        if self.gzipped_path:
            os.unlink(self.gzipped_path)
            self.gzipped_path = None

    def __unicode__(self):
        return '%s: %s (%d MB)' % (self.type, self.path, self.size / MB)
    
def build_package(name, path):
    
    cfg = PackageConfig(name,
                        [ExistingImageDisk(DISK_TYPE_HD, path)],
                        DISK_TYPE_HD,
                        True,
                        True,
                        True,
                        True,
                        True)
    
    for idx, disk in enumerate(cfg.disks):
        disk.internal_name = '%s%d.%s.gz' % (disk.type, idx, disk.image_type)

    tf_name = '%s.xvm2' % cfg.name
    tf = tarfile.open(tf_name, 'w')
    
    try:    
    
        try:

            m1 = StringIO(build_manifest1(cfg))
            m1_tf = tarfile.TarInfo(name='description.xml')
            m1_tf.size = len(m1.getvalue())
            tf.addfile(m1_tf, fileobj=m1)
            
            m2 = StringIO(build_manifest2(cfg))
            m2_tf = tarfile.TarInfo(name='manifest.txt')
            m2_tf.size = len(m2.getvalue())
            tf.addfile(m2_tf, fileobj=m2)
                
            for disk in cfg.disks:
                tf.add(disk.get_gzipped_path(), disk.internal_name)

        finally:
            
            tf.close()      

    except KeyboardInterrupt, AttributeError:
        os.unlink(tf_name)
                
    except:
        os.unlink(tf_name)
        raise
        
    for disk in cfg.disks:
        try:
            disk.cleanup()
        except Exception, e:
            sys.exit(1, 'Failed to cleanup disk "%s"' % disk)     
                
    return tf_name


def build_manifest1(cfg):
    m = ET.Element('domain')
    ET.SubElement(m, 'name').text=cfg.name
    ET.SubElement(m, 'uuid').text=gen_uuid()
    
    os = ET.SubElement(m, 'os')
    ET.SubElement(os, 'type').text='hvm'
    ET.SubElement(os, 'boot', dev=cfg.boot_from)
    
    features = ET.SubElement(m, 'features')
    if cfg.use_pae:
        ET.SubElement(features, 'pae')
    if cfg.use_acpi:
        ET.SubElement(features, 'acpi')
    if cfg.use_apic:
        ET.SubElement(features, 'apic')
    
    devices = ET.SubElement(m, 'devices')
    
    for idx, d in enumerate(cfg.disks):        
        device = 'disk'
        if d.type == DISK_TYPE_CDROM:
            device = 'cdrom'
        disk = ET.SubElement(devices, 'disk', device=device, type='file')
        devname = 'hd%s' % string.ascii_lowercase[idx]
        ET.SubElement(disk, 'source', file=d.internal_name)
        ET.SubElement(disk, 'target', dev=devname)
    
    return ET.tostring(m)

def build_manifest2(cfg):
    m = ''
    for disk in cfg.disks:
        name = disk.internal_name
        if name.endswith('.gz'):
            name = name[:-3]
        m += '%s %d %s\n' % (name, disk.get_size(), disk.get_hash())
    return m

def gzip_file_(file_path):
    "original gzip_file()"
    gz_path = tempfile.mkstemp(suffix='.gz')[1]
    try:
        proc = subprocess.Popen("nice gzip --fast -c %s > %s " % (file_path, gz_path),
                                shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _, stderr = proc.communicate()
        if proc.wait() != 0:
            raise Exception(stderr.strip())
        return gz_path
    except KeyboardInterrupt:
        os.unlink(gz_path)
        # TODO: and return None without exception ?
    except:
        os.unlink(gz_path)
        raise

def gzip_file(file_path):
    """pro: pure python, display progress
    cons: 20% slower compare to gzip -1"""
    bs = 10 * MB
    f = open(file_path)
    gz_path = tempfile.mkstemp(suffix='.gz')[1]
    gf = GzipFile(gz_path, "wb", 1)

    try:
        data = f.read(bs)
        chunk = 1
        chunks = int(round(os.path.getsize(file_path) / bs + 0.5))
        while len(data):
            print '\rCompressing: %2d%%...' % ((chunk*100)/chunks),
            sys.stdout.flush() 
            gf.write(data)
            data = f.read(bs)
            chunk += 1
        gf.close()
    except:
        os.unlink(gz_path)
        raise    
        
    return gz_path

def create_empty_disk(size):
    gz_path = tempfile.mkstemp(suffix='.gz')[1]
    bs=1024*1024
    count=size/bs
    call("dd if=/dev/zero bs=%d count=%d 2> /dev/null | nice gzip --fast > %s" % (bs, count, gz_path), shell=True)
    return gz_path

def calculate_empty_hash(size):
    
    """Calculate and return the hash for an empty disk, using the
    provided size."""
    
    empty_hash = md5()
    block_size = MB
    zero       = '\0' * block_size
    
    while size > block_size:
        
        empty_hash.update(zero)
        size -= block_size
        
    empty_hash.update(zero[:size])
    
    return empty_hash.hexdigest()

def calculate_hash(file_path):
    
    """Calculate and return the hash for the provided file path."""
    
    file_hash  = md5()
    block_size = MB
    
    with open(file_path, 'rb') as ifile:

        for buf in ifile.read(block_size):
            
            file_hash.update(buf)
            
    return file_hash.hexdigest()
            
class PackageConfig(object):
    def __init__(self, name, disks, boot_from, use_pae, use_acpi, use_apic, use_virtio, use_virtblk):
        self.name = name
        self.disks = disks
        self.boot_from = boot_from
        self.use_pae = use_pae
        self.use_acpi = use_acpi
        self.use_apic = use_apic
        self.use_virtio = use_virtio
        self.use_virtblk = use_virtblk
        
    def __repr__(self):
        return 'PackageConfig(%r, %r, %r, %r, %r, %r, %r, %r)' % (self.name, self.disks, self.boot_from, self.use_pae, self.use_acpi, self.use_apic, self.use_virtio, self.use_virtblk)

