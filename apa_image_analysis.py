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

import copy
import errno
import os 
import re
import subprocess
import tempfile
import time
import zipfile
import os
import mysql_db_util
import subprocess
import base64
import zipfile  
import tarfile
import mysql_db_util
import shutil
import json
import apa_config

import apa_util
import traceback


OPTIONS = apa_util.OPTIONS
OPTIONS.verbose = True

class BuildInfo:
  pass

def analysis_apk(buildInfo,apk,apktype,base_dir):
  #print '-------'
  #print "Scanning ", apk

  is_zip_check_ok = 1
  if not apa_util.is_zip_check_ok(apk):
    print "ERROR: Apk zip format error!"
    is_zip_check_ok = 0

  related_apk_name = apk[len(base_dir):]
  package_name = apa_util.get_package_name(apk)
  #print "package ", package_name
  sign_md5,sign_sha1,sign_detail = apa_util.get_apk_sign(apk)
  #print "Sign MD5", sign_md5
  #print "Sign SHA1", sign_sha1
  version_code,version_name = apa_util.get_package_version(apk)
  #print "Version Code", version_code
  #print "Version Name",version_name
  apk_size = apa_util.get_file_size(apk)
  #print "Size", apk_size
  odex_f =  apa_util.get_odex_file(apk)
  if odex_f==None:
    apk_size_odex = 0
  else:
    apk_size_odex = apa_util.get_file_size(odex_f)
    #print "Odex size", apk_size_odex

  apk_debuggable = apa_util.is_apk_debuggable(apk)
  sha1 = apa_util.sha1sum(apk)
  md5 = apa_util.md5sum(apk)

  support_langs = apa_util.get_apk_support_langs(apk)

  target_sdk_version = apa_util.get_apk_targetsdk_version(apk)

  aapt_dump = apa_util.get_apk_aapt_dump(apk)

  def insertDB(conn,cur):
    sql_query = ''' 
INSERT INTO `apk_file_info`
(`apk_file`,
`package_name`,
`sign_md5`,
`sign_sha1`,
`sign_detail`,
`apk_type`,
`apa_release_image_id`,
`is_zip_check_ok`,
`apk_version_code`,
`apk_version_name`,
`apk_size`,
`apk_size_odex`,
`apk_debuggable`,
`apk_md5`,
`apk_sha1`,
`support_langs`,
`target_sdk_version`,
`aapt_dump`)
VALUES
(%s, %s, %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    '''
    cur.execute(sql_query, (related_apk_name,package_name,sign_md5,sign_sha1,sign_detail,apktype,buildInfo.buildid,is_zip_check_ok,version_code,version_name,apk_size,apk_size_odex,apk_debuggable,md5,sha1,support_langs,target_sdk_version,aapt_dump))

  mysql_db_util.dbwork(insertDB)  

def analysis_file_size(buildInfo,base_dir):
  sql_insert_extra_check = '''INSERT INTO apk_file_info  (apa_release_image_id, apk_file, apk_size)  VALUES (%s,%s,%s)'''
  system_path  = os.path.join(base_dir,'SYSTEM')  
  print system_path
  for root,dirs,files in os.walk(system_path):
      for filespath in files:
          full_path = os.path.join(root,filespath)
          #print "MBT: ", full_path
          if not os.path.isfile(full_path):
            continue
          abs_path = full_path[len(system_path):]
          size = apa_util.get_file_size(full_path)
          #print "MBT: ", abs_path, size
          def insertDB(conn,cur):
             cur.execute(sql_insert_extra_check, (buildInfo.buildid,abs_path, size))
          mysql_db_util.dbwork(insertDB)



