#!/usr/bin/python3.6
from flask import Flask, request, render_template#, session, url_for,abort, redirect,g, flash, _app_ctx_stack
from flask_sqlalchemy import SQLAlchemy
from a_Model import ModelIt, SchedulingMap#, OneHotPotato
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from bokeh.embed import components
from bokeh.resources import INLINE




app = Flask(__name__)
app.config["DEBUG"] = False

js_resources = INLINE.render_js()
css_resources = INLINE.render_css()

#read the Bedplan data from a file on the server (Preload it)
Maternity = pd.DataFrame.from_csv('/home/InsightfullyYours/webapp/assets/files/DataForWebsite.csv')


#Introduction page for all projects
@app.route('/')
def choice():
    return render_template("AllProjectsIntroduction.html")




#The BedPlan Project

#Introductory Presentation
@app.route('/bedplanpresentation')
def BedPlanPresentation():
    return render_template("BedPlanPresentation.html")

#Details on the database
@app.route('/bedplandb')
def BedPlanDataBase():
    return render_template("BedPlanDatabase.html")

#User chooses the patient data
@app.route('/bedplanstart')
def BedPlanStart():

    #Create a list of options for the webform number of patients
    thelist = list(range(100))
    numselections = [x+1 for x in thelist]
    #large values for fun
    numselections.extend([500,1000])

    #Create a list of options for the webform time between beds.
    thelist2 = list(range(10))
    numselections2 = [x for x in thelist2]
    bedselections = list(numselections2)

    return render_template("BedPlaninput.html", numselections=numselections, bedselections=bedselections)#, tables=display.sample(10), titles=titles)

#Display the patient data and submit
@app.route('/bedplansubmit', methods=['GET','POST'])
def submit():

    #Get user inputs
    numstr=request.form.get('numselect')
    num=int(numstr)

    bedstr=request.form.get('bedselect')
    bed=int(bedstr)

    #Columns to display in the sample
    titles = ['subject_id','admitdate']
    SampleSet=Maternity.sample(num)
    display=pd.DataFrame(SampleSet[titles])

    Subject_IDs=SampleSet['subject_id'].values.tolist()

    #Change the column names for the display.
    display=display.rename(columns={'subject_id':'Patient ID','admitdate':'Admission Date'})

    return render_template("BedPlanSubmit.html", numselect = num, bedselect=bed, Subject_IDs=Subject_IDs, tables=[display.to_html(index=False, classes='table table-hover')])


#Output the plots and the schedule.
@app.route('/bedplanoutput', methods=['GET','POST'])
def output():

    Subject_IDs=request.form.get('subjectIDs')
    cushion=int(request.form.get('cushion'))

    #List of subject_ids comes in as a single string that must be parsed
    Subject_IDs=Subject_IDs.strip('[]')
    IntSubjectIDs=[int(s) for s in Subject_IDs.split(',')]

    InternalSampleSet=Maternity[Maternity['subject_id'].isin(IntSubjectIDs)]

    #Prepare input table for model
    NonHotData=InternalSampleSet[['subject_id','admittime','PredError','admitdate','Duration','difftime']]
    del InternalSampleSet['admittime']
    del InternalSampleSet['PredError']
    del InternalSampleSet['admitdate']
    del InternalSampleSet['Duration']
    del InternalSampleSet['difftime']

    #Set the prediction error to a timedelta
    NonHotData['PredError']=NonHotData.PredError.apply(lambda x: pd.Timedelta(x,unit='d'))

    the_result = ModelIt(InternalSampleSet)

    #Add the predictions to the dataframe, making sure the subject ids match and one copy is maintained
    NonHotData.set_index('subject_id',inplace=True,drop=False)
    the_result.set_index('subject_id',inplace=True)
    IncludePrediction=pd.concat([NonHotData,the_result],axis=1)

    #Run the model and the schedule
    G, ScheduleTable = SchedulingMap(IncludePrediction,cushion)

    script, div = components(G)

    #Columns to display in the sample
    titles = ['subject_id', 'Bed','Start_str','End_str']

    display=pd.DataFrame(ScheduleTable[titles])

    #Change the column titles for display purposes
    display=display.rename(columns={'subject_id':'Patient ID', 'Bed':'Assigned Bed','Start_str':'Admission Day','End_str':'Predicted Discharge Day'})

    the_result=ScheduleTable.Bed.max()


    return render_template("BedPlanoutput.html", the_result = the_result, tables=[display.to_html(index=False, classes='table table-hover')], fig_script=script, fig_div=div, js_resources = js_resources, css_resources=css_resources)




#The AIDS Crisis in the US Project

