#!/usr/bin/env python

import json
import re

with open('project-orig.json') as json_file:
    data = json.load(json_file)
    for p in data['issues']:
        description = p['description'].split("# Issue Description")
        timestamp = description[0].split(" ")
        created = timestamp[5]
        updated = timestamp[9]
        p['description'] = description[1]
        p['created_at'] = created
        p['updated_at'] = updated
        print('id: ' + str(p['id']) +  " " + str(p['iid']) + " " , created, updated)
        for n in p['notes']:
            note = n['note']
            if "Timestamp->" in note:
                note = n['note'].split("Timestamp->")
                timestamp = note[1].split(" ")
                created = timestamp[2]
                updated = timestamp[4]
                n['note'] = note[1]
                n['created_at'] = created
                n['updated_at'] = updated
                print('nid: ' + str(p['id']))

with open('project.json', 'w') as outfile:
    json.dump(data, outfile)
