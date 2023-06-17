# import the necessary packages
from flask import Flask, render_template, redirect, url_for, request,session,Response
from werkzeug.utils import secure_filename
from supportFile import *
import os
import pandas as pd
import utils
import moviepy.editor as mp
import speech_recognition as sr 
import sqlite3
from datetime import datetime

video = ''
name = ''

r = sr.Recognizer()

app = Flask(__name__)

app.secret_key = '1234'
app.config["CACHE_TYPE"] = "null"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.route('/', methods=['GET', 'POST'])
def landing():
	return render_template('home.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
	return render_template('home.html')

@app.route('/doctor', methods=['GET', 'POST'])
def doctor():
	return render_template('doctor.html')

@app.route('/input', methods=['GET', 'POST'])
def input():
	error = None
	
	if request.method == 'POST':
		if request.form['sub']=='Submit':
			num = request.form['num']
			
			users = {'Name':request.form['name'],'Email':request.form['email'],'Contact':request.form['num']}
			df = pd.DataFrame(users,index=[0])
			df.to_csv('users.csv',mode='a',header=False)

			sec = {'num':num}
			df = pd.DataFrame(sec,index=[0])
			df.to_csv('secrets.csv')

			name = request.form['name']
			num = request.form['num']
			email = request.form['email']
			password = request.form['password']
			age = request.form['age']
			gender = request.form['gender']

			con = sqlite3.connect('mydatabase.db')
			cursorObj = con.cursor()
			cursorObj.execute(f"SELECT Name from Users WHERE Name='{name}' AND password = '{password}';")
		
			if(cursorObj.fetchone()):
				error = "User already Registered...!!!"
			else:
				now = datetime.now()
				dt_string = now.strftime("%d/%m/%Y %H:%M:%S")			
				con = sqlite3.connect('mydatabase.db')
				cursorObj = con.cursor()
				cursorObj.execute("CREATE TABLE IF NOT EXISTS Users (Date text,Name text,Contact text,Email text,password text,age text,gender text)")
				cursorObj.execute("INSERT INTO Users VALUES(?,?,?,?,?,?,?)",(dt_string,name,num,email,password,age,gender))
				con.commit()

				return redirect(url_for('login'))

	return render_template('input.html',error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
	error = None
	global video
	global name
	if request.method == 'POST':
		name = request.form['name']
		password = request.form['password']
		savepath = r'upload/'
		video = request.files['video']
		print("filename=",video.filename)
		video.save(os.path.join(savepath,(secure_filename('test.mp4'))))
		con = sqlite3.connect('mydatabase.db')
		cursorObj = con.cursor()
		cursorObj.execute(f"SELECT Name from Users WHERE Name='{name}' AND password = '{password}';")

		if(cursorObj.fetchone()):
			return redirect(url_for('video'))
		else:
			error = "Invalid Credentials Please try again..!!!"
	return render_template('login.html',error=error)

@app.route('/video', methods=['GET', 'POST'])
def video():
	return render_template('video.html')

@app.route('/video_stream')
def video_stream():
	global video
	global name
	return Response(get_frame(video,name),mimetype='multipart/x-mixed-replace; boundary=frame')



@app.route('/record', methods=['GET', 'POST'])
def record():
	global name
	conn = sqlite3.connect('mydatabase.db', isolation_level=None,
						detect_types=sqlite3.PARSE_COLNAMES)
	db_df = pd.read_sql_query(f"SELECT * from Result WHERE Name='{name}';", conn)
	
	return render_template('record.html',tables=[db_df.to_html(classes='w3-table-all w3-hoverable w3-padding')], titles=db_df.columns.values)


@app.after_request
def add_header(response):
	# response.cache_control.no_store = True
	response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
	response.headers['Pragma'] = 'no-cache'
	response.headers['Expires'] = '-1'
	return response

from flask import Flask, render_template,request
import re
from nltk.stem import WordNetLemmatizer
import pickle

def preprocess(data):
    #preprocess
    a = re.sub('[^a-zA-Z]',' ',data)
    a = a.lower()
    a = a.split()
    # a = [wo.lemmatize(word) for word in a ]
    a = ' '.join(a)
    return a


tfidf_vectorizer = pickle.load(open('vectorizer.pkl','rb'))
model =  pickle.load(open('prediction.pkl','rb'))

@app.route('/text', methods=['GET', 'POST'])
def text():
    return render_template('text_1.html')


@app.route('/predict', methods= ['POST'])
def prediction():
    msg = request.form['mood_pred']
    a = preprocess(msg)

    # example_counts = vectorizer.transform( [a] )
    # prediction = mnb.predict( example_counts )
    # prediction[0]

    result = model.predict(tfidf_vectorizer.transform([a]))[0]
    return render_template('text_1.html',pred = "You are--{}".format(result))


from models import Model
# from depression_detection_tweets import DepressionDetection
# from TweetModel import process_message
# import os


# app = Flask(__name__)


@app.route('/question',methods=['GET', 'POST'])
def question():
    return render_template('questionary.html')
    

@app.route('/result_questionary', methods=["POST"])
def predict():
    q1 = int(request.form['a1'])
    q2 = int(request.form['a2'])
    q3 = int(request.form['a3'])
    q4 = int(request.form['a4'])
    q5 = int(request.form['a5'])
    q6 = int(request.form['a6'])
    q7 = int(request.form['a7'])
    q8 = int(request.form['a8'])
    q9 = int(request.form['a9'])
    q10 = int(request.form['a10'])

    values = [q1, q2, q3, q4, q5, q6, q7, q8, q9, q10]
    model = Model()
    classifier = model.svm_classifier()
    prediction = classifier.predict([values])
    if prediction[0] == 0:
            result = 'Your Depression test result : No Depression'
    if prediction[0] == 1:
            result = 'Your Depression test result : Mild Depression'
    if prediction[0] == 2:
            result = 'Your Depression test result : Moderate Depression'
    if prediction[0] == 3:
            result = 'Your Depression test result : Moderately severe Depression'
    if prediction[0] == 4:
            result = 'Your Depression test result : Severe Depression'
    return render_template("result_questionary.html", result=result)
  
    



if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True, threaded=True)
