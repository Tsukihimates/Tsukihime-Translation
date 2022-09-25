# Editing guidelines

In this document, we define some semantic, syntaxic and and grammatic guidelines concerning the speech patterns of some *Tsukihime Remake* characters that Nasu wrote specifically to be *excentric*, be it in speech or behavior, compared to others. That's is why it is particularly important to try to convey as much as possible their quirks in english.

The first general rule guiding your translation/editing should always be to try to convey meaning and atmosphere over exact structure. More precisely, you should always try to stick as close as possible to japanese for the structure of the sentence and the vocabulary used, unless a direct translation is not possible. This can be due in particular to unique idioms or references, to some vernacular grammatical or syntaxic element or to Nasu *unconventional*, to say the least, use of furigana/ruby. In this case, you must prioritize the precise meaning, feeling and emotion conveyed by the sentence over the exact same structure: when the player reads a sentence said by a fancy character, he should wonder **WHY** the character is saying it rather than **WHAT** the sentence means.

This is a <u>difficult exercise</u>. Whenever you're unsure of what to do with a particularly complex sentence, the best course of action would be to collect as much raw information as possible from the Japanese sentence and then ask for help in the #editing channel, so the other editors can think together on how convey what should be <u>conveyed the best</u>.

## General guidelines

- When a sentence starts with a 'stutter' (e.g. 「そ、そんなコト...」), then the
  duplicated translated sentence should keep case (e.g. N-No, that's not...).
- When translating active speech (voiced lines), the text should be enclosed in
  double quotes
  - > "This is someone actively speaking a voiced line"
- When translating active speech that contains quoted references, the inner
  quotes should be single quotes (')
  - > "This is someone speaking an actively voiced line referencing 'that' thing"
- When translating passive speech (narration that references a previous phrase or
  voiced line), the quoted text should be in single quotes
  - > When I think about the time they said 'this is someone actively speaking', I blah blah
  - Note that if passive text contains single quote characters, those characters
    remain as single quotes
    - > When I think about the time they said 'this is someone talking about 'that' thing', I blah blah
- For 'lead in' or 'lead out' of sentences (e.g.  "―――Nii-san," or "this time―――"),
  use 3 CJK dashes not ASCII dashes, since the game will combine the unicode ones into a single solid line.
- Abruptly cut-off sentences should also use 3 CJK dashes (e.g. "What are you talking ab―――")A.
- For in-sentence em-dashes, use 2 CJK dashes (e.g. "this tea――it's incredible!").
- Do NOT use CJK space characters (u3000), as these render at a different width than normal ascii space characters
- Do NOT use CJK ellipsis (…), it renders vertically justified. Replace with three ASCII dots.
- When ruby text is used, YOU MUST playtest the changes and add spaces to justify the text correctly.
  - The text renders too far to the right by default - append spaces to the ruby text to shift it left
  - The text renders very close together - for each character to display, insert an extra ' ' after it ('real' spaces become two spaces) to expand the text.
- When glueing lines, the '#' must be attached to the _preceding_ line in the event of a space.
  - Correct: `This is the first line.# This is the second line`
  - WRONG: `This is the first line. #This is the second line`
- In all sentences, the word 'anyway' should be used instead of 'anyways'
- All choices should be prefaced with a single space (e.g. `C:> Choice one`) so that choices beginning with ... are not merged with the choice numbering dots
- All choice options should start with a capital letter

***


## Specific characters

### Shiki(s)

When translating a particular reference to a Shiki, format the name accordingly:
- 志貴: Shiki
- 四季: SHIKI
- シキ: _Shiki_

### Noel

Noel tries to sound *young* and *appealing*, and at the same time a bit provocative, sometimes seducing. To convey this character, we will use a vocabular and grammar that can be sometimes a bit slangish or colloquial (e.g. "ain't", "Nah", etc.), we'll do heavy elision of words when necessary, but not too frequently (e.g. "y'know", etc.) and a bit provocative general tone.

Once she switches personality (going for the *nun mode*) she will not use elisions at all.

**<u>Sample sentence</u>**: "Huh? What's up with this atmosphere? Everyone suddenly froze up.. What's that, I'm a Basilisk woman? # Nah, the metaphor ain't clear, is it. Erm, in proper japanese, I'd be that TV haunting girl? But Sensei's name isn't Sadako y'know" (*filename 02_00_ARC02_1_1, page 6, line 2941*)

### Arihiko

Arihiko is a thug, but he's the usual cliché of the goofy thug with a golden heart helping the protagonist. In order to convey this and not to overstep Noel's speech pattern, we will use in his lines funny or weird idioms/expressions (they can be a bit old for example, or he can have an off-beat style), but a the same time some cursing ("what the hell", etc.) and sometimes elisions.

**Sample sentence**: "Tohno's picking up chicks? What the hell is going on? I thought you weren't interested in 'em." (*original VN*)

### Dr. Arach

Dr. Arach is a complete weirdo, and something of a *mad biologist*. Conveying her speech is probably the most difficult, but here are some guiding principles: she expresses herself in a very bombastic way, i.e. using exaggerations and a refined vocabulary ("Oh, sublime sugar!"), and sometimes she does biological/medical comparisons, and in this case we have to make these parts overly serious. The idea is to induce burlesque/surreal humor by creating a mismatch between the technical parts and the bombastic parts.

**Sample sentence:** "Oooh, sublime sugar! You're pervading all five of my senses! You're even making my uterus and my ovaries melt.. I feel it coming! Haah.. Thanks for the meaaal!" (*filename 02_00_ARC02_1B, page 39, line 2802*)

Arach has many different designators. For consistency, use:
阿良句先生 - Arach-sensei
阿良句医師 - Dr. Arach
阿良句博士 - Prof. Arach
阿良句女史 - Ms. Arach
阿良句氏 - Arach-shi


### Other characters

Here are some general specificities for other characters

## Contractions

All characters use contractions. However, the frequency of use and general
'tone' of each character is different. The following characters may be more
prone to casual speech:

- Shiki
- Arcueid
- Ciel
- Mio
- Saiki
- Satsuki
- All other students and teachers

Whereas these characters may tend to speak more formally:

- Akiha
- Hisui
- Vlov
- Roa

For these characters, it will really depend on the situation:

- Kohaku

### Ruby/furigana/gloss

1) **The normal use:** The ruby indicates the standard pronunciation of the word
Example: 琥珀さんは着物の<袖|そで>から、こそっと携帯電話を取りだした
そで is the standard pronunciation of 袖
**EN:** Disregard it entirely.

2) **The “different-but-close” use:** The ruby is a word that is different from what’s under but only slightly different in meaning, giving a nuance but not a whole different meaning.
Example: 遠野邸は<総|ま><耶|ち>の端に位置し
総耶 is pronounced Souya, the city in which Tsukihime takes place. The ruby is まち meaning “city”.
Other examples: <報道|ニュース>, <男子組|なかまたち>, <槙久|オヤジ> , <棘|パワー>, <思考|あたま>, <幻|ゆ><覚|め>, <筋力|ちから>, <彫刻品|オブジェ>, <怪物|ヴローヴ>
**EN:** Take one, either the ruby and what’s glossed (what’s under the ruby) but we won’t keep two words in English.

