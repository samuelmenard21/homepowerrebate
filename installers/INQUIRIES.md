# Installers who ask to be listed

Rule: money and requests never change rank. Every list is ordered by Google rating and review count. An inquiry only gets a business *considered*.

## When an email arrives (e.g. We Care Plumbing Heating and Air, San Marcos, asking for the Escondido list)
1. **Do not take the sender's numbers.** Open the business on Google Maps and read the rating, review count, address and category yourself.
2. **Check the service.** It must install what the list covers (heat pumps for heat-pump lists, and so on). Plumbing-only or repair-only shops do not qualify.
3. **Check the city.** A list covers one city page. Add the business to a city only if it says it serves that city and its address or service area makes that true. A city with no page of ours (such as San Marcos) cannot get its own list; offer a nearby city it serves.
4. **Licence.** Ask for the licence number and look it up with the state or province register (California CSLB, Ontario ESA/TSSA, BC Technical Safety BC, and so on). The log field `license_checked` stays false until you do. Never write "licensed" on a page without the check.
5. **Run the tool** (it prompts for the Google Places key, hidden):
   `python3 scripts/add_installer_inquiry.py --region ca --city Escondido --service heat-pump --name "..." --address "..." --contact <their email> --dry-run`
   then again without `--dry-run`, then the rebuild commands it prints.
6. **Check the result.** The business shows only if its Google rating and reviews place it in the list. If it does not make the list, tell the sender why and that the list is re-run when ratings change.
7. **Reply** (by hand, from hello@homepowerrebate.com): thank them, say how ranking works, ask for the licence number and service area, and ask them to add the free top-rated badge (`/installers/badge/`) if they are listed. Do not promise a placement.
8. **Log it.** The tool writes `data/installer-inquiries.json`; record rejections there too (status `declined` with a reason).

Mail rules: US installers fall under CAN-SPAM, Canadian under CASL. Replies to someone who wrote first are fine; do not add them to the outreach list unless they agree.
