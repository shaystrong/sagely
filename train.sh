#!/bin/bash
source /home/ubuntu/anaconda3/bin/activate mxnet_p36
pip install sagemaker
pip install shapely
pip install geopandas
pip install json
pip install numpy
python3 sagemaker_ssd.py --prefix transmission-ssd-test \
--sessname transpole-ss \
--nclass 12 \
--epochs 1 \
--mini_batch_size 4 \
--lr 0.001 \
--lr_scheduler_factor 0.1 \
--momentum 0.9 \
--weight_decay 0.0005 \
--overlap 0.5 \
--nms_thresh 0.45 \
--image_shape 256 \
--label_width 150 \
--n_train_samples 212 \
--network 'resnet-50' \
--optim 'optimizer' 

