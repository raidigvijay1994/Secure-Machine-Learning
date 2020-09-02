# -*- coding: utf-8 -*-
"""securemachinelearning.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1gZaYSCNeK1mr9LgGZv9_xNFYkt_W0ImI
"""

# Commented out IPython magic to ensure Python compatibility.
# %config IPCompleter.greedy=True
import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt
import seaborn as sns

from google.colab import files
uploaded = files.upload()

import io
raw_data = pd.read_csv(io.BytesIO(uploaded['creditcard.csv']))

shuffled_data = raw_data.sample(frac=1,random_state=4)

# Put all the fraud class in a separate dataset.
fraud_data = shuffled_data.loc[shuffled_data['Class'] == 1]

#Randomly select 866 observations from the non-fraud (majority class)
non_fraud_data = shuffled_data.loc[shuffled_data['Class'] == 0].sample(n=492,random_state=42)

# Concatenate both dataframes again
data = pd.concat([fraud_data, non_fraud_data])

plt.figure(figsize=(8, 8))
sns.countplot('Class', data=data)
plt.title('Balanced Classes')
plt.show()

X = data.iloc[:, 1:29].values
y = data.iloc[:, -1].values

# Splitting the dataset into the Training set and Test set
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.20, random_state = 50)

def model_report(y_act, y_pred):
    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, confusion_matrix, cohen_kappa_score, roc_curve,auc
    print("Confusion Matrix = ", confusion_matrix(y_act, y_pred))
    print("Accuracy = ", accuracy_score(y_act, y_pred))
    print("Precision = " ,precision_score(y_act, y_pred))
    print("Recall = " ,recall_score(y_act, y_pred))
    print("F1 Score = " ,f1_score(y_act, y_pred))
    false_positive_rate, true_positive_rate, thresholds = roc_curve(y_act, y_pred)
    print("AUC Score =", auc(false_positive_rate, true_positive_rate))
    print("Kappa score = ",cohen_kappa_score(y_act,y_pred))
    print("Error rate = " ,1 - accuracy_score(y_act, y_pred))
    print("AUC-ROC Curve: ")
    plt.plot([0, 1], [0, 1], linestyle='--')
    plt.plot(false_positive_rate, true_positive_rate,marker='.')
    plt.show()
    pass

#Importing Time for clalculating the training and testing time
    import time
    start_time = time.time()
    
    #importing Gaussian Naive Bayes
    from sklearn.naive_bayes import GaussianNB
    gnb = GaussianNB()
    gnb.fit(X_train, y_train)
    
    # Predicting the Test set results
    y_pred = gnb.predict(X_test)
    
    #Getting the predicting probability
    predict_probab = gnb.predict_proba(X_test)
    
    #Geting the log_loss value of the model
    from sklearn.metrics import log_loss
    logloss = log_loss(y_test, predict_probab)
    end_time = time.time()
    eta = end_time - start_time
    
    #10-fold cross validation score
    from sklearn.model_selection import cross_val_score
    accuracy_gausian = cross_val_score(estimator = gnb, X = X_train, y = y_train, cv =10)
    gnb_mean = accuracy_gausian.mean()
    print("10 Fold Cross Validation Score Of Gaussian Naive Bayes:", gnb_mean)
    print('Time Elapsed:', eta)
    print('Log Loss:', logloss)
     #printing the output using the model report function
    model_report(y_test, y_pred)

import lightgbm as lgb
d_train = lgb.Dataset(X_train, label=y_train)
params = {}
params['learning_rate'] = 0.03
params['boosting_type'] = 'gbdt'
params['objective'] = 'binary'
params['metric'] = 'binary_logloss'
params['sub_feature'] = 0.5
params['num_leaves'] = 20
params['min_data'] = 5
params['max_depth'] = 20
lgbm = lgb.train(params, d_train, 500)
#Prediction
y_pred=lgbm.predict(X_test)

for i in range(0,197):
    if y_pred[i]>=.5:       # setting threshold to .5
       y_pred[i]=1
    else:  
       y_pred[i]=0

model_report(y_test, y_pred)

#Light GBM - Confusion matrix
from sklearn.metrics import confusion_matrix

labels = ['Genuine', 'Fraud']
cm = confusion_matrix(y_test, y_pred, labels)
print(cm)
fig = plt.figure()
ax = fig.add_subplot(111)
cax = ax.matshow(cm)
plt.title('Confusion matrix of the classifier')
fig.colorbar(cax)
ax.set_xticklabels([''] + labels)
ax.set_yticklabels([''] + labels)
plt.xlabel('Predicted')
plt.ylabel('True')
plt.show()

