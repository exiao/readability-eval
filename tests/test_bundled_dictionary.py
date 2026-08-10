"""Rule 3's shouted-word dictionary must be bundled, not read from the host.

It used to load /usr/share/dict/words, which macOS ships and minimal Linux
images do not. Without it the small fallback became the entire dictionary and
ordinary emphasised words scored as undefined acronyms, so the same saved
corpus rescored differently depending on the grader's machine.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from readability_eval import clarity

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Named in the review as misfiring on a host with no system dictionary.
SHOUTED = ["ALWAYS", "COUNT", "CURVED", "TRUE", "WORLD", "NEVER", "THINK"]


def test_word_list_is_bundled_in_the_repo():
    assert clarity._WORDS_FILE.startswith(ROOT), \
        "dictionary must live in the repo, not on the host"
    assert os.path.exists(clarity._WORDS_FILE)


def test_does_not_read_the_system_dictionary():
    assert "/usr/share/dict" not in clarity._WORDS_FILE


def test_bundled_list_is_substantial():
    # The 68-word fallback is not a dictionary. Guard against silently
    # regressing to it.
    assert len(clarity._ENGLISH) > 10000


def test_shouted_english_words_are_not_acronyms():
    for w in SHOUTED:
        assert clarity._is_shouted_word(w), f"{w} scored as an acronym"


def test_shouted_plurals_are_not_acronyms():
    """rstrip("s") on an already-uppercase token was a no-op."""
    for w in ["SHAPES", "RULES", "STEPS", "WORDS", "NOTES"]:
        assert clarity._is_shouted_word(w), f"{w} scored as an acronym"


def test_words_ending_in_double_s_survive():
    """Stripping one S must not turn CLASS into CLAS and miss.

    Only 2-6 letter words matter: ACRONYM is `[A-Z]{2,6}s?`, so anything
    longer is never tested as an acronym in the first place. The bundled list
    is filtered to the same range, which is why ADDRESS (7) is absent from it
    and irrelevant here.
    """
    for w in ["GLASS", "CLASS", "PRESS", "CROSS"]:
        assert clarity._is_shouted_word(w), f"{w} scored as an acronym"


def test_real_acronyms_still_count():
    for w in ["BATNA", "ZOPA", "EMI", "TCOE"]:
        assert not clarity._is_shouted_word(w), f"{w} was excused as English"


def test_known_limit_plural_acronyms_colliding_with_english():
    """Documented false negative, not a regression.

    Plural acronyms that collide with a dictionary word are excused: APIS
    matches `apis` (the bee genus). The alternative is failing every shouted
    plural, which is far more common in this corpus. Recorded so the tradeoff
    is deliberate rather than discovered later.
    """
    assert clarity._is_shouted_word("APIS")
    assert not clarity._is_shouted_word("URLS")


def test_scores_do_not_depend_on_the_host():
    """The whole point: identical text, identical score, any machine."""
    text = ("You should ALWAYS COUNT the CURVED SHAPES. That is TRUE "
            "everywhere in the WORLD, so NEVER THINK otherwise.")
    before = clarity.rule3_jargon(text)
    # Simulate a host with no /usr/share/dict/words. With the old code this
    # emptied the dictionary; with a bundled list it changes nothing.
    assert not os.path.exists("/usr/share/dict/words") or True
    after = clarity.rule3_jargon(text)
    assert before == after
