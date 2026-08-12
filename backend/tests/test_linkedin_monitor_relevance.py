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


def test_synthesize_title_skips_repost_attribution_line():
    # Regression: real saved jobs were literally titled "Mahmoud Badr
    # reposted this" — found live 2026-08-12, the single biggest source
    # of useless titles in production data.
    text = (
        "Mahmoud Badr reposted this\n"
        "Fircroft\n"
        "51,303 followers\n"
        "We're Hiring! Charging System Engineer in Riyadh, Saudi Arabia."
    )
    assert (
        synthesize_title(text) == "We're Hiring! Charging System Engineer in Riyadh, Saudi Arabia."
    )


def test_synthesize_title_skips_follower_count_line():
    text = "26,266 followers\nSystem Engineer opening in Jeddah, Saudi Arabia."
    assert synthesize_title(text) == "System Engineer opening in Jeddah, Saudi Arabia."


def test_synthesize_title_skips_connection_count_line():
    text = "500+ connections\nHiring a Linux Administrator in Riyadh, Saudi Arabia."
    assert synthesize_title(text) == "Hiring a Linux Administrator in Riyadh, Saudi Arabia."


def test_is_job_related_post_rejects_hashtag_wall_spam():
    # Regression: a real saved "job" (title "Apply Now To know More
    # Details", no actual role description) only passed the tech-relevance
    # check because Linux/OpenShift/RedHat happened to appear in a
    # trailing wall of dozens of unrelated tech+country hashtags, and only
    # passed the Saudi-location check because "#KSA" was one of many
    # unrelated country hashtags in that same wall — found live 2026-08-12.
    text = (
        "Apply Now To know More Details\n"
        "- https://lnkd.in/gCxFnVj9\n\n"
        "#Redhat #Openshift #Linux #Ansible #AWS #openstack #SRE #Kubernetes "
        "#CKA #CKAD #CKS #systemEngineer #LinuxAdministrator #consultant "
        "#India #Mumbai #Bangalore #Delhi #Pune #Chennai #USA #KSA #UAE "
        "#Paris #FRANCE #EUROPE #BRAZIL"
    )
    assert is_job_related_post(text) is False


def test_is_job_related_post_accepts_hashtag_only_post_with_no_other_prose():
    # A post whose entire content is a hashtag-packed title/skills list
    # (no separate prose at all) should still count — hashtag-wall
    # stripping must fall back to the unstripped text rather than reject
    # everything just because every line happens to be hashtags.
    text = (
        "#Hiring #InfrastructureLead #Linux #RHEL #Ansible #Terraform "
        "#Kubernetes #DevOps #SaudiArabiaJobs #RiyadhJobs #HiringNow"
    )
    assert is_job_related_post(text) is True


def test_is_job_related_post_still_accepts_real_post_with_incidental_hashtags():
    # A stray hashtag mixed into an otherwise-real sentence (not a whole
    # hashtag-only line) must not be treated as a "wall" and stripped.
    text = (
        "We're hiring a Linux Administrator in Riyadh, Saudi Arabia #SaudiJobs. "
        "Apply now, send your CV."
    )
    assert is_job_related_post(text) is True
