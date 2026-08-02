/**
 * Content library for the Meta automation worker.
 *
 * Split into two pools that serve different jobs:
 *
 *   QUESTIONS — link-free posts. Facebook demotes anything pushing traffic
 *   off-platform, so these are what actually earn reach. Each one teaches
 *   something specific first, then asks a real question. The teaching is the
 *   point: a bare "what do you think?" reads as engagement bait and gets
 *   treated as such.
 *
 *   LINKS — one entry per page on the site. These convert the reach the
 *   question posts build.
 *
 * Both are walked in order by day (see cycleIndex in index.js) rather than
 * sampled randomly, so every page gets its turn instead of some running three
 * times before others run once.
 */

export const QUESTIONS = [
  "Quick one for BC homeowners — what's your January BC Hydro bill?\n\nWe hear anywhere from $180 to $400, and it tracks far more with heat pump vs baseboards than with square footage.\n\nCurious where people actually land.\n\n#BCHydro #BritishColumbia #BCHomeowners",

  "Heat pump sizing is where most BC installs go wrong.\n\nThe number that matters isn't headline capacity, it's what's retained at your design temperature — around -5°C in Vancouver, closer to -30°C in Prince George. Same unit, completely different outcome.\n\nAnyone been quoted a size that felt off?\n\n#HeatPump #BritishColumbia #CleanBC",

  "The most expensive mistake in a BC rebate application: starting work before written pre-approval arrives.\n\nNo pre-approval, no rebate, and there's no appeal for it.\n\nHas anyone here been caught by that one?\n\n#CleanBC #BCHydro #BritishColumbia",

  "Three BC programs people mix up constantly:\n\n▪️ CleanBC Better Homes — provincial, open to most homeowners\n▪️ CleanBC Income Qualified — income-tested, covers 100%\n▪️ Canada Greener Homes — federal, stacks with both\n\nThey stack. Most people claim one and stop there.\n\nWhich have you actually used?\n\n#CleanBC #BritishColumbia #BCHomeowners",

  "For anyone who's had a heat pump put in around BC — how long from first quote to actually running?\n\nWhat we hear ranges from three weeks to seven months, and it seems to come down almost entirely to the installer.\n\n#HeatPump #BritishColumbia #BCHomeowners",

  "Net metering in BC: credits roll over month to month, then reset annually.\n\nWhich means oversizing a solar array doesn't pay you out — it donates the surplus to BC Hydro. Size to annual usage, not your peak month.\n\nAnyone been quoted a system bigger than they needed?\n\n#SolarBC #NetMetering #BritishColumbia",

  "If your BC Hydro bill climbed this winter and nothing in the house changed, check whether the baseboards are still running alongside the heat pump.\n\nThey fight each other, and you pay for both.\n\nAnyone seen this one?\n\n#BCHydro #HeatPump #BritishColumbia",

  "Honest question — what actually stopped you from going ahead with a heat pump or solar?\n\nCost, finding an installer you trust, not understanding which rebates apply, or something else?\n\n#BritishColumbia #BCHomeowners #CleanBC",

  "Heat pump water heaters are the most overlooked rebate in BC.\n\nRoughly a third the cost of a full system, and about 3x the efficiency of a standard electric tank. The payback is faster than almost anything else on the list.\n\nAnyone made that swap?\n\n#BCHydro #CleanBC #BritishColumbia",

  "The single most useful question to ask a BC installer: \"What's your HPCN number?\"\n\nIf there's hesitation, you've learned what you needed. Most rebate programs require the certification.\n\nHow's your experience been finding a good one?\n\n#HeatPump #BritishColumbia #BCHomeowners",

  "Insulation first, or heat pump first?\n\nThe efficiency argument says insulation — a tighter envelope means a smaller unit does the same job for less. The comfort argument says heat pump, because you feel it the first week.\n\nWhich order did you go in?\n\n#CleanBC #Insulation #BritishColumbia",

  "BC's grid runs around 98% renewable — among the cleanest in North America.\n\nWhich is why switching from gas to electric heat here cuts far more emissions than the same swap would in Alberta. The grid does the heavy lifting.\n\nDid that factor into your decision at all?\n\n#CleanBC #BritishColumbia #HeatPump",

  "For BC folks running solar — how close was your actual annual production to what you were quoted?\n\nCurious how well the estimates hold up in practice.\n\n#SolarBC #BritishColumbia #NetMetering",

  "BC rebate applications ask for the model number, not the brand.\n\nTwo units from the same manufacturer, sitting side by side: one qualifies, one doesn't. The spec sheet decides, every time.\n\nAnyone been caught by this?\n\n#CleanBC #HeatPump #BritishColumbia",

  "What's the hardest part of the BC rebate process for you — working out what you qualify for, the paperwork itself, or waiting on the money?\n\n#CleanBC #BCHydro #BritishColumbia",

  "Ductless mini-split or ducted heat pump?\n\nMini-splits are cheaper and far easier to retrofit. Ducted is more even, if you already have ductwork worth keeping. Most BC homes built before 1990 end up on mini-splits.\n\nWhat did you go with?\n\n#HeatPump #BritishColumbia #BCHomeowners",

  "Home batteries in BC are less about saving money and more about riding out outages.\n\nOur power is cheap, which changes the math completely versus somewhere like California, where the savings case carries it.\n\nIf you've installed one — bills or backup?\n\n#HomeBattery #BCHydro #BritishColumbia",

  "One tip that reliably saves money: get three quotes, and make sure at least one comes from a smaller local outfit.\n\nThe spread on identical BC heat pump installs regularly runs $4,000 to $6,000.\n\nHow many did you get?\n\n#HeatPump #BritishColumbia #BCHomeowners",
];

