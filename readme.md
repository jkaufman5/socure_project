## Kaufman Entity Cohort Deliverable

My approach to solving the problem includes a constructor that reads each of two tab-separated files (entities.tsv and entity_cohorts.tsv) one line at a time, casting data types as appropriate, transforming, and storing as list of dictionaries.  For the purposes of this project, the main() function is within the same script.  It instantiates an object of type EntityCohortMatch, adds a new cohort, and includes six test cases per the provided instructions.

The script can be executed by the following command:
```shell
# python match_entity_cohorts.py
```
