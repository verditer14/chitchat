# chitchat
Group chat api using flask, pymongo and socket.io. 

Lets start!!
1. Install all the requirements (tested on MacOS)
	
		pip3 install -r requirements.txt
2. To run the flask-socketIO app
		
		python3 app.py
3. Go to:  http://127.0.0.1:5000/
			

Features Provided:
1. User
	
		1.1.Signup : http://127.0.0.1:5000/signup
		1.2.Login: http://127.0.0.1:5000/login
		1.3.Logout: http://127.0.0.1:5000/logout
		1.4.Edit User Account Details: http://127.0.0.1:5000/account
2. Group

		2.1.Create New Group: http://127.0.0.1:5000/new-group
		2.2.Edit Group Details: http://127.0.0.1:5000/groups/<group_id>/edit [<group_id> stored in mongodb]
		2.3.View Group information:  http://127.0.0.1:5000/groups/<group_id>/
		2.4.Get Older Messages : http://127.0.0.1:5000/groups/<group_id>/messages
3.Admin:

		3.1.Only admin can add and remove the members of the group [Refer: Edit Group Details]
4.Members of the group can chat with each other
5.Live notification when members join or leave the chat group


		

