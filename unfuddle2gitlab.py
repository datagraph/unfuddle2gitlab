#!/usr/bin/env python

from xml.sax import make_parser, handler
import xmltodict
import os
from shutil import copyfile
import gitlab
import sys
import pickle
from collections import defaultdict
import collections
import auth

maildomain = "example.net"
defaultpasswd = "defaultpasswd"

group_gl = {}
users_gl = {}

gitlab_server_object, tokens = auth.get_auth()

root_gl = gitlab.Gitlab(
    tokens["root"]['url'], private_token=tokens["root"]['api'], api_version=4)
root_gl.auth()
print("version of ", tokens["root"]['url'], "is ", root_gl.version())

doc = None
with open('backup.xml') as fd:
    doc = xmltodict.parse(fd.read())


def get_xml_number(xmlnumber):
    if xmlnumber:
        if "#text" in xmlnumber:
            return int(xmlnumber["#text"])
        if xmlnumber:
            return int(xmlnumber)
    return None


def get_user_gl_by_id(_id):
    if _id == None:
        print("userid ", _id, " not found, use root instead")
        return {'id': 1, 'first-name': 'root', 'last-name': 'root', 'email': 'root_at_dydra.com@'+ maildomain, 'auth': root_gl, 'user_gl': root_gl.users.get(1)}
    for user in users_gl:
        _uid = users_gl[user]['id']
        # print(type(_id),type(_uid))
        if isinstance(_uid, (int, str)) and isinstance(_id, (int, str)):
            if int(_uid) == int(_id):
                return users_gl[user]
    print("userid ", _id, " not found, create user unknown_name_"+str(_id)+" instead")
    return add_users_gl(_id)["unknown_name_" + str(_id)]

def get_label_gl_by_id(labels_gl, _id):
    if _id == None:
        return None
    for label in labels_gl:
        # if label.id == _id: # check gitlab id now deeper in struct ...
        if labels_gl[label]['id'] == _id:  # check unfuddle id
            return label
    return "None"


def get_label_gl_by_name(labels_gl, _name):
    for label in labels_gl:
        #print(label.name," ",label.id)
        if label.name == _name:
            return label
    return "None"


def get_labels_gl(labels_uf, project_gl):
    # print(labels_uf)
    for label in labels_uf:
        #print(label," ",labels_uf[label]['id'])
        label_gl = None
        try:
            color = '#8899aa'
            if label == 'priority::Highest':
                color = '#FF0000'
            if label == 'priority::High':
                color = '#F0AD4E'
            if label == 'priority::Normal':
                color = '#D1D100'
            if label == 'priority::Low':
                color = '#004E00'
            if label == 'priority::Lowest':
                color = '#A295D6'
            label_gl = project_gl.labels.create(
                {'name': label, 'color': color, 'description': label+' description'})
        except gitlab.exceptions.GitlabCreateError as err:
            if err.response_code == 409:
                print(err.error_message)
                labels_gl = project_gl.labels.list()
                for _label_gl in labels_gl:
                    if _label_gl.name == label:
                        label_gl = _label_gl
                        break
            else:
                raise err
        labels_uf[label]['label_gl'] = label_gl
    return labels_uf


def get_ticket_gl_iid_by_id(tickets, _id_uf):
    if _id_uf == None:
        return None
    try:
        return tickets[_id_uf]['issue_gl'].iid
    except:  # catch *all* exceptions
        e = sys.exc_info()[0]
        print(e)
    return "unknown iid for " + str(_id_uf)

def get_group_uf(doc):
    project = doc['account']['projects']["project"]
    return project


def get_group_gl(project):
    groupname = project["short-name"]
    group = None
    groups = root_gl.groups.list()
    for group_ in groups:
        if group_.name == groupname:
            group = group_

    if not group:
        print("XXXX Create the Group ", groupname, " XXXX")
        description = ""
        if project['title']:
            description = project["title"]+": "
        else:
            description = "title: "
        if project['description']:
            description += project["description"]
        group = root_gl.groups.create(
            {'name': groupname, 'path': groupname, 'visibility': 'private', 'description': description})
    else:
        #print("current roup.description:", group.description)
        #group.description = 'all about atomgraph'
        if group.visibility != 'private':
            group.visibility = 'private'
            group.save()
    return group


