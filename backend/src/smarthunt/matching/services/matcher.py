import re
from typing import Any, Dict, Set

# Found 2026-08-04: real jobs with a genuinely relevant, real description
# (e.g. "Storage Backup Engineer" — Veeam, storage administration, Dell
# EMC/HPE/NetApp) still scored a flat 0% because this list only covered a
# generic DevOps skill set (python/kubernetes/terraform/jenkins/git) that
# doesn't overlap at all with this owner's actual Linux/storage/
# virtualization/backup infrastructure background — extract_skills()
# found zero job_skills for such postings, and match() treats "no
# recognized skills in the job" as an automatic 0 regardless of resume
# content. Expanded to the owner's real technology domain, matching
# job_relevance.py's already-vetted scope (see CLAUDE.md's discovery
# notes) plus the specific tools named in the owner's own resume.
SKILLS = [
    "python",
    "linux",
    "aix",
    "openshift",
    "docker",
    "kubernetes",
    "ansible",
    "git",
    "jenkins",
    "terraform",
    "aws",
    "azure",
    "vmware",
    "vsphere",
    "esxi",
    "vcf",
    "red hat",
    "rhel",
    "centos",
    "ubuntu",
    "suse",
    "san",
    "nas",
    "storage",
    "backup",
    "veeam",
    "netbackup",
    "nutanix",
    "kvm",
    "hyper-v",
    "pacemaker",
    "satellite",
    "selinux",
    "high availability",
    "disaster recovery",
]


def extract_skills(text: str) -> Set[str]:
    """Extract known skills from a given text string."""
    if not text:
        return set()

    normalized_text = text.lower()
    found_skills = set()

    for skill in SKILLS:
        # استخدام Word Boundary أو بحث صريح للـ Multi-word skills
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, normalized_text):
            found_skills.add(skill)

    return found_skills


def match(resume_text: str, job_text: str) -> Dict[str, Any]:
    """Calculates matching percentage and skill gaps between resume and job description."""
    resume_skills = extract_skills(resume_text)
    job_skills = extract_skills(job_text)

    # لو الوظيفة ملهاش أي مهارات مطلوبة محددة في القائمة
    if not job_skills:
        return {
            "score": 0,
            "matched_skills": [],
            "missing_skills": [],
        }

    matched_skills = sorted(list(job_skills.intersection(resume_skills)))
    missing_skills = sorted(list(job_skills - resume_skills))

    score = round((len(matched_skills) / len(job_skills)) * 100)

    return {
        "score": score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
    }
