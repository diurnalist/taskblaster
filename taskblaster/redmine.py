from redminelib import Redmine


class RedmineProject:
    def __init__(self, url=None, api_key=None, project=None):
        self.client = Redmine(url, key=api_key)
        self.project = project
    
    def ticket(self, id):
        return self.client.issue.get(id)