def get_users_uf(doc):
    users = {}
    users_uf = doc['account']['people']
    for person in users_uf["person"]:
        #print("person: ", person["username"], " ", person["first-name"] , " ", person["last-name"], " ", person["email"] )
        username = ""
        if 'username' not in person:
            username = person["email"].replace("@", "_at_").replace("+","plus")
        else:
            username = person["username"]
        users[username] = {"id": get_xml_number(
            person["id"]), "first-name": person["first-name"], "last-name": person["last-name"], "email": person["email"]}
        if not users[username]["first-name"]:
            users[username]["first-name"] = "first-name_" + \
                str(get_xml_number(person["id"]))
        if not users[username]["last-name"]:
            users[username]["last-name"] = "last-name_" + \
                str(get_xml_number(person["id"]))
    return users


def get_users_gl(users_uf):
    for username in users_uf:
        users_uf[username]["email"] = users_uf[username]["email"].replace(
            "@", "_at_") + "@" + maildomain
        # print(users_gl[username]["email"])
        users = root_gl.users.list(username=username)
        if len(users) == 1:
            user = users[0]
            print(username)
            if username == "kernelport":
                continue
            try:
                member = group_gl.members.get(user.id)
                member.access_level = gitlab.DEVELOPER_ACCESS
                member.save()
            except:  # catch *all* exceptions
                member = group_gl.members.create(
                    {'user_id': user.id, 'access_level': gitlab.OWNER_ACCESS})
            if username not in tokens:
                api_token = user.impersonationtokens.create(
                    {'name': 'api_token', 'scopes': ['api']})
                tokens[username] = {"api": api_token.token}
                pickle.dump(tokens, open(gitlab_server_object, "wb"))
        elif len(users) == 0:
            print("XXXX Create the User "+username + " XXXX")
            user = root_gl.users.create({
                'skip_confirmation': True,
                'email': users_uf[username]["email"],
                'password': defaultpasswd,
                'username': username,
                'name': users_uf[username]["first-name"] + " " + users_uf[username]["last-name"]})
            api_token = user.impersonationtokens.create(
                {'name': 'token1', 'scopes': ['api']})
            tokens[username] = {"api": api_token.token}
            pickle.dump(tokens, open(gitlab_server_object, "wb"))
            group_gl.members.create(
                {'user_id': user.id, 'access_level': gitlab.OWNER_ACCESS})
        users_uf[username]["auth"] = gitlab.Gitlab(
            tokens["root"]['url'], private_token=tokens[username]['api'])
        #user.unblock()
        users_uf[username]["auth"].auth()
        users_uf[username]["user_gl"] = user
        #user.block()
    return users_uf


def add_users_gl(uid_uf):
    username = "unknown_name_" + str(uid_uf)
    print("XXXX Add the User "+username + " XXXX")
    #try:
    user = root_gl.users.create({
        'skip_confirmation': True,
        'email': username+'@'+maildomain,
        'password': defaultpasswd,
        'username': username,
        'name': 'first_'+username + " " + 'last_'+username})
    api_token = user.impersonationtokens.create(
        {'name': 'token1', 'scopes': ['api']})
    tokens[username] = {"api": api_token.token}
    pickle.dump(tokens, open(gitlab_server_object, "wb"))
    group_gl.members.create(
            {'user_id': user.id, 'access_level': gitlab.OWNER_ACCESS})
    users_gl[username] = {'id': uid_uf}      
    users_gl[username]["auth"] = gitlab.Gitlab(
        tokens["root"]['url'], private_token=tokens[username]['api'])
    #user.unblock()
    users_gl[username]["auth"].auth()
    users_gl[username]["user_gl"] = user
    #user.block()
    #except:  # catch *all* exceptions
    #    e = sys.exc_info()[0]
    #    print(e)

    return users_gl

def get_project_gl(project_name, group):
    project = None
    projects = root_gl.projects.list(search=project_name)
    for project_ in projects:
        if project_.namespace["name"] == group.name:
            project = project_
            break
    if not project:
        print("XXXX Create the Project "+project_name + " XXXX")
        project = root_gl.projects.create(
            {'name': project_name, 'namespace_id': group.id, 'visibility': 'private'})
    return root_gl.projects.get(project.id)


