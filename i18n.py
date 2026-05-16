import streamlit as st


LANG_OPTIONS = {
    "ru": "Русский",
    "en": "English",
}


def language_selector():
    selected = st.sidebar.radio(
        "Язык / Language",
        options=[LANG_OPTIONS["ru"], LANG_OPTIONS["en"]],
        index=0,
        key="hc_lang",
        horizontal=True,
    )
    return "ru" if selected == LANG_OPTIONS["ru"] else "en"


def tr(lang, en, ru):
    return ru if lang == "ru" else en


def unit_hours(lang):
    return tr(lang, "h", "ч")


def unit_minutes(lang):
    return tr(lang, "min", "мин")


def outcome_label(value, lang, compact=False):
    labels = {
        "died": {
            "en": "Died",
            "ru": "Смерть",
        },
        "skipped": {
            "en": "Rerolled" if compact else "Skipped (no death)",
            "ru": "Реролл" if compact else "Реролл без смерти",
        },
    }
    return labels.get(value, {}).get(lang, value)


def cause_label(value, lang):
    labels = {
        "Mob": {"en": "Mob", "ru": "Мобы"},
        "Environment": {"en": "Environment", "ru": "Среда"},
        "PvP": {"en": "PvP", "ru": "PvP"},
        "Other": {"en": "Other", "ru": "Другое"},
    }
    return labels.get(value, {}).get(lang, value)


# Players whose Russian verbs must use feminine past-tense forms.
# Single-source-of-truth for gender; expand if a new female player joins.
FEMALE_PLAYERS = {"trofimova2002"}


def is_female(player: str) -> bool:
    return player in FEMALE_PLAYERS


def ru_verb(player: str, masc: str, fem: str) -> str:
    """Pick the past-tense form that agrees with the player's grammatical gender.

    Use in f-strings like:  f"{player} {ru_verb(player, 'умер', 'умерла')}"
    """
    return fem if is_female(player) else masc


DEATH_MESSAGES_RU = {
    "drowned": "утонул",
    "fell from a high place": "разбился насмерть",
    "hit the ground too hard": "разбился вдребезги",
    "tried to swim in lava": "решил поплавать в лаве",
    "was blown up by Creeper": "был взорван Крипер",
    "was burned to a crisp while fighting Blaze": "был сожжен дотла, пока боролся с Всполох",
    "was doomed to fall by Ghast": "был обречен на падение благодаря Гаст",
    "was impaled by Drowned": "был пронзен Утопленник",
    "was impaled on a stalagmite": "был пронзен сталагмитом",
    "was killed by Ender Dragon using magic": "был убит Эндер-дракон с помощью магии",
    "was shot by Skeleton": "был застрелен Скелет",
    "was shot by axantroff": "был застрелен axantroff",
    "was slain by Blaze": "был убит Всполох",
    "was slain by Enderman": "был убит Эндермен",
    "was slain by Husk": "был убит Кадавр",
    "was slain by Iron Golem": "был убит Железный голем",
    "was slain by MurzichAI": "был убит MurzichAI",
    "was slain by Piglin": "был убит Пиглин",
    "was slain by Polar Bear": "был убит Белый медведь",
    "was slain by Wolf": "был убит Волк",
    "was slain by Zombie": "был убит Зомби",
    "was slain by axantroff": "был убит axantroff",
    "went up in flames": "умер в огне",
}

# Feminine counterparts — used when the player is in FEMALE_PLAYERS.
DEATH_MESSAGES_RU_FEMININE = {
    "drowned": "утонула",
    "fell from a high place": "разбилась насмерть",
    "hit the ground too hard": "разбилась вдребезги",
    "tried to swim in lava": "решила поплавать в лаве",
    "was blown up by Creeper": "была взорвана Крипером",
    "was burned to a crisp while fighting Blaze": "была сожжена дотла, пока боролась со Всполохом",
    "was doomed to fall by Ghast": "была обречена на падение благодаря Гасту",
    "was impaled by Drowned": "была пронзена Утопленником",
    "was impaled on a stalagmite": "была пронзена сталагмитом",
    "was killed by Ender Dragon using magic": "была убита Эндер-драконом с помощью магии",
    "was shot by Skeleton": "была застрелена Скелетом",
    "was shot by axantroff": "была застрелена axantroff",
    "was slain by Blaze": "была убита Всполохом",
    "was slain by Enderman": "была убита Эндерменом",
    "was slain by Husk": "была убита Кадавром",
    "was slain by Iron Golem": "была убита Железным големом",
    "was slain by MurzichAI": "была убита MurzichAI",
    "was slain by Piglin": "была убита Пиглином",
    "was slain by Polar Bear": "была убита Белым медведем",
    "was slain by Wolf": "была убита Волком",
    "was slain by Zombie": "была убита Зомби",
    "was slain by axantroff": "была убита axantroff",
    "went up in flames": "сгорела заживо",
}


