def test_health():
    from app.main import app

    assert app is not None
