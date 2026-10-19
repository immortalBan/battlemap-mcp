"""Other words an asset library uses for the thing a caller asked for.

Asset names are the author's vocabulary, not the brief's. A build that asked for
`bookshelf`, `rug`, `lectern`, `column` and `counter` found nothing for any of
them, while `bookcase`, `carpet`, `stand`, `pillar` and `bar` were sitting in
the same library. Every one of those blanks cost a round trip and a guess.

This is a small, hand-kept table of battlemap words that libraries use
interchangeably. It is NOT a thesaurus and nothing here understands meaning:
it is consulted only after a term found nothing, the alternatives are tried in
the order written, and the result always says which word actually matched, so
a caller never mistakes a `bar` for the `counter` it asked about without being
told.

Keep groups to words a library really uses for the same placeable thing. A
group that drifts into "related" words (table -> chair) turns a precise blank
into a confident wrong answer, which is worse.
"""

from __future__ import annotations

import re

# Each group: interchangeable names, most specific first. Alternatives for a
# word are the other members of its groups, in this order.
GROUPS: tuple[tuple[str, ...], ...] = (
    ("bookshelf", "bookcase", "bookshelves", "shelf", "shelves"),
    ("rug", "carpet", "mat"),
    ("lectern", "podium", "pulpit", "stand"),
    ("column", "pillar", "post"),
    ("counter", "bar"),
    ("mug", "tankard", "cup", "goblet"),
    ("vase", "urn", "jar", "pot"),
    ("candlestick", "candelabra", "candle"),
    ("sconce", "lantern", "lamp"),
    ("torch", "brazier"),
    ("chest", "trunk", "coffer"),
    ("crate", "box"),
    ("barrel", "cask", "keg"),
    ("sack", "bag"),
    ("bed", "cot", "bunk"),
    ("armchair", "chair", "seat"),
    ("stool", "seat"),
    ("pew", "bench"),
    ("desk", "table"),
    ("wardrobe", "cupboard", "cabinet", "dresser"),
    ("hearth", "fireplace", "chimney"),
    ("oven", "stove"),
    ("sculpture", "statue", "bust"),
    ("portrait", "painting", "picture", "frame"),
    ("drape", "curtain"),
    ("tapestry", "banner", "flag"),
    ("gate", "portcullis", "door"),
    ("staircase", "stairs", "stair", "steps"),
    ("shrub", "bush", "hedge"),
    ("boulder", "rock", "stone"),
    ("debris", "rubble"),
    ("corpse", "body", "skeleton", "bones", "skull"),
    ("gore", "blood"),
    ("tome", "book"),
    ("parchment", "scroll", "paper", "document"),
    ("letter", "paper", "note"),
    ("sword", "blade"),
    ("armour", "armor"),
    ("wagon", "cart"),
    ("boat", "ship"),
    ("railing", "fence"),
    ("dish", "plate", "bowl"),
    ("potion", "flask", "bottle"),
    ("shrine", "altar"),
    ("sarcophagus", "coffin"),
    ("tombstone", "headstone", "grave", "tomb"),
    ("cell", "cage"),
    ("shackle", "chain"),
    ("tub", "bathtub", "bath"),
    ("latrine", "toilet"),
    ("pail", "bucket"),
    ("pier", "jetty", "dock"),
    ("fungus", "shroom", "mushroom"),
    ("gem", "crystal"),
    ("treasure", "gold", "coin"),
    ("straw", "hay"),
    ("firewood", "log"),
    ("pillow", "cushion"),
    ("quilt", "blanket", "bedding"),
    ("chandelier", "candelabra"),
)

MAX_ALTERNATIVES = 6


def _words(text: str) -> list[str]:
    return [word for word in re.split(r"[^a-z0-9]+", text.lower()) if word]


def _members(word: str) -> list[str]:
    """Other names for one word, in table order, never the word itself."""
    out: list[str] = []
    for group in GROUPS:
        if word in group:
            out.extend(other for other in group if other != word and other not in out)
    return out


def alternatives(term: str) -> list[str]:
    """Other searches worth trying for a term that found nothing.

    A one-word term is swapped whole. In a longer term each word is swapped in
    turn, keeping the rest ("round rug" -> "round carpet"), so the qualifier the
    caller cared about survives. At most MAX_ALTERNATIVES, never the term itself.
    """
    words = _words(term)
    if not words:
        return []
    out: list[str] = []
    for position, word in enumerate(words):
        for other in _members(word):
            swapped = " ".join(words[:position] + [other] + words[position + 1 :])
            if swapped != " ".join(words) and swapped not in out:
                out.append(swapped)
    return out[:MAX_ALTERNATIVES]
