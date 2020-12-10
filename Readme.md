# setup python environment
python3 -m venv Unfuddle2GitlabEnv Unfuddle2GitlabEnv
source Unfuddle2GitlabEnv/bin/activate
pip install maya xmltodict wheel
pip install git+https://github.com/kernelport/python-gitlab.git@kernelport-patch-2
# the original without my patches pip install git+https://github.com/python-gitlab/python-gitlab

# export unfuddle project
As admin in unfuddle it is possible to export the whole project.   
This results in a bit tar file.

# import the unfuddle project int gitlab
At first we need a impersonation token API tokten from the gitlab admin account.   
This Token we have to enter in the gitlabtoken.py file.   

After that we have to extract the unfuddle tar file into the working directory.   
tar -xzvf ../datagraph.datagraph.20190807111353.tar.gz 

This extract contains a backup.xml file and the media folder which holds all relevant project informations.   
Addtionally it contains the git repositorys from this project as .dmp file.   

After that we can run the unfuddle2gitlab.py.py file.   
This sould create all Users, Notebooks and Tickets (with history) incl. Attachments in our gitlab. 

# Update Timestamps
mkdir export
cd export
## in Notebooks
git clone http://gitlab.server.com/group/notebooks.wiki.git
sh ./wiki-changedate.sh
cd notebooks-timed.wiki
git remote add origin http://gitlab.server.com/group/timednotebook.wiki.git
git push --set-upstream origin master --force
## in Tickets
export Project-Settings-Advanced-Export Check mail and download project
tar -xzvf ../2020-12-09_11-01-095_group_tickets_export.tar.gz
cp project.json project-orig.json
../modify_timestamp_gitlab_project_export.py
rm project-orig.json
tar -czvf ../../2020-12-09_11-01-095_group_tickets_import.tar.gz .
create a new import project in gitlab

# import the unfuddle git dmp repos into gitlab
tar -xzvf ../datagraph.datagraph.20190807111353.tar.gz
import-repos.py

## clean the import for the next unfuddle import
rm -rf *.dmp backup.xml media export 

## remove last created (24 hours) users and groups in gitlab
remove-last-users.py -d 1

