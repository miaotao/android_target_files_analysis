#!/usr/bin/env python
#
# Copyright (C) 2008 The Android Open Source Project

import sys
import apa_config

if sys.hexversion < 0x02040000:
  print >> sys.stderr, "Python 2.4 or newer is required."
  sys.exit(1)

import MySQLdb

def dbwork(caller):
  conn = None
  cur = None
  try:
    conn=MySQLdb.connect(host=apa_config.mysql_server,user=apa_config.mysql_user,passwd=apa_config.mysql_password,port=apa_config.mysql_port)
    cur=conn.cursor()   
    conn.select_db(apa_config.db_name)
    caller(conn,cur)
    conn.commit()
  except MySQLdb.Error,e:
    print "Mysql Error %d: %s" % (e.args[0], e.args[1])
  
  if cur:
    cur.close()
  if conn:
    conn.close()
