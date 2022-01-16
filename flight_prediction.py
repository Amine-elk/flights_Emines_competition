# -*- coding: utf-8 -*-
"""flight_prediction.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1NYYZv1r1iWMmC--XH6G1stcQyrNU_-KE
"""

from google.colab import drive
drive.mount('/content/drive')

#import the necessary librairies
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_style('whitegrid')

import warnings  
warnings.filterwarnings('ignore')

#import the train file and test file
df_train = pd.read_csv('/content/drive/MyDrive/Datacamp/flights_train.csv',decimal=',')
df_test = pd.read_csv('/content/drive/MyDrive/Datacamp/flights_Xtest.csv',decimal=',')
df_train.head()

df_train.dtypes

#convert the features to the appropriate type
df_train['from'] = df_train['from'].astype(str)
df_train['to'] = df_train['to'].astype(str)
df_test['from'] = df_test['from'].astype(str)
df_test['to'] = df_test['to'].astype(str)
df_train['avg_weeks'] = df_train['avg_weeks'].astype(float)
df_train['std_weeks'] = df_train['std_weeks'].astype(float)
df_test['avg_weeks'] = df_test['avg_weeks'].astype(float)
df_test['std_weeks'] = df_test['std_weeks'].astype(float)
df_train['target'] = df_train['target'].astype(float)

#Discovering the distribution of our target variable and its skewness
print(f"Skewness Co-efficient: {round(df_train.target.skew(), 3)}")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5), dpi=300)

##### HISTOGRAM #####
from scipy import stats
sns.distplot(df_train['target'] , fit=stats.norm, ax=ax1)
ax1.set_title('Histogram')

##### PROBABILITY / QQ PLOT #####
stats.probplot(df_train['target'], plot=ax2)

plt.show()

#calculating the pearson correlation between the variables
corrmat = df_train.corr()
plt.subplots(figsize=(12,9))
sns.heatmap(corrmat, vmax=0.9, square=True)

#checking the missing values
df_train.isna().sum()

#function that shows the distribution of a numerical variable and the scatterplot with the target variable and also its boxplot
def plot_numeric_features(feature):
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(10, 5), dpi=110)

    sns.distplot(df_train[feature], ax=ax1)
    sns.scatterplot(df_train[feature], df_train["target"], ax=ax2)
    sns.boxplot(df_train[feature], ax=ax3, orient='v', width=0.2)

    print("Skewness Coefficient of target is %.2f" %df_train[feature].skew())
    ax1.set_yticks([])
    
    return plt

plot_numeric_features("avg_weeks").show()
plot_numeric_features("std_weeks").show()

df_train['from'].value_counts()

df_train['to'].value_counts()

#convert flight fate to the proper format
import datetime
df_train['flight_date'] = pd.to_datetime(df_train['flight_date'],format='%Y-%m-%d', errors='ignore')
df_test['flight_date'] = pd.to_datetime(df_test['flight_date'],format='%Y-%m-%d', errors='ignore')

df_train.dtypes

print("Unique Values in `Flight Date` => {}".format(np.sort(df_train.flight_date.dt.strftime('%Y-%m-%d').unique())))

#plot the target variable as a function of time 
ax = df_train.plot(x='flight_date', y='target', figsize=(16,8))

# Get Day of the Week for flight_date 
df_train['flight_date_DOW'] = df_train['flight_date'].dt.strftime("%w")
df_test['flight_date_DOW'] = df_test['flight_date'].dt.strftime("%w")

# Get the month of the year for flight_date 
df_train['flight_date_month'] = df_train['flight_date'].dt.strftime("%m")
df_test['flight_date_month'] = df_test['flight_date'].dt.strftime("%m")

# Get the month of the year for flight_date 
df_train['flight_date_y'] = df_train['flight_date'].dt.strftime("%Y")
df_test['flight_date_y'] = df_test['flight_date'].dt.strftime("%Y")

df_train['flight_date_DOW'] = df_train['flight_date_DOW'].astype(int)
df_train['flight_date_month'] = df_train['flight_date_month'].astype(int)
df_test['flight_date_DOW'] = df_test['flight_date_DOW'].astype(int)
df_test['flight_date_month'] = df_test['flight_date_month'].astype(int)
df_train['flight_date_y'] = df_train['flight_date_y'].astype(int)
df_test['flight_date_y'] = df_test['flight_date_y'].astype(int)

df_train['weekend_indi'] = 0          # Initialize the column with default value of 0
df_train.loc[df_train['flight_date_DOW'].isin([5, 6]), 'weekend_indi'] = 1

df_test['weekend_indi'] = 0          # Initialize the column with default value of 0
df_test.loc[df_test['flight_date_DOW'].isin([5, 6]), 'weekend_indi'] = 1

