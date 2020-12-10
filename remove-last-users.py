#!/usr/bin/env python

import gitlab
import sys
import maya
from datetime import datetime, timedelta
import pytz
import getopt
import auth

group_gl = {}
users_gl = {}

gitlab_server_object, tokens = auth.get_auth()

root_gl = gitlab.Gitlab(tokens["root"]['url'], private_token=tokens["root"]['api'],api_version=4)
root_gl.auth()
print("version of ",tokens["root"]['url'], "is ", root_gl.version())

def remove_group_gl(since_hours):
    hours_since_now = datetime.now().replace(tzinfo=pytz.UTC) - timedelta(hours=since_hours)
    groups = root_gl.groups.list(all=True)
    for group in groups:
        #print("#####################")
        group_details = root_gl.groups.get(group.id)
        for project in group_details.projects.list():
            if project.name == "Notebooks":
                #print(project.created_at)
                dt = maya.parse(project.created_at).datetime()
                if dt > hours_since_now:
                    print("delete group: ",dt, group.name)
                    group.delete()
    return groups

def remove_project_gl(since_hours):
    hours_since_now = datetime.now().replace(tzinfo=pytz.UTC) - timedelta(hours=since_hours)
    projects = root_gl.projects.list(all=True)
    for project in projects:
        #print("#####################")
        #group_details = root_gl.projects.get(project.id)
        #for project in group_details.projects.list():
            if project.name == "Notebooks":
                #print(project.created_at)
                dt = maya.parse(project.created_at).datetime()
                if dt > hours_since_now:
                    print("delete project: ",dt, project.name_with_namespace)
                    project.delete()
    return projects

def remove_users_gl(since_hours):
    hours_since_now = datetime.now().replace(tzinfo=pytz.UTC) - timedelta(hours=since_hours)
    users = root_gl.users.list(all=True)
    for user in users:
        dt = maya.parse(user.created_at).datetime()
        print(dt, hours_since_now)
        if ( dt > hours_since_now
             and not user.name == 'Ghost User'
             and not user.name == 'Administrator'
             and not user.name == 'Frank Neuber'
             and not user.name == 'Dydra Tester'
           ):
                print("delete user: ",dt, user.name)
                user.delete()
    return users

days = 1
try:
   opts, args = getopt.getopt(sys.argv[1:],"hd:",["days="])
except getopt.GetoptError:
   print('cleanup-devel.py -d <number of days>')
   sys.exit(2)
for opt, arg in opts:
   if opt == '-h':
      print('cleanup-devel.py -d <number of days>')
      sys.exit()
   elif opt in ("-d", "--days"):
      days = int(arg)
print('clean "', days)

remove_users_gl(24*days)
remove_group_gl(4)
remove_project_gl(4)
sys.exit()

