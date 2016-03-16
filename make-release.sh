#!/usr/bin/env bash


python setup.py sdist --formats=zip

FNAME=$(ls -1t dist | head -n 1 | tr -d '\n')
cp "dist/$FNAME" dist/dwre-tools-latest.zip

aws s3 sync dist/ s3://devops-pixelmedia-com/packages-374e8dc7/ --acl public-read
