# Heat pump FAQ suggestions (drafts, 2026-11-19)

Source of the questions: a last-30-days read of r/heatpumps, r/HVAC, Hacker News and YouTube (14 Reddit threads, directional only, run 2026-11-19) plus our own Search Console heat pump queries. People ask owner and operating questions that our rebate-first pages do not answer: backup heat bills in a cold snap, running cost against gas and oil, minimum operating temperature, sizing from a load calculation, backup heat that runs too often, thermostat settings, and bills in a drafty home.

Rules for using these: they are drafts. Nothing here is published. Each answer is written at a Grade 6 level. Facts marked `VERIFY` need the cited source re-read on the day they are published, and anything we cannot source stays out. Add each FAQ to the page's own generator or data file (never hand-edit generated pages), then rebuild and run the post-steps. No FAQ may state a rebate amount; link to the rebate page instead.

Sources read on 2026-11-19 (secondary, not official standards; re-read before publishing):
- Carrier, "What is auxiliary heat?" (carrier.com/residential, HVAC glossary): balance point often about 30 to 35 F; big overnight setbacks can pull in the backup strips on the morning recovery.
- Google Nest Help, "Heat Pump Balance" (support.google.com/googlenest/answer/9248719): says backup heat can cost about 2 to 5 times as much as running the heat pump; the feature sets when backup heat may run.
- Sensi (Emerson) support, "Aux heat settings": backup heat lockout and balance point settings; the lockout cannot go below the balance point.
- NEEP, Cold Climate Air-Source Heat Pump Specification, Version 4.0 (neep.org): the cold-climate list. The exact test points were not confirmed in our read, so we do not quote them.
- Bonneville Power Administration, cold climate heat pump list FAQ (bpa.gov): look for units that deliver about 80 percent of rated capacity down to 5 F. `VERIFY`
- Building Science / Green Building Advisor, "Manual J doesn't tell you equipment capacity": Manual J gives the load, Manual S picks the equipment.

---

## 1. Cold-weather pages
Pages: `/blog/heat-pump-bc-winter-actually-works/`, `/blog/heat-pumps-cold-climate-bc-winter/`, `/blog/heat-pump-winter-ontario/`, `/blog/heat-pump-winter-massachusetts/`, `/blog/heat-pump-winter-bc/`, `/blog/heat-pumps-alberta-saskatchewan-cold-federal-rebate/`

**Q: What is backup heat, and why did my bill jump in the cold snap?**
A: Backup heat (also called aux or emergency heat) is a set of electric heating strips inside the indoor unit. They turn on when the heat pump alone cannot keep up, usually on the coldest days. Strips cost much more to run than the heat pump itself. Google's Nest help page says it can be about 2 to 5 times as much. So a few very cold days with the strips on can raise the bill a lot. `VERIFY`

**Q: Why does my heat pump keep switching to backup heat?**
A: Two common reasons. One is that the outdoor temperature is below the point where the heat pump can keep up by itself. Carrier says that point is often around 30 to 35 F, and it depends on the home and the unit. The other is a big change on the thermostat. If you turn the heat up by a few degrees, or let the house cool a lot overnight, the system may use the strips to catch up quickly. Smaller steps and steady settings use them less. `VERIFY`

**Q: Can I turn the backup heat off?**
A: Many thermostats let you set the lowest outdoor temperature at which the strips may run (Nest calls it Heat Pump Balance, Sensi calls it aux lockout). Setting it too low can leave the house cold on a very cold day, and a heat pump failure with the strips locked out can risk frozen pipes. Ask your installer what setting suits your home before you change it.

**Q: How cold can a heat pump run?**
A: It depends on the model. Standard units lose heating power as it gets colder. Cold-climate models are built to keep most of their rated power at low temperatures, and they are tested for it. Find your exact model's low-temperature numbers on its spec sheet, and look for the model on NEEP's cold-climate product list. We cannot give one temperature for every unit. `VERIFY` (NEEP test points)

## 2. Buyer guide and installer questions
Pages: `/blog/heat-pump-buyers-guide/`, `/blog/9-questions-to-ask-heat-pump-installer/`, `/blog/fair-heat-pump-quote-canada/`, `/blog/bc-heat-pump-rebate-energy-advisor-heat-load-calculation/`

