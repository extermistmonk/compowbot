Requires a B.net API developer account, and two reddit applications: a webapp and a script, with the latter having a corresponding bot account.

Must have an SSL cert because the B.net api requires it.

Use Python 2.7 to run register.py for the web interface, and run ranks.py and flairsupdate.py periodically in that order (every hour or so should be ok)