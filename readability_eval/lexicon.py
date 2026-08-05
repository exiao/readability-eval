"""Merged slop lexicon + detectors.

Sources, in order of authority:
  1. ~/.hermes/WRITING-STYLE.md          Eric's kill list + structural slop
  2. creative/humanizer 29 patterns      (blader/humanizer, MIT)
  3. creative/writer hard bans
  4. Wikipedia:Signs_of_AI_writing       (WP:AITELLS)

Wikipedia's "ineffective indicators" are deliberately NOT scored: perfect
grammar, formal prose generally, transition words in isolation, mixed
register. They generate false positives on good human writing.
"""
import re
import statistics

# ---------------------------------------------------------------- WORDS
WORDS = {
    "ai_vocab": ["delve", "realm", "robust", "seamless", "harness", "utilize",
                 "leverage", "empower", "underscore", "streamline", "ignite",
                 "unleash", "etched", "foster", "multifaceted", "intricate",
                 "intricacies", "interplay", "garner", "showcase", "enhance",
                 "pivotal", "crucial", "vital", "enduring", "vibrant",
                 "testament", "tapestry", "beacon", "cornerstone", "landscape",
                 "paradigm", "holistic", "transformative", "groundbreaking",
                 "cutting-edge", "meticulous", "renowned", "profound"],
    "promo": ["boasts", "nestled", "in the heart of", "breathtaking",
              "must-visit", "stunning", "exemplifies", "commitment to",
              "natural beauty", "diverse array", "rich cultural"],
    "hyphen_pairs": ["cross-functional", "client-facing", "data-driven",
                     "decision-making", "high-quality", "real-time",
                     "long-term", "end-to-end", "detail-oriented"],
}

PHRASES = {
    "significance": ["is a testament to", "is a reminder", "plays a vital role",
                     "plays a crucial role", "pivotal moment", "reflects broader",
                     "setting the stage for", "marks a shift", "key turning point",
                     "evolving landscape", "indelible mark", "deeply rooted",
                     "underscores its importance", "highlights its significance"],
    "vague_attrib": ["industry reports", "observers have cited", "experts argue",
                     "some critics argue", "has been described as",
                     "several publications", "studies have shown"],
    "fake_insider": ["the part nobody talks about", "what they don't tell you",
                     "the real secret is", "most people miss this",
                     "here's what most people get wrong", "here's the kicker",
                     "plot twist", "that's only half the story"],
    "authority_trope": ["the real question is", "at its core", "in reality",
                        "what really matters", "the deeper issue",
                        "the heart of the matter", "the key insight",
                        "what's really happening"],
    "signposting": ["let's dive in", "let's explore", "let's break this down",
                    "here's what you need to know", "now let's look at",
                    "without further ado", "in this article", "in this section"],
    "chatbot": ["i hope this helps", "great question", "excellent question",
                "you're absolutely right", "i'd be happy to", "let me know if",
                "would you like me to", "certainly!", "absolutely!",
                "happy to dig deeper"],
    "cutoff": ["as of my last", "up to my last training", "based on available information",
               "while specific details are limited", "while specific details are scarce"],
    "filler": ["it is important to note", "it's important to note", "worth noting",
               "needless to say", "as we all know", "in today's world",
               "when it comes to", "the fact of the matter is", "in order to",
               "due to the fact that", "at this point in time", "in the event that",
               "has the ability to", "on a regular basis", "with regard to"],
    "euphemism": ["rightsizing", "let go", "headwinds", "challenging quarter",
                  "learnings", "opportunity for improvement",
                  "not without its challenges", "suboptimal outcome",
                  "restructuring", "synergies"],
    "generic_close": ["the future looks bright", "exciting times", "in conclusion",
                      "at the end of the day", "step in the right direction",
                      "journey toward excellence", "watch this space"],
    "interpretive": ["that's the power of", "that's why this matters",
                     "this is what it actually looks like", "let that sink in",
                     "this changes everything"],
    "drop_ending": ["that's it.", "simple.", "full stop.", "that's the whole point."],
    "setup": ["what made it work:", "what made it possible:", "what unlocked it:",
              "the thing that changed everything:"],
    "challenges_section": ["despite these challenges", "faces several challenges",
                           "challenges and legacy", "future outlook"],
    "notability": ["independent coverage", "active social media presence",
                   "written by a leading expert", "media outlets", "trade publications"],
}

