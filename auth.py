import sys
import pickle
import gitlabtoken

def get_auth():
    tokens = {}

    gitlab_server_object = "tokens.gitlab.server.com.p"
    tokens["root"] = {"api": gitlabtoken.importservertoken,
                    "url": 'https://gitlab.server.com'}

    try:
        tokens = pickle.load(open(gitlab_server_object, "rb"))
        return gitlab_server_object, tokens

    except:  # catch *all* exceptions
        e = sys.exc_info()[0]
        print(e)
        pickle.dump(tokens, open(gitlab_server_object, "wb"))

