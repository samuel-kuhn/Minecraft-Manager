from flask import Flask, render_template, request, redirect, url_for, session, abort, flash
import mysql.connector, time, json, helper


#Flask Setup
app = Flask(__name__)
app.secret_key = 'efb10f7d3a69bee06eb1b943c0cce5dd'  # change this key!!!
app.config['PREFERRED_URL_SCHEME'] = 'https'

#User File
with open('users.json', 'r') as file:
    user_array = json.load(file)

#Functions
def get_user(username):
    return user_array[username]

def get_path(username):
    return get_user(username)['path']

def get_ports(username):
    ports_str = get_user(username)['ports']
    return ports_str.split(',')

#Routes
@app.route('/')
def home():
    if 'loggedin' in session:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        user = get_user(username)
        if user is not None and user['password'] == password:
            session['loggedin'] = True
            session['id'] = user['id']
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error_message='Invalid username or password.')
    else:
        return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        return render_template('dashboard.html', username=session['username'])
    else:
        return abort(401, 'You are not authorized to access this page!')

@app.route('/containers')
def containers():
    if 'loggedin' in session:
        error_message = None
        running = helper.ps(session['username'])[0]
        containers = helper.ps(session['username'])[1]
        ports = get_ports(session['username'])
        first = ports[0]
        last = ports[len(ports)-1]
        return render_template('containers.html', running = running, containers = containers, ports = ports, first=int(first), last=int(last))
    else:
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
        return redirect(url_for('containers'))
    else:
        return abort(403)

@app.route('/stop-container', methods=['POST'])
def stop_container():
    if 'loggedin' in session:
        container_name = request.form['stop']
        helper.stop(session['username'], container_name)
        time.sleep(1) #wait till the server was stopped
        return redirect(url_for('containers'))
    else:
        return abort(403)

@app.route('/reset', methods=['POST'])
def reset_container():
    if 'loggedin' in session:
        container_name = request.form['reset']
        helper.reset(session['username'], get_path(session['username']), container_name)
        return redirect(url_for('containers'))
    else:
        return abort(403)

@app.route('/remove', methods=['POST'])
def remove_container():
    if 'loggedin' in session:
        container_name = request.form['remove']
        helper.remove(session['username'], get_path(session['username']), container_name)
        return redirect(url_for('containers'))
    else:
        return abort(403)

@app.route('/exec', methods=['POST'])
def execute():
    if 'loggedin' in session:
        command = request.form['command']
        container = request.form['container_name']
        helper.exec(session['username'], container, command)
        return redirect(url_for('containers'))
    else:
        return abort(403)

@app.route('/change-port', methods=['POST'])
def change_port():
    if 'loggedin' in session:
        container = request.form['container_name']
        if helper.port_in_use(eval(helper.ps(session['username'])[1][container]['port'])):
            flash('Please stop the server before changing the port!')
            return redirect(url_for('containers'))
        port = request.form['port']
        helper.update_port(session['username'], container, port)
        return redirect(url_for('containers'))
    else:
        return abort(403)

@app.route('/create', methods=['POST', 'GET'])
def create():
    if 'loggedin' in session:
        if request.method == 'GET':
            available_ports = get_ports(session['username'])
            first = available_ports[0]
            last = available_ports[len(available_ports)-1]
            return render_template('create.html', first=int(first), last=int(last))
        if request.method == 'POST':
            user = session['username']
            name = request.form['name']
            port = request.form['port']
            path = get_path(session['username'])
            path = f'{path}/{name}'
            version = request.form['version']
            mode = request.form['mode']
            memory = request.form['memory']
            Type = request.form['type']
            motd = request.form['motd']
            status = helper.create(user, name, port, path, mode, version, memory, Type, motd)
            time.sleep(1)
            if status == 'error':
                return "There was an error while creating the new server. Please check all your options! (name, version and memory especially)"
            return redirect(url_for('containers'))
    else:
        return abort(401, 'You are not authorized to access this page!')

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run()