def get_associated_tickets(associated_tickets_uf):
    associated_tickets = {}
    relationship_l = []
    ticket_l = []
    if associated_tickets_uf:
        for associated_tickets_ in associated_tickets_uf:
            if associated_tickets_ == 'relationship':
                if isinstance(associated_tickets_uf['relationship'], list):
                    for relationship_ in associated_tickets_uf['relationship']:
                        relationship_l.append(relationship_)
                else:
                    relationship_l.append(
                        associated_tickets_uf['relationship'])
            if associated_tickets_ == 'ticket':
                if isinstance(associated_tickets_uf['ticket'], list):
                    for associated_ticket_ in associated_tickets_uf['ticket']:
                        ticket_l.append(associated_ticket_['id'])
                else:
                    ticket_l.append(associated_tickets_uf['ticket']['id'])
    relationship_nr = 0
    for ticket in ticket_l:
        associated_tickets[int(ticket)] = relationship_l[relationship_nr]
        relationship_nr += 1
    # print(associated_tickets)
    return associated_tickets


def get_attachments(attachments_uf):
    attachments = {}
    if attachments_uf:
        if 'created-at' in attachments_uf['attachment']:
            attachment = attachments_uf['attachment']
            attachments[int(attachment['id'])] = {'created-at': attachment['created-at'], 'updated-at': attachment['updated-at'],
                                                  'filename': attachment['filename'],
                                                  'content-type': attachment['content-type']}
        else:
            for attachment in attachments_uf['attachment']:
                attachments[int(attachment['id'])] = {'created-at': attachment['created-at'], 'updated-at': attachment['updated-at'],
                                                      'filename': attachment['filename'],
                                                      'content-type': attachment['content-type']}
    print(attachments)                                                  
    return attachments


def get_comments(comments_uf):
    comments = {}
    if comments_uf:
        if 'created-at' in comments_uf['comment']:
            comment = comments_uf['comment']
            comments[int(comment['id'])] = {'created-at': comment['created-at'], 'updated-at': comment['updated-at'], 'attachments': get_attachments(comment['attachments']),
                                            'author-id': (comment['author-id']), 'body': (comment['body'])}
        else:
            for comment in comments_uf['comment']:
                comments[int(comment['id'])] = {'created-at': comment['created-at'], 'updated-at': comment['updated-at'], 'attachments': get_attachments(comment['attachments']),
                                                'author-id': (comment['author-id']), 'body': (comment['body'])}
    return comments


def get_tickets_uf(doc):
    tickets_uf = doc['account']['projects']["project"]["tickets"]
    tickets = {}
    if tickets_uf:
        if 'created-at' in tickets_uf['ticket']:
            ticket = tickets_uf['ticket']
            tickets[int(ticket['id'])] = {'created-at': ticket['created-at'], 'updated-at': ticket['updated-at'], 'attachments': get_attachments(ticket['attachments']),
                                          'associated-tickets': get_associated_tickets(ticket['associated-tickets']),
                                          'status': ticket['status'],
                                          'priority': get_xml_number(ticket['priority']),
                                          'resolution': str(ticket['resolution']),
                                          'resolution-description': str(ticket['resolution-description']),
                                          'field1-value-id': get_xml_number(ticket['field1-value-id']),
                                          'field2-value-id': get_xml_number(ticket['field2-value-id']),
                                          'field3-value-id': get_xml_number(ticket['field3-value-id']),
                                          'summary': ticket['summary'],
                                          'assignee-id': get_xml_number(ticket['assignee-id']),
                                          'description': ticket['description'],
                                          'reporter-id': int(ticket['reporter-id']),
                                          'attachments': get_attachments(ticket['attachments']),
                                          'comments': get_comments(ticket["comments"])}
        else:
            for ticket in tickets_uf['ticket']:
                tickets[int(ticket['id'])] = {'created-at': ticket['created-at'], 'updated-at': ticket['updated-at'], 'attachments': get_attachments(ticket['attachments']),
                                              'associated-tickets': get_associated_tickets(ticket['associated-tickets']),
                                              'status': ticket['status'],
                                              'priority': get_xml_number(ticket['priority']),
                                              'resolution': str(ticket['resolution']),
                                              'resolution-description': str(ticket['resolution-description']),
                                              'field1-value-id': get_xml_number(ticket['field1-value-id']),
                                              'field2-value-id': get_xml_number(ticket['field2-value-id']),
                                              'field3-value-id': get_xml_number(ticket['field3-value-id']),
                                              'summary': ticket['summary'],
                                              'assignee-id': get_xml_number(ticket['assignee-id']),
                                              'description': ticket['description'],
                                              'reporter-id': int(ticket['reporter-id']),
                                              'attachments': get_attachments(ticket['attachments']),
                                              'comments': get_comments(ticket["comments"])}
    return tickets


