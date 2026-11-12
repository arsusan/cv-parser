import re
import phonenumbers
from pydantic import TypeAdapter, EmailStr, ValidationError
from rapidfuzz import fuzz
from .schemas import CVData, REQUIRED_FIELDS

EMAIL = TypeAdapter(EmailStr)
LINKEDIN = re.compile(r'^(https?://)?([a-z]{2,3}[.])?linkedin[.]com/(in|pub|company)/[A-Za-z0-9_%-]+/?$')
PLACEHOLDERS = {'', 'n/a', 'na', 'none', 'null', 'unknown', 'not provided', 'not available', '-'}


def _norm(s: str) -> str:
    return re.sub(r'[^a-z0-9@+]+', ' ', str(s).lower()).strip()


def _digits(s: str) -> str:
    return ''.join(ch for ch in str(s) if ch.isdigit())


def _grounded(value, source_norm: str, threshold: int = 85) -> bool:
    v = _norm(value)
    if not v or v in source_norm:
        return True
    return fuzz.partial_ratio(v, source_norm) >= threshold


def _phone_ok(p: str) -> bool:
    for region in (None, 'NP'):
        try:
            if phonenumbers.is_possible_number(phonenumbers.parse(p, region)):
                return True
        except phonenumbers.NumberParseException:
            continue
    return False


def validate(raw: dict, cv_text: str) -> dict:
    errors, warnings, checks = [], [], {}

    missing = [k for k in REQUIRED_FIELDS if k not in raw]
    checks['all_fields_present'] = not missing
    if missing:
        errors.append('Missing fields: ' + ', '.join(missing))

    try:
        data = CVData.model_validate(raw)
        checks['types_valid'] = True
    except ValidationError as e:
        checks['types_valid'] = False
        for x in e.errors():
            errors.append('.'.join(str(p) for p in x['loc']) + ': ' + x['msg'])
        return {'status': 'invalid', 'errors': errors, 'warnings': warnings, 'checks': checks}

    src = _norm(cv_text)
    src_lower = cv_text.lower()
    src_digits = _digits(cv_text)

    # missing information must be null / [] and not a placeholder string
    singles = [data.name, data.linkedin_url, data.address, data.last_working_company]
    lists = data.phone_numbers + data.email_addresses + data.skills + data.certifications + data.languages
    bad = [v for v in singles + lists if isinstance(v, str) and v.strip().lower() in PLACEHOLDERS and v != '']
    empties = [v for v in lists if v.strip() == '']
    checks['missing_handled'] = not bad and not empties
    if bad or empties:
        errors.append('Placeholder or empty strings used instead of null / empty list')
    if '@' in cv_text and not data.email_addresses:
        warnings.append('CV seems to contain an email but none was extracted')
    if 'linkedin.com' in src_lower and not data.linkedin_url:
        warnings.append('CV seems to contain a LinkedIn URL but none was extracted')

    # format checks
    fmt_ok = True
    for e in data.email_addresses:
        try:
            EMAIL.validate_python(e)
        except ValidationError:
            fmt_ok = False
            errors.append('Invalid email format: ' + e)
    for p in data.phone_numbers:
        if not _phone_ok(p):
            fmt_ok = False
            errors.append('Invalid phone number: ' + p)
    if data.linkedin_url and not LINKEDIN.match(data.linkedin_url.strip()):
        fmt_ok = False
        errors.append('Invalid LinkedIn URL: ' + data.linkedin_url)
    checks['formats_valid'] = fmt_ok

    # grounding: strong identifiers must exist in the CV (error), the rest are warnings
    grounded = True
    for e in data.email_addresses:
        if e.lower() not in src_lower:
            grounded = False
            errors.append('Email not found in CV (possible hallucination): ' + e)
    for p in data.phone_numbers:
        if _digits(p) and _digits(p) not in src_digits:
            grounded = False
            errors.append('Phone not found in CV (possible hallucination): ' + p)
    if data.linkedin_url and not _grounded(data.linkedin_url, src):
        grounded = False
        errors.append('LinkedIn URL not found in CV (possible hallucination)')

    soft = [('name', data.name), ('address', data.address), ('last_working_company', data.last_working_company)]
    soft += [('skill', s) for s in data.skills] + [('certification', s) for s in data.certifications]
    soft += [('language', s) for s in data.languages]
    for exp in data.experience:
        soft += [('company', exp.company), ('job title', exp.title)]
    for label, value in soft:
        if value and not _grounded(value, src):
            grounded = False
            warnings.append(f'{label} may not be in the CV: {value}')
    checks['grounded_in_cv'] = grounded

    status = 'invalid' if errors else ('warnings' if warnings else 'valid')
    return {'status': status, 'errors': errors, 'warnings': warnings, 'checks': checks}