def death_message_label(message, lang, player=None):
    """Translate a death message into the target language.

    When `lang == 'ru'` and `player` is female, returns the feminine form so
    things like trofimova2002's deaths read as "была убита" instead of
    "был убит".
    """
    if lang != "ru":
        return message
    if player and is_female(player):
        return DEATH_MESSAGES_RU_FEMININE.get(
            message, DEATH_MESSAGES_RU.get(message, message)
        )
    return DEATH_MESSAGES_RU.get(message, message)


ADVANCEMENTS_RU = {
    "A Seedy Place": "Поле чудес",
    "A Terrible Fortress": "Чертоги страха",
    "Acquire Hardware": "Куй железо...",
    "Bee Our Guest": "Пора подкрепиться",
    "Best Friends Forever": "Друг человека",
    "Cover Me with Diamonds": "Осыпь меня алмазами",
    "Crafting a New Look": "С чистого литья",
    "Diamonds!": "Алмазы!",
    "Eye Spy": "Недреманное око",
    "Fishy Business": "На крючке",
    "Getting an Upgrade": "Обновка!",
    "Hot Stuff": "Горячая штучка",
    "Ice Bucket Challenge": "Две стихии",
    "Into Fire": "В полымя",
    "Isn't It Iron Pick": "И кирка без дела ржавеет",
    "Minecraft: Trial(s) Edition": "Minecraft: пробное издание",
    "Monster Hunter": "Охотник на монстров",
    "Not Today, Thank You": "Не дождётесь!",
    "Spooky Scary Skeleton": "Бедный Йорик!",
    "Stone Age": "Каменный век",
    "Suit Up": "Дресс-код",
    "Sweet Dreams": "Спи, моя радость, усни",
    "Take Aim": "Точно в цель",
    "The End?": "Конец?",
    "The Parrots and the Bats": "Романтический ужин",
    "Those Were the Days": "Наф-Наф тут больше не живёт",
    "Voluntary Exile": "Добровольное изгнание",
    "We Need to Go Deeper": "Огненные недра",
    "What a Deal!": "Не отходя от кассы!",
}


ADVANCEMENT_IDS_RU = {
    "minecraft:adventure/adventuring_time": "Время приключений",
    "minecraft:adventure/kill_a_mob": "Охотник на монстров",
    "minecraft:adventure/kill_all_mobs": "Зверобой",
    "minecraft:adventure/minecraft_trials_edition": "Minecraft: пробное издание",
    "minecraft:adventure/root": "Приключения",
    "minecraft:adventure/shoot_arrow": "Точно в цель",
    "minecraft:adventure/sleep_in_bed": "Спи, моя радость, усни",
    "minecraft:adventure/trade": "Не отходя от кассы!",
    "minecraft:husbandry/balanced_diet": "Робин-Бобин",
    "minecraft:husbandry/root": "Сельское хозяйство",
    "minecraft:nether/explore_nether": "Горящий тур",
    "minecraft:nether/find_fortress": "Чертоги страха",
    "minecraft:nether/obtain_blaze_rod": "В полымя",
    "minecraft:nether/root": "Незер",
    "minecraft:story/deflect_arrow": "Не дождётесь!",
    "minecraft:story/enter_the_nether": "Огненные недра",
    "minecraft:story/form_obsidian": "Две стихии",
    "minecraft:story/iron_tools": "И кирка без дела ржавеет",
    "minecraft:story/lava_bucket": "Горячая штучка",
    "minecraft:story/mine_diamond": "Алмазы!",
    "minecraft:story/mine_stone": "Каменный век",
    "minecraft:story/obtain_armor": "Дресс-код",
    "minecraft:story/root": "Minecraft",
    "minecraft:story/shiny_gear": "Осыпь меня алмазами",
    "minecraft:story/smelt_iron": "Куй железо...",
    "minecraft:story/upgrade_tools": "Обновка!",
}


def advancement_label(name, lang):
    if lang == "ru":
        return ADVANCEMENTS_RU.get(name, name)
    return name


def advancement_id_label(advancement_id, fallback, lang):
    if lang == "ru":
        return ADVANCEMENT_IDS_RU.get(advancement_id, fallback)
    return fallback


