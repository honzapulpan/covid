#!/bin/bash

now=$(date +'%Y-%m-%d') 
git add .
git commit -a -m "Update ${now}"
git push origin master


