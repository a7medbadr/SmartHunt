from typing import Any, List, Optional, Tuple


def _get_field(job: Any, field_name: str) -> Any:
    """استخراج قيمة الحقل بشكل آمن سواء كان الوظيفة dict أو Object."""
    if isinstance(job, dict):
        return job.get(field_name)
    return getattr(job, field_name, None)


def filter_jobs(
    jobs: List[Any],
    keyword: Optional[str] = None,
    location: Optional[str] = None,
    source: Optional[str] = None,
) -> List[Any]:
    """
    تصفية قائمة الوظائف حسب:
    - keyword: البحث داخل title و description
    - location: التصفية حسب الموقع
    - source: التصفية حسب المصدر
    جميع المقارنات غير حساسة لحالة الأحرف (Case-insensitive).
    """
    filtered = jobs

    if keyword and keyword.strip():
        kw = keyword.strip().lower()
        filtered = [
            j
            for j in filtered
            if kw in str(_get_field(j, "title") or "").lower()
            or kw in str(_get_field(j, "description") or "").lower()
        ]

    if location and location.strip():
        loc = location.strip().lower()
        filtered = [
            j
            for j in filtered
            if loc in str(_get_field(j, "location") or "").lower()
        ]

    if source and source.strip():
        src = source.strip().lower()
        filtered = [
            j
            for j in filtered
            if src in str(_get_field(j, "source") or "").lower()
        ]

    return filtered


def sort_jobs(
    jobs: List[Any],
    sort_by: str = "title",
    order: str = "asc",
) -> List[Any]:
    """
    ترتيب الوظائف حسب حقل معين (title, location, source, ...)
    مع دعم الترتيب التصاعدي (asc) والتنازلي (desc).
    """
    if not jobs:
        return []

    is_desc = str(order).lower() == "desc"

    def _sort_key(job: Any) -> Any:
        val = _get_field(job, sort_by)
        if val is None:
            return ""
        if isinstance(val, str):
            return val.lower()
        return val

    try:
        return sorted(jobs, key=_sort_key, reverse=is_desc)
    except TypeError:
        return sorted(jobs, key=lambda j: str(_get_field(j, sort_by) or "").lower(), reverse=is_desc)


def paginate_jobs(
    jobs: List[Any],
    page: int = 1,
    limit: int = 10,
) -> Tuple[List[Any], int]:
    """
    تقسيم النتائج إلى صفحات (Pagination).
    ترجع قائمة الوظائف الخاصة بالصفحة الحالية مع الإجمالي الصحيح بعد الفلترة.
    """
    total = len(jobs)
    page = max(1, page)
    limit = max(1, limit)

    start = (page - 1) * limit
    end = start + limit

    return jobs[start:end], total
