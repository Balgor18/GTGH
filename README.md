# GTGH
Graph Traffic public repository Github

This project is here for check the number of visit on your public repository Github.

## Config Grafana

You Have to on `http://localhost:3000/connections/datasources` datasources page and add this link `http://prometheus:9090`.

After you do that go on a dashboard create a new view and select the source you create before.

After that select the metric between `github_repo_views` and `github_repo_clones`.

If you need the name of you'r repo on Legend. 

Go just down and select Legend -> Other -> and type `repo`.


The refresh from the python program is 1 hour. You can modify this easily in the code. Just take care the refresh on the github page is not 1 hour but probably 24h.