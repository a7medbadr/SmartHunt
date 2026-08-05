from smarthunt.email_apply.extraction import extract_email


def test_extract_email_finds_real_address():
    text = "Please send your CV to hr@acme-corp.com to apply."
    assert extract_email(text) == "hr@acme-corp.com"


def test_extract_email_returns_none_when_absent():
    text = "Apply through our website portal."
    assert extract_email(text) is None


def test_extract_email_skips_noreply_addresses():
    text = "This posting was sent from noreply@jobboard.com. Contact hiring@acme.com to apply."
    assert extract_email(text) == "hiring@acme.com"


def test_extract_email_searches_across_multiple_fields():
    assert extract_email(None, "Requirements text", "Send CV to jobs@acme.io") == "jobs@acme.io"


def test_extract_email_handles_empty_input():
    assert extract_email(None, "", None) is None
