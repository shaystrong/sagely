#!/bin/bash
python3 endpoint_infer_slippygeo.py -mod <my_endpoint> \
-c buildings \
-pa tiles/ \
-ro <role>  \
-access_key <access key>  \
-secret <secret key>  \
-t 0.6