def get_attachments_gl(project, attachments):
    uploads = []
    attachments_gl = {}
    attachments_gl['listformat'] = ""
    for attachment in attachments:
        filename = attachments[attachment]['filename']
        filepath_local = "media/"+str(attachment)
        upload = project.upload(filename, filepath=filepath_local)
        uploads.append(upload)
        attachments_gl['listformat'] = attachments_gl['listformat'] + \
            "   \n" + "[" + filename + "]({})".format(upload["url"])
    attachments_gl['uploads'] = uploads
    return attachments_gl

def get_wikiattachments_gl(project, attachments):
    uploads = []
    attachments_gl = {}
    attachments_gl['listformat'] = ""
    for attachment in attachments:
        filename = attachments[attachment]['filename']
        filepath_local = "media/"+str(attachment)
        upload = project.wikiattachment(filename, filepath=filepath_local)
        uploads.append(upload)
        print(upload)
        attachments_gl['listformat'] = attachments_gl['listformat'] + \
            "   \n" + "[" + filename + "]({})".format(upload['link']["url"])
    attachments_gl['uploads'] = uploads
    return attachments_gl

def get_comments_gl(issue, comments_uf):
    # print(issue.iid)
    for comment in comments_uf:
        timestamps = "Timestamp-> "
        if comments_uf[comment]['created-at']:
            timestamps = timestamps+"created-at: " + \
                comments_uf[comment]['created-at']+" "
        if comments_uf[comment]['updated-at']:
            timestamps = timestamps+"updated-at: " + \
                comments_uf[comment]['updated-at']+"   \n"
        author_id = comments_uf[comment]['author-id']
        #print(comment, author_id)
        author_obj = get_user_gl_by_id(author_id)
        user_gl = gitlab.Gitlab(
            tokens["root"]['url'], private_token=tokens[author_obj['user_gl'].username]['api'], api_version=4)
        project = user_gl.projects.get(issue.project_id, lazy=True)
        editable_issue = project.issues.get(issue.iid, lazy=True)
        attachments_gl = get_attachments_gl(
            project, comments_uf[comment]['attachments'])
        # print(comments_uf[comment]['attachments'])
        i_note = editable_issue.notes.create(
            {'body': timestamps+comments_uf[comment]['body']+attachments_gl['listformat']})
    return comments_uf


def get_labels_uf(doc):
    labels = {}
    custom_field_values = doc['account']['projects']["project"]["custom_field_values"]["custom-field-value"]
    for custom_field_value in custom_field_values:
        labels["custom::"+custom_field_value["value"]
               ] = {"id": int(custom_field_value["id"])}
    tickets = doc['account']['projects']["project"]["tickets"]
    if tickets:
        if 'created-at' in tickets['ticket']:
            ticket = tickets['ticket']
            labels["status::"+ticket["status"]] = {"id": -1}
        else:
            for ticket in tickets['ticket']:
                labels["status::"+ticket["status"]] = {"id": -1}
    labels["priority::Highest"] = {"id": 5}
    labels["priority::High"] = {"id": 4}
    labels["priority::Normal"] = {"id": 3}
    labels["priority::Low"] = {"id": 2}
    labels["priority::Lowest"] = {"id": 1}
    return labels


