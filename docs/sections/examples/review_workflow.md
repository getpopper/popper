# Review Workflow

The following provides a list of steps with the goal of reviewing a 
popper pipeline that someone else has created:

 1. The `popper workflow` command generates a graph that gives a 
    high-level view of what the pipeline does.

 2. Inspect the content of each of the scripts from the pipeline.

 3. Test that the pipeline works on your machine by running `popper 
    run`.

 4. Check that the git repo was archived (snapshotted) to zenodo or 
    figshare by running `popper zenodo` or `popper figshare`.
