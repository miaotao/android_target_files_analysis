#!/usr/bin/env python
#
# Copyright (C) 2008 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License. 



import sys

if sys.hexversion < 0x02040000:
  print >> sys.stderr, "Python 2.4 or newer is required."
  sys.exit(1)

 
import hashlib       #Python2.5 or later version    

    
import sys    
import urllib   
import os.path  
import copy
import errno
import os 
import re
import subprocess
import tempfile
import time
import zipfile
import os
import subprocess
import base64
import zipfile  
import tarfile
import shutil
import common
import apa_config
import email  
import mimetypes  
from email.MIMEMultipart import MIMEMultipart  
from email.MIMEText import MIMEText  
from email.MIMEImage import MIMEImage  
import smtplib  
import commands
import csv
import subprocess

OPTIONS = common.OPTIONS
OPTIONS.verbose = True
OPTIONS.auto_dir = []
OPTIONS.temdirorfile = []



def find_all_apk_file(dir):
  file_list = []
  for root,dirs,files in os.walk(dir):
    for x in files:
      if x[-4:].lower() == '.apk':
        file_list.append(os.path.join(root,x))
  return file_list

def find_max_file_size(dir):
  max_size = 0
  for root,dirs,files in os.walk(dir):
    for x in files:
      f = os.path.join(root,x)
      if os.path.isfile(f):
        s = os.path.getsize(f)
        if s>max_size:
          max_size = s
  return max_size

def parse_zip(f):
    zfile = zipfile.ZipFile(f,'r',allowZip64=True)  
    for filename in zfile.namelist():
        print filename

def parse_gz(f):
  zfile = tarfile.open(f,"r:gz")
  for filename in zfile.getnames():
        print filename


def clean_temp_file():
  for i in OPTIONS.temdirorfile:
    try:
      if os.path.isdir(i):
        shutil.rmtree(i)
      else:
        os.remove(i)
    except Exception as err:
      print err
  OPTIONS.temdirorfile = []

def unzip_tar_gz(file):
  t = tempfile.mkdtemp()
  OPTIONS.temdirorfile.append(t)
  try:
    cmd = '''tar zxvf "%s" -C "%s"'''%(file,t)
    #print cmd
    p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=None)
    p.stdout.read()
    return  t
  except Exception as e:
    print "unzip_tar_gz", e

def unzip_zip(file):
  t = tempfile.mkdtemp()
  OPTIONS.temdirorfile.append(t)
  try:
    cmd = '''unzip "%s" -d "%s"'''%(file,t)
    #print cmd
    p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=None)
    p.stdout.read()
    return  t
  except Exception as e:
    print "unzip_zip", e

def unzip_7z(file):
  t = tempfile.mkdtemp()
  OPTIONS.temdirorfile.append(t)
  try:
    cmd = '''7z x "%s" -o"%s" '''%(file,t)
    print cmd
    p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=None)
    p.stdout.read()
    return  t
  except Exception, e:
    print e

def execute_cmd(cmd):
  try:
      p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=None)
      return p.stdout.read()
  except Exception, e:
    pass
  


def parsePropStrToDict(propStr):
  prop_dic = {}
  for line in propStr.split('\n'):
    line = line.strip()
    if line.startswith('#'):
        continue
    tmp = line.split("=",1)
    if len(tmp)<2:
        continue
    prop_dic[tmp[0]] = tmp[1]

  return prop_dic

def unzipBuildPropFromTargetFile(f):
  
  propFileList = ['SYSTEM/build.prop', 'BOOT/RAMDISK/default.prop']
  propStr = ""

  z = zipfile.ZipFile(f,'r',allowZip64=True)
  for propFile in propFileList:
    if propFile in z.namelist():
      propStr = propStr+"\n\n####### %s\n\n"%(propFile) + z.read(propFile)
  z.close()
  prop_dic = parsePropStrToDict(propStr)

  #print prop_dic
  return propStr,prop_dic


def read_java_prop_file(f):
  propStr = open(f).read()
  prop_dic = {}
  for line in propStr.split('\n'):
    line = line.strip()
    if line.startswith('#'):
        continue
    tmp = line.split("=",1)
    if len(tmp)<2:
        continue
    prop_dic[tmp[0]] = tmp[1]
  return prop_dic



def unzip_target_files_based_on_type(f):
  t_dir = None
  try:
    if is_ota_zip(f):
      t_dir = unzip_zip(f)
    if is_ota_gz(f):
      t_dir = unzip_tar_gz(f)
  except Exception, e:
    print e

  return t_dir

def md5sum(f):
  fobj = open(f,'rb')  
  m = hashlib.md5()   
  while True:    
    d = fobj.read()    
    if not d:    
      break    
    m.update(d)    
    del(d)    
  return m.hexdigest()  


def sha1sum(f):
  fobj = open(f,'rb')  
  m = hashlib.sha1()
  while True:    
    d = fobj.read()    
    if not d:    
      break    
    m.update(d)    
    del(d)    
  return m.hexdigest()  



def get_package_name(apk):
    packageName = "NA"
    try:
        import subprocess
        command = '''%s dump badging "%s" '''%(apa_config.aapt_tool_path, apk)
        p = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=None)
        s = p.stdout.readline()
        #print s.split("'")
        packageName = s.split("'")[1]
    except Exception as e:
        print "WARNING, get_package_name,", e
    return packageName

