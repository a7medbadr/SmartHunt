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
    exclude_source: Optional[str] = None,
    review_status: Optional[str] = None,
) -> List[Any]:
    """
    تصفية قائمة الوظائف حسب:
    - keyword: البحث داخل title و description
    - location: التصفية حسب الموقع
    - source: التصفية حسب المصدر (تطابق تام، مش جزء من النص)
    - exclude_source: استبعاد مصدر أو أكتر (مفصولين بفاصلة)، تطابق تام لكل واحد
    - review_status: التصفية حسب حالة المراجعة (applied / not_suitable) —
      "none" بيرجع بس الوظايف اللي لسه ماتراجعتش (review_status فاضية)
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
        filtered = [j for j in filtered if loc in str(_get_field(j, "location") or "").lower()]

    if source and source.strip():
        # Exact match, not substring — found 2026-08-07 while building a
        # separate tab for LinkedIn-post-sourced jobs (source="linkedin_post")
        # from real LinkedIn-search-discovered ones (source="linkedin"):
        # substring matching meant filtering by source="linkedin" (e.g. the
        # Jobs page's "search this site directly" dropdown) silently pulled
        # in every linkedin_post row too, since "linkedin" is a substring of
        # "linkedin_post". Every real caller already sends an exact provider
        # name, never a partial one, so this tightens correctness with no
        # loss of existing functionality.
        src = source.strip().lower()
        filtered = [j for j in filtered if str(_get_field(j, "source") or "").lower() == src]

    if exclude_source and exclude_source.strip():
        # Comma-separated list — added 2026-08-09 for the discovered-jobs
        # "job sites" tab, which needs to exclude BOTH linkedin_post AND
        # whatsapp_message sources (each has its own separate tab
        # instead), not just the single source the original LinkedIn-only
        # split needed. A single value with no comma still works exactly
        # as before.
        excluded = {s.strip().lower() for s in exclude_source.split(",") if s.strip()}
        filtered = [
            j for j in filtered if str(_get_field(j, "source") or "").lower() not in excluded
        ]

    if review_status and review_status.strip():
        target = review_status.strip().lower()
        if target == "none":
            filtered = [j for j in filtered if not _get_field(j, "review_status")]
        else:
            filtered = [
                j for j in filtered if str(_get_field(j, "review_status") or "").lower() == target
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
        return sorted(
            jobs, key=lambda j: str(_get_field(j, sort_by) or "").lower(), reverse=is_desc
        )


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
