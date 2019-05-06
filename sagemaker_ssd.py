import sagemaker
from sagemaker import get_execution_role
from sagemaker.amazon.amazon_estimator import get_image_uri

import argparse
  

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--prefix', dest='prefix')
parser.add_argument('-s', '--sessname', dest='sessname')
parser.add_argument('-n', '--nclass', dest='nclass')
parser.add_argument('-e', '--epochs', dest='epochs')
parser.add_argument('-m', '--mini_batch_size', dest='mini_batch_size')
parser.add_argument('-l', '--lr', dest='lr')
parser.add_argument('-lsr', '--lr_scheduler_factor', dest='lr_scheduler_factor')
parser.add_argument('-mom', '--momentum', dest='epocmomentumhs')
parser.add_argument('-wd', '--weight_decay', dest='weight_decay')
parser.add_argument('-o', '--overlap', dest='overlap')
parser.add_argument('-mom', '--momentum', dest='epocmomentumhs')
parser.add_argument('-wd', '--weight_decay', dest='weight_decay')
parser.add_argument('-nt', '--nms_thresh', dest='nms_thresh')
parser.add_argument('-ims', '--image_shape', dest='image_shape')
parser.add_argument('-lw', '--label_width', dest='label_width')
parser.add_argument('-nts', '--n_train_samples', dest='n_train_samples')
parser.add_argument('-net', '--network', dest='network')
parser.add_argument('-op', '--optim', dest='optim')
parser.add_argument('-ro', '--role', dest='role')
args = parser.parse_args()


role = args.role
sess = sagemaker.Session()
bucket = sess.default_bucket()
prefix = args.prefix 
sessname=args.sessname 
nclass = args.nclass 


training_image = get_image_uri(sess.boto_region_name, sessname, repo_version="latest")
print (training_image)

# Upload the RecordIO files to train and validation channels
train_channel = prefix + '/train'
validation_channel = prefix + '/validation'

sess.upload_data(path='train.rec', bucket=bucket, key_prefix=train_channel)
sess.upload_data(path='val.rec', bucket=bucket, key_prefix=validation_channel)

s3_train_data = 's3://{}/{}'.format(bucket, train_channel)
s3_validation_data = 's3://{}/{}'.format(bucket, validation_channel)

s3_output_location = 's3://{}/{}/output'.format(bucket, prefix)
s3_output_location


od_model = sagemaker.estimator.Estimator(training_image,
                                         role, 
                                         train_instance_count=1, 
                                         train_instance_type='ml.p3.2xlarge',
                                         train_volume_size = 50,
                                         train_max_run = 360000,
                                         input_mode= 'File',
                                         output_path=s3_output_location,
                                         sagemaker_session=sess)
                                         
od_model.set_hyperparameters(base_network=args.network,
                             use_pretrained_model=1,
                             num_classes=nclass,
                             mini_batch_size=args.mini_batch_size,
                             epochs=args.epochs,
                             learning_rate=args.lr,
                             lr_scheduler_step='3,6',
                             lr_scheduler_factor=args.lr_scheduler_factor,
                             optimizer=args.optim,
                             momentum=args.momentum,
                             weight_decay=args.weight_decay,
                             overlap_threshold=args.overlap,
                             nms_threshold=args.nms,
                             image_shape=args.image_shape,   
                             label_width=args.label_width,		
                             num_training_samples=args.n_train_samples)

train_data = sagemaker.session.s3_input(s3_train_data, distribution='FullyReplicated', 
                        content_type='application/x-recordio', s3_data_type='S3Prefix')
validation_data = sagemaker.session.s3_input(s3_validation_data, distribution='FullyReplicated', 
                             content_type='application/x-recordio', s3_data_type='S3Prefix')
data_channels = {'train': train_data, 'validation': validation_data}
od_model.fit(inputs=data_channels, logs=True)    

#object_detector = od_model.deploy(initial_instance_count = 1,instance_type = 'ml.m4.xlarge')           #endpoint creation                          
