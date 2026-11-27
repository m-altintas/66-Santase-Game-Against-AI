# Santase rules (rules version 1)

Status: **approved** 2026-11-27 (reviewed by Mehmet with his father).

This file is the specification the engine is tested against. Every rule has an ID; every ID has
at least one test. Where sources disagree, the chosen option and the alternatives are listed.

Sources:

- **BG**: belot.bg, Santase rules, Bulgarian page <https://belot.bg/santase/rules/> (primary)
  and English page <https://belot.bg/en/rules-santase/>
- **WB**: Bulgarian Wikipedia, "Сантасе", <https://bg.wikipedia.org/wiki/Сантасе>
- **LB**: lan.bg, Santase 66 online rules, <https://lan.bg/Online/santase66> (an online
  variant; used only for comparison)
- **NE**: NikolayIT/SantaseGameEngine `RULES.md` (MIT), Bulgarian variant as used in that
  engine's AI competitions, <https://github.com/NikolayIT/SantaseGameEngine>
- **PG**: pagat.com, Sechsundsechzig, <https://pagat.com/marriage/66.html> (German 66, for
  comparison)

Principle for choices: follow the Bulgarian sources (BG, NE); where they are silent or split,
take the option that keeps decisions meaningful without adding hidden traps.

## 1. Cards and deal

- **R1.1** 24 cards: 9, J, Q, K, 10, A in four suits. Rank, low to high: 9, J, Q, K, 10, A.
  Card points: A 11, 10 10, K 4, Q 3, J 2, 9 0 (120 in total). (BG, NE, PG)
- **R1.2** The dealer's opponent cuts. Deal in packets of three, non-dealer first: 3 to the
  opponent, 3 to the dealer, 3 to the opponent, 3 to the dealer. Then the 13th card is turned
  face up as the trump card; it defines the trump suit, lies at the bottom of the talon and is
  drawn last. The talon holds 12 cards including the trump card. (BG Bulgarian page, WB, LB;
  matches Mehmet's family. The BG English page turns the trump between the packets, which gives
  the same card distribution.)
- **R1.3** The non-dealer leads the first trick.

## 2. Tricks and drawing

- **R2.1** The leader plays any legal card; the follower answers. The higher trump wins;
  otherwise the higher card of the led suit wins. A follower card that is neither a trump nor
  of the led suit always loses, whatever its rank. Every trick has exactly one winner.
- **R2.2** While the talon is open and not exhausted, the follower may play any card. (BG, NE, PG)
- **R2.3** After each trick, while the talon is open, the trick winner draws first, then the
  loser. When one face-down card and the trump card remain, the winner draws the face-down card
  and the loser takes the trump card. (PG; implied by NE)
- **R2.4** The trick winner leads the next trick.

## 3. Strict play (talon exhausted or closed)

- **R3.1** Once the talon is exhausted or closed, the follower must follow suit; if able to,
  must win the trick (play higher in the led suit); if void in the led suit, must play a trump;
  only when holding neither may any card be played. (NE, PG; BG states follow-suit and trump.)

## 4. Trump exchange

- **R4.1** The player on lead holding the 9 of trumps may exchange it for the trump card, before
  leading, while the talon holds more than 2 cards, not on the first trick, and not after the
  talon is closed. (BG, NE)
  - Note: "on lead, not on the first trick" already implies a trick won, so PG's "trick
    already won" condition adds nothing.
  - *Alternatives:* PG allows an exchange at the moment the opponent closes. Mehmet's family
    also exchanges with exactly 2 cards in the talon. Neither adopted.

## 5. Closing

- **R5.1** The player on lead may close the talon before leading, not on the first trick, while
  the talon holds more than 2 cards. The trump card is turned face down; no more cards are drawn
  and R3.1 applies. (NE)
  - *Alternative:* PG also allows closing with exactly 2 cards left. Not adopted.
- **R5.2** On the same lead a player may, in order: exchange the 9 (R4), close (R5), announce a
  marriage (R6), play a card. (NE)
- **R5.3** Closer reaches 66: game points as in R8.1, with the opponent's card points and tricks
  counted at the end of the deal. (NE, PG)
