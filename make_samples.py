from docx import Document


def make(path, full=True):
    d = Document()
    d.add_heading('Aarav Sharma', 0)
    if full:
        d.add_paragraph('Email: aarav.sharma@example.com | Phone: +977 9812345678 | '
                        'LinkedIn: https://www.linkedin.com/in/aarav-sharma-demo')
        d.add_paragraph('Address: Baneshwor, Kathmandu, Nepal')
    else:
        d.add_paragraph('Kathmandu')  # no email, phone or LinkedIn on purpose
    d.add_heading('Experience', 1)
    d.add_paragraph('Junior ML Engineer, Himal Analytics, Jan 2023 - present. Built text classification pipelines.')
    d.add_paragraph('Data Analyst Intern, Everest Data Labs, Jun 2022 - Dec 2022. Cleaned data and built dashboards.')
    d.add_heading('Skills', 1)
    d.add_paragraph('Python, SQL, PyTorch, FastAPI, Communication')
    if full:
        d.add_heading('Certifications', 1)
        d.add_paragraph('Google Data Analytics Certificate')
        d.add_heading('Languages', 1)
        d.add_paragraph('English, Nepali')
    d.save(path)


make('sample_cvs/sample_full.docx', True)
make('sample_cvs/sample_minimal.docx', False)