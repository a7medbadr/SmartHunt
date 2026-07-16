import hashlib

class DeduplicationEngine:
    @staticmethod
    def generate_hash(title: str, company: str, city: str, description: str) -> str:
        norm_text = f"{title.lower().strip()}|{company.lower().strip()}|{city.lower().strip()}|{description.lower().strip()}"
        return hashlib.sha256(norm_text.encode('utf-8')).hexdigest()

    @classmethod
    def deduplicate(cls, jobs: list) -> list:
        seen_hashes = set()
        seen_keys = set()
        unique_jobs = []
        for job in jobs:
            provider_key = (job.provider, job.external_id)
            desc_hash = cls.generate_hash(job.title, job.company, job.city or "", job.description)
            if provider_key not in seen_keys and desc_hash not in seen_hashes:
                seen_keys.add(provider_key)
                seen_hashes.add(desc_hash)
                unique_jobs.append(job)
        return unique_jobs
