import tensorflow as tf 
import numpy as np 
import cv2 

# To read the TF recorder, the Example should be read using Example.ParseFromString due to we write them with Example.SerializeToString method.
# 1. Reading the TFrecorder with tf.data.TFRecordDataset
# 2. parsing the TFrecorder from io.tf_record_iterator with Example.ParseFromString method  
# reference:
# https://zhuanlan.zhihu.com/p/40588218
# https://www.jianshu.com/p/78467f297ab5
# https://blog.gtwang.org/programming/tensorflow-read-write-tfrecords-data-format-tutorial/
# https://www.tensorflow.org/tutorials/load_data/tfrecord
# https://www.tensorflow.org/guide/data_performance#structure_of_an_input_pipeline

# set the basic parameters
# tfrecorder_name = 'pic.tfr' # this can be generated by using TFRecorder_create.py easily
tfrecorder_name = tf.data.Dataset.list_files(['*.tfr']) # or use the module in tutorial

# give the feature description
tfr_feature = { 
                'pic'     : tf.io.FixedLenSequenceFeature([], tf.int64, allow_missing=True) # if the content is dynamic, using FixedLenSequenceFeature with allow_missing is a good solution
               ,'size'    : tf.io.FixedLenFeature([2], tf.int64) # if the content is fixed, define the element number
               ,'channel' : tf.io.FixedLenFeature([], tf.int64) # 'channel' is the rank 1, so let [] be blank might be OK.
               ,'shape'   : tf.io.FixedLenFeature([3], tf.int64)
               ,'label'   : tf.io.FixedLenFeature([1], tf.int64)
              }

##### build the TFRecorder dataset object
reader = tf.data.TFRecordDataset(tfrecorder_name)
reader = reader.batch(2)
# reader = reader.prefetch(1)
print(reader)
print(dir(reader))
# exit()

##### create the dataset iterator
fetcher = reader.make_initializable_iterator()

##### comsuing the dataset
sess = tf.InteractiveSession()

# initialize the dataset
sess.run(fetcher.initializer)
# exit()

# fetch the dataset
example = sess.run(fetcher.get_next())
# exit()
# print(example)
# print(len(example))
# print(dir(example))
# exit()

## to fetching the dataset example, call basic method would be a way
# features = tf.train.Example.FromString(example[1]) # if the dataset have the batch n, the example will be a list haing n elements.
# print(features)
# print(dir(features))
# print(features.features)
# print(dir(features.features))
# print(features.features.feature)
# print(dir(features.features.feature))
# print(features.features.feature['size'])
# print(dir(features.features.feature['size']))
# print(features.features.feature['channel'].int64_list)
# print(dir(features.features.feature['channel'].int64_list))
# print(features.features.feature['channel'].int64_list.value)
# print(features.features.feature['size'].int64_list.value)
# exit()

# featch the dataset at ones
# keys = tfr_feature.keys()
pics, labels = [], []
for i in example:
    features = tf.train.Example.FromString(i)
    
    size   = features.features.feature['size'].int64_list.value
    channel= features.features.feature['channel'].int64_list.value
    shape  = features.features.feature['shape'].int64_list.value
    label  = features.features.feature['label'].int64_list.value
    pic    = np.array(features.features.feature['pic'].int64_list.value).reshape(shape)
    
    print(pic.shape)
    pics.append(pic)
    labels.append(label)

## try the tf.io.parse_single_example
# If your data have a "fixed" data, using FixedLenFeature, as mentioned in tutorial, would work,
# but since most data would not be the same, such as the difference size of picture, using
# 'FixedLenSequenceFeature' in feature descriptor would be suggested. Such as :
# tfr_feature = { 
#                 'pic'     : tf.io.FixedLenSequenceFeature([], tf.int64, allow_missing=True)
#                ,'size'    : tf.io.FixedLenSequenceFeature([2], tf.int64, allow_missing=True)
#                ,'channel' : tf.io.FixedLenSequenceFeature([], tf.int64, allow_missing=True)
#                ,'shape'   : tf.io.FixedLenSequenceFeature([3], tf.int64, allow_missing=True)
#                ,'label'   : tf.io.FixedLenSequenceFeature([], tf.int64, allow_missing=True)
#               }
# Remember to set "allow_missing=True" to allow the different size format

dataset = tf.data.TFRecordDataset(tfrecorder_name)

def _parse_img(example_proto):
    return tf.io.parse_single_example(example_proto, tfr_feature)

parsed_label = dataset.map(_parse_img)
parsed_label_iter = parsed_label.make_initializable_iterator()
parsed_label_go = parsed_label_iter.get_next()
recovered_pic = tf.reshape(parsed_label_go['pic'], parsed_label_go['shape'])
sess.run(parsed_label_iter.initializer)
print(sess.run(parsed_label_go))
recovered_pic = sess.run(recovered_pic)
print(recovered_pic)
print(np.shape(recovered_pic))

sess.close()