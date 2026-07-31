from smarthunt.career.schemas import CareerAdviceResponse


class CareerAdvisor:
    @staticmethod
    def generate_advice(resume: str) -> CareerAdviceResponse:
        resume_lower = resume.lower()

        # تحديد المستوى الحالي تلقائياً بناء على المهارات الموجودة
        skills_count = sum(
            1
            for skill in [
                "linux",
                "docker",
                "python",
                "aws",
                "openshift",
                "kubernetes",
                "terraform",
            ]
            if skill in resume_lower
        )

        if skills_count >= 5:
            current_level = "Senior-Level"
        elif skills_count >= 2:
            current_level = "Mid-Level"
        else:
            current_level = "Junior-Level"

        return CareerAdviceResponse(
            current_level=current_level,
            recommended_roles=["Linux Engineer", "Platform Engineer"],
            skills_to_learn=["Terraform", "AWS", "Kubernetes"],
            next_certifications=["RHCSA", "RHCE", "CKA"],
        )
