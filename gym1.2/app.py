from flask import Flask, render_template, flash, redirect, url_for, request, session, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, RadioField, SelectField, IntegerField
from wtforms.fields.html5 import DateField
from passlib.handlers.sha2_crypt import sha256_crypt
from flask_script import Manager
from functools import wraps
from datetime import datetime
app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'abc@12345'
app.config['MYSQL_DB'] = 'gym1'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Nice try, Tricks don\'t work, bud!! Please Login :)', 'danger')
			return redirect(url_for('login'))
	return wrap

@app.route('/')
def index():
	return render_template('home.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
	if request.method == 'POST':
		username = request.form['username']
		password_candidate = request.form['password']

		cur = mysql.connection.cursor()

		result = cur.execute('SELECT * FROM admin WHERE username = %s', [username])
		 
		print('yes')  
		if result>0:
			data = cur.fetchone()
			password = data['password']

			if sha256_crypt.verify(password_candidate, password):
				session['logged_in'] = True
				session['username'] = username
				session['prof']=1
				flash('You are logged in', 'success')
				return redirect(url_for('adminDash'))
			else:
				error = 'Invalid login'
				return render_template('login.html', error = error)

			cur.close()
		result1 = cur.execute('SELECT * FROM member WHERE username = %s', [username])	
		if result1>0:
			data = cur.fetchone()
			password = data['password']

			if sha256_crypt.verify(password_candidate, password):
				session['logged_in'] = True
				session['username'] = username
				session['prof']=2
				result2 = cur.execute('SELECT trainer_id FROM member WHERE username = %s', [username])	
				result3=cur.fetchone()
				result4=result3['trainer_id']
				print(result4)
				if result4==None:
					return redirect(url_for('fillDetails'))
				flash('You are logged in', 'success')
				return redirect(url_for('memberDash'))
			else:
				error = 'Invalid login'
				return render_template('login.html', error = error)

			cur.close();			
		else:
			error = 'Username NOT FOUND'
			return render_template('login.html', error = error)

	return render_template('login.html')

@app.route('/faq')
def faq():
	return render_template('faq.html')

@app.route('/adminDash')
@is_logged_in
def adminDash():
	return render_template('adminDash.html')

values = []
choices = []

class AddTrainorForm(Form):
	name = StringField('Name', [validators.Length(min = 1, max = 100)])
	trainer_id = IntegerField('Trainer id', [validators.NumberRange(min = 99, max = 1001)])
	street = StringField('Street', [validators.Length(min = 1, max = 100)])
	centre = SelectField('Select Centre', choices = choices)
	phone = StringField('Phone', [validators.Length(min = 1, max = 100)])


@app.route('/addTrainor', methods = ['GET', 'POST'])
@is_logged_in
def addTrainor():
	choices.clear()
	cur = mysql.connection.cursor()
	
	q = cur.execute("SELECT name FROM centre")
	b = cur.fetchall()
	for i in range(q):
		choices.append(b[i]['name'])
	cur.close()

	form = AddTrainorForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		street = form.street.data
		centre = form.centre.data
		phone = form.phone.data
		trainer_id = form.trainer_id.data
		cur = mysql.connection.cursor()
		cur.execute("SELECT centre_id FROM centre where name = %s",[centre])
		a=cur.fetchone()
		print(centre)
		x=a['centre_id']
		print(x)
		q=cur.execute("SELECT name FROM trainer where trainer_id = %s",[trainer_id])
		if q>0:
			flash('Duplicate trainer Id,rectify!!','danger')
			return redirect(url_for('addTrainor'))
		cur.execute("INSERT INTO trainer(trainer_id, name, centre_id, street, mobile) VALUES(%s, %s, %s, %s, %s)", (trainer_id, name, x, street, phone))
		mysql.connection.commit()
		cur.close()
		flash('You recruited a new Trainor!!', 'success')
		return redirect(url_for('adminDash'))
	return render_template('addTrainor.html', form=form)

class AddMemberForm(Form):
    username = StringField('Username', [validators.InputRequired(), validators.NoneOf(values = values, message = "Username already taken, Please try another")])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')
    membership_no = IntegerField('Membership No.',[validators.NumberRange(min = 9999, max = 100001)] )
    
@app.route('/addMember', methods = ['GET', 'POST'])
@is_logged_in
def addMember():
	choices.clear()
	cur = mysql.connection.cursor()
	form = AddMemberForm(request.form)
	if request.method == 'POST' and form.validate():
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data))
		membership_no = form.membership_no.data
		q=cur.execute("SELECT username FROM member where membership_no = %s",[membership_no])
		if q>0:
			flash('Duplicate Membership No,rectify!!','danger')
			return redirect(url_for('addMember'))
		cur.execute("INSERT INTO member(username, password, membership_no) VALUES(%s, %s, %s)", (username, password,membership_no))
		mysql.connection.commit()
		cur.close()
		choices.clear()
		flash('You added a new member!!', 'success')
		if(session['prof']==1):
			return redirect(url_for('adminDash'))
	return render_template('addMember.html', form=form)