def analysis_target_files_detail(buildInfo):

  print "\n\n\n\n"
  print "##########################################"
  print "Scanning ", buildInfo.path

  
  if buildInfo.path==None or not os.path.isfile(buildInfo.path):
    print "ERROR: Not  file "+buildInfo.path ;
    return

  def updateDB(conn,cur):
    sql_query = ''' UPDATE apa_release_images SET is_analysis_done=1 WHERE id=%s '''%(buildInfo.buildid)
    cur.execute(sql_query)
  
  mysql_db_util.dbwork(updateDB)

  def deleteOld(conn,cur):
    sql_query = ''' DELETE FROM apk_file_info   WHERE apa_release_image_id=%s '''%(buildInfo.buildid)
    cur.execute(sql_query)

  mysql_db_util.dbwork(deleteOld)


  target_files = buildInfo.path
   

  unzipped_target_files_dir = apa_util.unzip_zip(target_files)
  base_dir = unzipped_target_files_dir

  analysis_file_size(buildInfo,unzipped_target_files_dir)

  system_apk_list = apa_util.find_all_apk_file(os.path.join(unzipped_target_files_dir,'SYSTEM'))


  build_props = apa_util.read_java_prop_file(os.path.join(unzipped_target_files_dir,'SYSTEM','build.prop'))

  buildInfo.build_props = build_props

  system_used = apa_util.get_dir_size(os.path.join(unzipped_target_files_dir,'SYSTEM'));

  try:
    misc_dict = apa_util.read_java_prop_file(os.path.join(unzipped_target_files_dir,'META/misc_info.txt'))
    system_size = misc_dict['system_size']
  except Exception as e:
    print "read META/misc_info.txt error",e
    system_size =0

  print "system_size",system_size

  max_file_size_in_system = apa_util.find_max_file_size(os.path.join(unzipped_target_files_dir,'SYSTEM'))

  print "max_file_size_in_system", max_file_size_in_system

  def updateBuildSize(conn,cur):
    sql_query = ''' UPDATE apa_release_images 
    SET system_size=%s,max_file_size_in_system=%s
    WHERE id=%s '''
    cur.execute(sql_query,(system_size,max_file_size_in_system,buildInfo.buildid))
  
  mysql_db_util.dbwork(updateBuildSize)

  for x in system_apk_list:
    print "Scanning "+x
    analysis_apk(buildInfo,x, 'SYSTEM',base_dir)



def nalysis_target_files(target_file):
  props,prop_dic = apa_util.unzipBuildPropFromTargetFile(target_file);
  ota_version =  prop_dic['ro.build.version.incremental']
  try:
    fingerprint = prop_dic['ro.build.fingerprint']
  except:
    fingerprint = ""

  try:
    ota_model  = prop_dic['ro.product.ota.model']
  except:
    ota_model = prop_dic['ro.product.model']
    
  build_type = prop_dic['ro.build.type']
  build_date = prop_dic['ro.build.date']
  build_time_utc = prop_dic['ro.build.date.utc']

  def insertDB(conn,cur):
    n = cur.execute('''UPDATE apa_release_images SET path=%s  WHERE  fingerprint LIKE %s AND build_date_utc=%s''',(target_file,fingerprint,build_time_utc))
    if n<=0:
      cur.execute("""INSERT INTO apa_release_images (path, scan_date,ota_model,ota_version, build_type,fingerprint,build_date,full_build_prop,build_date_utc) VALUES (%s,now(),%s,%s,%s,%s,%s,%s,%s)""",
            (target_file,ota_model,ota_version,build_type,fingerprint,build_date,props,build_time_utc))
    else:
      print "WARNING:::File Path changed for %s %s to %s, just update the path!!!!"%(ota_model,ota_version, target_file)

  mysql_db_util.dbwork(insertDB)

  buildInfo = BuildInfo()
  buildInfo.path=target_file
  buildInfo.ota_version = ota_version
  buildInfo.ota_model = ota_model

  def db_find_id(conn,cur):
    sql_query = ''' SELECT id FROM apa_release_images WHERE path=%s ORDER BY build_date_utc DESC'''
    cur.execute(sql_query,(buildInfo.path,))
    buildInfo.buildid = int(cur.fetchone()[0])

  mysql_db_util.dbwork(db_find_id)


  analysis_target_files_detail(buildInfo)




def main():
  try:
    nalysis_target_files(sys.argv[1])
  except Exception as e:
    print "ERROR of analysis file ", sys.argv[1]
    traceback.print_exc()


if __name__ == '__main__':
  try:
    main()
  finally:
    apa_util.clean_temp_file()

