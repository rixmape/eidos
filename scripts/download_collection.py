"""
This module is used to download the collection from the Firestore database.
"""

import argparse
import json
from typing import Any, Dict, List

import firebase_admin
import toml
from firebase_admin import credentials, firestore


def load_secrets(file_path: str) -> Dict[str, Any]:
    """Load application secrets from a TOML file."""
    with open(file_path, "r") as file:
        return toml.load(file)


def initialize_firebase(secrets: Dict[str, Any]) -> None:
    """Initialize Firebase application with credentials."""
    certificate = secrets["firebase"]
    credential = credentials.Certificate(certificate)
    firebase_admin.initialize_app(credential)


def fetch_feedback(collection_name: str) -> Dict[str, Dict[str, Any]]:
    """Fetch user feedback from Firestore and process the data."""
    database = firestore.client().collection(collection_name).stream()

    feedback = {}
    for document in database:
        data = document.to_dict()
        data["timestamp"] = data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

        messages = data.get("messages", [])
        processed_messages = [
            {"content": json.loads(message["content"])} for message in messages
        ]
        data["messages"] = processed_messages

        feedback[document.id] = data

    return feedback


def write_feedback_to_file(
    feedback: Dict[str, Any],
    file_path: str = "feedback.json",
) -> None:
    """Write processed feedback to a JSON file."""
    with open(file_path, "w") as file:
        json.dump(feedback, file, indent=4)


def process_users_by_section(
    feedback: Dict[str, Any],
    target_password: str,
) -> Dict[str, List[str]]:
    """Process feedback to group users by section."""
    users_by_section = {}
    for value in feedback.values():
        if value.get("password") == target_password and "name" in value:
            section = (
                value.get("class_section", "NOSECTION")
                .replace("-", "")
                .replace(" ", "")
                .upper()
            )
            users_by_section.setdefault(section, []).append(
                value["name"].title()
            )

    return users_by_section


def write_users_by_section_to_file(
    users_by_section: Dict[str, List[str]],
    file_path: str = "users_by_section.json",
) -> None:
    """Write users grouped by section to a JSON file."""
    with open(file_path, "w") as file:
        json.dump(users_by_section, file, indent=4)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments for configurability."""
    parser = argparse.ArgumentParser(
        description="Process user feedback from Firestore."
    )

    parser.add_argument(
        "--config",
        type=str,
        default=".streamlit/secrets.toml",
        help="Path to the configuration file.",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="user_feedback",
        help="Name of the Firestore collection.",
    )
    parser.add_argument(
        "--password",
        type=str,
        default="lnhsHumanities",
        help="Target password for processing feedback.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    secrets = load_secrets(args.config)
    initialize_firebase(secrets)

    feedback = fetch_feedback(args.collection)
    write_feedback_to_file(feedback)

    users_by_section = process_users_by_section(feedback, args.password)
    write_users_by_section_to_file(users_by_section)

    print("Collection and user processing completed successfully.")


if __name__ == "__main__":
    main()
