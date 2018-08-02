import numpy as np
import keras
from keras.callbacks import LearningRateScheduler
import pickle
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from models import model, modelb
import cv2


# normalize - samplewise for CNN and featurewis for fullyconnected
def normalize(X_train, X_test):
    mean = np.mean(X_train, axis=(0, 1, 2, 3))
    std = np.std(X_train, axis=(0, 1, 2, 3))
    X_train = (X_train - mean) / (std + 1e-7)
    X_test = (X_test - mean) / (std + 1e-7)
    return X_train, X_test


def data_generator(X, batch_size=128):
    while True:
        random_perm = np.array([np.random.permutation(2 ** tiles_per_dim) for _ in range(batch_size)])
        idx = np.random.choice(range(len(X)), batch_size, replace=False)

        Xd = {}
        Yd = {}

        for i in idx:
            for j in range(2 ** tiles_per_dim):
                if j < 10:
                    img = cv2.imread("project/shraded_samesize" + str(tiles_per_dim) + "/" + X[i] +'0'+str(j)+'jpg', cv2.IMREAD_GRAYSCALE)
                else:
                    img = cv2.imread("project/shraded_samesize" + str(tiles_per_dim) + "/" + X[i] +str(j)+'jpg', cv2.IMREAD_GRAYSCALE)
                if X[i] not in Xd:
                    Xd.update({X[i]: []})
                    Yd.update({X[i]: []})
                Xd[X[i]].append(np.array(img))
                Yd[X[i]].append(j)

        X = []
        Y = []

        for pic in Xd:

            X_test = np.array(Xd[pic])
            y_tmp = np.array(Yd[pic]).astype(int)
            X_new = [0 for _ in range(2 ** tiles_per_dim)]
            for ind, y in enumerate(y_tmp):
                X_new[y] = X_test[ind]

            X.append(np.array(X_new))
            Y.append([i for i in range(2 ** tiles_per_dim)])



        x_samples = X
        x_samples_rnd_perm = np.array([x_samples[i][random_perm[i]] for i in range(batch_size)])
        x_samples = x_samples_rnd_perm[:, :, :, :, np.newaxis]
        x = [x_samples[:, i] for i in range(x_samples.shape[1])]
        y = Y[idx]
        y_rnd_perm = np.array([y[i][random_perm[i]] for i in range(batch_size)])
        y = keras.utils.to_categorical(y_rnd_perm, 2 ** tiles_per_dim)
        yield x, y


# drop decay
def schedule(epoch):
    return initial_lr * (0.1 ** (epoch // 50))


tiles_per_dim = 4

with open('files_names.pickle', 'rb') as handle:
    X = pickle.load(handle)

test_idxs = np.random.randint(0, len(X), int(0.1*len(X)))
X_test = X[test_idxs]
X_train = [x for i,x in enumerate(X) if i not in test_idxs]
train_size = len(X_train)
test_size = len(X_test)

image_shape = (223,223, 1)

X = None
Y = None

## TODO: when finished, train with all dataset!!

sinkhorn_on = False
weight_decay = 0.01
dropout = 0.3
initial_lr = 0.005
epochs = 30
batch_size = 64

model = modelb(tiles_per_dim, image_shape, sinkhorn_on, weight_decay, dropout)

model.compile(loss='categorical_crossentropy',
              optimizer=keras.optimizers.SGD(lr=initial_lr, momentum=0.9, nesterov=True),
              metrics=['accuracy'])
print(model.summary())

datagen = data_generator(X_train, batch_size=batch_size)
vdatagen = data_generator(X_test, batch_size=batch_size)

history = model.fit_generator(generator=datagen,
                              steps_per_epoch=train_size // batch_size,
                              validation_data=vdatagen,
                              validation_steps=test_size // batch_size,
                              epochs=epochs,
                              callbacks=[LearningRateScheduler(schedule)])

# summarize history for accuracy
plt.plot(history.history['acc'])
plt.plot(history.history['val_acc'])
plt.title('model accuracy')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.show()
# summarize history for loss
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('model loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.show()

model.save('test' + str(tiles_per_dim) + '.h5')