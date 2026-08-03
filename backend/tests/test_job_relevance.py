import pytest

from smarthunt.matching.services.job_relevance import is_relevant_job_title

# Exact titles the owner reported 2026-08-03 as showing up in the Jobs tab
# despite having nothing to do with their real skill set (Linux/AIX
# infrastructure, SAN/NAS storage, Red Hat OpenShift, VMware).
IRRELEVANT_TITLES = [
    "Admin Concierge - Raffles The Red Sea",
    "Admin Incharge",
    "Airport Systems Engineer ICT / ELV (Airport Experience)",
    "Associate Manager-Infrastructure Services(Windows/ADFS/Virtualization)-Saudi",
    "AV Consultants and Systems Engineer",
    "BMC Helix Administrator-Remote",
    "Cloud Engineer",
    "Cloud Specialist",
    "Cloudera Administrator",
    "Cloudera Data Lakehouse Platform Administrator & Support Engineer",
    "Data Center Technician - Asir - Abha - On-site",
    "Data Entry Admin Specialist (Remote)",
    "Data Management Specialist",
    "Database Administrator",
    "Database Administrator (DBA)",
    "Database Administrator (Saudi nationals preferred)",
    "Denodo Platform Administrator & Support Engineer",
    "DevSecOps, Architect",
    "Digital Solutions Specialist",
    "ECC/TOP Engineer -System Completion Engineer",
    "Estimation Administrator",
    "Finance System Administrator",
    "Fire & Security Systems Engineer",
    "FM Admin",
    "HPE Non Stop Engineer",
    "Information Technology Engineer",
    "Systems Engineer II- Fire Alaram & Public Address (Saudi National Only)",
    "Lean Systems Engineer",
    "IT Specialist - Odoo_ERP",
]

# A title naming the real tech stack, but still wrong (Saudi-national-only,
# or a Manager/Architect level the owner isn't targeting).
EXCLUDED_DESPITE_TECH_MATCH = [
    "Cloud Architect - OpenShift (Saudi National)",
    "Linux Infrastructure Manager",
]

RELEVANT_TITLES = [
    "Senior Linux Administrator",
    "RedHat Linux Administrator",
    "IBM CP4I OpenShift Administrator",
    "Storage Backup Engineer",
    "Senior VMware Administrator",
    "System/Infrastructure Administrator - Linux, AIX",
    "VMware vSphere Administrator",
    "SAN Storage Engineer",
    "Red Hat OpenShift Platform Engineer",
]


@pytest.mark.parametrize("title", IRRELEVANT_TITLES)
def test_rejects_reported_irrelevant_titles(title):
    assert is_relevant_job_title(title) is False


@pytest.mark.parametrize("title", EXCLUDED_DESPITE_TECH_MATCH)
def test_rejects_manager_architect_and_saudi_national_only(title):
    assert is_relevant_job_title(title) is False


@pytest.mark.parametrize("title", RELEVANT_TITLES)
def test_accepts_real_matching_titles(title):
    assert is_relevant_job_title(title) is True


def test_rejects_empty_title():
    assert is_relevant_job_title("") is False
    assert is_relevant_job_title(None) is False
