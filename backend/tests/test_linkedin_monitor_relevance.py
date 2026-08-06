from smarthunt.linkedin_monitor.relevance import is_job_related_post, synthesize_title


def test_is_job_related_post_accepts_real_hiring_post():
    text = (
        "We're looking for a Linux Administrator in Riyadh, Saudi Arabia. "
        "Send your CV to apply now."
    )
    assert is_job_related_post(text) is True


def test_is_job_related_post_rejects_missing_hiring_signal():
    text = "Just finished a great Linux training course in Riyadh!"
    assert is_job_related_post(text) is False


def test_is_job_related_post_rejects_missing_saudi_signal():
    text = "We're hiring a Linux Administrator, apply now, send your CV."
    assert is_job_related_post(text) is False


def test_is_job_related_post_rejects_irrelevant_title():
    text = "We're hiring a Sales Manager in Riyadh, Saudi Arabia, apply now."
    assert is_job_related_post(text) is False


def test_is_job_related_post_rejects_manager_role():
    text = "We're hiring a Linux Manager in Riyadh, Saudi Arabia, apply now, send your CV."
    assert is_job_related_post(text) is False


def test_is_job_related_post_accepts_arabic_hiring_post():
    # Gulf-region tech hiring posts very commonly mix languages — Arabic
    # sentence structure with the actual technology name kept in English
    # (e.g. "Linux", "RHEL") rather than transliterated. The skill-name
    # patterns reused from job_relevance.py are Latin-script only, so
    # this is the realistic case, not a simplification of the test.
    text = "مطلوب مهندس Linux في الرياض، السعودية. للتقديم ابعت السي في."
    assert is_job_related_post(text) is True


def test_is_job_related_post_rejects_empty_text():
    assert is_job_related_post("") is False


def test_is_job_related_post_rejects_job_seeker_own_post():
    # Regression: a real saved "job" turned out to be someone's own
    # #OpenToWork post, not a hiring post — it still added #Hiring/#ITJobs
    # hashtags itself (hoping recruiters would find it), which alone was
    # enough to pass the old hiring-signal check.
    text = (
        "#OpenToWork | Network Engineer\n"
        "السلام عليكم جميعاً 👋 أبحث حالياً عن فرصة جديدة في الرياض، السعودية "
        "في مجال Linux و Networking.\n"
        "#Hiring #ITJobs #SaudiArabia #Riyadh"
    )
    assert is_job_related_post(text) is False


def test_is_job_related_post_rejects_english_job_seeker_post():
    text = (
        "Open to work! I'm currently looking for a new opportunity as a "
        "Linux Administrator in Riyadh, Saudi Arabia. #Hiring #Linux"
    )
    assert is_job_related_post(text) is False


def test_synthesize_title_uses_first_nonempty_line():
    text = "\n\nHiring a Linux Administrator\nMore details below."
    assert synthesize_title(text) == "Hiring a Linux Administrator"


def test_synthesize_title_truncates_long_lines():
    text = "a" * 200
    title = synthesize_title(text, max_length=50)
    assert len(title) == 50