ITEMS_RU = {
    "air": "Воздух",
    "andesite": "Андезит",
    "apple": "Яблоко",
    "arrow": "Стрела",
    "beef": "Сырая говядина",
    "beetroot": "Свёкла",
    "beetroot_seeds": "Семена свёклы",
    "beetroots": "Свёкла",
    "birch_button": "Берёзовая кнопка",
    "birch_log": "Берёзовое бревно",
    "birch_planks": "Берёзовые доски",
    "birch_sapling": "Саженец берёзы",
    "blast_furnace": "Плавильная печь",
    "blaze": "Всполох",
    "blaze_rod": "Огненный стержень",
    "blue_bed": "Синяя кровать",
    "bone": "Кость",
    "bow": "Лук",
    "bread": "Хлеб",
    "bucket": "Ведро",
    "bush": "Куст",
    "carrot": "Морковь",
    "carrots": "Морковь",
    "chainmail_helmet": "Койф",
    "chainmail_leggings": "Кольчужные поножи",
    "chest": "Сундук",
    "chicken": "Сырая курица",
    "coal": "Уголь",
    "coal_ore": "Угольная руда",
    "cobbled_deepslate": "Колотый глубинный сланец",
    "cobblestone": "Булыжник",
    "composter": "Компостница",
    "cow": "Корова",
    "crafting_table": "Верстак",
    "creeper": "Крипер",
    "dandelion": "Одуванчик",
    "deepslate": "Глубинный сланец",
    "deepslate_diamond_ore": "Алмазоносный глубинный сланец",
    "deepslate_gold_ore": "Золотоносный глубинный сланец",
    "deepslate_iron_ore": "Железоносный глубинный сланец",
    "diamond": "Алмаз",
    "diamond_boots": "Алмазные ботинки",
    "diamond_chestplate": "Алмазный нагрудник",
    "diamond_helmet": "Алмазный шлем",
    "diamond_leggings": "Алмазные поножи",
    "dirt": "Земля",
    "dirt_path": "Тропинка",
    "dripstone_block": "Натёчный камень",
    "egg": "Яйцо",
    "emerald": "Изумруд",
    "feather": "Перо",
    "fire": "Огонь",
    "fletching_table": "Стол лучника",
    "flint": "Кремень",
    "flint_and_steel": "Огниво",
    "furnace": "Печь",
    "glass": "Стекло",
    "glass_pane": "Стеклянная панель",
    "glow_ink_sac": "Светящийся чернильный мешок",
    "granite": "Гранит",
    "grass_block": "Дёрн",
    "gravel": "Гравий",
    "grindstone": "Точило",
    "gunpowder": "Порох",
    "hay_block": "Сноп сена",
    "iron_axe": "Железный топор",
    "iron_boots": "Железные ботинки",
    "iron_ingot": "Железный слиток",
    "iron_leggings": "Железные поножи",
    "iron_ore": "Железная руда",
    "iron_pickaxe": "Железная кирка",
    "jump": "Прыжков",
    "lantern": "Фонарь",
    "lava_bucket": "Ведро лавы",
    "leaf_litter": "Сухие листья",
    "leather": "Кожа",
    "magma_cube": "Магмовый куб",
    "nether_bricks": "Незерские кирпичи",
    "oak_door": "Дубовая дверь",
    "oak_fence": "Дубовый забор",
    "oak_fence_gate": "Дубовая калитка",
    "oak_leaves": "Дубовые листья",
    "oak_log": "Дубовое бревно",
    "oak_planks": "Дубовые доски",
    "oak_sapling": "Саженец дуба",
    "oxeye_daisy": "Ромашка",
    "pig": "Свинья",
    "podzol": "Подзол",
    "pointed_dripstone": "Капельник",
    "porkchop": "Сырая свинина",
    "potato": "Картофель",
    "pumpkin_pie": "Тыквенный пирог",
    "raw_gold": "Рудное золото",
    "raw_iron": "Рудное железо",
    "red_bed": "Красная кровать",
    "rotten_flesh": "Гнилая плоть",
    "sand": "Песок",
    "shield": "Щит",
    "short_grass": "Низкая трава",
    "skeleton": "Скелет",
    "spawner": "Рассадник монстров",
    "spruce_door": "Еловая дверь",
    "spruce_fence": "Еловый забор",
    "spruce_leaves": "Хвоя",
    "spruce_log": "Еловое бревно",
    "spruce_planks": "Еловые доски",
    "spruce_sapling": "Саженец ели",
    "spruce_trapdoor": "Еловый люк",
    "stick": "Палка",
    "stone": "Камень",
    "stone_axe": "Каменный топор",
    "stone_pickaxe": "Каменная кирка",
    "stone_shovel": "Каменная лопата",
    "stone_slab": "Каменная плита",
    "stone_sword": "Каменный меч",
    "stripped_spruce_log": "Обтёсанное еловое бревно",
    "sugar_cane": "Сахарный тростник",
    "suspicious_stew": "Загадочное рагу",
    "tall_grass": "Высокая трава",
    "torch": "Факел",
    "tuff": "Туф",
    "wall_torch": "Настенный факел",
    "water_bucket": "Ведро воды",
    "wheat": "Пшеница",
    "wheat_seeds": "Семена пшеницы",
    "white_bed": "Белая кровать",
    "wither_skeleton": "Визер-скелет",
    "wooden_axe": "Деревянный топор",
    "wooden_pickaxe": "Деревянная кирка",
    "zombie": "Зомби",
    "zombie_villager": "Крестьянин-зомби",
}


def item_label(item, lang):
    if lang == "ru":
        return ITEMS_RU.get(item, item.replace("_", " "))
    return item.replace("_", " ").title()


def fmt_pct(value, lang):
    if lang == "ru":
        return f"{value:.0f}%"
    return f"{value:.0f}%"
