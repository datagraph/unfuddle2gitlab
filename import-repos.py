#!/usr/bin/env python

import os, glob
import xmltodict
import unfuddle2gitlab 

doc = None
with open('backup.xml') as fd:
    doc = xmltodict.parse(fd.read())

group_gl = unfuddle2gitlab.get_group_gl(unfuddle2gitlab.get_group_uf(doc))
os.system('ls -l *.dmp')
for file in glob.glob("*.dmp"):
    repo = file.split(".git.dmp")[0]
    print(repo)
    repo_gl = unfuddle2gitlab.get_project_gl(repo, group_gl)
    print(repo_gl.ssh_url_to_repo)
    os.system('rm -rf ' + repo)
    os.system('mkdir ' + repo)
    os.chdir(repo)
    os.system('git init')
    os.system('git fast-import < ../' + file)
    os.system('git remote add origin ' + repo_gl.ssh_url_to_repo) 
    os.system('git push -u origin --all')
    os.system('git push -u origin --tags')
    os.chdir('..')

