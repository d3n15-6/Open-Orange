#!/bin/sh
echo "recursively removing .svn folders from"
pwd
rm -rf `find . -type d -name .svn`

echo "borrar .pyc"

rm -rf `find -name .pyc` 

echo "totalmente limpio"

