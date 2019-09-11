#!/bin/bash
aws s3 cp s3://uw-geohack/sagely/rec_clean_demo/ rec/ --recursive --include '*rec' --exclude '*'  --no-sign-request
aws s3 cp s3://uw-geohack/sagely/tiles/ tiles/ --recursive --no-sign-request
aws s3 cp s3://uw-geohack/sagely/nzwani_dg_wv3_05032019_104001004A465900.mbtiles . --no-sign-request
aws s3 cp s3://uw-geohack/sagely/VOC1900/ VOC1900/ --recursive --no-sign-request
