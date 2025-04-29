import pandas as pd
import json

def parse_data():
    # Load CSV files
    people = pd.read_csv("Resume_Database/01_people.csv")
    abilities = pd.read_csv("Resume_Database/02_abilities.csv")
    education = pd.read_csv("Resume_Database/03_education.csv")
    experience = pd.read_csv("Resume_Database/04_experience.csv")
    person_skills = pd.read_csv("Resume_Database/05_person_skills.csv")

    # Drop unwanted columns
    people = people[["person_id", "name"]]
    education = education.drop(columns=["start_date", "location"])
    # For experience, we keep all columns

    # Build the result dictionary
    result = {}
    for _, row in people.iterrows():
        pid = row["person_id"]
        result[pid] = {
            "name": row["name"],
            "abilities": abilities.loc[abilities.person_id == pid, "ability"].tolist(),
            "education": education[education.person_id == pid]
                         .drop(columns=["person_id"])
                         .to_dict(orient="records"),
            "experience": experience[experience.person_id == pid]
                          .drop(columns=["person_id"])
                          .to_dict(orient="records"),
            "skills": person_skills.loc[person_skills.person_id == pid, "skill"].tolist()
        }
    return result

if __name__ == "__main__":
    data = parse_data()

    # Save the parsed data to a JSON file
    with open("parsed_data.json", "w") as f:
        json.dump(data, f, indent=2)

    print("✅ Parsing complete. Saved to 'parsed_data.json'")