goals_list =['Weight Loss', 'Muscle Gain', 'Stamina Building', 'Flexibility']

class fillDetailsForm(Form):
	f_name = StringField('First Name', [validators.Length(min = 1, max = 100)])
	l_name = StringField('Last Name', [validators.Length(min = 1, max = 1001)])
	start_date = DateField('Start Date', format='%Y-%m-%d')
	no_of_days =IntegerField('No. of Days', [validators.NumberRange(min = 1, max = 1000)])
	goals = SelectField('Select main goal', choices = goals_list)
	centre = SelectField('Select Centre', choices = choices)
	mobile_no = StringField('Contact No.', [validators.Length(min = 1, max = 100)])


@app.route('/fillDetails', methods = ['GET', 'POST'])
@is_logged_in
def fillDetails():
	choices.clear()
	cur = mysql.connection.cursor()
	
	q = cur.execute("SELECT name FROM centre")
	b = cur.fetchall()
	for i in range(q):
		choices.append(b[i]['name'])
	cur.close()

	form = fillDetailsForm(request.form)
	if request.method == 'POST' and form.validate():
		l_name = form.l_name.data
		f_name = form.f_name.data
		start_date = form.start_date.data
		centre = form.centre.data
		mobile_no = form.mobile_no.data
		goals = form.goals.data
		no_of_days = form.no_of_days.data
		cur = mysql.connection.cursor()
		cur.execute("SELECT centre_id FROM centre where name = %s",[centre])
		a=cur.fetchone()
		print(centre)
		x=a['centre_id']
		print(x)
		cur.execute("UPDATE member SET f_name = %s, l_name = %s, mobile_no = %s, start_date = %s, no_of_days = %s, goals = %s, centre_id = %s WHERE username = %s", (f_name, l_name, mobile_no, start_date, no_of_days, goals, x, session['username']))
		mysql.connection.commit()
		cur.close()
		print('yes')
		return redirect(url_for('fillDetails2'))
		print('yes')
	return render_template('fillDetails.html',form=form)

class fillDetails2Form(Form):
	name = SelectField('Select Trainer', choices = choices)
	time = SelectField('Select Time', choices = values)