# ------------------------------------------------------------- PATTERNS
PATTERNS = {
    # Requires just/only/merely, else fires on "I did not go, but I called."
    "not_x_but_y": r"\bnot\s+(?:just\s+|only\s+|merely\s+)[\w\s,'-]{2,40}?,?\s+but\s+(?:also\s+)?",
    # {1,} not {2,} — "It's not X. It's Y." has a one-char X and was missed.
    "antithesis": r"\b(?:it|this|that|the\s+\w+)'?s?\s+not\s+[\w\s'-]{1,40}?[.;,]\s*(?:it|this|that)'?s\s+",
    "isnt_its": r"\b\w+\s+(?:isn't|is\s+not|wasn't)\s+[\w\s'-]{1,40}?[,;.]\s*(?:it'?s|it\s+is)\s+",
    "less_more": r"\bless\s+[\w\s'-]{2,25}?,\s*more\s+",
    "copulative": r"\b(?:serves|stands|functions|acts)\s+as\b|\bboasts\b",
    "trailing_participle": r",\s+(?:highlighting|underscoring|reflecting|showcasing|emphasizing|symbolizing|contributing to|ensuring|cultivating|fostering|encompassing)\b",
    "false_range": r"\bfrom\s+[\w\s'-]{3,30}?\s+to\s+[\w\s'-]{3,30}?,\s*from\s+",
    "tailing_negation": r",\s*no\s+(?:guessing|wasted|fuss|nonsense|surprises)\b",
    "inline_header_list": r"(?m)^[\s]*[-*]\s+\*\*[^*]+\*\*\s*[:—-]",
    "emoji_bullet": r"(?m)^[\s]*[\U0001F300-\U0001FAFF\u2705\u2728\u26A1\U0001F4A1]",
    "artifact": r"oaicite|turn\d+search\d+|contentReference|\[cite:\s*\d+\]|grok_card|attached_file|ppl-ai-file-upload",
}


def strip_quoted(text):
    """Remove code spans, fences, and quoted strings.

    Without this, any document that DISCUSSES slop scores as slop. Running the
    scorer on our own SPEC.md returned 27.6 hits/1k where every single hit was
    the spec quoting a banned term. Mention is not use.
    """
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r'"[^"\n]{0,60}"', " ", text)
    return text


def _count(text, terms):
    low = text.lower()
    return sum(len(re.findall(r"\b" + re.escape(t) + r"\b", low)) for t in terms)


def score(text):
    """Returns (hits_per_1k, breakdown)."""
    words = max(1, len(text.split()))
    text = strip_quoted(text)
    b = {}
    for k, terms in {**WORDS, **PHRASES}.items():
        n = _count(text, terms)
        if n:
            b[k] = n
    for k, pat in PATTERNS.items():
        n = len(re.findall(pat, text, re.I))
        if n:
            b[k] = n

    # rule of three: three parallel comma items ending "and X"
    b_three = len(re.findall(r"\b\w+,\s+\w+,\s+and\s+\w+\b", text))
    if b_three:
        b["rule_of_three"] = b_three

    total = sum(b.values())
    return round(total / words * 1000, 1), b


def shape(text):
    """List-free signals. Metronomic cadence is a tell with zero banned words."""
    sents = [s for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s]
    lens = [len(s.split()) for s in sents]
    words = max(1, len(text.split()))
    cv = statistics.stdev(lens) / statistics.mean(lens) if len(lens) > 1 else 0.0
    frags = sum(1 for l in lens if l <= 4)
    return {
        "em_dash_per_100w": round(text.count("\u2014") / words * 100, 2),
        "sentence_cv": round(cv, 2),                    # <0.5 metronomic
        "frag_ratio": round(frags / max(1, len(lens)), 2),  # staccato stacking
        "bold_per_100w": round(len(re.findall(r"\*\*[^*]+\*\*", text)) / words * 100, 2),
        "comma_per_sent": round(text.count(",") / max(1, len(sents)), 2),
    }


if __name__ == "__main__":
    n = sum(len(v) for v in {**WORDS, **PHRASES}.values())
    print(f"lexicon: {n} terms, {len(PATTERNS)} patterns\n")

    slop = ("Great question! AI coding serves as an enduring testament to the "
            "transformative potential of LLMs, marking a pivotal moment in the "
            "evolving landscape. It's not just autocomplete; it's unlocking "
            "creativity at scale, streamlining processes, enhancing collaboration, "
            "and fostering alignment. Industry observers have noted this trend, "
            "highlighting its importance. In conclusion, the future looks bright. "
            "I hope this helps!")
    clean = ("AI coding assistants speed up boilerplate: config files, test "
             "scaffolding, repetitive refactors. They are bad at knowing when they "
             "are wrong. I have accepted suggestions that compiled, passed lint, and "
             "still did the wrong thing because I stopped paying attention.")

    for name, t in [("SLOP", slop), ("CLEAN", clean)]:
        s, b = score(t)
        print(f"{name}: {s} hits/1k")
        print("  ", dict(sorted(b.items(), key=lambda x: -x[1])))
        print("  ", shape(t), "\n")
