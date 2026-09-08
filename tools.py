from datetime import datetime


def get_current_date():

    today = datetime.now()

    return today.strftime("%d-%m-%Y")


def college_contact_information():

    information = """
    For official college contact information,
    please refer to the college website or administration office.
    """

    return information


def help_information():

    information = """
    I can help you with:

    1. College regulations
    2. Attendance rules
    3. Course syllabus
    4. Examination information
    5. College FAQs
    6. General student support questions
    """

    return information