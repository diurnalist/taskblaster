===========
taskblaster
===========

Because life is too short and there are too many ticketing systems.

Installation
============

The package is not currently uploaded to PyPI, so you have to run it locally. There is a ``run.sh`` script that will
automatically source the virtualenv created by ``tox`` (which is assumed to be installed.)

.. code-block:: shell

   # Create the virtualenv
   tox
   # Show the commands available
   ./run.sh --help


Usage
=====

First set up your environment. Create a file at ``.env`` that looks like this::

  # See: https://developer.atlassian.com/cloud/trello/guides/rest-api/api-introduction/#authentication-and-authorization
  TRELLO_API_KEY=<trello API key>
  TRELLO_TOKEN=<trello token>
  # See: https://www.redmine.org/boards/2/topics/53956
  REDMINE_URL=https://collab.tacc.utexas.edu
  REDMINE_USER=<redmine username>
  REDMINE_API_KEY=<redmine API key>

Syncing Trello cards to Redmine
-------------------------------

The sync command will look at all cards in the most current list, plus the list
named "Future Sync". It will then look at a custom field called "Redmine Ticket",
which is expected to contain the Redmine Issue #. If this field has the value
"new", a new Redmine Issue will be created and the Trello card will be updated with
the Issue's generated ID. If the field already has a valid ID, the issue will be
updated with the latest description, assignee, version, priority, and any updates
will be added to the issue as notes.

.. code-block:: shell

   taskblaster sync-to-redmine

   # If syncing multiple boards
   taskblaster sync-to-redmine --trello-board <board_id> --trello-board <board_id>

Creating a Trello standup report
--------------------------------

This will output some Markdown suitable for Slack, describing the updates to
any cards currently assigned to you and "in flight."

.. code-block:: shell

   taskblaster standup-report <trello username>
