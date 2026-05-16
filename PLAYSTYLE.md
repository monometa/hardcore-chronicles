# Playstyle Notes

How the group actually plays Minecraft hardcore — used to judge which dashboard stats are signal vs noise.

## Core idea: village-first economy

Every run starts by anchoring to a village. In the old days we'd hunt for one ourselves — usually **MurzichAI** scouted the world solo, and once he found a village the rest of us would run straight to it.

Inside the village, the whole playstyle is built around **trade**:

1. Level up the villager who trades **sticks for emeralds**.
2. Spend those emeralds on everything else — armor, weapons, food, tools.

That's why **wood is ~99% of our early-game resource demand** — we need enormous stacks of it just to feed the stick-trader. *That's also why at some point we added the **FallingTree** mod — we were tired of chopping by hand because we need so much of it.*

A typical session shape: find a village with villagers → settle in → farm wood-and-trade by day → sleep through nights together.

## Other early resources

Besides wood, the opening hours also need:

- **Flint** — occasionally, to craft the right workstation for villager profession-switching.
- **Cobblestone + basic stone tools** — standard early-tier loop.
- **Coal + a little iron** — same idea: enables profession-switching and tier-up.

## Roles

We've drifted into a stable division of labor over the 44 runs:

- **trofimova2002** — gathers stone / flint / coal alongside the wood, builds the main base, sorts the loot chests, and runs the household stuff (replanting saplings, etc.).
- **MurzichAI** — spends about **90% of his time trading with villagers**. He turns our base resources into ~95% of the gear the group ends up wearing, and only occasionally swings an axe himself. All that trading also pushes his XP up fast, so he's our enchanter.
- **axantroff (me)** — chops wood and stone early, loots a mine, then takes the gear MurzichAI cooks up and goes deeper. Ideal mid-game: I find iron and coal underground ***because MurzichAI keeps feeding himself to mobs every time we go caving together hehehehe — joke, joke. It's just that his playstyle on hardcore is very aggressive and, frankly, a bit reckless given the stakes.***

## Endgame

- **MurzichAI** and I go to the Nether and farm Blaze rods.
- **axantroff (me)** searches for the **End-portal stronghold** while the others enchant gear or top up supplies.

That's the average rhythm. Every run is a variation on this pattern.

## What stats are worth surfacing (given the playstyle above)

A non-exhaustive list of the **kinds** of stats that should land well given how we actually play. Examples — not a closed checklist; if a counter feels interesting and the data exists for it, it's probably worth surfacing.

### 1. Per-player "signature" stats

Things that one of us does a lot and the other two barely touch — these tell the story of each role. A few examples:

- **trofimova2002** — chests opened, saplings planted, items dropped-into-chests (sorting), crafting-table interactions, time at base.
- **MurzichAI** — villager trades performed, XP levels gained, items enchanted, emeralds earned.
- **axantroff** — distance from spawn, deepest Y reached, time in the Nether, time in the End.

If a counter is huge for one of us and near-zero for the others, it's almost always a real, story-worthy fact — and there are probably plenty more counters like this we haven't even thought to look at yet.

### 2. Head-to-head on the *core* resources (and on combat)

We bicker (jokingly) all the time about who's actually pulling their weight — *"why are you just running around and not chopping?"* — and it'd be cool to settle these with hard per-player counters. Examples of the kind of thing that'd land:

- **Wood mined** (oak / spruce / birch — broken down or summed)
- **Stone / cobblestone mined**
- **Coal / iron / diamonds mined**
- **Mobs killed** (combat / food)
- **Damage dealt and damage taken** — who's actually in the fight, who's hanging back, and who's getting wrecked
- **Food eaten** (who's burning through all the bread?)

…and similar comparisons on whatever else feels meaningful. The "View: All / per-player" toggle on page 2 is exactly the right vehicle for this.

> The data for most of this already lives in `data/live_stats_*.csv` (we just don't surface every counter yet). If a section above feels under-explored, the fix is usually a new chart on page 2, not a new parser.
