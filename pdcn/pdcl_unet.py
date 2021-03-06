# Requires Keras 2.1.1

###################################################
import tensorflow as tf
from keras import backend as K
sess = tf.Session()
K.set_session(sess)
###################################################

from keras.models import Model
from keras.layers import Input, Concatenate, Conv2D, MaxPooling2D, UpSampling2D, Reshape, core, Dropout, Add, Lambda
from keras.optimizers import Adam
from pixel_dcn import pixel_dcl

# Baseline U-Net incorporated with PixelDCL
def pdcl_unet(patch_height, patch_width, n_ch):
    inputs = Input(shape=(patch_height, patch_width, n_ch))
    conv1 = Conv2D(32, (3, 3), activation='relu', padding='same',data_format='channels_last')(inputs)
    conv1 = Dropout(0.2)(conv1)
    conv1 = Conv2D(32, (3, 3), activation='relu', padding='same',data_format='channels_last')(conv1)
    pool1 = MaxPooling2D((2, 2), data_format='channels_last')(conv1)
    
    conv2 = Conv2D(64, (3, 3), activation='relu', padding='same',data_format='channels_last')(pool1)
    conv2 = Dropout(0.2)(conv2)
    conv2 = Conv2D(64, (3, 3), activation='relu', padding='same',data_format='channels_last')(conv2)
    pool2 = MaxPooling2D((2, 2), data_format='channels_last')(conv2)
    
    conv3 = Conv2D(128, (3, 3), activation='relu', padding='same',data_format='channels_last')(pool2)
    conv3 = Dropout(0.2)(conv3)
    conv3 = Conv2D(128, (3, 3), activation='relu', padding='same',data_format='channels_last')(conv3)

    up1 = UpSampling2D(size=(2, 2), data_format='channels_last')(conv3)
    up1 = Concatenate(axis=3)([conv2, up1])
    
    conv4 = Conv2D(64, (3, 3), activation='relu', padding='same',data_format='channels_last')(up1)
    conv4 = Dropout(0.2)(conv4)
    conv4 = Conv2D(64, (3, 3), activation='relu', padding='same',data_format='channels_last')(conv4)
    
    up2 = Lambda(lambda x: pixel_dcl(inputs=x, out_num=64, kernel_size=(2, 2), scope='conv_pdcl', d_format='NHWC'))(conv4)
    up2 = Concatenate(axis=3)([conv1, up2])
    
    conv5 = Conv2D(32, (3, 3), activation='relu', padding='same',data_format='channels_last')(up2)
    conv5 = Dropout(0.2)(conv5)
    conv5 = Conv2D(32, (3, 3), activation='relu', padding='same',data_format='channels_last')(conv5)
    
    conv6 = Conv2D(2, (1, 1), activation='relu',padding='same',data_format='channels_last')(conv5)
    conv6 = core.Reshape((patch_height*patch_width, 2))(conv6)
    
    conv7 = core.Activation('softmax')(conv6)

    model = Model(inputs=inputs, outputs=conv7)
    print(model.summary())

    opt = Adam(lr=0.01, beta_1=0.9, beta_2=0.999, epsilon=0.1, decay=1e-5)  # amsgrad=True doesn't exist in Keras 2.1.1
    sess.run(tf.global_variables_initializer())
    model.compile(optimizer=opt, loss='categorical_crossentropy', metrics=['accuracy'])

    return model