"""Generate the BADLANDS drying-rack food line from one table.

Per family (Beef, Pork, Poultry, Game, Fish):
    KNX_<F>Strips, KNX_<F>StripsSalted     raw strips (hand craft: knife, +salt)
    KNX_<F>Dried,  KNX_<F>Jerky            rack outputs (unsalted / salted)
Recipes: KNX_Slice<F>, KNX_SliceSalt<F> (hand), KNX_Dry<F>, KNX_Cure<F> (rack,
Tags KNXDryRack, overlayStyle <F> -> the rack's per-family overlay art).

Field shapes are vanilla's: raw strips from Base.Steak (DangerousUncooked,
IsCookable, cook/burn minutes, 2/4 days); dried goods from Base.BeefJerky
(EvolvedRecipe list); salt as `item 2 [Base.Salt;Base.SeasoningSalt]` (vanilla
MakePizza / recipes_cooking consume salt by the unit).

    python examples/knx_jerky_gen.py      (writes scripts + translations into the mod)
"""
from __future__ import annotations

import json
from pathlib import Path

MOD = Path(r"C:\Users\KNX\dev\pz-jarvis-mods\mods\FullBookcases\42\media")

FAMILIES = [
    # key, food type, inputs, strip noun, jerky name, dried name, lipids
    ("Beef", "Beef", ["Base.Steak", "Base.Venison", "Base.MuttonChop"],
     "Meat", "Homemade Jerky", "Air-Dried Meat", 3.0),
    ("Pork", "Meat", ["Base.Pork", "Base.PorkChop"],
     "Pork", "Pork Jerky", "Air-Dried Pork", 6.0),
    ("Poultry", "Poultry", ["Base.Chicken", "Base.ChickenFillet", "Base.TurkeyFillet"],
     "Poultry", "Poultry Jerky", "Air-Dried Poultry", 2.5),
    ("Game", "Game", ["Base.Rabbitmeat", "Base.Smallanimalmeat", "Base.Smallbirdmeat"],
     "Game", "Game Jerky", "Air-Dried Game", 2.0),
    ("Fish", "Fish", ["Base.FishFillet", "Base.Salmon"],
     "Fish", "Dried Fish", "Air-Dried Fish", 2.0),
]
STRIPS_PER_CUT = 3
#: DryingCraftLogic time in game seconds at 1x (20 C).  Unsalted dries faster
#: but keeps about a week; salted takes longer and keeps for weeks.
T_SALTED, T_UNSALTED = 259200, 172800
JERKY_EVOLVED = "Stew:10;Pie:10;Stir fry:10;Sandwich:5;Salad:5;Rice:10;Pasta:10"


def food(name, icon, foodtype, weight, fresh, rotten, lipids, raw):
    lines = [f"    item {name}", "    {",
             "        DisplayCategory = Food,", "        ItemType = base:food,",
             f"        Weight = {weight},", f"        Icon = {icon},",
             f"        FoodType = {foodtype},",
             f"        DaysFresh = {fresh},", f"        DaysTotallyRotten = {rotten},",
             "        HungerChange = -10.0,", "        Calories = 75.0,",
             "        Carbohydrates = 0.0,", f"        Lipids = {lipids},", "        Proteins = 10.0,"]
    if raw:
        lines += ["        DangerousUncooked = true,", "        IsCookable = true,",
                  "        MinutesToCook = 15,", "        MinutesToBurn = 30,",
                  "        BadCold = true,", "        GoodHot = true,"]
    else:
        lines += [f"        EvolvedRecipe = {JERKY_EVOLVED},"]
    lines += ["    }", ""]
    return "\n".join(lines)