- **R5.4** Closer fails to reach 66 (or the opponent reaches 66 first): the opponent gets
  2 game points, or 3 if the opponent has no trick. (BG, WB; the sources name no subject for
  "has no trick", the natural reading is the opponent, counted at the end of the deal.)
  - *Alternatives:* NE and LB give a flat 3. PG gives 2 or 3 depending on whether the opponent
    had won a trick at the moment of closing. Not adopted.
- **R5.5** No last-trick bonus after a close (R7).

## 6. Marriages

- **R6.1** Holding K and Q of the same suit, the player on lead may announce a marriage before
  leading: 20 card points, 40 in trumps. At most one marriage per lead, and one of the two cards
  must be led at once. (NE, PG; BG gives 20/40 without detail.)
- **R6.2** Not on the first trick. Since announcing needs the lead, a player can only announce
  after winning a trick, so marriage points are never held by a player without a trick. (NE)
  - *Alternative:* PG lets the non-dealer announce on trick 1, counting only after a trick is won.
- **R6.3** Marriages remain allowed after the talon is exhausted or closed. (NE)
  - *Alternative:* PG forbids marriages once the talon is exhausted.

## 7. Last trick

- **R7.1** When the talon ran out naturally and all 12 tricks are played, the winner of the last
  trick gets 10 extra card points. Not after a close. (NE, PG)

## 8. End of the deal and scoring

- **R8.1** **Going out: declared.** A player who believes their card points (tricks plus
  marriages) are 66 or more may declare "out", only right after winning a trick or right after
  announcing a marriage. Play stops at once and the points are counted. (BG, PG)
  - Correct (66 or more): the declarer wins: 3 game points if the opponent has no trick, 2 if
    the opponent has fewer than 33 card points, otherwise 1. (BG, NE, PG)
  - **R8.1a** Wrong (fewer than 66): the opponent wins the deal and gets 2 game points, or 3
    if the opponent has no trick. Never 1. (BG, WB; PG gives a flat 2.) A closer who declares
    wrong is covered by R5.4, which gives the same points.
  - Declaring is optional. A player at 66 or more who does not declare plays on; the next
    chance comes after their next won trick or marriage, and the opponent may declare first.
    (PG; BG silent)
  - Running scores are hidden: the UI never shows card points during play, and the bots get
    no more information than a human would. (Mehmet: counting in your head is part of the game.)
  - Bots see only what a human at the table saw, but they recall all of it perfectly (played
    cards, won tricks, marriages, their own points). This is accepted: memory is a skill, not
    hidden information. Weaker difficulty levels may model imperfect recall instead.
- **R8.1b** Won tricks are turned face down and may not be looked at during the deal, and
  scores may not be written down. (BG; matches Mehmet's family.)
  - *Alternatives, later game settings:* last trick only (PG); all own tricks visible, an
    "easy mode" (LB).
- **R8.2** If all cards are played and nobody declared, the player with more card points
  (including R7.1) wins with game points as in R8.1. Equal points: no game points, and the
  same dealer deals again. (NE, PG)
- **R8.3** R5.3 and R5.4 override R8.1 and R8.2 when the talon was closed. When the hands
  run out after a close and nobody declared, the closer wins if they have 66 or more (R5.3),
  otherwise R5.4 applies; no declaration is needed once every card is played.

## 9. Match

- **R9.1** The first player to reach 11 game points wins the match. (BG, NE)
- **R9.2** The winner of a deal deals the next one; the non-dealer leads (R1.3). (NE, PG)

## Decisions

- 2026-11-27: Mehmet reviewed every section with his father. Bulgarian rules are kept as the
  standard throughout. Changes from the first draft: R8.1 (declared "out" instead of
  automatic), and R1.2, R5.4, R8.1a, R8.1b aligned with the Bulgarian-language BG page and
  WB. House variants are noted but not adopted; configurable rules may come later as game
  settings.
- 2026-11-27, engine: R8.3 spells out how a closed deal ends when the hands run out.

## Open questions for Mehmet

- None. R8.1a, R8.1b and the close-then-wrong case were settled from BG and WB on
  2026-11-27.
