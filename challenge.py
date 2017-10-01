# coding: utf-8
import pandas as pd
import numpy as np
import uuid


SUM_INTERVALS = [(-7,0), (-14,0), (-30,0)]

def compose_args_dict(features = ['feature_a', 'feature_b']):
    # I assume all entries of SUM_INTERVALS are of a form (-k,0)
    # this is tiny simplification, if second element of a tuple were supposed to be greater than zero
    # additional paramater to single_bin_sum_feature would do the trick
    assert np.all([ interval[0] < 0 and interval[1] == 0 for interval in SUM_INTERVALS])

    d = dict()
    for entry in SUM_INTERVALS:
        for feature in features:
            d[feature + '_' +str(abs(entry[0]))] = {'agg_feature_name': feature, 'days_threshold': abs(entry[0])}
    return d

# adding extra parameter 'offset' could easily extend the whole solution to accept SUM_INTERVALS with second parameter different than 0
# representing relative days distance to 'today'
def single_bin_sum_feature(input_row, agg_feature_name , days_threshold , delta_feature_name = 'days_delta', agg_f = np.sum):
    return agg_f((input_row[delta_feature_name].dt.days < days_threshold) * input_row[agg_feature_name])

# changed signature a bit to make it more 'flexible'
def bin_sum_features(data, today=pd.Timestamp('2016-02-01'), features_processed = ['feature_a', 'feature_b']):
    args_dict = compose_args_dict(features_processed)
    df = pd.DataFrame(data)
    df['days_delta'] = today - df['timestamp']

    grouped_on_id = df.groupby('id')
    result_dataframe =  grouped_on_id.apply(
        lambda x : pd.Series({k: single_bin_sum_feature(x, **(args_dict[k])) for k in args_dict})
    )
    # insert index as a column if needed
    # result_dataframe.insert(0, 'id', result_dataframe.index)
    return result_dataframe

if __name__=='__main__':

    # my simple test cases
    # (using unittest would be much better idea though)
    ###################################################################
    data = dict(
        id = ['a','b'] * 3,
        timestamp = [pd.Timestamp('2016-01-05'), pd.Timestamp('2016-01-30')] * 3,
        feature_a = [1] * 6,
        feature_b = [2] * 6
    )
    res = bin_sum_features(data,today=pd.Timestamp('2016-02-01'), features_processed = ['feature_a', 'feature_b'])
    assert res.loc['a']['feature_a_30'] == 3
    assert res.loc['a']['feature_a_7'] == 0
    assert res.loc['a']['feature_a_14'] == 0

    assert res.loc['b']['feature_b_7'] == 6
    assert res.loc['b']['feature_b_14'] == 6
    assert res.loc['b']['feature_b_30'] == 6

    ###################################################################
    data = dict(
        id = ['a','b','b'],
        timestamp = [pd.Timestamp('2016-01-05'), pd.Timestamp('2016-01-30'), pd.Timestamp('2016-01-05')],
        feature_a = [1,0,-2],
        feature_b = [1,-5,-5]
    )

    res = bin_sum_features(data, today=pd.Timestamp('2016-02-01'), features_processed = ['feature_b'])
    assert len(res.columns) == 3 # only 3 output columns generated
    assert res.loc['b']['feature_b_7'] == -5
    assert res.loc['b']['feature_b_14'] == -5
    assert res.loc['b']['feature_b_30'] == -10

    assert res.loc['a']['feature_b_7'] == 0
    assert res.loc['a']['feature_b_14'] == 0
    assert res.loc['a']['feature_b_30'] == 1

    ###################################################################
    SUM_INTERVALS = [(-365,0), (-150,0), (-50,0)]
    data = dict(
        id = ['a','b','b'],
        timestamp = [pd.Timestamp('2016-01-05'), pd.Timestamp('2016-01-30'), pd.Timestamp('2016-01-05')],
        feature_a = [1,0,-2],
        feature_b = [1,-5,-5]
    )
    res = bin_sum_features(data, today=pd.Timestamp('2016-02-01'), features_processed = ['feature_a'])
    assert len(res.columns) == 3 # only 3 output columns generated
    assert 'feature_a_365' in res.columns
    assert 'feature_a_150' in res.columns
    assert 'feature_a_50' in res.columns

    ###################################################################
    SUM_INTERVALS = [(-365,0), (-150,0), (-50,0)]
    data = dict(
        id = ['a','b','b'],
        timestamp = [pd.Timestamp('2016-01-05'), pd.Timestamp('2016-01-30'), pd.Timestamp('2016-01-05')],
        x = [1,0,-2],
        y = [1,-5,-5]
    )
    res = bin_sum_features(data, today=pd.Timestamp('2016-02-01'), features_processed = ['x'])
    assert len(res.columns) == 3 # only 3 output columns generated
    assert 'x_365' in res.columns
    assert 'x_150' in res.columns
    assert 'x_50' in res.columns

    ###################################################################
    SUM_INTERVALS = [(10,0)] # interval positive - future dates
    data = dict(
        id = ['a','b','b'],
        timestamp = [pd.Timestamp('2016-01-05'), pd.Timestamp('2016-01-30'), pd.Timestamp('2016-01-05')],
        x = [1,0,-2],
        y = [1,-5,-5]
    )
    try:
        bin_sum_features(data, today=pd.Timestamp('2016-02-01'), features_processed = ['x'])
        raise Exception("AssertionError should be thrown in bin_sum_features because of SUM_INTERVALS entry has positive interval value")
    except AssertionError:
        pass

    print "Green green green - hurray! All tests passed!"
