# popper
Falsify your research

Popper workflow:

 1. An `.esf` is given.
 2. Invokes it via the entrypoint
 3. Once experiment is done, aver gets invoked.
      * results are accessed via the backends that aver suports (csv, rdbms, tsdb, etc.)

So popper is super meta and very simple.

Idea: make popper generate the experimental section of an academic article.