**Q: What is a Manual J, and should my installer do one?**
A: A Manual J is a heat-loss and heat-gain calculation for your home. It uses your walls, windows, insulation, air leaks and local weather to estimate how much heating and cooling you need. Ask for it in writing. A guess based on the size of your old furnace is not the same thing.

**Q: My load calculation came out at 3.8 tons. Which size should I buy?**
A: The calculation gives your home's load. It does not pick the unit. The next step is choosing equipment, and the installer should explain the choice. Ask them to show the unit's heating output at your coldest design temperature, not just its size on the box, and to say why they picked a bigger or smaller one. A unit that is much too big can run in short bursts and may be less comfortable. A unit that is too small leans on backup heat in the cold. Sizes are limited, so the nearest size is normal. Ask for the numbers for both sizes.

**Q: Does it matter if the heat pump is variable speed?**
A: Variable-speed (inverter) units can run slowly for long periods, which helps with comfort and with small sizing gaps. Cold-climate units are almost all variable speed. Compare the heating output at cold temperatures on the spec sheet rather than judging by the name. `VERIFY`

## 3. Cost pages (against gas and oil)
Pages: `/blog/heat-pump-vs-air-conditioner-furnace/`, `/blog/heat-pump-natural-gas-home-federal-rebate/`, `/blog/newfoundland-oil-heat-prices-heat-pump-rebate/`, `/blog/new-york-cities-ranked-fastest-heat-pump-payback/`

**Q: Is a heat pump cheaper to run than a gas or oil furnace?**
A: It depends on your electricity price, your gas or oil price and how cold your winters are. You can compare them by the cost of the heat you actually get. For a heat pump, divide the electricity price per kWh by its efficiency number (COP) at your typical winter temperature. A COP of 2.5 means 2.5 kWh of heat for each 1 kWh of electricity. For gas, one therm holds about 29.3 kWh of heat, so divide the price per therm by 29.3 and then by your furnace efficiency. For oil, one US gallon holds about 40.6 kWh of heat (138,500 BTU). Example only, not a forecast: electricity at $0.15 per kWh with a COP of 2.5 is $0.06 per kWh of heat. Gas at $1.50 per therm with a 95 percent furnace is about $0.054. Use your own bills. Oil and electric-baseboard homes usually save the most; gas homes depend on local prices. `VERIFY` (conversion constants)

**Q: Will my heat pump bill be high if my house is drafty?**
A: A drafty or poorly insulated home needs more heat, so any heating system costs more to run. A heat pump may also use its backup strips more often in a very cold spell. Sealing air leaks and adding insulation lowers the load, and a lower load can mean a smaller unit. Check the rebate page for your region for insulation and air-sealing help.

## 4. Thermostat pages
Pages: `/blog/smart-thermostat-comparison-nest-ecobee-honeywell-mysa/`, `/blog/ontario-smart-thermostats-100-rebate-compared/`, `/ca/bc/smart-thermostats/`

**Q: Will my smart thermostat work with a heat pump, and what setting controls backup heat?**
A: Most ecobee, Nest and Honeywell/Sensi models support heat pumps, but wiring and settings depend on your unit. Check that the thermostat lists support for your system type before you buy. The settings to look for are the backup heat (aux) lockout and the balance point. Nest has a Heat Pump Balance feature, and Sensi has aux lockout and balance point. Wrong wiring or settings can make backup heat run when it should not, so ask your installer to check them after install. Mysa and Sinope control electric baseboards, not ducted heat pump systems. `VERIFY` (model support lists)

## 5. Brand comparison page
Page: `/blog/heat-pump-brands-comparison-mitsubishi-daikin-bosch/`

**Q: Does the brand matter more than the size and the installer?**
A: Compare the cold-weather heating numbers for the exact models, the warranty terms and who services the unit near you. A well-matched, properly sized and well-installed unit from a good brand usually beats an oversized or badly installed unit from a better-known one. Ask for the heating output at your coldest design temperature for each quote. `VERIFY` (needs an outside source before publishing, otherwise leave this one out)

---

Not written, because we could not source them: minimum safe operating temperature for named models (Trane XL16i and others; it is on the model's spec sheet), thermostat wiring steps for specific models, and any "free heat pump" city programme outside the regions we already cover.