from xgboost import XGBClassifier
xgb = XGBClassifier(tree_method = 'gpu_hist')
xgb.fit(X_train, y_train)
# Predicting the Test set results
y_pred = xgb.predict(X_test)
#10-fold cross validation score
from sklearn.model_selection import cross_val_score
accuracy = cross_val_score(estimator = xgb, X = X_train, y = y_train, cv =10)
xgb_cross = accuracy.mean()
print("10-Fold Cross  Validation Score(Without Paramter Tuning):", xgb_cross)

model_report(y_test, y_pred)

seed = 345
est = range(1,100,5)
eta = np.arange(0.01,0.2,0.05)
max_dept = range(3,10,1)
sub_sample = np.arange(0.5,1,0.1)
params = {
        'min_child_weight': [1, 5, 10],
        'gamma': [0.5, 1, 1.5, 2, 5],
        'subsample': [0.6, 0.8, 1.0],
        'colsample_bytree': [0.6, 0.8, 1.0],
        'max_depth': [3, 4, 5],
        'n_estimators' : est,
        'learning_rate' : np.linspace(1e-16,1,3),
        'eta' : eta,
        
        }
param_comb = 100

from sklearn.model_selection import RandomizedSearchCV
random_search = RandomizedSearchCV(xgb, param_distributions=params, n_iter=param_comb, scoring='accuracy', n_jobs= -1, verbose=3, random_state=50, cv = 3 )
random_search.fit(X_train, y_train)

print('\n All results:')
print(random_search.cv_results_)
print('\n Best estimator:')
print(random_search.best_estimator_)
print('\n Best hyperparameters:')
print(random_search.best_params_)
results = pd.DataFrame(random_search.cv_results_)

import lightgbm as lgb
lgbm = lgb.LGBMClassifier()

lgbmParams = {
    'learning_rate': np.arange(0.01,0.05,0.01),
    'num_leaves': range(10,200,5),
    'boosting_type' : ['gbdt'],
    'objective' : ['binary'],
    'max_depth' : np.arange(1,10,1),
    'random_state' : [501], 
    'colsample_bytree' : np.arange(0.1,1,0.1),
    'subsample' : np.arange(0.1,1,0.1),
    'min_split_gain' : np.arange(0.1,1,0.1),
    'min_data_in_leaf':range(1,20,1),
    'metric':['accuracy']
    }
param_comb = 100

from sklearn.model_selection import RandomizedSearchCV
random_search = RandomizedSearchCV(lgbm, param_distributions=lgbmParams, n_iter=param_comb, scoring='accuracy', n_jobs= -1, verbose=3, random_state=10 )

random_search.fit(X_train, y_train)

print('\n All results:')
print(random_search.cv_results_)
print('\n Best estimator:')
print(random_search.best_estimator_)
print('\n Best hyperparameters:')
print(random_search.best_params_)
results = pd.DataFrame(random_search.cv_results_)

from xgboost import XGBClassifier
xgb = XGBClassifier(subsample = 0.8, n_estimators = 56, min_child_weight = 1, max_depth = 5, learning_rate = 1.0, gamma = 5, eta = 0.16000000000000003, colsample_bytree = 1.0)

xgb.fit(X_train, y_train)
# Predicting the Test set results
y_pred = xgb.predict(X_test)
#10-fold cross validation score
from sklearn.model_selection import cross_val_score
accuracy = cross_val_score(estimator = xgb, X = X_train, y = y_train, cv =10)
xgb_cross = accuracy.mean()
print("10-Fold Cross  Validation Score(With Paramter Tuning):", xgb_cross)

model_report(y_test, y_pred)

import lightgbm as lgb
d_train = lgb.Dataset(X_train, label=y_train)
params = {}
params['learning_rate'] = 0.03
params['boosting_type'] = 'gbdt'
params['objective'] = 'binary'
params['metric'] = 'accuracy'
params['sub_feature'] = 0.5
params['num_leaves'] = 65
params['min_data'] = 5
params['max_depth'] = 8
params['subsample'] = 0.5
params['random_state'] = 501
params['min_data_in_leaf'] = 3
params['colsample_bytree'] = 0.9
params['min_split_gain'] = 0.7000000000000001
lgbm = lgb.train(params, d_train, 500)
#Prediction
y_pred=lgbm.predict(X_test)

for i in range(0,197):
    if y_pred[i]>=.5:       # setting threshold to .5
       y_pred[i]=1
    else:  
       y_pred[i]=0

model_report(y_test, y_pred)

#Light GBM - Confusion matrix
from sklearn.metrics import confusion_matrix

labels = ['Genuine', 'Fraud']
cm = confusion_matrix(y_test, y_pred, labels)
print(cm)
fig = plt.figure()
ax = fig.add_subplot(111)
cax = ax.matshow(cm)
plt.title('Confusion matrix of the classifier')
fig.colorbar(cax)
ax.set_xticklabels([''] + labels)
ax.set_yticklabels([''] + labels)
plt.xlabel('Predicted')
plt.ylabel('True')
plt.show()