export const LINKS = [
  // ---- Guides ----
  {
    path: "/guides/heat-pump-buyers-guide/",
    hook: "Everything that actually matters when buying a heat pump in BC — sizing, cold-climate ratings, which models clear the rebate requirements, and what to ask an installer before anything gets signed.",
    tags: "#HeatPump #CleanBC #BritishColumbia"
  },
  {
    path: "/guides/installer-vetting-checklist/",
    hook: "HPCN certification is the baseline, not the finish line.\n\nThis is the checklist to run an installer through before any money changes hands.",
    tags: "#BCHomeowners #HeatPump #BritishColumbia"
  },
  {
    path: "/guides/insulation-stacking-guide/",
    hook: "Federal and provincial insulation rebates stack in BC — but only in a specific order.\n\nGet the sequence wrong and you forfeit one of them entirely.",
    tags: "#CleanBC #Insulation #BritishColumbia"
  },
  {
    path: "/guides/solar-battery-decision-guide/",
    hook: "Solar first or battery first?\n\nDepends whether your problem is bills or outages. Both answers are defensible. Picking by gut isn't.",
    tags: "#SolarBC #HomeBattery #BritishColumbia"
  },

  // ---- Q&A pages ----
  {
    path: "/questions/bc-hydro-rebate-income-requirements/",
    hook: "The income-tested BC rebates go by household income, not individual — and the thresholds shift with household size.\n\nPlenty of families assume they earn too much and never check.",
    tags: "#CleanBC #BCHydro #BritishColumbia"
  },
  {
    path: "/questions/bc-hydro-solar-rebate-2026/",
    hook: "What BC Hydro actually pays out for solar in 2026, and who's eligible.\n\nShorter answer than most people are expecting.",
    tags: "#SolarBC #BCHydro #BritishColumbia"
  },
  {
    path: "/questions/bc-solar-payback-period-calculation/",
    hook: "Solar payback in BC usually lands between 9 and 14 years, and the spread comes down to three variables.\n\nHere's how to run the numbers for your own roof rather than a brochure's.",
    tags: "#SolarBC #BritishColumbia #NetMetering"
  },
  {
    path: "/questions/double-heat-pump-and-solar/",
    hook: "Can you claim rebates for a heat pump and solar in the same year in BC?\n\nYes. Most people don't, because they assume the programs cancel each other out.",
    tags: "#CleanBC #SolarBC #HeatPump #BritishColumbia"
  },
  {
    path: "/questions/ev-charger-rebate-bc-2026/",
    hook: "EV charger rebates in BC cover more of the job than people expect — including the electrical work, which is usually the expensive half.",
    tags: "#EVCharger #BCHydro #BritishColumbia"
  },
  {
    path: "/questions/heat-pump-rebate-landlord-tenant-bc/",
    hook: "Who claims the heat pump rebate on a rental — landlord or tenant?\n\nIt turns on who holds the utility account, and it catches a lot of people out.",
    tags: "#HeatPump #BCHydro #BritishColumbia"
  },
  {
    path: "/questions/heat-pump-winter-performance-cold-bc/",
    hook: "Do heat pumps really hold up through a BC winter?\n\nThe performance data says yes — with one caveat about sizing that most quotes skip straight past.",
    tags: "#HeatPump #BCWinter #BritishColumbia"
  },
  {
    path: "/questions/hpcn-certified-installers-list-bc/",
    hook: "HPCN certification is required for most BC heat pump rebates.\n\nHere's how to confirm an installer actually holds it, rather than taking their word for it.",
    tags: "#HeatPump #BCHomeowners #BritishColumbia"
  },
  {
    path: "/questions/is-tesla-powerwall-eligible-bc-hydro-rebate/",
    hook: "Is a Tesla Powerwall eligible for BC Hydro's battery rebate?\n\nShort answer: no. The longer answer explains why, and what to put in instead.",
    tags: "#Powerwall #BCHydro #HomeBattery #BritishColumbia"
  },
  {
    path: "/questions/peak-saver-program-bc-how-it-works/",
    hook: "BC Hydro's Peak Saver pays you to let them draw from your battery during demand peaks.\n\nIt's also the difference between a $5,000 rebate and a $1,500 one.",
    tags: "#PeakSaver #BCHydro #HomeBattery #BritishColumbia"
  },

  // ---- Blog: /blog/ ----
  {
    path: "/blog/bc-hydro-peak-saver-battery-rebate-5000-vs-1500.html",
    hook: "Same battery. Same install. $3,500 difference.\n\nBC Hydro pays $5,000 if you enrol in Peak Saver, $1,500 if you don't. Most people find out after the paperwork is already in.",
    tags: "#BCHydro #PeakSaver #HomeBattery #BritishColumbia"
  },
  {
    path: "/blog/tesla-powerwall-bc-hydro-rebate-not-qualified-alternatives.html",
    hook: "Tesla Powerwall doesn't qualify for BC Hydro's battery rebate.\n\nIf you've budgeted around that $5,000, it's a $5,000 hole. These are the systems that do qualify.",
    tags: "#BCHydro #Powerwall #HomeBattery #BritishColumbia"
  },
  {
    path: "/blog/cleanbc-income-qualified-free-heat-pump-2026.html",
    hook: "Under the income threshold, CleanBC covers a heat pump at 100%. Not a discount — the whole thing.\n\nPlenty of BC households qualify and never apply.",
    tags: "#CleanBC #HeatPump #BritishColumbia"
  },
  {
    path: "/blog/insulation-rebates-bc-stack-federal-provincial.html",
    hook: "Federal and provincial insulation rebates stack in BC. Together they reach $11,350.\n\nMost people claim one and stop.",
    tags: "#CleanBC #Insulation #BritishColumbia"
  },
  {
    path: "/blog/bosch-vs-mitsubishi-heat-pump.html",
    hook: "Bosch or Mitsubishi? Both are good units. Only certain models clear BC's rebate requirements.\n\nPick the wrong one and the rebate goes with it.",
    tags: "#HeatPump #BCHydro #CleanBC #BritishColumbia"
  },
  {
    path: "/blog/mysa-vs-ecobee-thermostat.html",
    hook: "Mysa or Ecobee for a BC heat pump?\n\nOne works with BC Hydro's Peak Saver credit. The other doesn't.",
    tags: "#SmartThermostat #BCHydro #BritishColumbia"
  },
  {
    path: "/blog/not-all-installers-trustworthy.html",
    hook: "If an installer wants payment in full before any work starts, walk away.\n\nBC homeowners have lost deposits to companies that stopped answering the phone. Here's what to check first.",
    tags: "#BCHomeowners #SolarBC #BritishColumbia"
  },
  {
    path: "/blog/solar-snow-coverage.html",
    hook: "Do solar panels still produce under BC snow?\n\nYes — and the winter drop-off is smaller than most people assume. The actual production numbers are inside.",
    tags: "#SolarBC #BCWinter #BritishColumbia"
  },
  {
    path: "/blog/solar-too-expensive-myth.html",
    hook: "\"Solar's too expensive in BC.\"\n\nThat held up in 2015. Run it again against today's rebates and net metering and you land somewhere quite different.",
    tags: "#SolarBC #NetMetering #BritishColumbia"
  },

  // ---- Blog: root-level comparisons ----
  {
    path: "/blog-bc-hydro-vs-fortisbc-rebates.html",
    hook: "BC Hydro and FortisBC don't pay the same for a heat pump — and which one you're on isn't always obvious, since plenty of BC homes are billed by one for electricity and the other for gas.\n\nWorth checking before you assume a number.",
    tags: "#BCHydro #FortisBC #HeatPump #BritishColumbia"
  },
  {
    path: "/blog-furnace-vs-heat-pump-which-qualifies-rebate.html",
    hook: "Replacing a gas furnace with another gas furnace gets you nothing from BC's rebate programs.\n\nFurnace to heat pump is where the money is. The gap between those two decisions runs into five figures.",
    tags: "#HeatPump #CleanBC #BritishColumbia"
  },
  {
    path: "/blog-heat-pump-vs-ac-cost-rebates.html",
    hook: "A heat pump is an air conditioner that also runs in reverse. Same hardware, one extra valve.\n\nWhich is why putting in straight AC in BC is usually the worse buy — you pay for most of a heat pump and forfeit the rebate.",
    tags: "#HeatPump #BCHydro #BritishColumbia"
  },
  {
    path: "/blog-island-vs-mainland-bc-heat-pump.html",
    hook: "The Island and the mainland face different problems. The Island deals with outages; the mainland deals with cold snaps.\n\nThat changes whether battery storage or heat pump capacity is the better first dollar.",
    tags: "#VancouverIsland #HeatPump #BritishColumbia"
  },
  {
    path: "/blog-kelowna-vs-kamloops-solar.html",
    hook: "Kelowna and Kamloops sit an hour apart and don't share the same solar potential.\n\nKamloops gets more direct sun hours. Kelowna gets milder shoulder seasons. The payback math lands differently.",
    tags: "#SolarBC #Kelowna #Kamloops #BritishColumbia"
  },
];

export const CITIES = [
  "abbotsford", "burnaby", "chilliwack", "coquitlam", "fort-st-john",
  "kamloops", "kelowna", "langley", "maple-ridge", "nanaimo",
  "penticton", "prince-george", "richmond", "squamish", "surrey",
  "vancouver", "vernon", "victoria"
];
