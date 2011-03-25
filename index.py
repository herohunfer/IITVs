#!/usr/bin/env python
# Ruoran Wang IITS

import os
import logging
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from util.sessions import Session
from google.appengine.ext import db


# A Model for a User
class User(db.Model):
    username = db.StringProperty()
    password = db.StringProperty()
    name = db.StringProperty()
    created = db.DateTimeProperty(auto_now=True)
    #admin = db.BooleanProperty()
    admin = db.StringProperty()
  
# A Model for a ChatMessage
class ChatMessage(db.Model):
    user = db.ReferenceProperty()
    text = db.StringProperty()
    created = db.DateTimeProperty(auto_now=True)


def doRender(handler, tname = 'index.html', values = { }):
    if tname == '/' or tname == '' or tname == None:
        tname = 'index.html'
    
    handler.session = Session()
    flag = True 
    if tname == '/loginscreen.html' or tname == '/register.html' or \
            tname =='loginscreen.html' or tname =='register.html':
        flag = False 

    if handler.session.get('username') == None and flag:
        tname = 'index.html'

    temp = os.path.join(os.path.dirname(__file__), 'templates/' + tname)
    if not os.path.isfile(temp):
        return False

    # Make a copy of the dictionary and add basic values
    newval = dict(values)
    newval['path'] = handler.request.path
    if 'username' in handler.session:
        newval['username'] = handler.session['username']

    outstr = template.render(temp, newval)
    handler.response.out.write(outstr)
    return True

class RegisterHandler(webapp.RequestHandler):
    def get(self):
        doRender(self, 'register.html') 

    def post(self):
        self.session = Session()
        n = self.request.get("name")
        un = self.request.get("username")
        pw = self.request.get("password")

        if pw == '' or un == '' or n == '':
            doRender(
                    self,
                    'register.html',
                    {'error' : 'Please fill in all fields'} )
            return

        que = db.Query(User).filter('username =', un)
        results = que.fetch(limit = 1)

        if len(results) > 0:
            doRender(
                    self,
                    'register.html',
                    {'error' : 'Username already exists'} )
            return

        #if success, create new user
        newuser = User(name = n, username = un, password = pw, admin = "False")
        pkey = newuser.put()
        self.session['username'] = un 
        self.session['userkey'] = pkey
        doRender(self, 'register.html', 
            {'error' : 'Register Success! Welcome, ' + un} )
      
class LoginHandler(webapp.RequestHandler):
    def get(self):
        doRender(self, 'loginscreen.htm')
    
    def post(self):
        self.session = Session()
        un = self.request.get('username')
        pw = self.request.get('password')

        self.session.delete_item('username')
        self.session.delete_item('userkey')

        if pw == '' or un == '':
            doRender(
                    self,
                    'loginscreen.html',
                    {'error': 'Please specify Username and Password'} )
            return

        que = db.Query(User)
        que = que.filter('username =', un)
        que = que.filter('password =', pw)
        # above two may combine

        results = que.fetch(limit = 1)

        if len(results) > 0:
            user = results[0]
            self.session['userkey'] = user.key()
            self.session['username'] = un
            doRender(self,'main.html', {} ) # if ok, go to main.html (logged in)
        else:
            doRender(
                    self,
                    'loginscreen.html',
                    {'error' : 'Username or Password wrong' } )

class LogoutHandler(webapp.RequestHandler):
    def get(self):
        self.session = Session()
        un = self.session.get('username')
        self.session.delete_item('username')
        self.session.delete_item('userkey')
        doRender(self, 'index.html', {'msg' : un + ' logout successful.'} ) 


class IndexHandler(webapp.RequestHandler):
    def get(self):
        if doRender(self,self.request.path) :
            return
        doRender(self,'index.html')

class MainHandler(webapp.RequestHandler):
    def get(self):
        self.session = Session()
        if self.session.get('username') == None:
            self.redirect('/')
        doRender(self, 'main.html')
     
    def post(self):
        doRender(self, 'test.html')

class ShowuserHandler(webapp.RequestHandler):
    def get(self):
        self.session = Session()
        pkey = self.session.get('userkey')
        current_user = db.get(pkey)
        if current_user.admin == "True":
            doRender(self, 'showuser.html', { })
        else:
            doRender(self, 'main.html', {'msg' : 'Require admin previlege!'})

    def post(self):
        self.session = Session()
        pkey = self.session.get('userkey')
        current_user = db.get(pkey)
        
        if current_user.admin == "False":
            doRender(self, 'main.html', {'msg' : 'Require admin previlege!'})
            return

        que = db.Query(User)
        
        if self.request.get('show_admin') == 'True': # if this will show admin
            admin = que.filter('admin =', 'True')
            admin = admin.fetch(limit = 100) 
            doRender(self, 'showuser.html', {'user_list' : admin } )
            return
        else:
            user = que.filter('admin =', 'False')
            user = user.fetch(limit = 500)
            doRender(self, 'showuser.html', {'user_list' : user } )
            return

class DeleteuserHandler(webapp.RequestHandler):
    def post(self):
        self.session = Session()
        pkey = self.session.get('userkey')
        current_user = db.get(pkey)
        
        if current_user.admin == "False":
            doRender(self, 'main.html', {'msg' : 'Require admin previlege!'})
            return

        delete_list = self.request.get('key_to_delete')
        hello = delete_list[1]
        doRender(self, 'test.html', {'msg' : hello})
        return
        if len(delete_list) == 0:
            return

        for item in delete_list:
            que = db.Query(User).filter('username =', item)
            result = que.fetch(limit = 1)
            result[0].delete()

        doRender(self, 'showuser.html', {})

        

def main():
    application = webapp.WSGIApplication([
        ('/login', LoginHandler),
        ('/logout', LogoutHandler),
        ('/register', RegisterHandler),
        ('/main', MainHandler), 
        ('/showuser', ShowuserHandler),
        ('/deleteuser', DeleteuserHandler),
        ('/.*', IndexHandler)],
        debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
    main()

