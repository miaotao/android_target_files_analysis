#!/bin/bash
export LANG=en_US
export LANGUAGE=en_US
FILE=$1

cert_XSA=`jar tf $FILE | grep META-INF |grep SA`

jar xf $FILE $cert_XSA

#keytool -printcert -file $cert_XSA | grep MD5 > "$FILE.certMD5"
keytool -printcert -file $cert_XSA
