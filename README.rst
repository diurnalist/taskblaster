===========
taskblaster
===========

Because life is too short and there are too many ticketing systems.

Usage
=====

First set up your environment. Create a file at ``.env`` that looks like this::

  TRELLO_API_KEY=<trello API key>
  TRELLO_TOKEN=<trello token>
  REDMINE_URL=https://collab.tacc.utexas.edu
  REDMINE_USER=<redmine username>
  REDMINE_API_KEY=<redmine API key>

Syncing Trello cards to Redmine
-------------------------------

.. code-block:: shell

   taskblaster sync-to-redmine

Creating a Trello standup report
--------------------------------

This will output some Markdown suitable for Slack, describing the updates to
any cards currently assigned to you and "in flight."

.. code-block:: shell

   taskblaster standup-report <trello username>
