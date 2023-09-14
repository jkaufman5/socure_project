import os
import logging
from typing import Dict, List


ENTITY_FILENAME = "entities.tsv"
ENTITY_COHORT_FILENAME = "entity_cohorts.tsv"


class EntityCohortMatch:
    def __init__(self, entity_filepath: str, entity_cohort_filepath: str) -> None:
        self.logger = self.get_logger()
        self.entity_filepath = entity_filepath
        self.entity_cohort_filepath = entity_cohort_filepath
        self.entity_data = self.parse_entities()
        self.entity_cohort_data = self.parse_entity_cohorts()

    @staticmethod
    def get_logger() -> logging.Logger:
        logging.basicConfig(
            format="%(asctime)s %(levelname)-8s %(message)s",
            level=logging.INFO,
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        return logging.getLogger("entity_cohort_match")

    def parse_entities(self) -> List[Dict]:
        """
        Read in entities file

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
        self.logger.info("Reading in %s:" % self.entity_filepath)

        if os.path.exists(self.entity_filepath):
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

            with open(self.entity_filepath, "r") as file:
                # For each line of the file
                for line in file:
                    # Exclude column header
                    if not line.startswith("eid"):
                        data_line = dict()
                        # Split by tab
                        columns = line.replace("\n", "").split("\t")

                        # Map based on order
                        for col, i in data_format.items():
                            column_value = columns[i]

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

                        data.append(data_line)
        else:
            raise IOError("The file path, %s, does not exist" % self.entity_filepath)

        for row in data:
            self.logger.info(row)

        return data

    def parse_entity_cohorts(self) -> List[Dict]:
        """
        Read in entity cohorts TSV file

        Sample result:
        [
            {"cohort": "1", "last_name": "Chen", "age": "[10,50]", "country": "US"},
            {"cohort": "2", "age": "(15,45]", "country": "CH", "emails": "hotmail.com"},
            {"cohort": "3", "first_name": "John", "zip_code": "91003"},
            {"cohort": "4", "country": "US", "emails": "gmail.com"},
        ]
        """
        self.logger.info("Reading in %s:" % self.entity_cohort_filepath)

        if os.path.exists(self.entity_cohort_filepath):
            data = list()

            with open(self.entity_cohort_filepath, "r") as file:
                # For each line of the file
                for line in file:
                    data_line = dict()
                    # Split by tab
                    columns = line.replace("\n", "").split("\t")

                    # Map based on key/value
                    for col_mapping in columns:
                        col_mapping = col_mapping.split(":")
                        data_line[col_mapping[0]] = col_mapping[1]

                    data.append(data_line)
        else:
            raise IOError(
                "The file path, %s, does not exist" % self.entity_cohort_filepath
            )

        for row in data:
            self.logger.info(row)

        return data

    def find_entity_cohorts(self, eid: int) -> List[str]:
        """
        Find all cohort ID's ("cohort") associated with a specified entity ID ("eid")
        """
        cohort_results = list()
        entity_row = [row for row in self.entity_data if row["eid"] == eid][0]

        for cohort_row in self.entity_cohort_data:
            this_cohort_matches = True

            for key, value in cohort_row.items():
                # Exclude cohort
                if key == "cohort":
                    continue
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

                    if min_range == "(":
                        if entity_row[key] <= min_age:
                            this_cohort_matches = False
                    elif min_range == "[":
                        if entity_row[key] < min_age:
                            this_cohort_matches = False
                    else:
                        raise ValueError("%s must be [ or ( only" % min_range)

                    if max_range == ")":
                        if entity_row[key] >= max_age:
                            this_cohort_matches = False
                    elif max_range == "]":
                        if entity_row[key] > max_age:
                            this_cohort_matches = False
                    else:
                        raise ValueError("%s must be ] or ) only" % max_range)
                # Email domain matches
                elif key == "emails":
                    entity_email_domains = [
                        email.split("@")[1] for email in entity_row[key]
                    ]

                    if cohort_row[key] not in entity_email_domains:
                        this_cohort_matches = False
                else:
                    raise ValueError("The key, %s, is not expected" % key)

            if this_cohort_matches:
                cohort_results.append(cohort_row["cohort"])

        return cohort_results

    def add_entity_cohort(self, cohort: str) -> bool:
        """
        Add a new cohort or update a pre-existing cohort
        """
        cohort_row = dict()
        cohort_found_and_replaced = False

        # Split by tab
        columns = cohort.split("\t")

        # Map based on key/value
        for col_mapping in columns:
            col_mapping = col_mapping.split(":")
            cohort_row[col_mapping[0]] = col_mapping[1]

        # Replace if already exists
        for i in range(len(self.entity_cohort_data)):
            if cohort_row["cohort"] == self.entity_cohort_data[i]["cohort"]:
                self.entity_cohort_data[i] = cohort_row
                self.logger.info(
                    "Cohort %s found and replaced as %s" % (cohort, cohort_row)
                )
                cohort_found_and_replaced = True

        # If not replaced, add it
        if not cohort_found_and_replaced:
            self.entity_cohort_data.append(cohort_row)
            self.logger.info("Cohort %s added as %s" % (cohort, cohort_row))

        # Return True if cohort added or updated successfully
        return True


def main():
    # Instantiate entity, which reads in two files
    entity = EntityCohortMatch(
        entity_filepath=ENTITY_FILENAME, entity_cohort_filepath=ENTITY_COHORT_FILENAME
    )

    # Add new Cohort 5
    entity.add_entity_cohort(cohort="cohort:5\tlast_name:Jackson\tage:(18,26)")

    # Test cases
    assert entity.find_entity_cohorts(eid=1) == ["3", "4"]
    assert entity.find_entity_cohorts(eid=2) == []
    assert entity.find_entity_cohorts(eid=3) == []
    assert entity.find_entity_cohorts(eid=4) == ["2"]
    assert entity.find_entity_cohorts(eid=5) == []
    assert entity.entity_cohort_data[4] == {
        "cohort": "5",
        "last_name": "Jackson",
        "age": "(18,26)",
    }


if __name__ == "__main__":
    main()
