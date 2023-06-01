from flask import Flask, render_template, request, redirect, url_for, session, abort, flash
import mysql.connector, time, datetime, helper

#Flask Setup
app = Flask(__name__)
app.secret_key = 'c6dca54943a50a565248f7329617aeb7'  # secret key for session management


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
        error_message = None
        running = helper.ps(session['username'])[0]
        containers = helper.ps(session['username'])[1]
        ports = helper.used_minecraft_ports()
        log_entry(request.remote_addr, request.method + " " + request.url, 200)
        return render_template('containers.html', running = running, containers = containers, ports = ports)
    else:
        log_entry(request.remote_addr, request.method + " " + request.url, 401)
        return abort(401, 'You are not authorized to access this page!')

@app.route('/start-container', methods=['POST'])
def start_container():
    if 'loggedin' in session:
        container_name = request.form['start']
        if helper.port_in_use(eval(helper.ps(session['username'])[1][container_name]['port'])):
            flash('This port is already in use!')
            return redirect(url_for('containers'))
        helper.start(session['username'], container_name)
        time.sleep(1) #wait till the server was started
        log_entry(request.remote_addr, request.method + " " + request.url, 302)
        return redirect(url_for('containers'))
    else:
        log_entry(request.remote_addr, request.method + " " + request.url, 403)
        return abort(403)

@app.route('/stop-container', methods=['POST'])
def stop_container():
    if 'loggedin' in session:
        container_name = request.form['stop']
        helper.stop(session['username'], container_name)
        time.sleep(1) #wait till the server was stopped
        log_entry(request.remote_addr, request.method + " " + request.url, 302)
        return redirect(url_for('containers'))
    else:
        log_entry(request.remote_addr, request.method + " " + request.url, 403)
        return abort(403)

@app.route('/reset', methods=['POST'])
def reset_container():
    if 'loggedin' in session:
        container_name = request.form['reset']
        helper.reset(session['username'], session['temp_data'], container_name)
        log_entry(request.remote_addr, request.method + " " + request.url, 302)
        return redirect(url_for('containers'))
    else:
        log_entry(request.remote_addr, request.method + " " + request.url, 403)
        return abort(403)

@app.route('/remove', methods=['POST'])
def remove_container():
    if 'loggedin' in session:
        container_name = request.form['remove']
        helper.remove(session['username'], session['temp_data'], container_name)
        log_entry(request.remote_addr, request.method + " " + request.url, 302)
        return redirect(url_for('containers'))
    else:
        log_entry(request.remote_addr, request.method + " " + request.url, 403)
        return abort(403)

@app.route('/exec', methods=['POST'])
def execute():
    if 'loggedin' in session:
        command = request.form['command']
        container = request.form['container_name']
        helper.exec(session['username'], container, command)
        log_entry(request.remote_addr, request.method + " " + request.url, 302)
        return redirect(url_for('containers'))
    else:
        log_entry(request.remote_addr, request.method + " " + request.url, 403)
        return abort(403)        

@app.route('/create', methods=['POST', 'GET'])
def create():
    if 'loggedin' in session:
        if request.method == 'GET':
            log_entry(request.remote_addr, request.method + " " + request.url, 200)
            return render_template('create.html', username=session['username'])
        if request.method == 'POST':
            user = session['username']
            name = request.form['name']
            port = request.form['port']
            path = session['temp_data']
            version = request.form['version']
            mode = request.form['mode']
            memory = request.form['memory']
            Type = request.form['type']
            motd = request.form['motd']
            status = helper.create(user, name, port, path, mode, version, memory, Type, motd)
            time.sleep(1)
            if status == 'error':
                return "There was an error while creating the new server. Please check all your options! (name, version and memory especially)"
            log_entry(request.remote_addr, request.method + " " + request.url, 302)
            return redirect(url_for('containers'))
    else:
        log_entry(request.remote_addr, request.method + " " + request.url, 401)
        return abort(401, 'You are not authorized to access this page!')



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
    from waitress import serve
    serve(app, host="0.0.0.0", port=8569)
