import tornado.ioloop
import tornado.web
import json
import sqlite3
import time
import hashlib
import uuid
from os import listdir
from os.path import isfile, join

proctected_image_array = {}
session_array = {}

class StdLib():

    def AddImageArray(self,filename,data):
        proctected_image_array[filename] = data
        return True
    
    def UpdateImageArray(self,filename,data):
        proctected_image_array.update(filename=data)
        return True

    def loadImage(self,filename):
        return proctected_image_array[filename]

    def OpenProtectedImage(self,session,filename):
        #
        # Open the protected image
        #
        global proctected_image_array

        print('[OpenProtectedImage] - StdLib.OpenProtectedImage : Opening protected image [{}] -[{}]'.format(session,filename))

        if filename == '' or filename is None:
            filename = 'lock.png'

        if self.CheckSession(session):
            if filename in proctected_image_array:
                print('loading {} from array'.format(filename))
                return self.loadImage(filename)
            else:
                with open('./static/protected_images/'+filename,'rb') as prot_file:
                    print('loading {} from file'.format(filename))
                    self.AddImageArray(filename,prot_file.read())
                    return self.loadImage(filename)
        else:
            if "lock.png" in proctected_image_array:
                print('loading {} from array'.format('lock.png'))
                return self.loadImage("lock.png")
            else:
                with open('./static/images/lock.png','rb') as prot_file:
                    print('loading {} from file'.format('lock.png'))
                    self.AddImageArray("lock.png",prot_file.read())
                    return self.loadImage("lock.png")
    
    def CheckSessionDB(self,sessions):
        # check if the session is valid
        conn = sqlite3.connect('./db/users.db')
        c = conn.cursor()
        #
        # We check if the time is more than 5 minutes old
        #
        c.execute("SELECT * FROM sessions WHERE sessions = ? AND lastupdated > ?", (sessions, time.time() - 300))
        data = c.fetchone()
        conn.close()
        if data is None:
            return False
        else:
            #
            # Update the session when it is valid
            #
            self.UpdateSession(sessions)
            return True
    def CheckSession(self,session):
        # Check if the session is in the in-memory database
        if session in session_array:
            return True
        else:
            return False

    def AddSessionDB(self,sessions):
        #
        # Add the session to the in-memory database
        #
        print('[AddSession] - StdLib.AddSession : Adding session db')

        conn = sqlite3.connect('./db/users.db')
        c = conn.cursor()
        
        try:
            #
            # New session
            #
            c.execute("INSERT INTO sessions(sessions,lastupdated) VALUES(?,?)", (sessions, time.time(),))
        except:
            #
            # Update Existing session
            #
            c.execute("UPDATE sessions SET lastupdated = ? WHERE sessions = ?", (time.time(),sessions,))

        conn.commit()
        conn.close()

    def AddSession(self,session):
        # Add the session to the in-memory database
        print('[AddSession] - StdLib.AddSession : Adding session [{}]'.format(session))
        session_array[session] = time.time()
    
    def UpdateSessionDB(self,session):
        # Update the session time in the in-memory database
        print('[UpdateSession] - StdLib.UpdateSession : Updating session [{}] into db [{}]'.format(session,time.time()))

        conn = sqlite3.connect('./db/users.db')
        c = conn.cursor()
        c.execute("UPDATE sessions SET lastupdated=? WHERE sessions=?", (time.time(),session))
        conn.commit()
        conn.close()
    
    def UpdateSession(self,session):
        # Update the session time in the in-memory database
        print('[UpdateSession] - StdLib.UpdateSession : Updating session [{}] into cache [{}]'.format(session,time.time()))
        session_array.update(session=time.time())

    def GenSession(self,remote_ip, username):
        #
        # Generate a session for the user using the IP and username
        #
        # session = hashlib.sha256(str(uuid.uuid4()).encode('utf-8')).hexdigest()
        session = hashlib.sha256(str(remote_ip+username).encode('utf-8')).hexdigest()
        self.AddSession(session)
        return session

    def CheckLogin(self,username,password):
        # Check if the username and password are correct in the Physical Database located in ./db/users.db
        conn = sqlite3.connect('./db/users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username,password))
        data = c.fetchone()
        conn.close()
        if data is None:
            return False
        else:
            return True
StdLib = StdLib()


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        print("MainHandler")
        self.render("./views/index.html", title="Ryan's Python Learning Demo")

class LoginHandler(tornado.web.RequestHandler):
    def post(self):
        print("LoginHandler")
        #
        # Get the POST Data from JSON
        # Get IP Address
        # X-Forwarded-For
        # 
        remoteIP = self.request.remote_ip # This is the ipaddress
        xforwardedfor = self.request.headers.get("X-Forwarded-For") # If you are behind a proxy 

        print("remoteIP: " + str(remoteIP) + ' X-Forwarded-For: ' + str(xforwardedfor))

        try:
            data = tornado.escape.json_decode(self.request.body)

        except:

            print('Error: Could not parse JSON')
            data = { "username": "", "password": "" }

        if (StdLib.CheckLogin(data['username'],data['password'])):
            session = StdLib.GenSession(remoteIP, data['username'])
            data = { "status": "success", "message": "OK", "url": "/dashboard?sessionkey="+session, "session": session }
        else:
            data = { "status": "failed", "message": "Username/Password mismatch", "url": "/"}
        self.write(data)      

class DashboardHandler(tornado.web.RequestHandler):
    def get(self):
        #
        # Check if the session is valid
        #
        session = self.get_query_argument("sessionkey", "")
        if (StdLib.CheckSession(session)):
            print('sessionkey: ' + session + ', is valid')
            #
            # session is valid so we update the session
            #

            #
            # List all files in the proctected images folder
            #
            protected_files = [f for f in listdir('./static/protected_images') if isfile(join('./static/protected_images', f))]

            self.render("./views/dashboard.html",title="Dashboard", sessionkey=session, images=protected_files)
        else:
            self.redirect("/")

class LoadImageHandler(tornado.web.RequestHandler):
    def get(self):
        #
        # Get sessionley and filena,e
        #
        session = self.get_query_argument("sessionkey", "")
        filename = self.get_query_argument("filename", "")

        #
        # Call the OpenProtectedImage function 
        #

        print('filename: ' + filename)

        data = StdLib.OpenProtectedImage(session,filename)

        #
        # Set the content type to image/png
        # Set the content length to the length of the data
        # Write the image-data to the response
        #

        self.add_header("Content-type",  "image/png")
        self.add_header("Content-length", len(data))
        self.write(data)

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler), # The root path
        (r"/api/login", LoginHandler), # The API to login
        (r"/api/loadimage", LoadImageHandler), # The API to load images")
        (r"/dashboard", DashboardHandler), # After Login we show the dashboard check for session
        (r"/images/(.*)",tornado.web.StaticFileHandler, {"path": "./static/images"},), # Static files for images
        (r"/css/(.*)",tornado.web.StaticFileHandler, {"path": "./static/css"},), # Static files for css
        (r"/fonts/(.*)",tornado.web.StaticFileHandler, {"path": "./static/fonts"},), # Static files for fonts
        (r"/js/(.*)",tornado.web.StaticFileHandler, {"path": "./static/js"},), # Static files for js
        (r"/scss/(.*)",tornado.web.StaticFileHandler, {"path": "./static/scss"},) # Static files for scss
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()