@app.route('/fillDetails2', methods = ['GET', 'POST'])
@is_logged_in
def fillDetails2():
	choices.clear()
	values.clear()
	cur = mysql.connection.cursor()
	a=session['username']
	cur.execute("SELECT centre_id FROM member where username = %s",[a])
	b=cur.fetchone()
	c=b['centre_id']
	print(b)
	q=cur.execute("SELECT name FROM trainer where centre_id = %s",[c])
	b = cur.fetchall()
	l = b
	for i in range(q):
		g=b[i]['name']
		choices.append(g)
	result1=()
	q=cur.execute("select w.trainer_id,w.batch_id from trainer t,workduring w where w.trainer_id=t.trainer_id and t.centre_id = %s",[c])
	r=cur.fetchall()
	for i in range(q):
		r1=r[i]['trainer_id']
		cur.execute("SELECT name FROM trainer WHERE trainer_id = %s",[r1])
		t=cur.fetchone()
		g=t['name']
		#choices.append(g)
		#cur.execute("SELECT trainer_id FROM trainer WHERE name = %s",[g])
		#r=cur.fetchone()
		#cur.execute("SELECT batch_id FROM workduring WHERE trainer_id = %s",[r1])
		#s=cur.fetchone()
		s1=r[i]['batch_id']
		cur.execute("SELECT time FROM timeslots WHERE batch_id = %s",[s1])
		t=cur.fetchone()
		t1=t['time']
		cur.execute("select avg(rating) as value_avg from quality where trainer_id = %s;",[r1])
		u=cur.fetchone()
		u1=u['value_avg']
		print(u1)
		result2=list(result1)
		result3={'name': g,'time': t1,'rate': u1}
		result2.append(result3)
		result1=tuple(result2)
	q1=cur.execute("SELECT time FROM timeslots")
	b1 = cur.fetchall()
	for i in range(q1):
		values.append(b1[i]['time'])
	cur.close()
	if len(choices)==0:
		flash('No Trainer!!','danger')
		return redirect(url_for('fillDetails'))
	form = fillDetails2Form(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		time = form.time.data
		cur = mysql.connection.cursor()
		cur.execute("SELECT trainer_id FROM trainer where name = %s",[name])
		a=cur.fetchone()
		x=a['trainer_id']
		cur.execute("SELECT batch_id FROM timeslots where time = %s",[time])
		a=cur.fetchone()
		y=a['batch_id']
		q=cur.execute("SELECT batch_id FROM workduring where trainer_id = %s AND batch_id = %s",(x,y))
		if q==0:
			flash('No such class,rectify!!','danger')
			return redirect(url_for('fillDetails2'))
		cur.execute("UPDATE member SET trainer_id = %s, batch_id = %s WHERE username = %s", (x, y, session['username']))
		mysql.connection.commit()
		cur.close()
		print('yes')
		return redirect(url_for('memberDash'))
		print('yes')
	return render_template('fillDetails2.html',form=form,progress=result1)

class AddScheduleForm(Form):
	name = SelectField('Select Trainer', choices = values)
	time = SelectField('Select Timeslot', choices = choices)


@app.route('/addSchedule', methods = ['GET', 'POST'])
@is_logged_in
def addSchedule():
	values.clear()
	choices.clear()
	cur = mysql.connection.cursor()
	
	q = cur.execute("SELECT name FROM trainer")
	b = cur.fetchall()
	for i in range(q):
		values.append(b[i]['name'])

	q = cur.execute("SELECT time FROM timeslots")
	b = cur.fetchall()
	for i in range(q):
		choices.append(b[i]['time'])
	cur.close()

	form = AddScheduleForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		time = form.time.data
		print(name)
		print(time)
		cur = mysql.connection.cursor()
		cur.execute("SELECT trainer_id FROM trainer WHERE name = %s",[name])
		a=cur.fetchone()
		x=a['trainer_id']
		c = cur.execute("SELECT batch_id FROM timeslots WHERE time = %s",[time])
		a=cur.fetchone()
		y=a['batch_id']
		q=cur.execute("SELECT trainer_id FROM workduring where trainer_id = %s AND batch_id = %s",(x,y))
		if q>0:
			flash('Class already exists!!','danger')
			return redirect(url_for('addSchedule'))
		cur.execute("INSERT INTO workduring(trainer_id, batch_id) VALUES(%s, %s)", (x,y))
		mysql.connection.commit()
		cur.close()
		flash('You added a new class', 'success')
		return redirect(url_for('adminDash'))
	return render_template('addSchedule.html', form=form)

class AddCentreForm(Form):
	name = StringField('Name', [validators.Length(min = 1, max = 100)])
	centre_id = IntegerField('Centre id', [validators.NumberRange(min = 0, max = 10)])
	location = StringField('Location', [validators.Length(min = 1, max = 100)])
	contact_no = StringField('Contact No.', [validators.Length(min = 1, max = 100)])


@app.route('/addCentre', methods = ['GET', 'POST'])
@is_logged_in
def addCentre():
	form = AddCentreForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		location = form.location.data
		contact_no = form.contact_no.data
		centre_id = form.centre_id.data
		cur = mysql.connection.cursor()
		q=cur.execute("SELECT name FROM centre where centre_id = %s",[centre_id])
		if q>0:
			flash('Duplicate Centre Id,rectify!!','danger')
			return redirect(url_for('addCentre'))
		cur.execute("INSERT INTO centre(centre_id, name, location, contact_no) VALUES(%s, %s, %s, %s)", (centre_id, name, location, contact_no))
		mysql.connection.commit()
		cur.close()
		flash('You added a new Centre!!', 'success')
		return redirect(url_for('adminDash'))
	return render_template('addCentre.html', form=form)


class DeleteTrainorForm(Form):
	name = SelectField(u'Choose which one you wanted to delete', choices=choices)

@app.route('/deleteTrainor', methods = ['GET', 'POST'])
@is_logged_in
def deleteTrainor():
	choices.clear()
	cur = mysql.connection.cursor()
	q = cur.execute("SELECT name FROM trainer")
	b = cur.fetchall()
	for i in range(q):
		tup = (b[i]['name'],b[i]['name'])
		print(tup)
		choices.append(tup)
	form = DeleteTrainorForm(request.form)
	if len(choices)==1:
		flash('You cannot remove your only Trainer!!', 'danger')
		return redirect(url_for('adminDash'))
	if request.method == 'POST':
		#app.logger.info(form.username.data)
		name = form.name.data
		cur.execute("SELECT trainer_id FROM trainer where name = %s", [name])
		b = cur.fetchone()
		x=b['trainer_id']
		cur.execute("SELECT centre_id FROM trainer where name = %s", [name])
		b = cur.fetchone()
		j=b['centre_id']
		q=cur.execute("SELECT w.trainer_id FROM workduring w,trainer t WHERE t.trainer_id=w.trainer_id AND t.centre_id = %s  AND w.trainer_id != %s",(j,x))
		if q==0:
			flash('You cannot remove your only working Trainer!!', 'success')
			return redirect(url_for('adminDash'))
		cur.execute("DELETE FROM workduring WHERE trainer_id = %s", [x])
		q = cur.execute("SELECT membership_no FROM member WHERE trainer_id = %s",[x])
		b = cur.fetchall()
		q11=cur.execute("SELECT w.trainer_id FROM workduring w,trainer t WHERE t.trainer_id=w.trainer_id AND t.centre_id = %s",[j])
		b11=cur.fetchone()
		x11=b11['trainer_id']
		q2=cur.execute("SELECT batch_id FROM workduring where trainer_id = %s",[x11])
		b12=cur.fetchone()
		x12=b12['batch_id']
		for i in range(q):
			y=b[i]['membership_no']
			r=cur.execute("SELECT batch_id FROM member WHERE membership_no = %s",[y])
			r1=cur.fetchone()
			z=r1['batch_id']
			q1=cur.execute("SELECT w.trainer_id FROM workduring w,trainer t WHERE t.trainer_id=w.trainer_id AND t.centre_id = %s AND w.batch_id = %s",(j,z))
				
			if q1>0:
				b1= cur.fetchone()
				x1=b1['trainer_id']
				cur.execute("UPDATE member SET trainer_id = %s WHERE membership_no = %s", ([x1],[y]))
			else:
				cur.execute("UPDATE member SET trainer_id = %s WHERE membership_no = %s", ([x11],[y]))
				cur.execute("UPDATE member SET batch_id = %s WHERE membership_no = %s", ([x12],[y]))		

		cur.execute("DELETE FROM quality WHERE trainer_id = %s", [x])
		cur.execute("DELETE FROM trainer WHERE trainer_id = %s", [x])
		mysql.connection.commit()
		cur.close()
		choices.clear()
		flash('You removed your Trainer!!', 'success')
		return redirect(url_for('adminDash'))
	return render_template('deleteTrainer.html', form = form)

class DeleteScheduleForm(Form):
	name = SelectField(u'Choose which one you wanted to delete', choices=choices)
	time = SelectField(u'Choose which one you wanted to delete', choices=values)

@app.route('/deleteSchedule', methods = ['GET', 'POST'])
@is_logged_in
def deleteSchedule():
	choices.clear()
	values.clear()
	cur = mysql.connection.cursor()
	q = cur.execute("SELECT DISTINCT trainer_id FROM workduring")
	b = cur.fetchall()
	for i in range(q):
		l=b[i]['trainer_id']
		r = cur.execute("SELECT name FROM trainer WHERE trainer_id = %s",[l])
		r1=cur.fetchone()
		choices.append(r1['name'])
	q1 = cur.execute("SELECT DISTINCT batch_id FROM workduring")
	b1 = cur.fetchall()
	for i in range(q1):
		m=b1[i]['batch_id']
		s = cur.execute("SELECT time FROM timeslots WHERE batch_id = %s",[m])
		s1=cur.fetchone()
		values.append(s1['time'])
	form = DeleteScheduleForm(request.form)
	name=form.name.data
	time=form.time.data
	if len(values)==1 and len(choices)==1:
		flash('You cannot remove your only Class!!', 'danger')
		return redirect(url_for('adminDash'))
	if request.method == 'POST':
		cur.execute("SELECT trainer_id FROM trainer where name = %s", [name])
		c=cur.fetchone()
		trainer_id=c['trainer_id']
		cur.execute("SELECT batch_id FROM timeslots where time = %s", [time])
		c2=cur.fetchone()
		batch_id=c2['batch_id']
		q4 = cur.execute("SELECT trainer_id FROM workduring WHERE trainer_id = %s AND batch_id = %s",(trainer_id,batch_id))
		b4 = cur.fetchall()
		if q4==0:
			flash('No such Class!!', 'danger')
			return redirect(url_for('deleteSchedule'))
		cur.execute("DELETE FROM workduring WHERE trainer_id = %s AND batch_id = %s", (trainer_id,batch_id))
		q3 = cur.execute("SELECT membership_no FROM member WHERE trainer_id = %s AND batch_id = %s",(trainer_id,batch_id))
		b3 = cur.fetchall()
		q11=cur.execute("SELECT trainer_id FROM workduring")
		b11=cur.fetchone()
		x11=b11['trainer_id']
		q2=cur.execute("SELECT batch_id FROM workduring where trainer_id = %s",[x11])
		b12=cur.fetchone()
		x12=b12['batch_id']
		for i in range(q3):
			y=b3[i]['membership_no']
			q1=cur.execute("SELECT trainer_id FROM workduring WHERE batch_id = %s",[batch_id])
				
			if q1>0:
				b1= cur.fetchone()
				x1=b1['trainer_id']
				cur.execute("UPDATE member SET trainer_id = %s WHERE membership_no = %s", ([x1],[y]))
			else:
				cur.execute("UPDATE member SET trainer_id = %s WHERE membership_no = %s", ([x11],[y]))
				cur.execute("UPDATE member SET batch_id = %s WHERE membership_no = %s", ([x12],[y]))		

		
		mysql.connection.commit()
		cur.close()
		choices.clear()
		flash('You removed your class!!', 'success')
		return redirect(url_for('adminDash'))
	return render_template('deleteSchedule.html', form = form)

@app.route('/viewTrainerDetails')
def viewTrainerDetails():
	cur = mysql.connection.cursor()
	cur.execute("SELECT name FROM trainer")
	result = cur.fetchall()
	print(result)
	return render_template('viewTrainerDetails.html', result = result)

class DeleteMemberForm(Form):
	username = SelectField(u'Choose which one you wanted to delete', choices=choices)
@app.route('/deleteMember', methods = ['GET', 'POST'])
@is_logged_in
def deleteMember():
	choices.clear()
	cur = mysql.connection.cursor()
	q = cur.execute("SELECT username FROM member")
	b = cur.fetchall()
	for i in range(q):
		tup = (b[i]['username'],b[i]['username'])
		choices.append(tup)
	form = DeleteMemberForm(request.form)
	if request.method == 'POST':
		username = form.username.data
		cur = mysql.connection.cursor()
		q = cur.execute("SELECT membership_no FROM member where username = %s", [username])
		b = cur.fetchone()
		print("Hello1")
		membership_no=b['membership_no']
		cur.execute("DELETE FROM quality WHERE membership_no = %s", ([membership_no]))
		cur.execute("DELETE FROM progress WHERE membership_no = %s", ([membership_no]))
		cur.execute("DELETE FROM member WHERE username = %s", [username])
		mysql.connection.commit()
		cur.close()
		choices.clear()
		flash('You deleted a member from the GYM!!', 'success')
		if(session['prof']==1):
			return redirect(url_for('adminDash'))
		return redirect(url_for('recepDash'))
	return render_template('deleteRecep.html', form = form)

@app.route('/memberDash')
@is_logged_in
def memberDash():
	cur = mysql.connection.cursor()
	q = cur.execute("SELECT membership_no FROM member where username = %s", [session['username']])
	b = cur.fetchone()
	print("Hello1")
	membership_no=b['membership_no']
	a=cur.execute("SELECT date, weight, height, bmi FROM progress where membership_no = %s", [membership_no])
	print("Hello2")
	result = cur.fetchall()	
	for i in range(a):
		if result[i]['bmi']<18.5:
			result[i]['status'] = 'underweight'
		elif result[i]['bmi']>18.5 and result[i]['bmi']<25:
			result[i]['status']='normal'
		elif result[i]['bmi']>=25 and result[i]['bmi']<30:
			result[i]['status']='overweight'
		else:
			result[i]['status']='obese'

	return render_template('memberDash.html', result = result)


@app.route('/attendance', methods = ['GET', 'POST'])
@is_logged_in
def attendance():
	cur = mysql.connection.cursor()
	result = cur.execute('SELECT date FROM member WHERE username = %s', [session['username']])
	result1=cur.fetchone()
	result2=result1['date']
	today=datetime.date(datetime.now())
	print(today)
	if result2==today:
		print('yes1')
		flash('Already marked for the day!!', 'danger')
		return redirect(url_for('memberDash'))
	else:
		cur.execute("UPDATE member SET date = %s WHERE username = %s", ([today], [session['username']]))
		result = cur.execute('SELECT no_of_days FROM member WHERE username = %s', [session['username']])
		b = cur.fetchone()
		result2 = b['no_of_days']
		print(result2)
		result3 = result2-1
		if result3>0:
			cur.execute("UPDATE member SET no_of_days = %s WHERE username = %s", ([result3], [session['username']]))
			mysql.connection.commit()
			cur.close()
			print('yes')
			flash('Attendance marked for the day!!', 'success')
			return render_template('memberDash.html')
		else:
			q = cur.execute("SELECT membership_no FROM member where username = %s", [session['username']])
			b = cur.fetchone()
			print("Hello1")
			membership_no=b['membership_no']
			cur.execute("DELETE FROM quality WHERE membership_no = %s", ([membership_no]))
			cur.execute("DELETE FROM progress WHERE membership_no = %s", ([membership_no]))
			cur.execute("DELETE FROM member WHERE username = %s", ([session['username']]))
			mysql.connection.commit()
			cur.close()
			session.clear()
			flash('Your plan is over!!', 'danger')
			return redirect(url_for('login'))
		return redirect(url_for('memberDash'))
	return render_template('memberDash.html')
	

@app.route('/profile1/<string:username>')
@is_logged_in
def profile1(username):
	if username == session['username'] and session['prof']==1:
		cur = mysql.connection.cursor()
		cur.execute("SELECT * FROM admin WHERE username = %s", [username])
		result = cur.fetchone()
		q = cur.execute("SELECT name FROM centre WHERE centre_id = %s", [result['centre_id']])
		b = cur.fetchone()
		result['centre_id'] = b['name']
		return render_template('profile1.html', result = result)
	flash('You cannot view other\'s profile', 'warning')
	if session['prof']==1:
		return redirect(url_for('adminDash'))
	return redirect(url_for('adminDash', username = username))

@app.route('/profile2/<string:name>', methods = ['GET', 'POST'])
@is_logged_in
def profile2(name):
	cur = mysql.connection.cursor()
	cur.execute("SELECT * FROM trainer WHERE name = %s", [name])
	result = cur.fetchone()
	print(name)
	q = cur.execute("SELECT name FROM centre WHERE centre_id = %s", [result['centre_id']])
	b = cur.fetchone()
	result['centre_id'] = b['name']
	return render_template('profile2.html', result = result)
	
@app.route('/profile3/<string:username>', methods = ['GET', 'POST'])
@is_logged_in
def profile3(username):
	cur = mysql.connection.cursor()
	cur.execute("SELECT * FROM member WHERE username = %s", [username])
	result = cur.fetchone()
	q = cur.execute("SELECT name FROM trainer WHERE trainer_id = %s", [result['trainer_id']])
	if q!=0:
		b = cur.fetchone()
		result['trainer_id'] = b['name']
		q = cur.execute("SELECT time FROM timeslots WHERE batch_id = %s", [result['batch_id']])
		b = cur.fetchone()
		result['batch_id'] = b['time']	
	
	return render_template('profile3.html', result = result)

@app.route('/profileCentre/<string:name>', methods = ['GET', 'POST'])
@is_logged_in
def profileCentre(name):
	cur = mysql.connection.cursor()
	cur.execute("SELECT * FROM centre WHERE name = %s", [name])
	result = cur.fetchone()
	return render_template('profileCentre.html', result = result)

class ChangePasswordForm(Form):
	old_password = PasswordField('Existing Password')
	new_password = PasswordField('Password', [
		validators.DataRequired(),
		validators.EqualTo('confirm', message = 'Passwords aren\'t matching pal!, check \'em')
	])
	confirm = PasswordField('Confirm Password')


@app.route('/update_password/<string:username>', methods = ['GET', 'POST'])
def update_password(username):
	form = ChangePasswordForm(request.form)
	if request.method == 'POST' and form.validate():
		new = form.new_password.data
		entered = form.old_password.data
		if session['prof']==1:
			cur = mysql.connection.cursor()
			cur.execute("SELECT password FROM admin WHERE username = %s", [username])
			old = (cur.fetchone())['password']
			if sha256_crypt.verify(entered, old):
				cur.execute("UPDATE admin SET password = %s WHERE username = %s", (sha256_crypt.encrypt(new), username))
				mysql.connection.commit()
				cur.close()
				flash('New password will be in effect from next login!!', 'info')
				return redirect(url_for('adminDash', username = session['username']))
			cur.close()
			flash('Old password you entered is wrong!!, try again', 'warning')
		if session['prof']==2:
			cur = mysql.connection.cursor()
			cur.execute("SELECT password FROM member WHERE username = %s", [username])
			old = (cur.fetchone())['password']
			if sha256_crypt.verify(entered, old):
				cur.execute("UPDATE member SET password = %s WHERE username = %s", (sha256_crypt.encrypt(new), username))
				mysql.connection.commit()
				cur.close()
				flash('New password will be in effect from next login!!', 'info')
				return redirect(url_for('memberDash', username = session['username']))
			cur.close()
			flash('Old password you entered is wrong!!, try again', 'warning')
		return render_template('updatePassword.html', form = form)
	return render_template('updatePassword.html', form = form)

class EditForm(Form):
    f_name = StringField('First Name', [validators.Length(min=1, max=50)])
    l_name = StringField('Last Name', [validators.Length(min = 1, max = 100)])
    goals = SelectField('Select main goal', choices = goals_list)
    mobile_no = StringField('Contact No.', [validators.Length(min = 1, max = 100)])

@app.route('/edit_profile/<string:username>', methods = ['GET', 'POST'])
@is_logged_in
def edit_profile(username):
	cur = mysql.connection.cursor()
	cur.execute("SELECT * FROM member WHERE username = %s", [username])
	result = cur.fetchone()
	print(result)
	form = EditForm(request.form)
	print(result)
	form.f_name.data = result['f_name']
	form.l_name.data = result['l_name']
	form.goals.data = result['goals']
	form.mobile_no.data = result['mobile_no']
	cur.close()
	print(result)
	if request.method == 'POST' and form.validate():
		print(result)
		#app.logger.info("setzdgxfhcgjvkhbjlkn")
		f_name = request.form['f_name']
		l_name =  request.form['l_name']
		goals =  request.form['goals']
		mobile_no =  request.form['mobile_no']
		#app.logger.info(name)
		#app.logger.info(street)
		#app.logger.info(city)
		print(result)
		cur = mysql.connection.cursor()

		q = cur.execute("UPDATE member SET f_name = %s, l_name = %s, goals = %s, mobile_no = %s WHERE username = %s", (f_name, l_name, goals, mobile_no, username))
		#app.logger.info(q)
		mysql.connection.commit()
		cur.close()
		flash('You successfully updated your profile!!', 'success')
		if session['prof']==2:
			return redirect(url_for('memberDash', username = username))
		return render_template('edit_profile.html', form=form)
	return render_template('edit_profile.html', form=form)



@app.route('/viewMemberDetails', methods = ['GET', 'POST'])
def viewMemberDetails():
	cur = mysql.connection.cursor()
	cur.execute("SELECT username FROM member")
	result = cur.fetchall()
	return render_template('viewMemberDetails.html', result = result)

@app.route('/viewCentreDetails', methods = ['GET', 'POST'])
def viewCentreDetails():
	cur = mysql.connection.cursor()
	cur.execute("SELECT name FROM centre")
	result = cur.fetchall()
	return render_template('viewCentreDetails.html', result = result)

@app.route('/viewScheduleDetails')
def viewScheduleDetails():
	choices.clear()
	cur = mysql.connection.cursor()
	q=cur.execute("SELECT * FROM workduring")
	result = cur.fetchall()
	print(result)
	result1=[]
	for i in range(q):
		result2={}
		a=result[i]['trainer_id']
		cur.execute("SELECT name FROM trainer WHERE trainer_id = %s",[a])
		r=cur.fetchone()
		result2['name']=r['name']
		b=result[i]['batch_id']
		cur.execute("SELECT time FROM timeslots WHERE batch_id = %s",[b])
		s=cur.fetchone()
		result2['time']=s['time']
		cur.execute("SELECT c.name cname FROM centre c, trainer t WHERE c.centre_id=t.centre_id and trainer_id = %s",[a])
		s=cur.fetchone()
		result2['cname']=s['cname']
		result1.append(result2)
	return render_template('viewScheduleDetails.html', result = result1)

class FeedbackForm(Form):
	report = StringField('Descriptive Feedback', [validators.InputRequired()])
	rate = RadioField('Rating', choices = [('good', 'good'),('average', 'average'),('poor', 'poor') ])


@app.route('/feedback', methods = ['GET', 'POST'])
@is_logged_in
def feedback():
	cur = mysql.connection.cursor()
	q = cur.execute("SELECT trainer_id FROM member WHERE username = %s", [session['username']])
	b = cur.fetchone()
	trainer_id=b['trainer_id']
	q = cur.execute("SELECT membership_no from member where username = %s", [session['username']])
	b = cur.fetchone()
	membership_no=b['membership_no']
	cur.close()

	form = FeedbackForm(request.form)

	if request.method == 'POST':
		report = form.report.data
		rate = form.rate.data
		if rate == 'good':
			rate = 3
		elif rate == 'average':
			rate = 2
		else:
			rate = 1
		
		cur = mysql.connection.cursor()
		p = cur.execute("SELECT rating from quality WHERE membership_no = %s",[membership_no])
		
		if p!=0:
			cur.execute("UPDATE quality SET rating = %s, description = %s WHERE membership_no = %s", (rate, report, membership_no))
			mysql.connection.commit()
			cur.close()
			choices.clear()
			flash('Succesfully updated!', 'success')
			return redirect(url_for('memberDash'))
		else:
			cur.execute("INSERT into quality(membership_no,trainer_id,rating,description) VALUES(%s, %s, %s, %s)", (membership_no,trainer_id,rate, report ))
			mysql.connection.commit()
			cur.close()
			choices.clear()
			flash('Succesfully inserted!', 'success')
			return redirect(url_for('memberDash'))
	return render_template('feedback.html',form=form)

class ProgressForm(Form):
	weight = IntegerField('Weight in kg', [validators.NumberRange(min = 0, max = 400)])
	height = IntegerField('Height in cm', [validators.NumberRange(min = 0, max = 300)])

@app.route('/progress', methods = ['GET', 'POST'])
def progress():
	cur = mysql.connection.cursor()
	q = cur.execute("SELECT membership_no FROM member where username = %s", [session['username']])
	b = cur.fetchone()
	membership_no=b['membership_no']
	result = cur.execute('SELECT date FROM progress WHERE membership_no = %s', [membership_no])
	result1=cur.fetchall()
	if result!=0:
		result2=result1[-1]['date']
		today1=datetime.date(datetime.now())
		#print(today)
		if result2==today1:
			print('yes1')
			flash('Already marked for the day!!', 'danger')
			return redirect(url_for('memberDash'))
	cur.close()
	form = ProgressForm(request.form)
	print(form.weight.data, form.height.data)
	cur = mysql.connection.cursor()
	today=datetime.date(datetime.now())
	print(today)
	if request.method == 'POST' and form.validate():
		weight = form.weight.data
		height = form.height.data
		bmi=(weight/(height*height))*10000
		cur.execute("INSERT INTO progress(membership_no, date, weight, height, bmi) VALUES(%s, %s, %s, %s, %s)", (membership_no, today, weight, height, bmi))
		mysql.connection.commit()
		cur.close()
		return redirect(url_for('memberDash'))
	return render_template('progress.html',form=form)

@app.route('/logout')
@is_logged_in
def logout():
	session.clear()
	flash('You are now logged out', 'success')
	return redirect(url_for('login'))

app.secret_key = '528491@JOKER'
app.run(debug=True)    