def get_package_version(apk):
    version_code = "NA"
    version_name = "NA"
    try:
        command = '''%s dump badging "%s" '''%(apa_config.aapt_tool_path, apk)
        p = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=None)
        s = p.stdout.readline()
        #print s.split("'")
        array = s.split("'")
        version_code = array[3]
        version_name = array[5]
    except Exception as e:
        print "WARNING, get_package_version,", e
    return version_code,version_name

def is_apk_debuggable(apk):
  try:
        command = '''%s dump badging "%s" '''%(apa_config.aapt_tool_path, apk)
        p = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=None)
        s = p.stdout.read()
        if 'application-debuggable' in s:
              return True
        return False
  except Exception as e:
    print "is_apk_debugable",e
    return False

def get_apk_support_langs(apk):
  try:
        command = '''%s dump badging "%s" '''%(apa_config.aapt_tool_path, apk)
        p = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=None)
        for line in p.stdout.readlines():
              print line
              if line.startswith('locales:'):
                return line[9:].strip()
        return ""
  except Exception as e:
    print "get_apk_support_langs",e
    return ""

def get_apk_targetsdk_version(apk):
  try:
        command = '''%s dump badging "%s" '''%(apa_config.aapt_tool_path, apk)
        p = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=None)
        for line in p.stdout.readlines():
              print line
              if line.startswith('targetSdkVersion:'):
                return line.split("'")[1]
        return ""
  except Exception as e:
    print "[ERROR]get_apk_targetsdk_version",e
    return ""

def get_apk_aapt_dump(apk):
  try:
        command = '''%s dump badging "%s" '''%(apa_config.aapt_tool_path, apk)
        return commands.getoutput(command)
  except Exception as e:
    print "[ERROR]get apk sdk version error",e
    return 0


def is_zip_check_ok(apk):
    try:
        import subprocess
        command = '''7z t "%s" '''%(apk)
        p = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=None)
        s = p.stdout.read()
        if  s.find(r'Everything is Ok')>=0:
          return True

    except Exception as e:
        print "WARNING, is_zip_file_ok,", e
    return False  


def get_apk_sign(apk):

    signMD5 = "NA"
    signDetail = "NA"
    signSha1 = "NA"
    try:
        command = '''%s "%s" '''%(apa_config.get_sign_key_tool_path,apk)
        p = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=None)
        s = p.stdout.read()
        #print s.split("'")
        signDetail = s
        if signDetail != "NA":
          m = re.search('(?<=MD5:)\s*([0-9A-Fa-f]{2}:){15}[0-9A-Fa-f]{2}',signDetail)
          signMD5 = m.group(0).strip()
          m = re.search('(?<=SHA1:)\s*([0-9A-Fa-f]{2}:){19}[0-9A-Fa-f]{2}',signDetail)
          signSha1 = m.group(0).strip()
    except Exception as e:
        print "WARNING, get_apk_sign,",e

    return signMD5,signSha1,signDetail



def get_odex_file(f):
  p = f[:-4]+'.odex'
  if os.path.isfile(p):
    return p
  #For Android L, odex is under arm or arm64
  path,fname = os.path.split(p)
  arm_odex = os.path.join(path,'arm',fname)
  #print arm_odex
  arm64_odex = os.path.join(path,'arm64',fname)
  #print arm64_odex
  if os.path.isfile(arm_odex):
    return arm_odex
  if os.path.isfile(arm64_odex):
    return arm64_odex
  return None


def get_file_size(f):
  try:
    return os.stat(f).st_size
  except Exception, e:
    print "get_file_size",e
    return 0

def get_dir_size(path):
  try:
    return int(commands.getoutput('du -sb "%s" '%(path)).split()[0])
  except Exception as e:
    print "get_dir_size",e
    return 0




def get_xml_without_comments(s):
  return_str = "";
  i=0
  in_comments = False
  while i<len(s)-4:
    if s[i:i+4] == '<!--':
      in_comments = True
    if in_comments and s[i:i+3]=='-->':
      in_comments = False
      i+=3
    if not in_comments:
      return_str += s[i]
    i+=1
  return return_str+s[i:]


def find_file_contains(f, subs, suffix = None):
      if not os.path.isfile(f):
        print "[WARNING] not a file ", f
        return [];
      m = open(f)
      data = m.read()
      if suffix != None and suffix=='.xml':
        data = get_xml_without_comments(data)
      if re.search(subs, data) != None:
        return [f,]
      else:
        return []

#Find any file contains subs in the dir
def find_files_in_dir_contains(dir, subs, suffix = None):
  result_list = []
  for base, pathes, files  in os.walk(dir):
    for f in files:
      full_path = os.path.join(base, f)
      if suffix != None and not full_path.endswith(suffix):
        continue
      if  len(find_file_contains(full_path, subs, suffix))>0 :
        result_list.append(full_path)
  return result_list




def getOtaFullPatchByTargetFiles(f):
  dir_path = f
  for loop in range(1,3):
    dir_path = os.path.split(dir_path)[0]
    files = scan_dir_for_otafull(dir_path)
    if len(files)==1:
      return files[0]
    elif len(files)>1:
      return ""