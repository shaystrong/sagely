#!/bin/bash
aws s3 cp s3://uw-geohack/sagely/rec_clean_demo/ rec/ --recursive --include '*rec' --exclude '*' 
aws s3 cp s3://uw-geohack/sagely/tiles/ tiles/ --recursive

