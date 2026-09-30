/* HomePowerRebate rebate engine. One engine for every province and state.
   A region is data only: /calculator/data/<code>.json (built by scripts/build_calculator.py from data/calc + data/verified-facts).
   Nothing in this file names a region, program or dollar amount. */
(function (root) {
  "use strict";

  var STATUS_LABEL = { active: "Open", upcoming: "Starts soon", waitlist: "Waitlist", paused: "Paused", closed: "Closed", check: "Confirm status", info: "Note" };
  var COUNTED = { active: true };

  function money(n, cur) {
    return "$" + Math.round(n).toLocaleString("en-CA") + (cur && cur !== "USD" ? "" : "");
  }

  function values(region, a) {
    var v = {}, k;
    for (k in a) v[k] = a[k];
    var cq = region.questions.filter(function (q) { return q.id === "city"; })[0];
    if (cq && a.city) {
      var opt = cq.options.filter(function (o) { return o.value === a.city; })[0];
      if (opt && opt.set) for (k in opt.set) v[k] = opt.set[k];
    }
    var d = region.derived && region.derived.income_level;
    if (d) {
      var inc = parseFloat(String(a.income || "").replace(/[^0-9.]/g, ""));
      var hh = parseInt(a.household, 10);
      v.income_level = "unknown";
      if (inc > 0 && hh > 0) {
        var i = Math.min(hh, 7) - 1;
        v.income_level = "none";
        ["L1", "L2", "L3"].some(function (L) {
          if (inc <= d.limits[L][i]) { v.income_level = L; return true; }
          return false;
        });
      }
    }
    return v;
  }

  function match(p, v) {
    var k;
    if (p.when) for (k in p.when) if (p.when[k].indexOf(v[k]) < 0) return false;
    if (p.when_any) {
      var ok = p.when_any.some(function (w) {
        for (var key in w) if (w[key].indexOf(v[key]) < 0) return false;
        return true;
      });
      if (!ok) return false;
    }
    return true;
  }

  function dictMatch(w, v) {
    for (var k in w) if (w[k].indexOf(v[k]) < 0) return false;
    return true;
  }

  /* Amount models: {max}, {by: question, values: {answer: amount}}, or {per: {unit, rate, bonus_rate, bonus_when, question, cap}} for per-ton / per-kW programs. */
  function amountOf(p, v) {
    var a = p.amount;
    if (a.by) return a.values[v[a.by]] || 0;
    if (a.per) {
      var n = parseFloat(v[a.per.question]);
      if (!(n > 0)) return 0;
      var rate = a.per.bonus_when && dictMatch(a.per.bonus_when, v) ? a.per.bonus_rate : a.per.rate;
      var t = rate * n;
      return a.per.cap ? Math.min(t, a.per.cap) : t;
    }
    return a.max || 0;
  }

  function labelOf(p, v, amount) {
    var a = p.amount;
    if (a.label) return a.label;
    if (!a.per) return null;
    var rate = a.per.bonus_when && dictMatch(a.per.bonus_when, v) ? a.per.bonus_rate : a.per.rate;
    var base = "$" + Math.round(rate).toLocaleString("en-CA") + " per " + a.per.unit;
    return amount > 0 ? "$" + Math.round(amount).toLocaleString("en-CA") + " (" + base + ")" : base;
  }

  /* Returns {items, total, unknownIncome}. items carry counted=true when they add to the total. */
  function evaluate(region, a, plan) {
    var v = values(region, a);
    var matched = region.programs.filter(function (p) { return match(p, v); });
    var others = matched.filter(function (p) { return plan.indexOf(p.upgrade) < 0; });
    var hit = matched.filter(function (p) { return plan.indexOf(p.upgrade) >= 0; });
    var changed = true;
    while (changed) {
      changed = false;
      var ids = hit.map(function (p) { return p.id; });
      hit = hit.filter(function (p) {
        if (p.requires && ids.indexOf(p.requires) < 0) { changed = true; return false; }
        return true;
      });
    }
    var items = hit.map(function (p) {
      return { id: p.id, name: p.name, upgrade: p.upgrade, group: p.group || null, amount: amountOf(p, v), label: labelOf(p, v, amountOf(p, v)),
               status: p.status, requires: p.requires || null, verified_on: p.verified_on, source_url: p.source_url, rules: p.rules, counted: false, covered: false };
    });
    var best = {};
    items.forEach(function (it) {
      if (!COUNTED[it.status] || !it.group) return;
      if (!best[it.group] || it.amount > best[it.group].amount) best[it.group] = it;
    });
    var total = 0, byId = {};
    items.forEach(function (it) { byId[it.id] = it; });
    items.forEach(function (it) {
      if (!COUNTED[it.status] || it.requires) return;
      if (it.group) {
        if (best[it.group] === it) { it.counted = true; total += it.amount; } else it.covered = true;
      } else { it.counted = true; total += it.amount; }
    });
    /* Add-ons (bonus, top-up) count only when the offer they build on is the one counted. */
    items.forEach(function (it) {
      if (!it.requires || !COUNTED[it.status]) return;
      if (byId[it.requires] && byId[it.requires].counted) { it.counted = true; total += it.amount; } else it.covered = true;
    });
    return { items: items, others: others.map(function (p) { return { id: p.id, name: p.name, upgrade: p.upgrade, amount: amountOf(p, v), label: labelOf(p, v, amountOf(p, v)), status: p.status, verified_on: p.verified_on, source_url: p.source_url, rules: p.rules, counted: false, covered: false }; }), total: total, incomeUnknown: v.income_level === "unknown", incomeLevel: v.income_level };
  }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function pill(status) {
    return el("span", "rc-pill rc-" + status, STATUS_LABEL[status] || status);
  }

  function fmtDate(iso) {
    var m = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    var p = iso.split("-");
    return m[parseInt(p[1], 10) - 1] + " " + parseInt(p[2], 10) + ", " + p[0];
  }

  function card(it, region) {
    var c = el("div", "rc-card" + (it.counted ? "" : " rc-muted"));
    var top = el("div", "rc-card-top");
    top.appendChild(el("h4", null, it.name));
    var amt = it.label ? it.label : (it.amount ? "Up to " + money(it.amount, region.currency) : "See program");
    top.appendChild(el("div", "rc-amt", amt));
    c.appendChild(top);
    var meta = el("div", "rc-meta");
    meta.appendChild(pill(it.status));
    if (it.covered) meta.appendChild(el("span", "rc-note", "Not added: a larger offer covers the same upgrade"));
    c.appendChild(meta);
    c.appendChild(el("p", "rc-rules", it.rules));
    var f = el("p", "rc-src");
    var a = el("a", null, "Official source");
    a.href = it.source_url; a.rel = "nofollow noopener"; a.target = "_blank";
    f.appendChild(a);
    f.appendChild(document.createTextNode(" · Last verified " + fmtDate(it.verified_on)));
    c.appendChild(f);
    return c;
  }

  function mount(host, region, opts) {
    opts = opts || {};
    host.textContent = "";
    var form = el("form", "rc-form");
    form.setAttribute("novalidate", "");
    var answers = {};
    var params = new URLSearchParams(location.search);
    region.questions.forEach(function (q) {
      var wrap = el("div", "rc-field");
      var label = el("label", null, q.label);
      label.setAttribute("for", "rc-" + q.id);
      wrap.appendChild(label);
      var input;
      if (q.type === "select") {
        input = el("select");
        var ph = el("option", null, q.placeholder || (q.optional ? "Skip" : "Choose one"));
        ph.value = "";
        input.appendChild(ph);
        q.options.forEach(function (o) { var op = el("option", null, o.label); op.value = o.value; input.appendChild(op); });
      } else {
        input = el("input");
        input.type = "text"; input.inputMode = "numeric"; input.placeholder = "for example 85000"; input.autocomplete = "off";
      }
      input.id = "rc-" + q.id; input.name = q.id;
      var pre = params.get(q.id) || (opts.defaults && opts.defaults[q.id]);
      if (pre) { input.value = pre; answers[q.id] = pre; }
      input.addEventListener("input", function () { answers[q.id] = input.value; render(); });
      wrap.appendChild(input);
      if (q.help) wrap.appendChild(el("p", "rc-help", q.help));
      form.appendChild(wrap);
    });
    var plan = params.get("plan") ? params.get("plan").split(",") : [];
    var fs = el("fieldset", "rc-plan");
    fs.appendChild(el("legend", null, "Which upgrades are you planning?"));
    region.upgrades.forEach(function (u) {
      var lab = el("label", "rc-check");
      var cb = el("input"); cb.type = "checkbox"; cb.value = u.id; cb.checked = plan.indexOf(u.id) >= 0;
      cb.addEventListener("change", function () {
        plan = region.upgrades.map(function (x) { return x.id; }).filter(function (id) { return form.querySelector('.rc-plan input[value="' + id + '"]').checked; });
        render();
      });
      lab.appendChild(cb); lab.appendChild(document.createTextNode(" " + u.label));
      fs.appendChild(lab);
    });
    form.appendChild(fs);
    host.appendChild(form);
    var out = el("div", "rc-out");
    out.setAttribute("aria-live", "polite");
    host.appendChild(out);

    function ready() {
      return plan.length > 0 && region.questions.every(function (q) { return q.optional || answers[q.id]; });
    }

    function render() {
      out.textContent = "";
      var q = new URLSearchParams();
      for (var k in answers) if (answers[k] && k !== "income" && k !== "household") q.set(k, answers[k]);
      if (plan.length) q.set("plan", plan.join(","));
      try { history.replaceState(null, "", location.pathname + (q.toString() ? "?" + q.toString() : "")); } catch (e) { /* embedded */ }
      if (!ready()) {
        out.appendChild(el("p", "rc-empty", "Answer the questions and pick at least one upgrade. Your rebates appear here."));
        return;
      }
      var r = evaluate(region, answers, plan);
      var box = el("div", "rc-total");
      box.appendChild(el("div", "rc-total-label", "Most you could get for the upgrades you picked"));
      box.appendChild(el("div", "rc-total-num", money(r.total, region.currency)));
      box.appendChild(el("p", "rc-total-sub", "Adds the biggest open offer for each upgrade you picked. Only programs open today are counted."));
      out.appendChild(box);
      if (r.incomeUnknown) out.appendChild(el("p", "rc-hint", "Add your household size and income to check income-qualified programs. They pay the most."));
      else if (r.incomeLevel === "none") out.appendChild(el("p", "rc-hint", "Your income is above the income-qualified limits, so only the general programs apply."));
      var groups = {}, order = [];
      var open = r.items.filter(function (it) { return it.status === "active"; });
      var later = r.items.filter(function (it) { return it.status !== "active"; });
      var label = {}; region.upgrades.forEach(function (u) { label[u.id] = u.label; });
      open.forEach(function (it) { if (!groups[it.upgrade]) { groups[it.upgrade] = []; order.push(it.upgrade); } groups[it.upgrade].push(it); });
      order.forEach(function (m) {
        out.appendChild(el("h3", "rc-h", label[m]));
        groups[m].forEach(function (it) { out.appendChild(card(it, region)); });
      });
      if (!open.length) out.appendChild(el("p", "rc-empty", "We found no open program for these answers. Check your inputs or see the programs below."));
      if (later.length) {
        out.appendChild(el("h3", "rc-h", "Not open yet, or waiting"));
        later.forEach(function (it) { out.appendChild(card(it, region)); });
      }
      var more = r.others.filter(function (it) { return it.status === "active"; });
      if (more.length) {
        var det = el("details", "rc-more");
        det.appendChild(el("summary", null, "Other rebates that fit your home (" + more.length + ", not in your total)"));
        more.forEach(function (it) { det.appendChild(card(it, region)); });
        out.appendChild(det);
      }
      if (region.closed && region.closed.length) {
        out.appendChild(el("h3", "rc-h", "Ended programs (don't count on these)"));
        var ul = el("ul", "rc-closed");
        region.closed.forEach(function (c) {
          var li = el("li");
          li.appendChild(document.createTextNode(c.name + ". "));
          li.appendChild(pill(c.status));
          li.appendChild(document.createTextNode(" "));
          var a = el("a", null, "Source");
          a.href = c.source_url; a.rel = "nofollow noopener"; a.target = "_blank";
          li.appendChild(a);
          ul.appendChild(li);
        });
        out.appendChild(ul);
      }
      if (region.notes) {
        var nl = el("ul", "rc-notes");
        region.notes.forEach(function (n) { nl.appendChild(el("li", null, n)); });
        out.appendChild(nl);
      }
      if (!opts.embed) out.appendChild(savePlan(region, answers));
      var links = el("p", "rc-links");
      var a1 = el("a", null, "See installers ranked by Google reviews");
      a1.href = region.installers || "/installers/";
      links.appendChild(a1);
      links.appendChild(document.createTextNode(" · "));
      var a2 = el("a", null, region.name + " rebate guide");
      a2.href = region.hub;
      links.appendChild(a2);
      out.appendChild(links);
    }
    render();
  }

  function savePlan(region, answers) {
    var f = el("form", "rc-save");
    f.appendChild(el("h3", "rc-h", "Email me when something changes"));
    f.appendChild(el("p", "rc-help", "One short email when a program in " + region.name + " opens, closes or changes. No installer will call you."));
    var i = el("input"); i.type = "email"; i.required = true; i.placeholder = "you@example.com"; i.setAttribute("aria-label", "Email address");
    var b = el("button", null, "Notify me"); b.type = "submit";
    var msg = el("p", "rc-help");
    f.appendChild(i); f.appendChild(b); f.appendChild(msg);
    f.addEventListener("submit", function (e) {
      e.preventDefault();
      b.disabled = true;
      fetch("https://leads.homepowerrebate.com/newsletter", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: i.value, city: answers.city || "", page: location.pathname, province: region.code.toUpperCase() })
      }).then(function (r) {
        if (!r.ok) throw new Error("bad");
        f.textContent = "";
        f.appendChild(el("p", "rc-help", "You're in. Check your inbox for a welcome email."));
      }).catch(function () { b.disabled = false; msg.textContent = "Something went wrong. Please try again."; });
    });
    return f;
  }

  root.HPRCalc = { evaluate: evaluate, values: values, mount: mount };
  if (typeof module !== "undefined") module.exports = root.HPRCalc;
})(typeof window !== "undefined" ? window : globalThis);
