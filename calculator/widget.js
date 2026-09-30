/* HomePowerRebate rebate calculator widget.
   Paste on your site:  <div data-hpr-calc="bc"></div><script src="https://homepowerrebate.com/calculator/widget.js" async></script>
   It shows a free calculator in a frame, with a visible link to the full calculator. No tracking, no cookies. */
(function () {
  var base = "https://homepowerrebate.com";
  function build(host) {
    var code = (host.getAttribute("data-hpr-calc") || "bc").toLowerCase().replace(/[^a-z-]/g, "");
    var f = document.createElement("iframe");
    f.src = base + "/calculator/embed/" + code + "/";
    f.title = "Rebate calculator";
    f.loading = "lazy";
    f.style.cssText = "width:100%;max-width:820px;height:640px;border:1px solid #d9d0c1;border-radius:12px;background:#faf7f2";
    host.textContent = "";
    host.appendChild(f);
    var p = document.createElement("p");
    p.style.cssText = "font:14px system-ui,sans-serif;margin:6px 0 0";
    var a = document.createElement("a");
    a.href = base + "/calculator/" + code + "/";
    a.textContent = "Rebate calculator by HomePowerRebate";
    p.appendChild(a);
    host.appendChild(p);
    window.addEventListener("message", function (ev) {
      if (ev.origin === base && ev.source === f.contentWindow && ev.data && ev.data.hprCalcHeight) f.style.height = (ev.data.hprCalcHeight + 16) + "px";
    });
  }
  Array.prototype.forEach.call(document.querySelectorAll("[data-hpr-calc]"), build);
})();