def hand(name, fam, salted):
    key, _, inputs, *_ = fam
    out = f"Base.KNX_{key}StripsSalted" if salted else f"Base.KNX_{key}Strips"
    salt = "            item 2 [Base.Salt;Base.SeasoningSalt],\n" if salted else ""
    return (f"    craftRecipe {name}\n    {{\n        timedAction = SliceBread_Surface,\n"
            f"        time = {70 if salted else 50},\n        category = Cooking,\n"
            "        Tags = AnySurfaceCraft;Cooking,\n        xpAward = Cooking:3,\n"
            "        inputs\n        {\n"
            "            item 1 tags[base:dullknife;base:sharpknife;base:meatcleaver] mode:keep flags[MayDegradeVeryLight],\n"
            f"            item 1 [{';'.join(inputs)}] flags[ItemCount],\n{salt}"
            "        }\n        outputs\n        {\n"
            f"            item {STRIPS_PER_CUT} {out},\n        }}\n    }}\n")


def rack(name, fam, salted):
    key = fam[0]
    src = f"Base.KNX_{key}StripsSalted" if salted else f"Base.KNX_{key}Strips"
    dst = f"Base.KNX_{key}Jerky" if salted else f"Base.KNX_{key}Dried"
    return (f"    craftRecipe {name}\n    {{\n        time = {T_SALTED if salted else T_UNSALTED},\n"
            "        Tags = KNXDryRack,\n        category = Cooking,\n"
            f"        overlayStyle = {key},\n        inputs\n        {{\n"
            f"            item variable[1:20] [{src}] flags[ItemCount] mode:destroy,\n"
            "        }\n        outputs\n        {\n"
            f"            item variable[1:20] {dst},\n        }}\n    }}\n")


def main() -> None:
    items, recipes, names, rnames = [], [], {}, {}
    for fam in FAMILIES:
        key, ft, _, noun, jerky, dried, lip = fam
        items.append(food(f"KNX_{key}Strips", f"KNX_{key}Strips", ft, 0.1, 2, 4, lip, True))
        items.append(food(f"KNX_{key}StripsSalted", f"KNX_{key}StripsSalted", ft, 0.1, 4, 7, lip, True))
        items.append(food(f"KNX_{key}Dried", f"KNX_{key}Dried", ft, 0.04, 6, 10, lip, False))
        items.append(food(f"KNX_{key}Jerky", f"KNX_{key}Jerky", ft, 0.04, 45, 75, lip, False))
        names.update({f"Base.KNX_{key}Strips": f"{noun} Strips",
                      f"Base.KNX_{key}StripsSalted": f"Salted {noun} Strips",
                      f"Base.KNX_{key}Dried": dried, f"Base.KNX_{key}Jerky": jerky})
        recipes += [hand(f"KNX_Slice{key}", fam, False), hand(f"KNX_SliceSalt{key}", fam, True),
                    rack(f"KNX_Dry{key}", fam, False), rack(f"KNX_Cure{key}", fam, True)]
        rnames.update({f"KNX_Slice{key}": f"Slice {noun} for Drying",
                       f"KNX_SliceSalt{key}": f"Slice and Salt {noun}",
                       f"KNX_Dry{key}": f"Air-Dry {noun}", f"KNX_Cure{key}": f"Cure {noun}"})
    head = ("module Base\n{\n    /* GENERATED by pz-sprite-forge examples/knx_jerky_gen.py -- edit the\n"
            "       table there, not this file. */\n\n")
    (MOD / "scripts" / "items_knx_jerky.txt").write_text(head + "\n".join(items) + "}\n", encoding="utf-8")
    (MOD / "scripts" / "recipes_knx_jerky.txt").write_text(head + "\n".join(recipes) + "}\n", encoding="utf-8")
    en = MOD / "lua" / "shared" / "Translate" / "EN"
    for fname, add in (("ItemName.json", names), ("Recipes.json", rnames)):
        p = en / fname
        d = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        d.update(add)
        p.write_text(json.dumps(d, indent=4, ensure_ascii=False) + "\n", encoding="utf-8", newline="\r\n")
    print(f"{len(items)} items, {len(recipes)} recipes, {len(names)} names")


if __name__ == "__main__":
    main()
