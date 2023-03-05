#Chat application prototype using flask, mongo and socket.io
from datetime import datetime
from bson.json_util import dumps
from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, join_room, leave_room
from pymongo.errors import DuplicateKeyError

from mongo_store import get_user, edit_user, save_user, save_group, add_group_members, get_groups_for_user, get_group, is_group_member, \
    get_group_members, is_group_admin, update_group, remove_group_members, save_message, get_messages

app = Flask(__name__)
app.secret_key = "sfdjkafnk"
socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@app.route('/')
def home():
    groups = []
    if current_user.is_authenticated:
        groups = get_groups_for_user(current_user.username)
    return render_template("index.html", groups=groups)

#sign up and store details in mongo db 
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            save_user(email, username, password)
            return redirect(url_for('login'))
        except DuplicateKeyError:
            message = "User already exists! Please login"
    return render_template('signup.html', message=message)

#login and redirect to the home page 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password_input = request.form.get('password')
        user = get_user(username)

        if user and user.check_password(password_input):
            login_user(user)
            return redirect(url_for('home'))
        else:
            message = 'Username or Password is incorrect. If not signup, please sign up'
    return render_template('login.html', message=message)

#View the user account details and edit it.
@app.route("/account/", methods=['GET', 'POST'])
@login_required
def account():
    message = ''
    updated_user = {'email': current_user.email, 'username': current_user.username}
    if request.method == 'POST':
        updated_user['email'] = request.form.get('email')
        edit_user(updated_user)
        message = "Details updates successfully"
    return render_template('account.html',message=message, username=current_user.username,email=updated_user["email"])

@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

#Create a new group and add members
@app.route('/new-group/', methods=['GET', 'POST'])
@login_required
def create_group():
    message = 'Add Participants'
    if request.method == 'POST':
        usernames = [username.strip() for username in request.form.get('members').split(',')]
        group_name = request.form.get('group_name')
        
        if len(group_name) and len(usernames):
            group_id = save_group(group_name, current_user.username)
            if current_user.username in usernames:
                usernames.remove(current_user.username)
            print(current_user.username)
            add_group_members(group_id, group_name, usernames, current_user.username)
            return redirect(url_for('view_group', group_id=group_id))
        else:
            message = "Failed to create group"
    return render_template('new_group.html', message=message)

#edit the existing group; Only admin can add and remove the members in the group

@app.route('/groups/<group_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_group(group_id):
    group = get_group(group_id)
    if group:
        existing_group_members = [member['_id']['username'] for member in get_group_members(group_id)]
        group_members_str = ",".join(existing_group_members)
        message = ''
        if request.method == 'POST':
            group_name = request.form.get('group_name')
            group['name'] = group_name
            update_group(group_id, group_name)
            if is_group_admin(group_id, current_user.username):
                new_members = [username.strip() for username in request.form.get('members').split(',')]
                members_to_add = list(set(new_members) - set(existing_group_members))
                members_to_remove = list(set(existing_group_members) - set(new_members))
                if len(members_to_add):
                    add_group_members(group_id, group_name, members_to_add, current_user.username)
                if len(members_to_remove):
                    remove_group_members(group_id, members_to_remove)
                group_members_str = ",".join(new_members)
            message = group_name + ' group edited successfully'
        return render_template('edit_group.html', group=group, group_members_str=group_members_str, message=message)
    else:
        return "group with group_id " + group_id + " not found", 404

#To view the group details
@app.route('/groups/<group_id>/')
@login_required
def view_group(group_id):
    group = get_group(group_id)
    if group and is_group_member(group_id, current_user.username):
        group_members = get_group_members(group_id)
        messages = get_messages(group_id)
        return render_template('view_group.html', username=current_user.username, group=group, group_members=group_members,
                               messages=messages)
    else:
        return "group with group_id " + group_id + " not found", 404

#To get the older messages
@app.route('/groups/<group_id>/messages/')
@login_required
def get_older_messages(group_id):
    group = get_group(group_id)
    if group and is_group_member(group_id, current_user.username):
        page = int(request.args.get('page', 0))
        messages = get_messages(group_id, page)
        return dumps(messages)
    else:
        return "group not found", 404


@socketio.on('send_message')
def handle_send_message_event(data):
    app.logger.info("{} has sent message to the group {}: {}".format(data['username'],
                                                                    data['group'],
                                                                    data['message']))
    data['created_at'] = datetime.now().strftime("%d %b, %H:%M")
    save_message(data['group'], data['message'], data['username'])
    socketio.emit('receive_message', data, group=data['group'])


@socketio.on('join_group')
def handle_join_group_event(data):
    app.logger.info("{} has joined the group {}".format(data['username'], data['group']))
    join_room(data['group'])
    socketio.emit('join_group_announcement', data, group=data['group'])


@socketio.on('leave_group')
def handle_leave_group_event(data):
    app.logger.info("{} has left the group {}".format(data['username'], data['group']))
    leave_room(data['group'])
    socketio.emit('leave_group_announcement', data, group=data['group'])


@login_manager.user_loader
def load_user(username):
    return get_user(username)


if __name__ == '__main__':
    socketio.run(app, debug=True)
