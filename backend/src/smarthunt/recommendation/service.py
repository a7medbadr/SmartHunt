from smarthunt.recommendation.schemas import JobRecommendation, RecommendationResponse

class RecommendationService:
    @staticmethod
    def recommend_jobs(resume: str) -> RecommendationResponse:
        resume_lower = resume.lower()
        
        jobs_db = [
            {"title": "Linux Engineer", "keywords": ["linux", "bash", "rhcsa", "openshift"]},
            {"title": "Platform Engineer", "keywords": ["openshift", "docker", "kubernetes", "python", "terraform"]},
            {"title": "DevOps Engineer", "keywords": ["docker", "python", "aws", "linux", "ci/cd"]},
            {"title": "Cloud Engineer", "keywords": ["aws", "cloud", "terraform", "openshift"]},
            {"title": "Python Developer", "keywords": ["python", "django", "fastapi", "api"]}
        ]
        
        recommendations = []
        for job in jobs_db:
            matched_count = sum(1 for kw in job["keywords"] if kw in resume_lower)
            if matched_count > 0:
                # حساب نتيجة تقريبية بناءً على الكلمات المطابقة
                score = min(100, 60 + (matched_count * 10))
                recommendations.append(JobRecommendation(title=job["title"], score=score))
        
        # ترتيب النتائج من الأكفي للأقل
        recommendations.sort(key=lambda x: x.score, reverse=True)
        
        # إرجاع أعلى نتائج أو نتائج افتراضية لو مفيش مطابقة
        if not recommendations:
            recommendations = [
                JobRecommendation(title="Linux Engineer", score=70),
                JobRecommendation(title="DevOps Engineer", score=65)
            ]
            
        return RecommendationResponse(recommendations=recommendations)