def get_tickets_gl(tickets_uf, project_gl, labels_gl):
    for ticket in tickets_uf:
        labels = []
        resolutionr_description = ""
        timestamps = "# Timestamp:   \n"
        assignee_obj = get_user_gl_by_id(
            tickets_uf[ticket]['assignee-id'])
        reporter_obj = get_user_gl_by_id(
            tickets_uf[ticket]['reporter-id'])
        if tickets_uf[ticket]['created-at']:
            timestamps = timestamps+"created-at: " + \
                tickets_uf[ticket]['created-at']+"   \n"
        if tickets_uf[ticket]['updated-at']:
            timestamps = timestamps+"updated-at: " + \
                tickets_uf[ticket]['updated-at']+"   \n"
        if tickets_uf[ticket]['priority']:
            labels.append(get_label_gl_by_id(
                labels_gl, tickets_uf[ticket]['priority']))
        if tickets_uf[ticket]['resolution']:
            if tickets_uf[ticket]['resolution'] != "None":
                labels.append("resolution::"+tickets_uf[ticket]['resolution'])
        if tickets_uf[ticket]['status']:
            labels.append("status::"+tickets_uf[ticket]['status'])
        if tickets_uf[ticket]['field1-value-id']:
            labels.append(get_label_gl_by_id(
                labels_gl, tickets_uf[ticket]['field1-value-id']))
        if tickets_uf[ticket]['field2-value-id']:
            labels.append(get_label_gl_by_id(
                labels_gl, tickets_uf[ticket]['field2-value-id']))
        if tickets_uf[ticket]['field3-value-id']:
            labels.append(get_label_gl_by_id(
                labels_gl, tickets_uf[ticket]['field3-value-id']))
        if tickets_uf[ticket]['resolution-description']:
            if tickets_uf[ticket]['resolution-description'] != "None":
                resolutionr_description = "   \n# Resolution Description\n" + \
                    str(tickets_uf[ticket]['resolution-description'])
        user_gl = gitlab.Gitlab(
            tokens["root"]['url'], private_token=tokens[reporter_obj['user_gl'].username]['api'], api_version=4)
        project = user_gl.projects.get(project_gl.id)
        attachments_gl = get_attachments_gl(
            project, tickets_uf[ticket]['attachments'])
        attachments = attachments_gl['listformat']
        print(labels)
        print(str(tickets_uf[ticket]['resolution']))
        print(str(tickets_uf[ticket]['resolution-description']))
        if assignee_obj:
            issue = project.issues.create({
                'title': str(tickets_uf[ticket]['summary']),
                'description': timestamps+"# Issue Description   \n"+str(tickets_uf[ticket]['description'])+resolutionr_description+attachments,
                'labels': labels,
                'assignee_id': assignee_obj['user_gl'].id
            })
        else:
            issue = project.issues.create({
                'title': str(tickets_uf[ticket]['summary']),
                'description': timestamps+"# Issue Description   \n"+str(tickets_uf[ticket]['description'])+resolutionr_description+attachments,
                'labels': labels,
            })

        get_comments_gl(issue, tickets_uf[ticket]['comments'])

        if 'status::closed' in labels or 'status::Resolved' in labels or 'status::Unaccepted' in labels:
            issue.state_event = 'close'
            issue.save()
            # print(issue)

        tickets_uf[ticket]['issue_gl'] = issue    

    return tickets_uf


def get_tickets_assosiation_gl(tickets):
    for ticket in tickets:
        issue = tickets[ticket]['issue_gl']
        update_description = False
        # if isinstance(tickets[ticket]['associated-tickets'], list):
        description = issue.description + "   \n# Associated Tickets   \n"
        for aticket in tickets[ticket]['associated-tickets']:
            update_description = True
            description += "#" + str(get_ticket_gl_iid_by_id(tickets, aticket)) + \
                " " + \
                tickets[ticket]['associated-tickets'][aticket] + "   \n"
        if update_description:
            issue.description = description
            issue.save()
    return tickets

def get_pages(pages_uf):
    pages_dic = defaultdict(dict)
    if pages_uf:
        if 'created-at' in pages_uf['page']:
            page = pages_uf['page']
            pages_dic[int(page['number'])][int(page['version'])] = {'created-at': page['created-at'],
                                                                    'updated-at': page['updated-at'],
                                                                    'notebook-id': page['notebook-id'],
                                                                    'id': int(page['id']),
                                                                    'version': int(page['version']),
                                                                    'number': int(page['number']),
                                                                    'author-id': int(page['author-id']),
                                                                    'body': page['body'],
                                                                    'title': page['title']}
        else:
            for page in pages_uf['page']:
                pages_dic[int(page['number'])][int(page['version'])] = {'created-at': page['created-at'],
                                                                        'updated-at': page['updated-at'],
                                                                        'notebook-id': page['notebook-id'],
                                                                        'id': int(page['id']),
                                                                        'version': int(page['version']),
                                                                        'number': int(page['number']),
                                                                        'author-id': int(page['author-id']),
                                                                        'body': page['body'],
                                                                        'title': page['title']}


    return pages_dic


