from datetime import date
from redminelib import Redmine


class RedmineProject:
    def __init__(self, url=None, api_key=None, project=None):
        self.client = Redmine(url, key=api_key)
        self.project = project
    
    def get_ticket(self, id):
        return self.client.issue.get(id)

    def create_ticket(self, **fields):
        return self.client.issue.create(**fields)

    def update_ticket(self, id, **fields):
        return self.client.issue.update(id, **fields)

    def list_categories(self):
        return list(self.client.issue_category.filter(project_id=self.project))

    def list_members(self):
        return list(self.client.project_membership.filter(project_id=self.project))

    def get_member(self, id):
        return self.client.user.get(id)

    def get_current_version(self):
        open_versions = [
            v for v in
            self.client.version.filter(project_id=self.project)
            if v.status == "open"
        ]
        
        due_soonest = None
        
        def is_due_sooner(version):
            due = version.due_date
            return (due > date.today() and 
                (not due_soonest or version.due_date < due_soonest.due_date))
        
        for v in open_versions:
            if is_due_sooner(v):
                due_soonest = v

        return due_soonest
