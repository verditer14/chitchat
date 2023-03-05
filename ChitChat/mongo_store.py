#Queries for Mongodb
from datetime import datetime
from bson import ObjectId
from werkzeug.security import generate_password_hash,check_password_hash
from pymongo import MongoClient, DESCENDING


msg_limit= 3

class User:

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

    @staticmethod
    def is_authenticated():
        return True

    def get_id(self):
        return self.username

    def check_password(self, input_pwd):
        return check_password_hash(self.password, input_pwd)

    @staticmethod
    def is_active():
        return True

    @staticmethod
    def is_anonymous():
        return False

client = MongoClient('localhost', 27017)


chat_store = client["ChatStore"]
users_collection = chat_store["users"]
messages_collection = chat_store["messages"]
groups_collection = chat_store["groups"]
group_members_collection = chat_store["group_members"]

#Save, Edit and Get user details from mongodb
def save_user(email, username, password):
    password_hash = generate_password_hash(password)
    users_collection.insert_one({'_id': username, 'email': email, 'password': password_hash})

def edit_user(data):
    users_collection.update_one({'_id': data["username"]}, {'$set': {'email': data["email"]}})

def get_user(username):
    user_data = users_collection.find_one({'_id': username})
    return User(user_data['_id'], user_data['email'], user_data['password']) if user_data else None


#Save, Update and Get group details from mongodb
def save_group(group_name, created_by):
    group_id = groups_collection.insert_one(
        {'name': group_name, 'created_by': created_by, 'created_at': datetime.now()}).inserted_id
    add_group_member(group_id, group_name, created_by, created_by, is_group_admin=True)
    return group_id

def get_group(group_id):
    return groups_collection.find_one({'_id': ObjectId(group_id)})

def update_group(group_id, group_name):
    groups_collection.update_one({'_id': ObjectId(group_id)}, {'$set': {'name': group_name}})
    group_members_collection.update_many({'_id.group_id': ObjectId(group_id)}, {'$set': {'group_name': group_name}})



# Add, Remove and Get group member/members 
def add_group_member(group_id, group_name, username, added_by, is_group_admin=False):
    group_members_collection.insert_one(
        {'_id': {'group_id': ObjectId(group_id), 'username': username}, 'group_name': group_name, 'added_by': added_by,
         'added_at': datetime.now(), 'is_group_admin': is_group_admin})


def add_group_members(group_id, group_name, usernames, added_by):
    group_members_collection.insert_many(
        [{'_id': {'group_id': ObjectId(group_id), 'username': username}, 'group_name': group_name, 'added_by': added_by,
          'added_at': datetime.now(), 'is_group_admin': False} for username in usernames])


def remove_group_members(group_id, usernames):
    group_members_collection.delete_many(
        {'_id': {'$in': [{'group_id': ObjectId(group_id), 'username': username} for username in usernames]}})


def get_group_members(group_id):
    return list(group_members_collection.find({'_id.group_id': ObjectId(group_id)}))


#List all the groups which user is part of
def get_groups_for_user(username):
    return list(group_members_collection.find({'_id.username': username}))

#Check if user is the member of the group
def is_group_member(group_id, username):
    return group_members_collection.count_documents({'_id': {'group_id': ObjectId(group_id), 'username': username}})


#Check if user is admin
def is_group_admin(group_id, username):
    return group_members_collection.count_documents(
        {'_id': {'group_id': ObjectId(group_id), 'username': username}, 'is_group_admin': True})


# Save and get messages
def save_message(group_id, text, sender):
    messages_collection.insert_one({'group_id': group_id, 'text': text, 'sender': sender, 'created_at': datetime.now()})


def get_messages(group_id, page=0):
    offset = page * msg_limit
    messages = list(
        messages_collection.find({'group_id': group_id}).sort('_id', DESCENDING).limit(msg_limit).skip(offset))
    for message in messages:
        message['created_at'] = message['created_at'].strftime("%d %b %y, %H:%M")
    return messages[::-1]
