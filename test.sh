#!/bin/bash
python3 endpoint_infer_slippygeo.py -mod object-detection-2019-08-04-22-32-07-138 \
-c buildings \
-pa tiles/ \
-ro <role>  \
-t 0.6

