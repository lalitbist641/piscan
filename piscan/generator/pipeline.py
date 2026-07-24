"""Budgeted generation pipeline with hash dedup and full provenance.

The pipeline treats the layers as a *sampling* process, not a cross-product:
each generated payload draws a random, capped subset of transforms from a random
seed. Every payload is deduplicated on its exact final string, so the output
count is a true count of unique payloads. Full provenance is attached to each.
"""

from dataclasses import dataclass, field
import random

from .seeds import all_seeds
from .mutations import apply_mutations, SURFACE_MUTATIONS, ENCODING_MUTATIONS
from .personas import PERSONAS
from .wrappers import WRAPPERS
from .languages import LANGUAGES, localize


@dataclass
class GenConfig:
    target: int = 50000
    seed: int = 1337
    max_mutations: int = 2          # cap on stacked mutations (avoid unparseable)
    p_persona: float = 0.5
    p_wrapper: float = 0.4
    p_language: float = 0.35
    p_mutation: float = 0.8
    include_benign: bool = True
    benign_ratio: float = 0.06      # ~6% benign controls
    max_attempts_factor: int = 40   # give up after target * factor tries
    fields: tuple = field(default=("subcategory", "goal", "provenance"))


class Generator:
    def __init__(self, config: GenConfig = None):
        self.cfg = config or GenConfig()
        self.rng = random.Random(self.cfg.seed)
        self.attack_seeds = [s for s in all_seeds(include_benign=False)]
        self.benign_seeds = [s for s in all_seeds() if s["category"] == "benign"]

    # -- transform one attack seed into a payload dict ------------------------
    def _mutate_seed(self, seed):
        prov = {"seed_id": seed["seed_id"], "mutations": [], "persona": None,
                "wrapper": None, "lang": None}
        category = seed["category"]

        # multi-turn: transform only the final (payload) turn, no wrappers
        if "turns" in seed:
            turns = list(seed["turns"])
            payload = turns[-1]
            payload, prov = self._apply_text_layers(payload, prov, allow_wrapper=False,
                                                     category_ref=[category])
            turns[-1] = payload
            return {"turns": turns, "category": category, "prov": prov}

        text = seed["text"]
        cat_ref = [category]
        text, prov = self._apply_text_layers(text, prov, allow_wrapper=True,
                                             category_ref=cat_ref)
        return {"text": text, "category": cat_ref[0], "prov": prov}

    def _apply_text_layers(self, text, prov, allow_wrapper, category_ref):
        rng = self.rng
        # Layer 5: language (before encoding so stems still match)
        if rng.random() < self.cfg.p_language:
            lang = rng.choice(LANGUAGES)
            loc = localize(text, lang)
            if loc is not None:
                text = loc
                prov["lang"] = lang
        # Layer 3: persona
        if rng.random() < self.cfg.p_persona:
            name = rng.choice(list(PERSONAS))
            text = PERSONAS[name].format(t=text)
            prov["persona"] = name
        # Layer 4/9: wrapper (turns a direct attack into indirect)
        if allow_wrapper and rng.random() < self.cfg.p_wrapper:
            name = rng.choice(list(WRAPPERS))
            text = WRAPPERS[name].format(t=text)
            prov["wrapper"] = name
            if category_ref[0] in ("direct", "role", "extraction"):
                category_ref[0] = "indirect"
        # Layer 2: mutations (capped, encoding applied last)
        if rng.random() < self.cfg.p_mutation:
            k = rng.randint(1, self.cfg.max_mutations)
            pool = SURFACE_MUTATIONS + ENCODING_MUTATIONS
            names = rng.sample(pool, min(k, len(pool)))
            text, applied = apply_mutations(text, names)
            prov["mutations"] = applied
        return text, prov

    @staticmethod
    def _key(item):
        if "turns" in item:
            return "".join(item["turns"]).strip().lower()
        return item["text"].strip().lower()

    def generate(self):
        cfg = self.cfg
        out = {}
        order = []
        counts = {"attack": 0, "benign": 0}

        def add(item):
            k = self._key(item)
            if k and k not in out:
                out[k] = item
                order.append(k)
                counts["benign" if item["category"] == "benign" else "attack"] += 1
                return True
            return False

        # 1. seed the pool with every base attack (unmutated)
        for s in self.attack_seeds:
            base = ({"turns": list(s["turns"])} if "turns" in s else {"text": s["text"]})
            base.update({"category": s["category"], "subcategory": s["subcategory"],
                         "goal": s["goal"], "source": s["source"],
                         "prov": {"seed_id": s["seed_id"], "mutations": [], "persona": None,
                                  "wrapper": None, "lang": None}})
            add(base)

        n_benign = int(cfg.target * cfg.benign_ratio) if cfg.include_benign else 0
        attack_target = cfg.target - n_benign

        # 2. budgeted sampling of attack variants
        attempts = 0
        max_attempts = cfg.target * cfg.max_attempts_factor
        while counts["attack"] < attack_target and attempts < max_attempts:
            attempts += 1
            s = self.rng.choice(self.attack_seeds)
            m = self._mutate_seed(s)
            item = {k: m[k] for k in m if k in ("text", "turns")}
            item.update({"category": m["category"], "subcategory": s["subcategory"],
                         "goal": s["goal"], "source": s["source"], "prov": m["prov"]})
            add(item)

        # 3. benign controls (with light persona/language variation, no attack goal)
        b_attempts = 0
        while n_benign and counts["benign"] < n_benign and b_attempts < n_benign * 40:
            b_attempts += 1
            s = self.rng.choice(self.benign_seeds)
            text = s["text"]
            prov = {"seed_id": s["seed_id"], "mutations": [], "persona": None,
                    "wrapper": None, "lang": None}
            if self.rng.random() < 0.5:
                name = self.rng.choice(list(PERSONAS))
                text = PERSONAS[name].format(t=text)
                prov["persona"] = name
            add({"text": text, "category": "benign", "subcategory": "benign",
                 "goal": "none", "source": s["source"], "prov": prov})

        # 4. finalize: assign ids
        payloads = []
        for i, k in enumerate(order):
            item = out[k]
            item["id"] = f"GEN-{i:06d}"
            payloads.append(item)
        return payloads
