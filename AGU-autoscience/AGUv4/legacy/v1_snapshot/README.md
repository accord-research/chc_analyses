# v1 pilot snapshot — frozen, do not edit

The exact files that `atlas-wf-v1`, `atlas-kf-v1`, `fixedmean-*-v1` and `grid-*-v1` were
registered against, plus the artifacts the v1 pilot produced.

`atlas-wf-v1` and runs r:19–r:23 are preserved in the rx record as pilot/audit material.
Their locked hashes refer to the files snapshotted here; the working tree moved on to v2
after review found three defects in v1 (see SPEC Amendment 1):

  1. the legacy check never directly verified the published 0.79 / 0.77 eastern-zone MAM
     rates, and SPEC promised an ARI=1 comparison against a legacy label vector that does
     not exist;
  2. only one of SPEC §16's three scorer-agreement links was actually run;
  3. the calendar-year field permutation cannot preserve complete outcomes for wrapping
     windows — NDJ can splice Nov–Dec from one donor year with January from another.

**No v1 number, and neither of the two smoke-null replicates, was used to choose among
methods.** Every v2 rule was fixed in Amendment 1 before v2 produced a number.
