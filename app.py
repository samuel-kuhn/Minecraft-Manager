from flask import Flask, render_template, request, redirect, url_for, session, abort
import mysql.connector, docker_helper, time, datetime

#Flask Setup
app = Flask(__name__)
app.secret_key = 'c6dca54943a50a565248f7329617aeb7'  # secret key for session management

#Docker Setup

#DB Setup
db = mysql.connector.connect(
  host="172.20.0.12",
  user="root",
  password="5PMcMRb79q",
  database="monitor"
)


#Database functions
def get_user(user):
    cursor = db.cursor()
    query = "SELECT * FROM users where name = %s"
    cursor.execute(query, (user,))
    return cursor.fetchone()

def log_entry(ip_address, request, response_status):
    cursor = db.cursor()
    timestamp = datetime.datetime.now()    
    sql = "INSERT INTO logs (ip_address, timestamp, request, response_status) VALUES (%s, %s, %s, %s)"
    values = (ip_address, timestamp, request, response_status)
    cursor.execute(sql, values)
    db.commit()

#Routes
@app.route('/')
def home():
    if 'loggedin' in session:
        log_entry(request.remote_addr, request.method + " " + url_for('dashboard'), 200)
        return redirect(url_for('dashboard'))

    else:
        log_entry(request.remote_addr, request.method + " " + request.url, 302)
        return redirect(url_for('login'))

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        db_user = get_user(username)
        if db_user is not None and db_user[2] == password:
            session['loggedin'] = True
            session['id'] = db_user[0]
            session['username'] = db_user[1]
            session['temp_data'] = db_user[3] #the path to the containers
            log_entry(request.remote_addr, request.method + " " + request.url, 302)
            return redirect(url_for('dashboard'))
        else:
            log_entry(request.remote_addr, request.method + " " + request.url, 200)
            return render_template('login.html', error_message='Invalid username or password.')
    else:
        log_entry(request.remote_addr, request.method + " " + request.url, 200)
        return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        log_entry(request.remote_addr, request.method + " " + request.url, 200)
        return render_template('dashboard.html', username=session['username'])
    else:
        log_entry(request.remote_addr, request.method + " " + request.url, 401)
        return abort(401, 'You are not authorized to access this page!')

@app.route('/containers')
def containers():
    if 'loggedin' in session:
        running = docker_helper.ps(session['temp_data'])
        containers = docker_helper.list(session['temp_data'])
        log_entry(request.remote_addr, request.method + " " + request.url, 200)
        return render_template('containers.html', running = running, containers = containers)
    else:
        log_entry(request.remote_addr, request.method + " " + request.url, 401)
        return abort(401, 'You are not authorized to access this page!')

@app.route('/start-container', methods=['POST'])
def start_container():
    if 'loggedin' in session:
        container = request.form['start']
        folder = docker_helper.list(session['temp_data'])[container]['folder']
        docker_helper.up(folder)
        time.sleep(1) #wait till the server was started
        log_entry(request.remote_addr, request.method + " " + request.url, 302)
        return redirect(url_for('containers'))
    else:
        log_entry(request.remote_addr, request.method + " " + request.url, 403)
        return abort(403)

@app.route('/stop-container', methods=['POST'])
def stop_container():
    if 'loggedin' in session:
        container = request.form['stop']
        folder = docker_helper.list(session['temp_data'])[container]['folder']
        docker_helper.down(folder)
        time.sleep(1) #wait till the server was stopped
        log_entry(request.remote_addr, request.method + " " + request.url, 302)
        return redirect(url_for('containers'))
    else:
        log_entry(request.remote_addr, request.method + " " + request.url, 403)
        return abort(403)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('temp_data', None)
    # Redirect to login page
    log_entry(request.remote_addr, request.method + " " + request.url, 302)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8888) # 0.0.0.0 meaning every ip