def get_notebooks(doc):
    notebooks = {}
    notebooks_uf = doc['account']['projects']["project"]["notebooks"]
    if notebooks_uf:
        if 'created-at' in notebooks_uf['notebook']:
            notebook = notebooks_uf['notebook']
            notebooks[int(notebook['id'])] = {'created-at': notebook['created-at'], 'updated-at': notebook['updated-at'], 'attachments': get_attachments(notebook['attachments']),
                                              'pages': get_pages(notebook['pages']), 'title': notebook['title']}
        else:
            for notebook in notebooks_uf['notebook']:
                notebooks[int(notebook['id'])] = {'created-at': notebook['created-at'], 'updated-at': notebook['updated-at'], 'attachments': get_attachments(notebook['attachments']),
                                                  'pages': get_pages(notebook['pages']), 'title': notebook['title']}
    return notebooks

def get_notebooks_gl(notebooks_uf, project_gl ):


    notebook_od = collections.OrderedDict(sorted(notebooks_uf.items()))
    for notebook in notebook_od:
        attachments_gl = get_wikiattachments_gl(project_gl, notebooks_uf[notebook]['attachments'])
        # print("####", attachments_gl)
        pages_dic = notebooks_uf[notebook]['pages']
        number_od = collections.OrderedDict(sorted(pages_dic.items()))
        print("Notebook Numer: ", notebook, "with ", len(number_od), " pages", "Title: ", notebooks_uf[notebook]['title'])      
        for i in number_od:
            version_od = collections.OrderedDict(sorted(pages_dic[i].items()))
            title_prev = None
            slug = None
            print("  Page Numer: ", i, "with ", len(version_od), " versions")
            for jj in version_od:
                print("####", pages_dic[i][jj]['author-id'])
                reporter_obj = get_user_gl_by_id(pages_dic[i][jj]['author-id'])
                user_gl = gitlab.Gitlab(tokens["root"]['url'], private_token=tokens[reporter_obj['user_gl'].username]['api'], api_version=4)
                project = user_gl.projects.get(project_gl.id)
                title=str(pages_dic[i][jj]['title']).replace(' - ', '-')
                if not title_prev:
                    title_prev=title
                elif title_prev!=title:
                    print("!!!Change the Title means change the slug with lost history!!!"+title_prev + "!=" + title)
                    title_prev=title
                    # raise title_prev + "!=" + title
                print(attachments_gl['listformat'])    
                # if attachments_gl['listformat'] == '':
                #      continue
                body = str(pages_dic[i][jj]['body'])    
                for ii in attachments_gl['uploads']:
                    body = body.replace("{{"+ii['file_name']+"}}", ii['link']['url'])
                content="created-at: #" + pages_dic[i][jj]['created-at'] + '#   \nupdated-at: #'+pages_dic[i][jj]['updated-at'] + '#   \n' + body + '#Attachments   \n' + str(attachments_gl['listformat'])
                print("    version=", pages_dic[i][jj]['version'],  "Title: ", title)
                if not slug:
                    title_c=(notebooks_uf[notebook]['title'] + "/" + str(pages_dic[i][jj]['title'])).replace(' - ', '-')
                    page_gl = project.wikis.create({'title': title_c, 'content': content, 'slug': str(i) + "/" + str(jj) })
                    slug = page_gl.slug
                    continue
                page_gl = project.wikis.get(slug)
                page_gl.title = title
                page_gl.content = content
                pp = page_gl.save()
                slug = pp['slug']

    return notebooks_uf

if __name__ == "__main__":

    group_gl = get_group_gl(get_group_uf(doc))
    users_gl = get_users_gl(get_users_uf(doc))
    print(users_gl)

    tickets_project_gl = get_project_gl("Tickets", group_gl)
    notebooks_project_gl = get_project_gl("Notebooks", group_gl)

    labels_gl = get_labels_gl(get_labels_uf(doc), tickets_project_gl)
    #print(labels_gl)
    #sys.exit()


    notebooks_gl = get_notebooks_gl(get_notebooks(doc),notebooks_project_gl)
    #print(notebooks_gl)

    tickets_gl = get_tickets_gl(get_tickets_uf(doc),tickets_project_gl,labels_gl)
    #print(tickets_gl)

    get_tickets_assosiation_gl(tickets_gl)