3) **The “too-important” use:** The ruby really gives an additional meaning to what’s glossed. Obviously, there is some personal interpretation to whether a gloss in English is necessary or not. But some cases should be clear enough.
Example: <獲物|おんな> (<prey|woman>)
**EN:** You can keep the ruby here. Sometimes, it’s possible to write explicitly the ruby and the glossed word in the sentence. In case of doubt especially if you’re first to do the file, keep the ruby, the various proofreadings will decide at a later point.
Note: There is also the emphasis dot, things like: <ひ|・><と|・><り|・><だ|・><け|・><世|・><界|・><が|・><違|・><う|・>. This is a way in Japanese to put emphasis, similar to bold or italics in English.

Overall, ruby whatever its purpose is something very familiar to a Japanese reader. It doesn’t exist in English but the game engine still gives us the possibility to use it. It can be useful but will necessarily be seen as intrusive in English. So we should keep it to a minimum.

One last thing, it is also possible to add ruby in the English translation where it wasn’t in Japanese. Use your discretion, but it can be an inventive way to get out of formulations that are too convoluted in English while retaining a nuance you don’t want to lose.

### Time Format

Whenever time is mentioned in the script, it should be written in the o'clock format.

For example
- > "The night just turned past nine o'clock"

However, if the time has minutes, then leave it as it is.

For example
- > "The time is 7:30 AM"
- > "The time is 6:33 PM"

### Ellipses

When ellipses are used after a word, leave a space before typing the next word.
- Example:
    - > Everything suddenly froze in place... etc etc

When ellipses are used at the beginning of a sentence, do not leave a space.
- Example:
    - > "...I see"

### Special Terms

Vampire ranks:
- 死者: The Dead. In Japanese, this is used to refer to both Rank I vampires,
      and also the group containing all vampires in ranks I to III. When
      translating this word in a context where the use is confusing, then use
      'The Dead' to refer to the group, and 'Corpse' to return to Rank I
      vampires.
- 屍鬼: Ghoul
- 不死: Undead
- 夜属: Nightkin
- 夜魔: Nightmare
- 死徒: Dead Apostle

Vampire husbandry related terms:
- 親基: Usually parent vampire / parent.
- 親: When used in quotes in the source text, 'Sire'