counts_df = df_train['weekend_indi'].value_counts()
fig, ax = plt.subplots()
counts_df.plot(kind="bar", color=['navy', 'orange'], ax=ax)
ax.set_ylabel("Count")
fig.suptitle("Weekend")
counts_df

#check the U.S holidays
import holidays
from datetime import date
for day in sorted(holidays.USA(years = 2012 ).items()):
    print(day)

#set a new index Holiday that contains information if the day is a holiday or not 
import holidays
from datetime import date

usa_holidays = holidays.UnitedStates()
df_train['Holiday'] = df_train['flight_date'].apply(lambda x: int(x in usa_holidays))
df_train['Holiday'].value_counts()

df_test['Holiday'] = df_test['flight_date'].apply(lambda x: int(x in usa_holidays))
df_test['Holiday'].value_counts()

df_train.drop(['flight_date'], axis=1, inplace=True)
df_test.drop(['flight_date'], axis=1, inplace=True)

#get dummies to catogrical variables ('from' and 'to')
df_train = pd.get_dummies(df_train)
df_test = pd.get_dummies(df_test)

df_train

import optuna
import xgboost as xgb
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split

target=df_train['target']
y = df_train['target']
X = df_train.drop(['target'],axis='columns')
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

#function that fit the xgboost model with its hyperparameters
def objective(trial,data=df_train,target=target):
    
    param = {
        'tree_method':'gpu_hist',  # this parameter means using the GPU when training our model to speedup the training process
        'lambda': trial.suggest_loguniform('lambda', 1e-3, 10.0),
        'alpha': trial.suggest_loguniform('alpha', 1e-3, 10.0),
        'colsample_bytree': trial.suggest_categorical('colsample_bytree', [0.3,0.4,0.5,0.6,0.7,0.8,0.9, 1.0]),
        'subsample': trial.suggest_categorical('subsample', [0.4,0.5,0.6,0.7,0.8,1.0]),'learning_rate': trial.suggest_categorical('learning_rate', [0.008,0.009,0.01,0.012,0.014,0.016,0.018, 0.02]),
        'n_estimators': 4000,
        'max_depth': trial.suggest_categorical('max_depth', [5,7,9,11,13,15,17,20]),
        'random_state': trial.suggest_categorical('random_state', [24, 48,2020]),
        'min_child_weight': trial.suggest_int('min_child_weight', 1, 300),
    }
    model = xgb.XGBRegressor(**param)  
    
    model.fit(X_train,y_train,eval_set=[(X_test,y_test)],early_stopping_rounds=100,verbose=False)
    
    preds = model.predict(X_test)
    rmse = mean_squared_error(y_test, preds,squared=False)
    
    return rmse

#optimizing xgboost hyperparameters with optuna 
study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=50)
print('Number of finished trials:', len(study.trials))
print('Best trial:', study.best_trial.params)

study.trials_dataframe()

optuna.visualization.plot_optimization_history(study)

optuna.visualization.plot_parallel_coordinate(study)

optuna.visualization.plot_slice(study)

optuna.visualization.plot_contour(study, params=['alpha',
                            #'max_depth',
                            'lambda',
                            'subsample',
                            'learning_rate',
                            'subsample'])

optuna.visualization.plot_param_importances(study)

optuna.visualization.plot_edf(study)

Best_trial= {'lambda': 0.030122615277663786, 'alpha': 0.49109871854247905, 'colsample_bytree': 0.8, 'subsample': 1.0, 'learning_rate': 0.008, 'max_depth': 13, 'random_state': 24, 'min_child_weight': 16,'tree_method':'gpu_hist'}

xgboost = XGBRegressor(learning_rate=0.3,n_estimators=200,
                                     max_depth=3, min_child_weight=0,
                                     gamma=0, subsample=0.7,
                                     colsample_bytree=0.7,
                                     objective='reg:linear', nthread=-1,
                                     scale_pos_weight=1, seed=27,
                                     reg_alpha=0.006)
xgb = xgboost.fit(X_train, y_train)

from lightgbm import LGBMRegressor
lightgbm = LGBMRegressor(objective='regression', 
                                       num_leaves=6,
                                       learning_rate=0.6, 
                                       n_estimators=1500,
                                       max_bin=100, 
                                       bagging_fraction=0.75,
                                       bagging_freq=5, 
                                       bagging_seed=7,
                                       feature_fraction=0.2,
                                       feature_fraction_seed=7,
                                       verbose=-1,
                                       )
gbm = lightgbm.fit(X_train, y_train)

tot = ((0.5 * xgb.predict(df_test))+ (0.5*gbm.predict(df_test)))

"""we combine our two models to obtain a more accurate model. """

x= tot
y = pd.Series(x)
print(y)
y.to_csv('test1_flight.csv',index=False)