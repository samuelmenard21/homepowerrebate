# Installer Outreach

Goal: get listed installers to link back to their HomePowerRebate profile.
Backlinks from ~90 BC-domain local businesses is the strongest available signal
for local search, and it opens the relationship for paid placement later.

---

## Before sending: CASL

You're a Canadian business emailing Canadian businesses, so Canada's
Anti-Spam Legislation applies. Penalties run to $10M, so this isn't optional
detail.

**Why this is permitted.** CASL recognises *implied consent* through
"conspicuous publication": if a business publishes its email address publicly
(on its own website), doesn't state that it refuses unsolicited commercial
messages, and your message is relevant to its business role — you may send.
Every address in `installer-emails.csv` was scraped from a public page on the
company's own site, and a note about their listing in a BC installer directory
is squarely relevant to their business. That's the exemption.

**What's still required on every message:**

1. **Identify yourself** — real name and business name, no ambiguity.
2. **Contact info** — a mailing address plus a phone number or email, valid for
   at least 60 days after sending.
3. **A working unsubscribe** — functional for at least 60 days, honoured within
   10 business days.

A cold blast from personal Gmail with no unsubscribe line violates CASL even
with implied consent. Send it through a proper email tool (Mailchimp handles
identification and unsubscribe automatically) rather than by hand.

**Also honour the spirit of it.** If someone asks to be removed, remove them
that day. This list is a long-term asset; burning it for a few extra sends is a
bad trade.

---

## Deliverability

Sending ~90 cold emails in one burst from a domain with no sending history is
the fastest way to land in spam permanently, and it can damage the domain for
ordinary mail too.

- Set up SPF, DKIM and DMARC on homepowerrebate.com **first**
- Send in batches of 15–20 per day, not all at once
- Plain text beats heavy HTML for this kind of message
- Personalise the subject with the city — generic subjects get filtered

---

## Sequence

Order matters. Don't send until the thing you're pointing at exists.

1. Generate the installer profile pages
2. Deploy them (live URLs)
3. Verify a few pages render and the details are accurate
4. Then send, in daily batches

Emailing someone a link to a page that doesn't exist yet wastes the one
introduction you get.

---

## Draft

Subject: `You're listed on HomePowerRebate ({City} installers)`

```
Hi {Business Name},

I run HomePowerRebate — a free guide to BC home energy rebates covering
heat pumps, solar, batteries and insulation. We list installers by city so
homeowners working out what they qualify for can find someone local.

You're listed here:
{profile_url}

The details came from your Google Business Profile ({rating}★, {reviews}
reviews). If anything's out of date, reply and I'll correct it.

Two things:

1. If you'd like a "Listed on HomePowerRebate" badge for your own site,
   it's here: https://homepowerrebate.com/installers/badge

2. If you'd rather not be listed at all, reply and I'll remove you today.

No cost either way — the directory is free and stays free.

Sam Menard
HomePowerRebate
{mailing address}
samuelmenard@gmail.com

Unsubscribe: {unsubscribe_link}
```

**Why this works:** it leads with something already done for them rather than
asking for a favour, the badge gives a concrete reason to link back, and the
opt-out offer signals you're not running a scrape-and-spam operation — which is
what most of them will assume at first glance.

**Don't** ask for a link outright in the first email. The badge is the ask,
framed as a benefit. Installers who take it link back on their own.

---

## Tracking

- Tag badge links `?utm_source=installer&utm_medium=badge&utm_campaign={slug}`
  so you can see which installers actually deployed it
- Watch Search Console → Links for referring domains appearing over 4–8 weeks
- Expect 10–20% badge adoption. From ~90 sends that's 9–18 local backlinks,
  which is a strong result for a single campaign