#Introduction to the project
@app.route('/Crisis')
def CrisisIntroduction():
    """Introduction page"""
    return render_template('CrisisIntroduction.html')

#Details on the database
@app.route('/CrisisDatabase')
def DatabaseDetails():
    """Displays the details about the database."""
    return render_template('CrisisDatabaseDetails.html')

#Initial exploration of all data with time
@app.route('/CrisisShape')
def CrisisShape():
    """Displays the first analysis page."""
    return render_template('CrisisShape.html')

#All diagnoses by age and year
@app.route('/CrisisLandscape')
def CrisisLandscape():
    """Display the second analysis page."""
    return render_template('CrisisLandscape.html')

#Transmission routes
@app.route('/CrisisCauses')
def CrisisCauses():
    """Displays the third analysis page."""
    return render_template('CrisisCauses.html')

#Mortality details by age and transmission route
@app.route('/CrisisMortality')
def CrisisMortality():
    """Displays the fourth analysis page."""
    return render_template('CrisisMortality.html')

#Summary of the results
@app.route('/CrisisFinalThoughts')
def CrisisFinalThoughts():
    """Displays the concluding analysis page"""
    return render_template('CrisisFinalThoughts.html')

#Landing page for the user's regional comparison of the crisis.
@app.route('/CrisisExploreLocationStart')
def ExploreLocationStart():

    #Only open a database connection if desired
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
        username="InsightfullyYour",
        password="InsightMySQL",
        hostname="InsightfullyYours.mysql.pythonanywhere-services.com",
        databasename="InsightfullyYour$AIDSData",
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_POOL_RECYCLE"] = 299

    db = SQLAlchemy(app)



    """Presents the user with the Location (from the database) and other options to produce plots."""

    resultTable=db.engine.execute('SHOW TABLES')

    #This code currently assumes the first table in the database is the AIDSDB
    for row in resultTable:
        TableChoice = row[0]

    SQL='SHOW COLUMNS FROM ' + TableChoice
    resultColumns = db.engine.execute(SQL)

    Columns=[]
    for column in resultColumns:
        Columns.append(column[0])
    np_columns=np.array(Columns)
    Column_names=np.unique(np_columns)

    #Set up a SQL string that extracts only unique Locations
    sql = 'SELECT DISTINCT(LOCATION) FROM ' + TableChoice + ' ORDER BY Location ASC'
    resultData = db.engine.execute(sql)

    #Take the results and format them into a DataFrame with both string (location) and numeric (rest) data
    df_result=pd.DataFrame(resultData.fetchall()[:][:])

    #Have the Locations.  Close the db connection
    resultData.close()

    #Get all locations
    AllLocations = df_result.iloc[1:][0]   #eliminates the Null that the subsequent code can't handle yet.

    return render_template('CrisisExploreLocationStart.html', entries=AllLocations)
 #  return redirect(url_for('ExploreLocationStart', entries=TableChoice))

