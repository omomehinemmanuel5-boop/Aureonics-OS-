from services.growth.engine import GrowthEngine
from services.growth.reply_classifier import ReplyClassifier


def test_daily_cycle_generates_metrics():
    engine = GrowthEngine()
    snap = engine.run_daily_cycle()
    assert snap["messages_sent"] >= 1
    assert "new_hook" in snap


def test_reply_classifier_paths():
    c = ReplyClassifier()
    assert c.classify("yes let's book") == "positive_interest"
    assert c.classify("how does this integrate") == "technical_question"
    assert c.classify("not now") == "objection"
    assert c.classify("unsubscribe") == "rejection"
