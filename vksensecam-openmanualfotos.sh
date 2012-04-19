#!/bin/sh

## searches for manual SenseCam-images and opens them one by one

for myfile in `ls -1 *_manual_*`; do open "${myfile}"; done

#end