#Present the results of the analysis on the user's choices
@app.route('/CrisisExploreLocationResults', methods=['GET','POST'])
def ExploreLocationFinal():

    #Only open a database connection if desired
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
        username="InsightfullyYour",
        password="InsightMySQL",
        hostname="InsightfullyYours.mysql.pythonanywhere-services.com",
        databasename="InsightfullyYour$AIDSData",
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_POOL_RECYCLE"] = 299

    db = SQLAlchemy(app)

    #Scripts that help generate plots
    from AIDSAnalysisProcedures import CreateDataGrid, contourplotVitalAge,contourplotVital,contourplotAIDSByAgeGroup,contourplotAIDSByAgeGroupLogNorm,contourplotHIVExpByYear,contourplotHIVExpByYearLogNorm,contourplotHIVExpByAge
    from AIDSAnalysisProcedures2 import contourplotVitalAge2,contourplotVital2,contourplotAIDSByAgeGroup2,contourplotAIDSByAgeGroupLogNorm2,contourplotHIVExpByYear2,contourplotHIVExpByYearLogNorm2,contourplotHIVExpByAge2

    plt.close()

    #Get user inputs
    FirstCity=request.form.get('CityOne')
    SecondCity=request.form.get('CityTwo')

    #Get only the relevant data
    #Set up a SQL string that extracts only complete data for analysis
    sql = 'SELECT LOCATION, MONTH_DIAGNOSED_CODE, Age_at_Diagnosis_Code, HIV_Exposure_Category_Code, Vital_Status_Code, Cases FROM AIDSDB WHERE ((LOCATION= "' + FirstCity + '" OR LOCATION = "' + SecondCity + '") AND MONTH_DIAGNOSED_CODE IS NOT NULL AND Age_at_Diagnosis_Code IS NOT NULL AND HIV_Exposure_Category_Code IS NOT NULL AND Vital_Status_Code IS NOT NULL AND Cases IS NOT NULL)'
    resultData = db.engine.execute(sql)

    #Take the results and format them into a DataFrame with both string (location) and numeric (rest) data
    df_result=pd.DataFrame(resultData.fetchall()[:][:])
    #Replace hexadecimal age range code with numbers
    df_result.iloc[:][2]=df_result.iloc[:][2].replace(['A','B','C'],['10','11','12'])
     #Convert Month code to decimal number: from YYYY/MM (1995/01/02/03=1995/Jan/Feb/Mar)) to YYYY.MM (1995/0.0/0.083/0.0167 (Jan/Feb/Mar)
    df_result.iloc[:][1]=df_result.iloc[:][1].replace(['/All Months','/01','/02','/03','/04','/05','/06','/07','/08','/09','/10','/11','/12'],['.000','.000','.083','.167','.250','.333','.417','.500','.583','.667','.750','.833','.917'],regex=True)
    #convert numeric columns saved as strings to numbers
    df_result.iloc[:][1]=df_result.iloc[:][1].apply(pd.to_numeric)#Year of diagnosis
    df_result.iloc[:][2]=df_result.iloc[:][2].apply(pd.to_numeric)#Age at diagnosis code
    df_result.iloc[:][3]=df_result.iloc[:][3].apply(pd.to_numeric)#HIV Exposure Category code
    df_result.iloc[:][4]=df_result.iloc[:][4].apply(pd.to_numeric)#Vital Status Code
    df_result.iloc[:][5]=df_result.iloc[:][5].apply(pd.to_numeric)#Number of cases

    #Have the data.  Close the db connection
    resultData.close()

    #Create the labels for any sort of plot, etc.  The code number in the database acts as the index of the list, which is why "None" was added to the HIV Exposure category.  There is no category 6, as well.
    Vital_Code_Label = ['Alive Before 2001', 'Dead Before 2001']
    Age_At_Diagnosis_Label =    [	'< 1 Year Old',
    							'1-12 Years Old',
    							'13-19 Years Old',
    							'20-24 Years Old',
    							'25-29 Years Old',
    							'30-34 Years Old',
    							'35-39 Years Old \n or Age is Missing',
    							'40-44 Years Old',
    							'45-49 Years Old',
    							'50-54 Years Old',
    							'55-59 Years Old',
    							'60-64 Years Old',
    							'65+ Years Old'
    							]
    HIV_Exposure_Category_Label =   [
    								'Male homosexual/\nbisexual contact',
    								'IV drug use\n(female and hetero male)',
    								'Male homo/bisexual\nand IV drug use',
    								'Hemophilia/coagulation\ndisorder',
    								'Heterosexual contact\n with HIV',
    								'Receipt of blood, blood \ncomponents or tissue',
    								'Risk not reported\n or identified',
    								'Pediatric hemophilia',
    								'Mother with HIV\n or HIV risk',
    								'Pediatric receipt\n of blood',
    								'Pediatric risk not\n reported or identified'
                                    ]

    #Bar plot of age at diagnosis for all years, First City
    np_AgeAtDiag=np.array([df_result[df_result[:][0]==FirstCity][2], df_result[df_result[:][0]==FirstCity][5]])
    AgeResult=np.zeros((13,2))
    for index in range(0,13):
        AgeResult[index,0]=index
        AgeResult[index,1]=sum(np_AgeAtDiag[1,np_AgeAtDiag[0,:]==index])
    plt.close()
    fig = plt.figure()
    plt.bar(AgeResult[:,0],AgeResult[:,1])
    plt.xticks(AgeResult[:,0],Age_At_Diagnosis_Label, rotation='vertical')
    plt.ylabel('Number of Diagnoses')
    plt.title('AIDS Diagnoses By Age Group: All Years in ' + str(FirstCity))
    plt.tight_layout()
    plt.savefig('/home/InsightfullyYours/webapp/assets/images/C1F3.png')
    plt.close
    Age_At_Diagnosis_Code=AgeResult[:,0]

    #Bar plot of age at diagnosis for all years, Second City
    np_AgeAtDiag=np.array([df_result[df_result[:][0]==SecondCity][2], df_result[df_result[:][0]==SecondCity][5]])
    AgeResult=np.zeros((13,2))
    for index in range(0,13):
        AgeResult[index,0]=index
        AgeResult[index,1]=sum(np_AgeAtDiag[1,np_AgeAtDiag[0,:]==index])
    plt.close()
    fig = plt.figure()
    plt.bar(AgeResult[:,0],AgeResult[:,1])
    plt.xticks(AgeResult[:,0],Age_At_Diagnosis_Label, rotation='vertical')
    plt.ylabel('Number of Diagnoses')
    plt.title('AIDS Diagnoses By Age Group: All Years in ' + str(SecondCity))
    plt.tight_layout()
    plt.savefig('/home/InsightfullyYours/webapp/assets/images/C2F3.png')
    plt.close

    #Contour plot of age at diagnosis for per reporting year for FirstCity
    #Separate the diagnoses into bins based on year and age bracket.
    #Create the grid for plotting

    #Take columns 1,2,5: Year of Diagnosis, Age at Diagnosis, and Cases
    np_AgeAtDiagByYear=np.array([df_result[df_result[:][0]==FirstCity][1],df_result[df_result[:][0]==FirstCity][2], df_result[df_result[:][0]==FirstCity][5]])
    #create Datagrid
    datagridAgeAtDiag=CreateDataGrid(np_AgeAtDiagByYear)

    #plot results
    x = np.unique(np_AgeAtDiagByYear[0,:])
    y = np.unique(np_AgeAtDiagByYear[1,:])
    z = datagridAgeAtDiag

    contourplotAIDSByAgeGroup(x,y,z,Age_At_Diagnosis_Label,AgeResult[:,0],FirstCity)
    z[z==0]=0.1     #replace values of zero with 0.1 for log scale.
    contourplotAIDSByAgeGroupLogNorm(x,y,z,Age_At_Diagnosis_Label,AgeResult[:,0],FirstCity)

    #Bar plot of all diagnoses by year
    plt.close()
    fig = plt.figure()
    plt.bar(x,datagridAgeAtDiag.sum(axis=1),width=0.1)
    plt.xlabel('Year')
    plt.ylabel('Number of Diagnoses')
    plt.title('AIDS Diagnoses By Year in ' + str(FirstCity))
    plt.tight_layout()
    plt.xlim([1980,2005])
    plt.savefig('/home/InsightfullyYours/webapp/assets/images/C1F1.png')

    #Bar plot of cumulative diagnoses by year
    plt.close()
    fig = plt.figure()
    plt.bar(x,np.cumsum(datagridAgeAtDiag.sum(axis=1)),width=0.1)
    plt.xlabel('Year')
    plt.ylabel('Cumulative Diagnoses')
    plt.title('Cumulative AIDS Diagnoses By Year in ' + str(FirstCity))
    plt.tight_layout()
    plt.xlim([1980,2005])
    plt.savefig('/home/InsightfullyYours/webapp/assets/images/C1F2.png')

    #Contour plot of age at diagnosis for per reporting year for SecondCity
    #Separate the diagnoses into bins based on year and age bracket.
    #Create the grid for plotting

    #Take columns 1,2,5: Year of Diagnosis, Age at Diagnosis, and Cases
    np_AgeAtDiagByYear=np.array([df_result[df_result[:][0]==SecondCity][1],df_result[df_result[:][0]==SecondCity][2], df_result[df_result[:][0]==SecondCity][5]])
    #create Datagrid
    datagridAgeAtDiag=CreateDataGrid(np_AgeAtDiagByYear)

    #plot results
    x = np.unique(np_AgeAtDiagByYear[0,:])
    y = np.unique(np_AgeAtDiagByYear[1,:])
    z = datagridAgeAtDiag

    contourplotAIDSByAgeGroup2(x,y,z,Age_At_Diagnosis_Label,AgeResult[:,0],SecondCity)
    z[z==0]=0.1     #replace values of zero with 0.1 for log scale.
    contourplotAIDSByAgeGroupLogNorm2(x,y,z,Age_At_Diagnosis_Label,AgeResult[:,0],SecondCity)

    #Bar plot of all diagnoses by year
    plt.close()
    fig = plt.figure()
    plt.bar(x,datagridAgeAtDiag.sum(axis=1),width=0.1)
    plt.xlabel('Year')
    plt.ylabel('Number of Diagnoses')
    plt.title('AIDS Diagnoses By Year in ' + str(SecondCity))
    plt.tight_layout()
    plt.xlim([1980,2005])
    plt.savefig('/home/InsightfullyYours/webapp/assets/images/C2F1.png')

    #Bar plot of cumulative diagnoses by year
    plt.close()
    fig = plt.figure()
    plt.bar(x,np.cumsum(datagridAgeAtDiag.sum(axis=1)),width=0.1)
    plt.xlabel('Year')
    plt.ylabel('Cumulative Diagnoses')
    plt.title('Cumulative AIDS Diagnoses By Year in ' + str(SecondCity))
    plt.tight_layout()
    plt.xlim([1980,2005])
    plt.savefig('/home/InsightfullyYours/webapp/assets/images/C2F2.png')


    #Take columns 1,3,5: Year of Diagnosis, HIV Exposure Category, and Cases for the FirstCity
    #Bar plot of HIV Exposure code for all years
    np_HIVExposeCat=np.array([df_result[df_result[:][0]==FirstCity][3], df_result[df_result[:][0]==FirstCity][5]])
    HIVArray=np.zeros((13,2))
    for index in range(0,13):
        HIVArray[index,0]=index
        HIVArray[index,1]=sum(np_HIVExposeCat[1,np_HIVExposeCat[0,:]==index])
    #There are two categories labels that are created but unused: 0 and 6.  Renive and refactor
    HIVArray = np.delete(HIVArray,6,axis=0)
    HIVArray = np.delete(HIVArray,0,axis=0)
    for index in range(len(HIVArray)):
        HIVArray[index,0]=index

    #Bar Plot
    plt.close()
    fig = plt.figure()
    plt.bar(HIVArray[:,0],HIVArray[:,1])
    plt.xticks(HIVArray[:,0],HIV_Exposure_Category_Label, rotation='vertical')
    plt.ylabel('Number of Diagnoses')
    plt.title('AIDS Diagnoses By HIV Exposure Category: All Years in ' + str(FirstCity))
    plt.tight_layout()
    plt.savefig('/home/InsightfullyYours/webapp/assets/images/C1F5.png')

    #Bar Plot log scale
    plt.close()
    fig = plt.figure()
    plt.bar(HIVArray[:,0],HIVArray[:,1],log=True)
    plt.xticks(HIVArray[:,0],HIV_Exposure_Category_Label, rotation='vertical')
    plt.ylabel('Number of Diagnoses')
    plt.title('AIDS Diagnoses By HIV Exposure Category: All Years in ' + str(FirstCity))
    plt.tight_layout()
    plt.savefig('/home/InsightfullyYours/webapp/assets/images/C1F5log.png')

    np_HIVExposeCatByYear=np.array([df_result[df_result[:][0]==FirstCity][1], df_result[df_result[:][0]==FirstCity][3], df_result[df_result[:][0]==FirstCity][5]])
    #create Datagrid
    datagridHIVExpByYear=CreateDataGrid(np_HIVExposeCatByYear)

    #plot results
    x = np.unique(np_HIVExposeCatByYear[0,:])
    z = datagridHIVExpByYear
    y = np.linspace(0,z.shape[1]-1,z.shape[1])

    contourplotHIVExpByYear(x,y,z,HIV_Exposure_Category_Label,y,FirstCity)
    z[z==0]=0.1 #replace all zeros with 0.1 in order to produce a prettier contour graph
    contourplotHIVExpByYearLogNorm(x,y,z,HIV_Exposure_Category_Label,y,FirstCity)

    #Take columns 1,3,5: Year of Diagnosis, HIV Exposure Category, and Cases for the SecondCity

    #Bar plot of HIV Exposure code for all years
    np_HIVExposeCat=np.array([df_result[df_result[:][0]==SecondCity][3], df_result[df_result[:][0]==SecondCity][5]])
    HIVArray=np.zeros((13,2))
    for index in range(0,13):
        HIVArray[index,0]=index
        HIVArray[index,1]=sum(np_HIVExposeCat[1,np_HIVExposeCat[0,:]==index])
    #There are two categories labels that are created but unused: 0 and 6.  Renive and refactor
    HIVArray = np.delete(HIVArray,6,axis=0)
    HIVArray = np.delete(HIVArray,0,axis=0)
    for index in range(len(HIVArray)):
        HIVArray[index,0]=index

    #Bar Plot
    plt.close()
    fig = plt.figure()
    plt.bar(HIVArray[:,0],HIVArray[:,1])
    plt.xticks(HIVArray[:,0],HIV_Exposure_Category_Label, rotation='vertical')
    plt.ylabel('Number of Diagnoses')
    plt.title('AIDS Diagnoses By HIV Exposure Category: All Years in ' + str(SecondCity))
    plt.tight_layout()
    plt.savefig('/home/InsightfullyYours/webapp/assets/images/C2F5.png')

    #Bar Plot log scale
    plt.close()
    fig = plt.figure()
    plt.bar(HIVArray[:,0],HIVArray[:,1],log=True)
    plt.xticks(HIVArray[:,0],HIV_Exposure_Category_Label, rotation='vertical')
    plt.ylabel('Number of Diagnoses')
    plt.title('AIDS Diagnoses By HIV Exposure Category: All Years in ' + str(SecondCity))
    plt.tight_layout()
    plt.savefig('/home/InsightfullyYours/webapp/assets/images/C2F5log.png')

    np_HIVExposeCatByYear=np.array([df_result[df_result[:][0]==FirstCity][1], df_result[df_result[:][0]==FirstCity][3], df_result[df_result[:][0]==FirstCity][5]])
    #create Datagrid
    datagridHIVExpByYear=CreateDataGrid(np_HIVExposeCatByYear)

    #plot results
    x = np.unique(np_HIVExposeCatByYear[0,:])
    z = datagridHIVExpByYear
    y = np.linspace(0,z.shape[1]-1,z.shape[1])

    contourplotHIVExpByYear2(x,y,z,HIV_Exposure_Category_Label,y,SecondCity)
    z[z==0]=0.1 #replace all zeros with 0.1 in order to produce a prettier contour graph
    contourplotHIVExpByYearLogNorm2(x,y,z,HIV_Exposure_Category_Label,y,SecondCity)

    #Take columns 2,3,5: Age at Diagnosis, HIV Exposure Category, and Cases for the FirstCity
    np_HIVExposeCatByAge=np.array([df_result[df_result[:][0]==FirstCity][2], df_result[df_result[:][0]==FirstCity][3], df_result[df_result[:][0]==FirstCity][5]])
    #create Datagrid
    datagridHIVExpByAge=CreateDataGrid(np_HIVExposeCatByAge)

    #plot results
    x = np.unique(np_HIVExposeCatByAge[0,:])
    z = datagridHIVExpByAge
    y = np.linspace(0,z.shape[1]-1,z.shape[1])

    contourplotHIVExpByAge(x,y,z,HIV_Exposure_Category_Label,y,Age_At_Diagnosis_Label,Age_At_Diagnosis_Code, FirstCity)

    #Take columns 2,3,5: Age at Diagnosis, HIV Exposure Category, and Cases for the SecondCity

    np_HIVExposeCatByAge=np.array([df_result[df_result[:][0]==SecondCity][2], df_result[df_result[:][0]==SecondCity][3], df_result[df_result[:][0]==SecondCity][5]])
    #create Datagrid
    datagridHIVExpByAge=CreateDataGrid(np_HIVExposeCatByAge)

    #plot results
    x = np.unique(np_HIVExposeCatByAge[0,:])
    z = datagridHIVExpByAge
    y = np.linspace(0,z.shape[1]-1,z.shape[1])

    contourplotHIVExpByAge2(x,y,z,HIV_Exposure_Category_Label,y,Age_At_Diagnosis_Label,Age_At_Diagnosis_Code, SecondCity)

    #Take columns 1,3,4,5: Year of Diagnosis, HIV Exposure, Vital Stats, and Cases for first city
    np_VitalYear=np.array([df_result[df_result[:][0]==FirstCity][1], df_result[df_result[:][0]==FirstCity][3], df_result[df_result[:][0]==FirstCity][4], df_result[df_result[:][0]==FirstCity][5]])

    #Separate data based upon vital stats.  Set cases to zero so all dates can be represented in subsequent analysis
    np_VitalYearZero=np_VitalYear
    np_VitalYearZero[3,np_VitalYearZero[2,:]==1]=0
    np_VitalYearZero=np.delete(np_VitalYearZero,2,axis=0)
    datagridVitalYearZero=CreateDataGrid(np_VitalYearZero)

    #Have to repeat due to a subtle bug in which both vital years were affected by the zeroing command
    np_VitalYear=np.array([df_result[df_result[:][0]==FirstCity][1], df_result[df_result[:][0]==FirstCity][3], df_result[df_result[:][0]==FirstCity][4], df_result[df_result[:][0]==FirstCity][5]])
    np_VitalYearOne=np_VitalYear
    np_VitalYearOne[3,np_VitalYearOne[2,:]==0]=0
    np_VitalYearOne=np.delete(np_VitalYearOne,2,axis=0)
    datagridVitalYearOne=CreateDataGrid(np_VitalYearOne)

    totalVitalDataGrid=datagridVitalYearZero+datagridVitalYearOne

    #Calculate percentage of diagnoses dead at 2001
    PercentVitalYearOne = np.round(np.divide(datagridVitalYearOne,totalVitalDataGrid,out=np.zeros_like(datagridVitalYearOne), where=totalVitalDataGrid!=0),2)

    #plot results
    x = np.unique(np_VitalYear[0,:])
    z = PercentVitalYearOne
    y = np.linspace(0,z.shape[1]-1,z.shape[1])

    contourplotVital(x,y,z,HIV_Exposure_Category_Label,y,FirstCity)


    #Take columns 1,3,4,5: Year of Diagnosis, HIV Exposure, Vital Stats, and Cases for second city

    np_VitalYear=np.array([df_result[df_result[:][0]==SecondCity][1], df_result[df_result[:][0]==SecondCity][3], df_result[df_result[:][0]==SecondCity][4], df_result[df_result[:][0]==SecondCity][5]])

    #Separate data based upon vital stats.  Set cases to zero so all dates can be represented in subsequent analysis
    np_VitalYearZero=np_VitalYear
    np_VitalYearZero[3,np_VitalYearZero[2,:]==1]=0
    np_VitalYearZero=np.delete(np_VitalYearZero,2,axis=0)
    datagridVitalYearZero=CreateDataGrid(np_VitalYearZero)

    #Have to repeat due to a subtle bug in which both vital years were affected by the zeroing command
    np_VitalYear=np.array([df_result[df_result[:][0]==SecondCity][1], df_result[df_result[:][0]==SecondCity][3], df_result[df_result[:][0]==SecondCity][4], df_result[df_result[:][0]==SecondCity][5]])
    np_VitalYearOne=np_VitalYear
    np_VitalYearOne[3,np_VitalYearOne[2,:]==0]=0
    np_VitalYearOne=np.delete(np_VitalYearOne,2,axis=0)
    datagridVitalYearOne=CreateDataGrid(np_VitalYearOne)

    totalVitalDataGrid=datagridVitalYearZero+datagridVitalYearOne

    #Calculate percentage of diagnoses dead at 2001
    PercentVitalYearOne = np.round(np.divide(datagridVitalYearOne,totalVitalDataGrid,out=np.zeros_like(datagridVitalYearOne), where=totalVitalDataGrid!=0),2)

    #plot results
    x = np.unique(np_VitalYear[0,:])
    z = PercentVitalYearOne
    y = np.linspace(0,z.shape[1]-1,z.shape[1])

    contourplotVital2(x,y,z,HIV_Exposure_Category_Label,y,SecondCity)

    #Take columns 1,2,4,5: Year of Diagnosis, Age At Exposure, Vital Stats, and Cases
    np_VitalAgeYear=np.array([df_result[df_result[:][0]==FirstCity][1], df_result[df_result[:][0]==FirstCity][2], df_result[df_result[:][0]==FirstCity][4], df_result[df_result[:][0]==FirstCity][5]])

    #Separate data based upon vital stats.  Set cases to zero so all dates can be represented in subsequent analysis
    np_VitalAgeYearZero=np_VitalAgeYear
    np_VitalAgeYearZero[3,np_VitalAgeYearZero[2,:]==1]=0
    np_VitalAgeYearZero=np.delete(np_VitalAgeYearZero,2,axis=0)
    datagridVitalAgeYearZero=CreateDataGrid(np_VitalAgeYearZero)

    #Have to repeat due to a subtle bug in which both vital years were affected by the zeroing command
    np_VitalAgeYear=np.array([df_result[df_result[:][0]==FirstCity][1], df_result[df_result[:][0]==FirstCity][2], df_result[df_result[:][0]==FirstCity][4], df_result[df_result[:][0]==FirstCity][5]])
    np_VitalAgeYearOne=np_VitalAgeYear
    np_VitalAgeYearOne[3,np_VitalAgeYearOne[2,:]==0]=0
    np_VitalAgeYearOne=np.delete(np_VitalAgeYearOne,2,axis=0)
    datagridVitalAgeYearOne=CreateDataGrid(np_VitalAgeYearOne)

    totalVitalAgeDataGrid=datagridVitalAgeYearZero+datagridVitalAgeYearOne

    #Calculate percentage of diagnoses dead at 2001
    PercentVitalAgeYearOne = np.round(np.divide(datagridVitalAgeYearOne,totalVitalAgeDataGrid,out=np.zeros_like(datagridVitalAgeYearOne), where=totalVitalAgeDataGrid!=0),2)

    #plot results
    x = np.unique(np_VitalAgeYearOne[:][0])
    y = np.unique(np_VitalAgeYearOne[:][1])
    z = PercentVitalAgeYearOne

    contourplotVitalAge(x,y,z,Age_At_Diagnosis_Label,AgeResult[:,0],FirstCity)

    #Bar chart showing total cases and deaths by 2000
    totalOne=datagridVitalAgeYearOne.sum(axis=1)
    totalYear=totalVitalAgeDataGrid.sum(axis=1)

    #create a fake data set to put on top of deaths from 2000 on becaus otherwise it fills to 2003 with a flat line.
    yq=np.array(x)
    yq[yq<2000]=0
    yq[yq>=2000]=np.amax(np.cumsum(totalOne))

    plt.close()
    fig = plt.figure()
    p1 = plt.bar(x,np.cumsum(totalYear), width=0.1,color='b')
    p2 = plt.bar(x,np.cumsum(totalOne),width=0.1,color='#d62728')
    p3 = plt.bar(x,yq,width=0.1,color='b')
    plt.ylabel('Total Diagnoses')
    plt.xlabel('Year')
    plt.title('Cumulative AIDS Diagnoses By Year and Mortality by 2000 in ' + str(FirstCity))
    plt.legend((p1[0],p2[0]),('Total Diagnoses','Dead by 2000'))
    plt.xlim([1980,2005])
    plt.savefig('/home/InsightfullyYours/webapp/assets/images/C1F10.png')

    #Take columns 1,2,4,5: Year of Diagnosis, Age At Exposure, Vital Stats, and Cases

    np_VitalAgeYear=np.array([df_result[df_result[:][0]==SecondCity][1], df_result[df_result[:][0]==SecondCity][2], df_result[df_result[:][0]==SecondCity][4], df_result[df_result[:][0]==SecondCity][5]])

    #Separate data based upon vital stats.  Set cases to zero so all dates can be represented in subsequent analysis
    np_VitalAgeYearZero=np_VitalAgeYear
    np_VitalAgeYearZero[3,np_VitalAgeYearZero[2,:]==1]=0
    np_VitalAgeYearZero=np.delete(np_VitalAgeYearZero,2,axis=0)
    datagridVitalAgeYearZero=CreateDataGrid(np_VitalAgeYearZero)

    #Have to repeat due to a subtle bug in which both vital years were affected by the zeroing command
    np_VitalAgeYear=np.array([df_result[df_result[:][0]==SecondCity][1], df_result[df_result[:][0]==SecondCity][2], df_result[df_result[:][0]==SecondCity][4], df_result[df_result[:][0]==SecondCity][5]])
    np_VitalAgeYearOne=np_VitalAgeYear
    np_VitalAgeYearOne[3,np_VitalAgeYearOne[2,:]==0]=0
    np_VitalAgeYearOne=np.delete(np_VitalAgeYearOne,2,axis=0)
    datagridVitalAgeYearOne=CreateDataGrid(np_VitalAgeYearOne)

    totalVitalAgeDataGrid=datagridVitalAgeYearZero+datagridVitalAgeYearOne

    #Calculate percentage of diagnoses dead at 2001
    PercentVitalAgeYearOne = np.round(np.divide(datagridVitalAgeYearOne,totalVitalAgeDataGrid,out=np.zeros_like(datagridVitalAgeYearOne), where=totalVitalAgeDataGrid!=0),2)


    #plot results
    x = np.unique(np_VitalAgeYearOne[:][0])
    y = np.unique(np_VitalAgeYearOne[:][1])
    z = PercentVitalAgeYearOne

    contourplotVitalAge2(x,y,z,Age_At_Diagnosis_Label,AgeResult[:,0],SecondCity)

    #Bar chart showing total cases and deaths by 2000
    totalOne=datagridVitalAgeYearOne.sum(axis=1)
    totalYear=totalVitalAgeDataGrid.sum(axis=1)

    #create a fake data set to put on top of deaths from 2000 on becaus otherwise it fills to 2003 with a flat line.
    yq=np.array(x)
    yq[yq<2000]=0
    yq[yq>=2000]=np.amax(np.cumsum(totalOne))

    plt.close()
    fig = plt.figure()
    p1 = plt.bar(x,np.cumsum(totalYear), width=0.1,color='b')
    p2 = plt.bar(x,np.cumsum(totalOne),width=0.1,color='#d62728')
    p3 = plt.bar(x,yq,width=0.1,color='b')
    plt.ylabel('Total Diagnoses')
    plt.xlabel('Year')
    plt.title('Cumulative AIDS Diagnoses By Year and Mortality by 2000 in ' + str(SecondCity))
    plt.legend((p1[0],p2[0]),('Total Diagnoses','Dead by 2000'))
    plt.xlim([1980,2005])
    plt.savefig('/home/InsightfullyYours/webapp/assets/images/C2F10.png')



    #Presents the user with the graphs generated by their request.
    return render_template('CrisisExploreLocationFinal.html', CityOne=FirstCity, CityTwo=SecondCity)








