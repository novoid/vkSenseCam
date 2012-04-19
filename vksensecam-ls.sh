#!/bin/sh

## lists all SenseCam files which were either manually taken or renamed:

## *optional* parameter: a subfolder of current folder:
[ "${1}x" = x ] || cd "${1}"

ls -la *|egrep "(_manual_|_SenseCam_(light|IR|manual)_.........+\.)"

[ "${1}x" = x ] || cd ..

#end