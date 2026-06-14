# Veridex — Brand Spec

> Machine-readable brand guideline. Paste into any AI tool to produce on-brand work.
> Generated to satisfy the `/build-a-brand` intent directly in code (the full 15-page
> PDF pipeline requires the Pika MCP agent — initialize it on pika.me to render the book).

## Quick reference

| | |
|---|---|
| **Name** | Veridex |
| **Tagline** | Every IMEI, verified in seconds. |
| **Category** | Device verification / IMEI intelligence service |
| **Signature color** | Scan Teal `#10D0BE` |
| **Ink** | Space Navy `#0A1124` |
| **Display font** | Space Grotesk |
| **Body font** | Inter |
| **Mono font** | JetBrains Mono (IMEI digits, codes, statuses) |
| **Voice** | Precise · confident · reassuring · technical-but-human |

## Positioning

Veridex turns a 15-digit number into a clear answer. Where competitors bury results in
clunky dashboards and cryptic codes, Veridex gives a buyer or seller a plain-language
verdict — *clean, blacklisted, locked, or stolen* — fast enough to use mid-conversation
in a marketplace deal.

**Audience**
- **Primary:** second-hand phone buyers/sellers who need to verify a device *before money changes hands*.
- **Secondary:** small repair shops & resellers checking stock; travelers verifying carrier/SIM-lock status.
- **Anchor persona:** Maya, 27, buying a used iPhone from a marketplace listing — she wants to know in 60 seconds whether it's stolen or iCloud-locked before she meets the seller.

## Brand foundation

- **Mission:** make device history transparent, so no one buys a locked or stolen phone again.
- **Values:** Clarity over jargon · Speed without sloppiness · Honest verdicts (we say "we don't know" when we don't).
- **Why it exists:** A used phone can hide a blacklist, an unpaid bill, or an iCloud lock that makes it a brick. The data to catch that exists — it's just locked behind carrier and registry systems. Veridex queries those sources and returns one readable answer.

## Color system

| Token | Hex | Role |
|---|---|---|
| `--ink` | `#0A1124` | Primary / headings on light, dark surfaces |
| `--ink-2` | `#131C33` | Elevated dark surface |
| `--ink-3` | `#1E2A44` | Dark borders / hairlines |
| `--paper` | `#F6F8FC` | App background |
| `--surface` | `#FFFFFF` | Cards |
| `--brand` (Scan Teal) | `#10D0BE` | Signature accent, scan motif |
| `--brand-deep` | `#0BA89E` | Teal hover / text-on-light |
| `--electric` | `#4F7CFF` | Secondary accent, gradient end |
| `--verified` | `#1FBF6B` | Status: clean / unlocked |
| `--warning` | `#F6A623` | Status: caution / pending |
| `--danger` | `#FF5470` | Status: blacklisted / locked / stolen |
| `--text` | `#0A1124` | Body text on light |
| `--text-muted` | `#48566F` | Secondary text on light (≥4.5:1 on paper) |

**Signature gradient:** `linear-gradient(135deg, #10D0BE 0%, #4F7CFF 100%)` — the "scan" gradient. Use on the logo mark, the scan beam, and one primary CTA per screen. Never as a full-page wash.

## Typography

- **Display — Space Grotesk** (600/700): headings, the wordmark, big numbers. Technical character, slightly condensed.
- **Body — Inter** (400/500/600): UI, paragraphs, labels.
- **Mono — JetBrains Mono** (500, tabular): IMEI digits, order references, status codes. Always tabular figures so digits don't shift.

Scale (px): 12 · 14 · 16 · 18 · 22 · 28 · 36 · 48 · 64. Body 16px min, line-height 1.6.

## Logo

- **Mark:** a squircle "scan badge" — gradient stroke, an inner checkmark that doubles as a *V*, crossed by a horizontal scan line. Reads at 16×16 (favicon) and 512×512.
- **Wordmark:** `veridex` set in Space Grotesk, lowercase, tight tracking, with the `i` dot recolored Scan Teal.
- **Lockup:** mark + wordmark, horizontal. Clear space = height of the mark on all sides.

## Voice & tone

- **Headline:** "Is this phone clean? Find out before you pay."
- **Button:** "Verify IMEI" / "Run the check" (never "Submit").
- **Result (clean):** "Clean. No blacklist, no lock. Safe to buy."
- **Result (flagged):** "Flagged. This device is reported lost or stolen. Do not buy."
- **Error:** "That's not a valid IMEI — it should be 15 digits. Dial *#06# on the phone to find it."
- **Forbidden words:** premium, cutting-edge, revolutionary, seamless, world-class, unlock magic.

## Do & don't

- **Do** lead with the verdict, then the detail.
- **Do** use the mono font for every IMEI and reference number.
- **Do** keep the scan-teal for *one* signature moment per screen.
- **Don't** wash whole pages in the gradient.
- **Don't** use emoji as icons (use the SVG set).
- **Don't** promise outcomes we can't verify — say "we couldn't reach the registry" honestly.
