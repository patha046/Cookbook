import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

print("OS: ", sys.platform)
print("Python: ", sys.version)
print("NumPy: ", np.__version__)
print("Pandas: ", pd.__version__)

# Formatting for seaborn plots
sns.set_context("notebook", font_scale=1.1)
sns.set_style("ticks")

# Displays all dataframe columns
pd.set_option('display.max_columns', None)

%matplotlib inline


### Checking Missing Values
import missingno as msno  # Visualizes missing values
msno.matrix(df)
msno.heatmap(df)  # Co-occurrence of missing values

### Quick EDA report on dataframe
import pandas_profiling
profile = pandas_profiling.ProfileReport(df)
profile.get_rejected_variables(threshold=0.9)  # Rejected variables w/ high correlation
profile.to_file(outputfile="/tmp/myoutputfile.html")  # Saving report as a file


### Preprocessing
# Normalizing
from sklearn import preprocessing
X_norm = preprocessing.normalize(X, norm='max', axis = 1)  # Normalizing across columns

### Cross Validation
# Holdout method
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.30, random_state = 46)

# K-fold cross validation
from sklearn.model_selection import KFold
k_fold = KFold(len(y), n_folds=10, shuffle=True, random_state=46)
cross_val_score(model, X, y, cv=k_fold, n_jobs=-1)


### Probability Threshold Search - xgboost
cv = cross_validation.KFold(len(X), n_folds=5, shuffle=True, random_state=46)

# Making a dataframe to store results of various iterations
xgbResults = pd.DataFrame(columns=['probabilityThreshold', 'f1'])
accuracy, precision, recall, f1 = [],[],[],[]

# Parameters for the model
num_rounds = 8000
params = {'booster': 'gbtree', 'max_depth': 4, 'eta': 0.001, 'objective': "binary:logistic"}

for traincv, testcv in cv:
    
    # Converting the data frames/series to DMatrix objects for xgboost
    Dtrain = xgb.DMatrix(X.ix[traincv], label=y[traincv])
    Dtest = xgb.DMatrix(X.ix[testcv])
    
    # Building the model and outputting class probability estimations
    model = xgb.train(params, Dtrain, num_rounds)
    predictions = model.predict(Dtest)
    temporaryResults = pd.DataFrame(columns=['probabilityThreshold', 'f1'])
    
    # Looping through probability thresholds to gather the f1 score at each threshold
    for probabilityThreshold in np.linspace(0,0.1,100):
        predBin = pd.Series(predictions).apply(lambda x: 1 if x > probabilityThreshold else 0)
        threshF1 = {'probabilityThreshold': probabilityThreshold, 'f1': f1_score(y[testcv], predBin)}
        temporaryResults = temporaryResults.append(threshF1, ignore_index=True)
    
    # Retrieving the f1 score and probability thresholds at the highest f1 score
    bestIndex = list(temporaryResults['f1']).index(max(temporaryResults['f1']))
    bestTempResults = {'probabilityThreshold': temporaryResults.ix[bestIndex][0], 'f1': temporaryResults.ix[bestIndex][1]}
    xgbResults = xgbResults.append(bestTempResults, ignore_index=True)    

print("The Model performace is:")
print(xgbResults.mean())


### Probability Threshold Search - scikit-learn
predicted = model.predict_proba(X_test)[:, 1]
expected = y_test

# Creating an empty dataframe to fill
results = pd.DataFrame(columns=['threshold', 'f1'])

# Looping trhough different probability thresholds
for thresh in np.arange(0, 30000):
    pred_bin = pd.Series(predicted).apply(lambda x: 1 if x > (thresh / 100000) else 0)
    f1 = metrics.f1_score(expected, pred_bin)
    tempResults = {'threshold': (thresh / 100000), 'f1': metrics.f1_score(pred_bin, y_test)}
    results = results.append(tempResults, ignore_index = True)
    
best_index = list(result['f1']).index(max(results['f1']))
print(results.ix[best_index])


### Grid search
from sklearn.model_selection import GridSearchCV
parameters = {'kernel':('linear', 'rbf'), 'C':[1, 10]}
svc = svm.SVC()
clf = GridSearchCV(svc, parameters)
clf.fit(iris.data, iris.target)
sorted(clf.cv_results_.keys())


### Ensemble Model Importance
def feature_importance(model):
    """
    Plots the feature importance for an ensemble model
    """
    feature_importance = model.feature_importances_
    feature_importance = 100.0 * (feature_importance / feature_importance.max())
    sorted_idx = np.argsort(feature_importance)
    pos = np.arange(sorted_idx.shape[0]) + .5
    plt.figure(figsize = (15, 15))
    plt.subplot(1, 2, 2)
    plt.barh(pos, feature_importance[sorted_idx], align='center')
    plt.yticks(pos, df.drop(['adopter', 'user_id'], axis = 1)[sorted_idx])
    plt.xlabel('Relative Importance')
    plt.title('Variable Importance')
    plt.show()
