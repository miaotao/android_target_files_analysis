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

import copy
import errno
import getopt
import getpass
import imp
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile

try:
  from hashlib import sha1 as sha1
except ImportError:
  from sha import sha as sha1

# missing in Python 2.4 and before
if not hasattr(os, "SEEK_SET"):
  os.SEEK_SET = 0

class Options(object): pass
OPTIONS = Options()
OPTIONS.search_path = "out/host/linux-x86"
OPTIONS.verbose = False
OPTIONS.tempfiles = []
OPTIONS.device_specific = None
OPTIONS.extras = {}
OPTIONS.info_dict = None

