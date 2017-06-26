#!/usr/bin/python3.6
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  2 21:57:56 2017

@author: The Computer
"""

def ModelIt(SubjectIDandOneHotEncoded):

    import numpy as np
    from sklearn.externals import joblib

    SubjectIDandOneHotEncoded.fillna(value=0,inplace=True)

    #import the model
    clf=joblib.load('/home/InsightfullyYours/webapp/assets/files/modeldump2.pk1')

    #extract the predictions
    SubjectIDandOneHotEncoded['Prediction2']=np.round(np.exp(clf.predict(SubjectIDandOneHotEncoded.iloc[:,1:])),0)

    Predictions=SubjectIDandOneHotEncoded[['subject_id','Prediction2']]

    result = Predictions
    return result

def SchedulingMap(GroupedDF,cushion):
    from bokeh.plotting import figure
    from bokeh.models import ColumnDataSource, Range1d
    from bokeh.models.tools import HoverTool
    import datetime
    from datetime import datetime as dt
    import numpy as np
    import pandas as pd

    DF=GroupedDF

    #convert all the times appropriately and calculate relevant dependent times
    DF['Start_dt']=DF['admitdate'].apply(lambda x: dt.strptime(x, '%Y-%m-%d'))
    DF['Duration']=pd.to_timedelta(DF['Duration'])
    DF['DurationNegError']=DF['Duration']-DF['PredError']
    DF['DurationPosError']=DF['Duration']+DF['PredError']
    DF['End_dt']=DF['Start_dt']+DF['Duration'] #recreate end date
    DF['End_dt_w_pos_error']=DF['Start_dt']+DF['DurationPosError']
    DF['End_dt_w_neg_error']=DF['Start_dt']+DF['DurationNegError']
    DF['Start_str']=DF['Start_dt'].apply(lambda x: dt.strftime(x,'%Y-%m-%d'))
    DF['End_str']=DF['End_dt'].apply(lambda x: dt.strftime(x,'%Y-%m-%d'))
    DF['End_str_w_pos_error']=DF['End_dt_w_pos_error'].apply(lambda x: dt.strftime(x,'%Y-%m-%d'))
    DF['End_str_w_neg_error']=DF['End_dt_w_neg_error'].apply(lambda x: dt.strftime(x,'%Y-%m-%d'))

    #Prepare variables
    ScheduleMap= pd.DataFrame(np.zeros((len(DF), 1098)).astype(int))
    DF['Bed']=0
    DF['BedError']=0

    #Scheduling algoritm.  Greedy and slow.
    for row in range(len(DF)):
        startcol=DF['Start_dt'].iloc[row].timetuple().tm_yday
        endcol=DF['Start_dt'].iloc[row].timetuple().tm_yday+DF['DurationPosError'].iloc[row].days+cushion
        for row2 in range(len(ScheduleMap)):
            if ScheduleMap.iloc[row2,startcol:endcol].sum() == 0:
                ScheduleMap.iloc[row2,startcol:endcol] = 1
                DF['Bed'].iloc[row]=row2+1
                DF['BedError'].iloc[row]=row2+1
                break

    DF = DF.sort_values('Bed',ascending=True).reset_index(drop=True)

    x_range=Range1d(DF.Start_dt.min()-datetime.timedelta(days=15),DF.End_dt_w_pos_error.max()+datetime.timedelta(days=15))

    G=figure(title='Hospital BedPlan',
             x_axis_type='datetime',
             width=800,
             height=400,
             y_range=[min(DF.Bed)-1,max(DF.Bed)+1],
             x_range=x_range,
             x_axis_label="Dates",
             y_axis_label="Bed")

    G.yaxis.minor_tick_line_color = None

    hover=HoverTool(tooltips="Patient ID: @subject_id<br>\
    Start: @Start_str<br>\
    Predicted End: @End_str<br>\
    Prediction Error Range: @End_str_w_neg_error to @End_str_w_pos_error")
    G.add_tools(hover)

    #Bar heights
    DF['ID']=DF.Bed-0.2
    DF['ID1']=DF.Bed+0.2
    DF['ErID']=DF.Bed-0.15
    DF['ErID1']=DF.Bed+0.15

    CDS=ColumnDataSource(DF)

    G.quad(left='Start_dt', right='End_dt', bottom='ID', top='ID1',source=CDS, color='blue')
    G.quad(left='End_dt_w_neg_error', right='End_dt_w_pos_error', bottom='ErID', top='ErID1',source=CDS, color='yellow')

    figschedule=G
    tableschedule=DF

    return figschedule, tableschedule

#automatically one-hot-encode columns
def OneHotPotato(Matrix):
    import pandas as pd
    from sklearn.preprocessing import OneHotEncoder, LabelEncoder

    Matrix.fillna(value='NA',inplace=True)
    OutputMatrix=pd.concat([Matrix['subject_id'],Matrix['hadm_id']],axis=1)

    for col in range(len(Matrix.columns)):
        #Make sure not the subject or hospital ID
        if Matrix.columns[col] == 'subject_id':
            continue
        elif Matrix.columns[col] == 'hadm_id':
            continue
        elif Matrix.columns[col] == 'admittime':
            continue
        elif Matrix.columns[col] == 'admitdate':
            continue

        if isinstance(Matrix[Matrix.columns[col]].iloc[0], str) == True:
            le=LabelEncoder()
            le.fit(Matrix[Matrix.columns[col]])
            Labelled=le.transform(Matrix[Matrix.columns[col]])
            LabelName=le.classes_


            ohe=OneHotEncoder()
            ohe.fit(Labelled.reshape(-1,1))
            output = ohe.transform(Labelled.reshape(-1,1)).toarray()

            #OutputMatrix=pd.concat([OutputMatrix, pd.DataFrame(output,columns=LabelName,copy=True, index=OutputMatrix.index)],axis=1, copy=True)
            OutputMatrix=pd.concat([OutputMatrix, pd.DataFrame(output,columns=LabelName,copy=True, index=OutputMatrix.index)],axis=1, copy=False)
        else:
            #OutputMatrix=pd.concat([OutputMatrix, Matrix[Matrix.columns[col]]],axis=1,copy=True)
            OutputMatrix=pd.concat([OutputMatrix, Matrix[Matrix.columns[col]]],axis=1,copy=False)


    return OutputMatrix





















