from app.utils import total_years
from app.validators import validate

BASE = {'name': None, 'linkedin_url': None, 'phone_numbers': [], 'email_addresses': [],
        'address': None, 'experience': [], 'years_of_experience': None,
        'last_working_company': None, 'skills': [], 'certifications': [], 'languages': []}


def test_overlapping_jobs_are_merged():
    exp = [{'start_date': '2020-01', 'end_date': '2021-12'},
           {'start_date': '2021-06', 'end_date': '2022-12'}]
    assert total_years(exp) == 3.0


def test_missing_fields_are_invalid():
    assert validate({'name': 'A'}, 'A')['status'] == 'invalid'


def test_hallucinated_email_is_caught():
    raw = {**BASE, 'email_addresses': ['fake@nowhere.com']}
    assert validate(raw, 'John Doe, Python developer')['status'] == 'invalid'


def test_clean_result_passes():
    raw = {**BASE, 'name': 'John Doe', 'email_addresses': ['john@example.com']}
    assert validate(raw, 'John Doe john@example.com')['status'] == 'valid'