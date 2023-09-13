import os
from typing import Dict, List


ENTITY_FILENAME = "entities.tsv"
ENTITY_COHORT_FILENAME = "entity_cohorts.tsv"


class EntityInitializer:
    def __init__(self, entity_filepath: str, entity_cohort_filepath: str) -> None:
        self.entity_data = self.parse_entities(filepath=entity_filepath)
        self.entity_cohort_data = self.parse_entity_cohorts(
            filepath=entity_cohort_filepath
        )

    #
    @staticmethod
    def parse_entities(filepath: str) -> List[Dict]:
        """
        Sample result:
        [
            {
                "eid": 1,
                "first_name": "John",
                "last_name": "Lee",
                "age": 22,
                "country": "US",
                "zip_code": "91003",
                "emails": ["jlee@yahoo.com", "johnl@aol.com", "jl123@gmail.com"],
            },
            {
                "eid": 5,
                "first_name": "Tom",
                "last_name": "Tan",
                "age": 81,
                "country": "CH",
                "zip_code": "349999",
                "emails": [],
            }
        ]
        """
        if os.path.exists(filepath):
            data = list()
            data_format = {
                "eid": 0,
                "first_name": 1,
                "last_name": 2,
                "age": 3,
                "country": 4,
                "zip_code": 5,
                "emails": 6,
            }
            #
            with open(filepath, "r") as file:
                # For each line of the file
                for line in file:
                    # Exclude column header
                    if not line.startswith("eid"):
                        data_line = dict()
                        # Split by tab
                        columns = line.replace("\n", "").split("\t")
                        #
                        # Map based on order
                        for col, i in data_format.items():
                            column_value = columns[i]
                            #
                            # Handle columns that can be interpreted as a list of strings to be so
                            if column_value.startswith("[") and column_value.endswith(
                                "]"
                            ):
                                # Handle empty list
                                if len(column_value) == 2:
                                    data_line[col] = []
                                else:
                                    data_line[col] = column_value.strip("[]").split(",")
                            else:
                                # Data type handling
                                if col in ("eid", "age"):
                                    data_line[col] = int(column_value)
                                else:
                                    data_line[col] = column_value
                        #
                        data.append(data_line)
        else:
            raise IOError("The file path, %s, does not exist" % filepath)
        #
        return data

    #
    @staticmethod
    def parse_entity_cohorts(filepath: str) -> List[Dict]:
        """
        Sample result:
        [
            {"cohort": "1", "last_name": "Chen", "age": "[10,50]", "country": "US"},
            {"cohort": "2", "age": "(15,45]", "country": "CH", "emails": "hotmail.com"},
            {"cohort": "3", "first_name": "John", "zip_code": "91003"},
            {"cohort": "4", "country": "US", "emails": "gmail.com"},
        ]
        """
        if os.path.exists(filepath):
            data = list()
            #
            with open(filepath, "r") as file:
                # For each line of the file
                for line in file:
                    data_line = dict()
                    # Split by tab
                    columns = line.replace("\n", "").split("\t")
                    #
                    # Map based on key/value
                    for col_mapping in columns:
                        col_mapping = col_mapping.split(":")
                        data_line[col_mapping[0]] = col_mapping[1]
                    #
                    data.append(data_line)
        else:
            raise IOError("The file path, %s, does not exist" % filepath)
        #
        return data

    #
    def find_entity_cohorts(self, eid: int) -> List[str]:
        """
        Find all cohort ID's ("cohort") associated with a specified entity ID ("eid")
        """
        cohort_results = list()
        entity_row = [row for row in self.entity_data if row["eid"] == eid][0]
        #
        for cohort_row in self.entity_cohort_data:
            this_cohort_matches = True
            #
            for key, value in cohort_row.items():
                # Exact value matches
                if key in ("first_name", "last_name", "country", "zip_code"):
                    if entity_row[key] != cohort_row[key]:
                        this_cohort_matches = False
                # Age range matches
                elif key == "age":
                    min_range = cohort_row[key][0]
                    max_range = cohort_row[key][-1]
                    min_max_age_ranges = cohort_row[key].strip("[]()").split(",")
                    min_age = int(min_max_age_ranges[0])
                    max_age = int(min_max_age_ranges[1])
                    #
                    if min_range == "(":
                        if entity_row[key] <= min_age:
                            this_cohort_matches = False
                    elif min_range == "[":
                        if entity_row[key] < min_age:
                            this_cohort_matches = False
                    else:
                        raise ValueError("%s must be [ or ( only" % min_range)
                    #
                    if max_range == ")":
                        if entity_row[key] >= max_age:
                            this_cohort_matches = False
                    elif max_range == "]":
                        if entity_row[key] > max_age:
                            this_cohort_matches = False
                    else:
                        raise ValueError("%s must be ] or ) only" % max_range)
                # Email domain matches
                elif key == "email":
                    entity_email_domain = entity_row[key].split("@")[1]
                    #
                    if entity_email_domain != cohort_row[key]:
                        this_cohort_matches = False
                    #
            if this_cohort_matches:
                cohort_results.append(cohort_row["cohort"])
            #
        return cohort_results


# 2. List<String> findEntityCohorts(int eid) //Input an entity ID (eid),
# find which cohorts it can match to. Keep in mind an entity could match to multiple cohorts.
# Return all matched cohort IDs.
# 3. boolean addEntityCohort(String cohort) //Add a new cohort (fields delimited by TAB)
# or change/overwrite an existing cohort’s rule. e.g,
# a. INPUT: "cohort:5 last_name:Jackson age:(18,26)",
# b. RETURN: true (if successful)


def main():
    # Instantiate entity, which reads in two files
    entity = EntityInitializer(
        entity_filepath=ENTITY_FILENAME, entity_cohort_filepath=ENTITY_COHORT_FILENAME
    )

    entity.find_entity_cohorts(eid=1)

    # TODO tmp
    #  for row in entity.entity_data: print(row)
    #  for row in entity.entity_cohort_data: print(row)


if __name__ == "__main__":
    main()
