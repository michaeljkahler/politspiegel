/* ═══════════════════════════════════════════════════════════════════════════
   Kantonsrat Schaffhausen · Kantonsratsspiegel
   Wird von scripts/build3.py eingebettet. Die Daten stehen im Script-Tag
   #daten, die Stimmen kompakt kodiert: J = Ja, N = Nein, E = Enthaltung,
   A = abwesend.

   Grundsatz für alle Kennzahlen: bei Umkehrabstimmungen (v.inv) wird Ja und
   Nein vor der Aggregation getauscht, denn dort bedeutet ein Ja im Rat die
   Ablehnung dessen, worüber abgestimmt wurde. Die Rohstimmen werden nie
   verändert, die Abstimmungskarten zeigen weiter das protokollierte Ergebnis.
   ═══════════════════════════════════════════════════════════════════════════ */
(function () {
  "use strict";

  var D = JSON.parse(document.getElementById("daten").textContent);
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ── Kleine Helfer ────────────────────────────────────────────────────── */
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function zahl(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " "); }
  function pz(x, nk) { return (x || 0).toFixed(nk == null ? 1 : nk).replace(".", ","); }
  function kuerz(t, n) {
    t = String(t || "").trim();
    return t.length <= n ? t : t.slice(0, n).replace(/\s+\S*$/, "") + "…";
  }

  var FRAK_KEY = {
    "SVP-EDU": "svp",
    "SP": "sp", "SP-JUSO": "sp", "SP-JUSO-GRÜNE-Junge Grüne": "sp",
    "GLP-EVP": "glp",
    "FDP-Die Mitte": "fdp", "FDP-Die Mitte-JF": "fdp",
    "FDP-CVP": "fdp", "FDP-CVP-JF": "fdp",
    "AL-Grüne": "al", "AL-GRÜNE-Junge Grüne": "al", "AL-GRÜNE-JUNGE GRÜNE": "al",
    "GRÜNE-Junge Grüne": "gru"
  };
  var PARTEI_KEY = {
    "svp": "svp", "jsvp": "svp", "svp senioren": "svp", "svp agro": "svp", "svp kmu": "svp",
    "edu": "edu", "sp": "sp", "juso": "sp", "grüne": "gru", "junge grüne": "gru",
    "al": "al", "al-grüne": "al", "glp": "glp", "evp": "evp",
    "fdp": "fdp", "jf": "fdp", "jfdp": "fdp", "die mitte": "mitte", "cvp": "mitte",
    "parteilos": "none"
  };
  function fkey(f) { return FRAK_KEY[f] || "none"; }
  function pkey(p) { return PARTEI_KEY[String(p || "").trim().toLowerCase()] || "none"; }
  function fvar(f) { return "var(--p-" + fkey(f) + ")"; }

  var LABEL = { J: "Ja", N: "Nein", E: "Enthaltung", A: "abwesend" };
  var KLASSE = { J: "ja", N: "nein", E: "enth", A: "abw" };

  /* Stimme eines Mitglieds bei Abstimmung i, roh */
  function roh(m, i) { return m.v.charAt(i) || "A"; }
  /* Richtungskorrigiert: bei Umkehr sind Ja und Nein getauscht */
  function korr(m, i, inv) {
    var c = roh(m, i);
    if (!inv) return c;
    return c === "J" ? "N" : c === "N" ? "J" : c;
  }
  function istUmkehr(v) { return v.inv === 1; }

  /* ── Auswertung ──────────────────────────────────────────────────────── */
  function tally(s, i) {
    var t = { J: 0, N: 0, E: 0, A: 0 };
    for (var k = 0; k < s.m.length; k++) t[roh(s.m[k], i)]++;
    return t;
  }
  function ergebnis(s, i) {
    var t = tally(s, i), v = s.v[i], inv = istUmkehr(v);
    if (t.J === t.N) return { text: "Stimmengleichheit", key: "enth", t: t };
    var jaGewinnt = t.J > t.N, an = inv ? !jaGewinnt : jaGewinnt;
    return { text: an ? "Angenommen" : "Abgelehnt", key: an ? "ja" : "nein", t: t };
  }

  /* ── Zustandsverwaltung ──────────────────────────────────────────────── */
  var st = {
    tab: "neu",
    scope: null,          /* {typ:'leg'|'sess', wert} */
    suche: "",
    mitglied: null,       /* Schlüssel "Nachname|Vorname" */
    thema: null,
    formen: [],           /* Abstimmungsformen, mehrere möglich */
    t1: null, t2: null, t3: null,   /* Schlagworte, drei Ebenen */
    modus: null,          /* Matching: 12, 36 oder 72 Fragen */
    frakFilter: "",
    sortKey: "quote", sortDir: -1,
    antworten: {},        /* Matching */
    spider: {}
  };

  function scopeSessions() {
    if (!st.scope) return D.sessions;
    if (st.scope.typ === "sess") {
      return D.sessions.filter(function (s) { return s.s === st.scope.wert; });
    }
    return D.sessions.filter(function (s) { return String(s.leg) === String(st.scope.wert); });
  }
  function scopeLabel() {
    if (st.scope && st.scope.typ === "sess") return st.scope.wert;
    var L = D.leg[String(st.scope ? st.scope.wert : D.aktLeg)];
    return L ? L.label : "Alle Legislaturen";
  }

  /* Alle Abstimmungen im Bereich als flache Liste */
  function alleVotes() {
    var out = [];
    scopeSessions().forEach(function (s) {
      s.v.forEach(function (v, i) { out.push({ s: s, v: v, i: i }); });
    });
    return out;
  }

  /* Mitgliederstatistik über den Bereich, richtungskorrigiert */
  function mitgliedStats() {
    var map = {};
    scopeSessions().forEach(function (s) {
      s.m.forEach(function (m) {
        var k = m.n;
        if (!map[k]) {
          map[k] = { k: k, name: m.n.split("|")[0] + " " + m.n.split("|")[1],
                     nach: m.n.split("|")[0], f: m.f, p: m.p,
                     J: 0, N: 0, E: 0, A: 0, total: 0, sitzungen: 0 };
        }
        var e = map[k];
        e.f = m.f; e.p = m.p; e.sitzungen++;
        for (var i = 0; i < s.v.length; i++) {
          e[korr(m, i, istUmkehr(s.v[i]))]++;
          e.total++;
        }
      });
    });
    return Object.keys(map).map(function (k) {
      var e = map[k];
      e.abgegeben = e.J + e.N + e.E;
      e.quote = e.abgegeben ? e.J / e.abgegeben * 100 : 0;
      e.praesenz = e.total ? e.abgegeben / e.total * 100 : 0;
      e.enthQuote = e.abgegeben ? e.E / e.abgegeben * 100 : 0;
      return e;
    });
  }

  /* Fraktionsstatistik, richtungskorrigiert, inklusive Geschlossenheit */
  function frakStats() {
    var map = {};
    scopeSessions().forEach(function (s) {
      var proFrak = {};
      s.m.forEach(function (m) {
        if (!map[m.f]) map[m.f] = { f: m.f, J: 0, N: 0, E: 0, A: 0, total: 0,
                                    sitze: 0, mehrheitSumme: 0, geprueft: 0 };
        proFrak[m.f] = proFrak[m.f] || [];
        proFrak[m.f].push(m);
      });
      Object.keys(proFrak).forEach(function (f) {
        var leute = proFrak[f], e = map[f];
        e.sitze = leute.length;
        for (var i = 0; i < s.v.length; i++) {
          var inv = istUmkehr(s.v[i]), ja = 0, nein = 0, enth = 0;
          leute.forEach(function (m) {
            var c = korr(m, i, inv);
            e[c]++; e.total++;
            if (c === "J") ja++; else if (c === "N") nein++; else if (c === "E") enth++;
          });
          /* Geschlossenheit als Anteil der Fraktion, der gleich stimmt. Die
             frühere Zählung «alle einig, ja oder nein» bevorzugte kleine
             Fraktionen: eine 7er-Fraktion ist rein zufällig viel öfter
             einstimmig als eine 23er. */
          var ab = ja + nein + enth;
          if (ab > 0) { e.geprueft++; e.mehrheitSumme += Math.max(ja, nein, enth) / ab; }
        }
      });
    });
    return Object.keys(map).map(function (f) {
      var e = map[f];
      e.abgegeben = e.J + e.N + e.E;
      e.quote = e.abgegeben ? e.J / e.abgegeben * 100 : 0;
      e.praesenz = e.total ? e.abgegeben / e.total * 100 : 0;
      e.enthQuote = e.abgegeben ? e.E / e.abgegeben * 100 : 0;
      e.disziplin = e.geprueft ? e.mehrheitSumme / e.geprueft * 100 : 0;
      e.opposition = e.abgegeben ? e.N / e.abgegeben * 100 : 0;
      return e;
    }).sort(function (a, b) { return b.sitze - a.sitze; });
  }

  /* ── Bausteine ───────────────────────────────────────────────────────── */
  function tallyHtml(t, klein) {
    var ges = t.J + t.N + t.E + t.A, teile = [];
    ["J", "N", "E", "A"].forEach(function (c) {
      if (!t[c]) return;
      var p = ges ? t[c] / ges * 100 : 0;
      teile.push('<span class="seg seg-' + KLASSE[c] + '" style="flex:' + t[c] + ' 0 0"' +
        ' aria-label="' + LABEL[c] + ": " + t[c] + '">' + (p >= 7.5 ? t[c] : "") + "</span>");
    });
    return '<div class="tally' + (klein ? " tally-sm" : "") + '">' + teile.join("") + "</div>";
  }
  function legendeHtml(t) {
    return '<div class="legende">' + ["J", "N", "E", "A"].map(function (c) {
      return '<span class="lg lg-' + KLASSE[c] + '"><i></i><b>' + t[c] + "</b>" + LABEL[c] + "</span>";
    }).join("") + "</div>";
  }

  /* Titel einer Abstimmung, verlinkt aufs Wortprotokoll der Sitzung. Fehlt das
     Protokoll, bleibt es beim reinen Text: ein toter Link wäre schlechter als
     keiner. */
  /* Interessenbindungen im Profil, nach Herkunft getrennt.
     Blau: auf sh.ch selbst deklariert. Gelb: nur im Handelsregister gefunden
     und von Hand am Registerauszug bestätigt. Die Farbe steht nie allein, jede
     Gruppe trägt eine Überschrift und jeder gelbe Eintrag den Link zum Auszug. */
  /* Ausgeschieden: in der laufenden Legislatur hat die Person mitgestimmt, sie
     steht aber nicht mehr auf der Mitgliederliste von sh.ch. Belegen lässt sich
     nur die letzte Sitzung, an der sie teilgenommen hat; ein Rücktrittsdatum
     steht in keiner der Quellen. In abgeschlossenen Legislaturen ist der
     Vermerk sinnlos, dort sind alle ausgeschieden. */
  function wegSeit(k) {
    if (!D.weg) return null;
    // Nur wenn die laufende Legislatur im Blick ist, entweder als Ganzes oder
    // über eine ihrer Sitzungen. Bei «Alle Legislaturen» wäre der Vermerk
    // ebenso irreführend wie in einer abgeschlossenen.
    var s = st.scope;
    if (!s) return null;
    if (s.typ === "leg" && String(s.wert) !== String(D.aktLeg)) return null;
    if (s.typ === "sess") {
      var tref = D.sessions.filter(function (x) { return x.s === s.wert; })[0];
      if (!tref || String(tref.leg) !== String(D.aktLeg)) return null;
    }
    return D.weg[k] || null;
  }

  function wegChip(k) {
    var s = wegSeit(k);
    if (!s) return "";
    return '<span class="wegchip" title="Hat in dieser Legislatur mitgestimmt, steht ' +
      'aber nicht mehr auf der Mitgliederliste von sh.ch. Letzte Sitzung: ' +
      esc(s) + '">ausgeschieden</span>';
  }

  /* Im Rat, aber ohne Personenkasten auf sh.ch. Ohne Kasten keine contentid,
     ohne contentid kein Profil: weder Porträt noch Interessenbindungen. Das ist
     eine Lücke der Quelle und keine Aussage über die Person, und es gehört
     hingeschrieben, statt eine leere Seite zu zeigen. */
  function ohneProfil(k) {
    return !!(D.ohneProfil && D.ohneProfil.indexOf(k) >= 0);
  }

  function ibBlock(pr) {
    var dekl = pr.ib || [], hr = pr.hr || [];
    if (!dekl.length && !hr.length) return "";
    var s = '<div class="sec"><h2>Interessenbindungen</h2><p>' +
      (dekl.length ? dekl.length + (dekl.length === 1 ? " deklariertes Mandat" : " deklarierte Mandate") : "keine Deklaration") +
      (hr.length ? ", " + hr.length + (hr.length === 1 ? " weiteres im Handelsregister" : " weitere im Handelsregister") : "") +
      "</p></div>";
    if (dekl.length) {
      s += '<ul class="iblist">' + dekl.map(function (x) {
        return '<li class="q-d"><span class="qtag qtag-d">deklariert</span>' + esc(x) + "</li>";
      }).join("") + "</ul>";
    }
    if (hr.length) {
      s += '<ul class="iblist">' + hr.map(function (x) {
        return '<li class="q-r"><span class="qtag qtag-r">nur Handelsregister</span>' +
          "<b>" + esc(x.f) + "</b>" + (x.o ? ", " + esc(x.o) : "") +
          (x.r ? '<span class="ibrolle">' + esc(x.r) + "</span>" : "") +
          (x.url ? ' <a class="plink" href="' + esc(x.url) + '" target="_blank" rel="noopener" ' +
            'title="Registerauszug auf sh.chregister.ch öffnen">Auszug' +
            '<svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true">' +
            '<path d="M6 3h7v7M13 3L6.5 9.5M11 9.5V13H3V5h3.5" stroke="currentColor" ' +
            'fill="none" stroke-width="1.4"/></svg></a>' : "") + "</li>";
      }).join("") + "</ul>";
    }
    s += '<p class="ibquelle">Blau: Selbstdeklaration auf sh.ch' +
      (D.personen.stand ? ", Stand " + esc(D.personen.stand) : "") + ". " +
      (hr.length ? "Gelb: Eintrag im Handelsregister des Kantons Schaffhausen, der in der " +
        "Deklaration fehlt, einzeln am Registerauszug geprüft. Ein fehlender Eintrag muss " +
        "nichts bedeuten: die Deklarationspflicht deckt nicht jedes Mandat, und Angaben " +
        "können veralten. Verbindlich ist der beglaubigte Registerauszug." : "") + "</p>";
    return s;
  }

  function protokollFehlt(s) {
    return s.pf === 2 ? "Wortprotokoll noch nicht publiziert" : "Wortprotokoll zurzeit nicht abrufbar";
  }

  /* Kasten im Sitzungskopf, wenn das Wortprotokoll fehlt. Der Kanton publiziert
     es meist einige Wochen nach der Sitzung; bis dahin gibt es die Traktanden
     und die Abstimmungsergebnisse (PDF, Excel) auf der Sitzungsseite. */
  function protokollHinweis(s) {
    if (!s || !s.pf) return "";
    return '<p class="prothinweis">' + protokollFehlt(s) + ". Titel und Ergebnisse stammen aus der Excel-Publikation " +
      "der Parlamentsdienste; Debattenbelege und Einordnungen folgen, sobald das Protokoll vorliegt." +
      (s.pu ? ' <a href="' + esc(s.pu) + '" target="_blank" rel="noopener">Sitzungsseite mit Traktanden und Abstimmungsergebnissen auf sh.ch &rarr;</a>' : "") + "</p>";
  }

  function protokollLink(s, text, tooltip) {
    var t = esc(text);
    if (!s || !s.pu || s.pf) {
      // Ohne Wortprotokoll bleibt der Titel ein Titel; der Hinweis steht im Sitzungskopf und im Fuss.
      return '<span title="' + esc(tooltip || text) + (s && s.pf ? " — " + protokollFehlt(s) : "") + '">' + t + "</span>";
    }
    return '<a class="plink" href="' + esc(s.pu) + '" target="_blank" rel="noopener" ' +
      'title="' + esc(tooltip || text) + (s.pf ? ' — Sitzungsseite auf sh.ch öffnen (' + protokollFehlt(s) + ')' : ' — Wortprotokoll der Sitzung öffnen') + '">' + t +
      '<svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true">' +
      '<path d="M6 3h7v7M13 3L6.5 9.5M11 9.5V13H3V5h3.5" stroke="currentColor" ' +
      'stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg></a>';
  }

  var HERKUNFT = {
    protokoll: "am Wortprotokoll überprüft",
    manuell: "von Hand am Wortprotokoll geprüft",
    konvention: "nach Konvention für Sachtitel",
    regel: "regelbasiert, nicht am Protokoll überprüft"
  };

  function umkehrHtml(v) {
    if (v.inv !== 1 && v.inv !== 0) return "";
    if (v.inv === 0) {
      return '<div class="umkehr"><b>Umkehrhinweis, Richtung ungeklärt</b>' +
        "<p>" + esc(v.iv) + ". Für diese Abstimmung ist nicht abschliessend geklärt, " +
        "was ein Ja inhaltlich bedeutet. Sie zählt darum bei den Quoten nicht mit.</p></div>";
    }
    var beleg = v.bl ? '<span class="ubeleg">Im Wortprotokoll: «' + esc(v.bl) + "»</span>" : "";
    var q = HERKUNFT[v.hk] ? '<span class="uquelle">' + HERKUNFT[v.hk] + "</span>" : "";
    return '<div class="umkehr"><b>Umkehrabstimmung</b><p>' + esc(v.iv) +
      ". Ein Ja ist hier also keine Zustimmung zur ursprünglichen Vorlage.</p>" +
      beleg + q + "</div>";
  }

  function frakZeilenHtml(s, i) {
    var proFrak = {};
    s.m.forEach(function (m) {
      proFrak[m.f] = proFrak[m.f] || { J: 0, N: 0, E: 0, A: 0 };
      proFrak[m.f][roh(m, i)]++;
    });
    return Object.keys(proFrak).sort(function (a, b) {
      var sa = proFrak[a], sb = proFrak[b];
      return (sb.J + sb.N + sb.E + sb.A) - (sa.J + sa.N + sa.E + sa.A);
    }).map(function (f) {
      var t = proFrak[f], ab = t.J + t.N + t.E;
      var einig = ab > 0 && Math.max(t.J, t.N) === ab;
      return '<div class="frow"><div class="fname"><i class="pdot p-' + fkey(f) + '"></i>' +
        '<span title="' + esc(f) + '">' + esc(f) + "</span></div>" +
        tallyHtml(t, true) +
        '<div class="fval">' + t.J + '<span class="sep">:</span>' + t.N + "</div>" +
        '<div class="ftag">' + (einig ? "<em>geschlossen</em>" : "") + "</div></div>";
    }).join("");
  }

  function namenSpaltenHtml(s, i) {
    var grp = { J: [], N: [], E: [], A: [] };
    s.m.forEach(function (m) { grp[roh(m, i)].push(m); });
    return '<div class="ncols">' + ["J", "N", "E", "A"].map(function (c) {
      var leute = grp[c].sort(function (a, b) { return a.n.localeCompare(b.n, "de"); });
      var items = leute.map(function (m) {
        var t = m.n.split("|");
        return '<li><button type="button" data-member="' + esc(m.n) + '">' +
          '<i class="pdot p-' + pkey(m.p) + '"></i>' + esc(t[0]) + " " + esc(t[1]) +
          "<em>" + esc(m.p) + "</em></button></li>";
      }).join("") || '<li class="leer" style="padding:0">niemand</li>';
      return '<div class="ncol nc-' + KLASSE[c] + '"><h4>' + LABEL[c] +
        "<span>" + leute.length + "</span></h4><ul>" + items + "</ul></div>";
    }).join("") + "</div>";
  }

  /* Livestream des Kantons auf YouTube: v.yt = "<Video-ID>|<Sekunde>", die
     Sekunde ist der Beginn des Traktandums in der Videobeschreibung (Kapitel),
     nicht der Moment der Abstimmung. Zuordnung in scripts/youtube.py. */
  function zeitmarke(sek) {
    sek = parseInt(sek, 10) || 0;
    var h = Math.floor(sek / 3600), m = Math.floor((sek % 3600) / 60), s = sek % 60;
    return (h ? h + ":" + (m < 10 ? "0" : "") : "") + m + ":" + (s < 10 ? "0" : "") + s;
  }
  function livestreamHtml(v) {
    if (!v.yt) return "";
    var teile = v.yt.split("|");
    var url = "https://www.youtube.com/watch?v=" + encodeURIComponent(teile[0]) + "&t=" + (parseInt(teile[1], 10) || 0) + "s";
    return '<p class="vlive"><a class="vlive-knopf" href="' + url + '" target="_blank" rel="noopener" ' +
      'title="Livestream der Sitzung auf YouTube, ab Beginn der Debatte zu diesem Geschäft">' +
      '<svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true"><path d="M2.5 3.5h11v9h-11z" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linejoin="round"/><path d="M6.8 6v4l3.4-2z" fill="currentColor"/></svg>' +
      "Debatte im Livestream, ab " + zeitmarke(teile[1]) + "</a></p>";
  }

  function voteCardHtml(s, v, i, opt) {
    opt = opt || {};
    var e = ergebnis(s, i), t = e.t;
    var chips = [];
    (v.tf || []).forEach(function (f) { chips.push('<span class="chip">' + esc(f) + "</span>"); });
    if (!(v.tf || []).length && v.ty) chips.push('<span class="chip">' + esc(v.ty) + "</span>");
    (v.t1 || []).forEach(function (t) { chips.push('<span class="chip chip-thema">' + esc(t) + "</span>"); });
    if (!(v.t1 || []).length && v.th) chips.push('<span class="chip chip-thema">' + esc(v.th) + "</span>");
    if (opt.zeigeSitzung) chips.push('<span class="chip chip-thema">' + esc(s.dt) + "</span>");
    var knapp = Math.abs(t.J - t.N);
    var knappHtml = (t.J && t.N && knapp <= 4)
      ? '<span class="knapp">knapp, ' + knapp + " Stimmen Unterschied</span>" : "";
    var id = "v-" + s.s.replace(/[^a-z0-9]/gi, "") + "-" + v.nr;
    return '<article class="vcard" id="' + id + '" data-sess="' + esc(s.s) + '" data-idx="' + i + '">' +
      '<header class="vhead"><span class="vnr">Nr. ' + esc(v.nr) + "</span>" + chips.join("") +
      '<span class="badge b-' + e.key + '">' + e.text + "</span></header>" +
      '<h3 class="vtitel">' + protokollLink(s, v.t, v.tr) + "</h3>" +
      (v.rf ? '<p class="vref">' + esc(v.rf) + "</p>" : "") +
      (v.kx ? '<p class="vkontext">' + esc(v.kx) +
        (v.kq ? '<span class="kq">Einordnung aus ' + esc(v.kq) + "</span>" : "") + "</p>" : "") +
      (v.d && v.d !== v.t ? '<p class="vdetails">' + esc(v.d) + "</p>" : "") +
      livestreamHtml(v) +
      umkehrHtml(v) +
      tallyHtml(t) + legendeHtml(t) +
      (knappHtml ? '<div class="legende">' + knappHtml + "</div>" : "") +
      '<div class="folds">' +
      '<details class="fold"><summary><span class="caret"></span>So haben die Fraktionen gestimmt</summary>' +
      '<div class="foldbody">' + frakZeilenHtml(s, i) + "</div></details>" +
      '<details class="fold"><summary><span class="caret"></span>Wer hat wie gestimmt?</summary>' +
      '<div class="foldbody">' + namenSpaltenHtml(s, i) + "</div></details>" +
      "</div></article>";
  }

  function gruppenHtml(s, votes) {
    /* votes: [{v,i}] einer Sitzung, gebündelt nach Geschäft */
    var gr = [], idx = {}, ohne = [];
    votes.forEach(function (x) {
      if (x.v.b) {
        if (!idx[x.v.b]) { idx[x.v.b] = { b: x.v.b, g: x.v.g, liste: [] }; gr.push(idx[x.v.b]); }
        idx[x.v.b].liste.push(x);
      } else ohne.push(x);
    });
    if (ohne.length) gr.push({ b: null, g: "", liste: ohne });
    return gr.map(function (g) {
      var n = g.liste.length, zahlText = n === 1 ? "1 Abstimmung" : n + " Abstimmungen";
      var kopf = g.b
        ? '<div class="ghead"><div><span class="glabel">Geschäft</span><h3>' + esc(g.b) +
          '</h3></div><span class="gcount">' + zahlText + "</span></div>" +
          (g.g ? '<p class="gfull">' + esc(g.g) + "</p>" : "")
        : '<div class="ghead"><div><span class="glabel">Ohne übergeordnetes Geschäft</span>' +
          "<h3>Einzelne Vorlagen und Vorstösse</h3></div>" +
          '<span class="gcount">' + zahlText + "</span></div>";
      return '<section class="gruppe">' + kopf + '<div class="cards">' +
        g.liste.map(function (x) { return voteCardHtml(s, x.v, x.i); }).join("") +
        "</div></section>";
    }).join("");
  }

  /* Die Mailadresse wird erst hier zusammengesetzt und steht darum nirgends am
     Stück im Quelltext. Das hält einfache Adress-Sammler ab, mehr nicht: wer
     die Seite ausführt, sieht sie. Ein wirksamerer Schutz wäre ein Formular,
     und das hiesse einen Server zu betreiben, was diese Seite gerade nicht tut. */
  function kontakt() {
    var a = ["politspiegel.sh", "gmail.com"].join("@");
    return '<a href="' + "mail" + "to:" + a + '">' + a + "</a>";
  }

  function fussHtml(s) {
    var quelle = s ? " (" + esc(s.q) + ")" : "";
    var prot = s && s.pu ? (s.pf
      ? " " + protokollFehlt(s) + '; Traktanden und Abstimmungsergebnisse auf der <a href="' + esc(s.pu) + '" target="_blank" rel="noopener">Sitzungsseite von sh.ch</a>.'
      : ' <a href="' + esc(s.pu) + '" target="_blank" rel="noopener">Wortprotokoll</a>.') : "";
    return '<footer class="foot"><p class="foot-melden"><a href="#" data-melden>Fehler auf dieser Seite melden &rarr;</a></p>' +
      "<b>Datenquelle:</b> Kanton Schaffhausen, namentliche " +
      "Abstimmungen des Kantonsrats, Excel-Publikation der Parlamentsdienste" + quelle + "." + prot +
      " Aufbereitung ohne Gewähr." +

      "<br><b>Interessenbindungen:</b> Selbstdeklaration der Ratsmitglieder auf sh.ch, " +
      "ergänzt um Einträge des Handelsregisteramts des Kantons Schaffhausen und der " +
      "Zefix-REST-API des Bundesamts für Justiz. Ein Registerfund erscheint erst, wenn er " +
      "von Hand am Registerauszug bestätigt worden ist. Andere Quellen werden nicht " +
      "herangezogen." +

      "<br><b>Richtungskorrektur:</b> Bei Umkehrabstimmungen werden " +
      "Ja und Nein vor der Aggregation getauscht, die Herkunft des Entscheids steht auf jeder " +
      "betroffenen Karte. Ausmehrungen ohne eindeutige Richtung bleiben aus den Quoten draussen." +

      "<br><b>Grenzen der Daten:</b> Die Richtungskorrektur ist zu 88 Prozent am Wortprotokoll " +
      "oder von Hand geprüft. Der Rest folgt einer Regel, deren Fehlerquote bei rund " +
      "5 Prozent gemessen wurde. Wer einzelne Zahlen zitiert, sollte sie an der Quelle " +
      "nachschlagen." +

      "<br><b>Parteifarben</b> nach srfdata/swiss-party-colors (CC BY-SA 4.0), angepasst für die " +
      "Schaffhauser Parteien. Ja und Nein sind bewusst parteiunabhängig eingefärbt." +

      "<br><b>Datenschutz:</b> Diese Seite sendet nichts. Die Antworten im Reiter «Wer stimmt " +
      "wie ich» bleiben im Browser, es gibt weder Konto noch Cookie noch Zählpixel und keine " +
      "eingebundenen Dienste Dritter. Die Seite liegt allerdings bei GitHub Pages, und GitHub " +
      "hält als Betreiber der Server eigene Zugriffsprotokolle, in denen unter anderem die " +
      "IP-Adresse steht. Darauf hat der Betreiber dieser Seite keinen Zugriff." +

      "<br><b>Impressum:</b> Verantwortlich für den Inhalt ist Michael Kahler, " +
      "erreichbar unter " + kontakt() + ". Diese Seite ist ein privates, nichtkommerzielles " +
      "Projekt und steht in keinem Zusammenhang mit dem Kantonsrat oder der Verwaltung des " +
      "Kantons Schaffhausen. Wer einen Fehler findet, melde ihn bitte an diese Adresse." +
      "</footer>";
  }

  /* ═══ Rubrik: Zuletzt entschieden ═══════════════════════════════════════ */
  function renderNeu(el) {
    var s = D.sessions[0];
    var votes = s.v.map(function (v, i) { return { v: v, i: i }; });
    var gesamt = 0, abgegeben = 0, ohneGegen = 0;
    s.v.forEach(function (v, i) {
      var t = tally(s, i);
      gesamt += t.J + t.N + t.E + t.A; abgegeben += t.J + t.N + t.E;
      if (t.N === 0 && t.E === 0) ohneGegen++;
    });
    var kz = [
      [s.v.length, "namentliche Abstimmungen", "in dieser Sitzung"],
      [s.m.length, "Ratsmitglieder", (D.leg[String(s.leg)] || {}).label || ""],
      [pz(gesamt ? abgegeben / gesamt * 100 : 0) + " %", "Präsenz", "abgegebene Stimmen"],
      [ohneGegen, "ohne Gegenstimme", "von " + s.v.length + " Abstimmungen"]
    ];
    var vorige = D.sessions.slice(1, 9);
    el.innerHTML =
      '<header class="hero"><div class="eyebrow">Zuletzt entschieden</div><h1>' + esc(s.n) + "</h1>" +
      '<p class="subline">Sitzung vom <b>' + esc(deDatum(s.dt)) + "</b>" +
      (s.z ? " · " + esc(s.z) : "") + ". Der Rat hat <b>" + s.v.length + " Mal</b> namentlich " +
      "abgestimmt. Alle " + s.m.length + " Ratsmitglieder und ihre Stimmen sind zu jeder Frage " +
      "aufklappbar." + (s.yt ? ' <a href="https://www.youtube.com/watch?v=' + encodeURIComponent(s.yt) +
        '" target="_blank" rel="noopener">Livestream der Sitzung auf YouTube</a>.' : "") + "</p>" +
      protokollHinweis(s) + "</header>" +
      '<div class="kzs">' + kz.map(function (k) {
        return '<div class="kz"><div class="kzn">' + k[0] + '</div><div class="kzl">' + k[1] +
          '</div><div class="kzsub">' + k[2] + "</div></div>";
      }).join("") + "</div>" +
      '<div class="sec"><h2>Alle Abstimmungen dieser Sitzung</h2><p>gebündelt nach Geschäft</p></div>' +
      gruppenHtml(s, votes) +
      '<div class="sec" style="margin-top:44px"><h2>Frühere Sitzungen</h2><p>Auswahl der letzten acht</p></div>' +
      '<div class="chips">' + vorige.map(function (x) {
        return '<button type="button" class="tchip" data-goto-sess="' + esc(x.s) + '">' +
          esc(x.n) + '<span class="n">' + esc(x.dt) + "</span></button>";
      }).join("") + "</div>" + fussHtml(s);
  }

  function deDatum(d) {
    var M = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
             "September", "Oktober", "November", "Dezember"];
    var m = /^(\d{2})\.(\d{2})\.(\d{4})/.exec(d || "");
    return m ? parseInt(m[1], 10) + ". " + M[parseInt(m[2], 10) - 1] + " " + m[3] : d;
  }

  /* ═══ Rubrik: Abstimmungen ═════════════════════════════════════════════ */
  function hatTag(v, feld, wert) {
    var l = v[feld];
    return !!l && l.indexOf(wert) !== -1;
  }
  /* Mehrere Formen wirken als Oder: gezeigt wird, was mindestens eine trägt. */
  function passtForm(v) {
    if (!st.formen.length) return true;
    for (var i = 0; i < st.formen.length; i++) {
      if (hatTag(v, "tf", st.formen[i])) return true;
    }
    return false;
  }
  function passt(x) {
    var v = x.v;
    if (!passtForm(v)) return false;
    if (st.t1 && !hatTag(v, "t1", st.t1)) return false;
    if (st.t2 && !hatTag(v, "t2", st.t2)) return false;
    if (st.t3 && !hatTag(v, "t3", st.t3)) return false;
    if (!st.suche) return true;
    var q = st.suche.toLowerCase();
    var hay = [v.t, v.tr, v.d, v.g, v.th, v.ty, v.kx, x.s.s]
      .concat(v.t1 || [], v.t2 || [], v.t3 || [], v.sw || []).join(" ").toLowerCase();
    return hay.indexOf(q) !== -1;
  }
  function zaehleTag(liste, feld) {
    var z = {};
    liste.forEach(function (x) {
      (x.v[feld] || []).forEach(function (t) { z[t] = (z[t] || 0) + 1; });
    });
    return z;
  }
  function tagZeile(z, aktiv, attr, titel) {
    var namen = Object.keys(z).sort(function (a, b) { return z[b] - z[a] || a.localeCompare(b, "de"); });
    if (!namen.length) return "";
    return '<div class="tagzeile"><span class="tagtitel">' + titel + "</span>" +
      namen.map(function (t) {
        return '<button type="button" class="tchip' + (aktiv === t ? " on" : "") +
          '" data-' + attr + '="' + esc(t) + '">' + esc(t) +
          '<span class="n">' + z[t] + "</span></button>";
      }).join("") + "</div>";
  }
  function renderVotes(el) {
    var alle = alleVotes();
    /* Die Schlagwortzeilen zählen jeweils auf Basis der Ebenen darüber, damit
       die Zahlen zur getroffenen Auswahl passen. */
    var nachSuche = alle.filter(function (x) {
      if (!passtForm(x.v)) return false;
      if (!st.suche) return true;
      var q = st.suche.toLowerCase();
      return [x.v.t, x.v.tr, x.v.d, x.v.g, x.v.th, x.v.kx, x.s.s]
        .concat(x.v.t1 || [], x.v.t2 || [], x.v.t3 || [], x.v.sw || [])
        .join(" ").toLowerCase().indexOf(q) !== -1;
    });
    var ebene1 = zaehleTag(nachSuche, "t1");
    var nach1 = st.t1 ? nachSuche.filter(function (x) { return hatTag(x.v, "t1", st.t1); }) : nachSuche;
    var ebene2 = st.t1 ? zaehleTag(nach1, "t2") : {};
    var nach2 = st.t2 ? nach1.filter(function (x) { return hatTag(x.v, "t2", st.t2); }) : nach1;
    var ebene3 = st.t2 ? zaehleTag(nach2, "t3") : {};

    var liste = alle.filter(passt);
    var maxKarten = 120;
    var nachSitzung = [], aktuell = null;
    liste.slice(0, maxKarten).forEach(function (x) {
      if (!aktuell || aktuell.s !== x.s) { aktuell = { s: x.s, liste: [] }; nachSitzung.push(aktuell); }
      aktuell.liste.push(x);
    });
    var gefiltert = st.suche || st.formen.length || st.t1 || st.t2 || st.t3;
    var formZaehler = zaehleTag(alle, "tf");

    el.innerHTML =
      '<header class="hero"><div class="eyebrow">' + esc(scopeLabel()) + "</div>" +
      "<h1>Abstimmungen</h1>" +
      '<p class="subline">Jede namentliche Abstimmung mit Resultat, Fraktionsaufteilung und ' +
      "Namensliste. Suchen Sie oben nach Stichwort, oder grenzen Sie über Form und " +
      "Schlagworte ein.</p></header>" +
      '<div class="vfilter">' +
      '<div class="tagzeile"><span class="tagtitel">Form</span>' +
      (D.formen || []).filter(function (f) { return formZaehler[f]; }).map(function (f) {
        var an = st.formen.indexOf(f) !== -1;
        return '<label class="kaestchen' + (an ? " on" : "") + '">' +
          '<input type="checkbox" data-form="' + esc(f) + '"' + (an ? " checked" : "") + ">" +
          esc(f) + '<span class="n">' + formZaehler[f] + "</span></label>";
      }).join("") +
      (gefiltert ? '<button type="button" class="tchip" id="vReset">zurücksetzen</button>' : "") +
      '<span class="zaehler">' + zahl(liste.length) + " von " + zahl(alle.length) +
      " Abstimmungen" + (liste.length > maxKarten ? ", erste " + maxKarten + " gezeigt" : "") +
      "</span></div>" +
      tagZeile(ebene1, st.t1, "t1", "Thema") +
      tagZeile(ebene2, st.t2, "t2", "Unterthema") +
      tagZeile(ebene3, st.t3, "t3", "Detail") +
      "</div>" +
      (liste.length ? nachSitzung.map(function (g) {
        return '<section class="gruppe"><div class="ghead"><div>' +
          '<span class="glabel">Sitzung</span><h3>' + esc(g.s.n) + "</h3></div>" +
          '<span class="gcount">' + esc(g.s.dt) + (g.s.z ? " · " + esc(g.s.z) : "") + "</span></div>" +
          '<div class="cards">' + g.liste.map(function (x) {
            return voteCardHtml(g.s, x.v, x.i);
          }).join("") + "</div></section>";
      }).join("") : '<p class="leer">Keine Abstimmung passt zu dieser Auswahl.</p>') +
      fussHtml(null);

    $$("[data-form]", el).forEach(function (cb) {
      cb.addEventListener("change", function () {
        var f = cb.getAttribute("data-form"), i = st.formen.indexOf(f);
        if (i === -1) st.formen.push(f); else st.formen.splice(i, 1);
        render();
      });
    });
    var reset = $("#vReset", el);
    if (reset) reset.addEventListener("click", function () {
      st.formen = []; st.t1 = st.t2 = st.t3 = null; st.suche = "";
      var s = $("#suche"); if (s) s.value = "";
      render();
    });
    ["t1", "t2", "t3"].forEach(function (stufe) {
      $$("[data-" + stufe + "]", el).forEach(function (b) {
        b.addEventListener("click", function () {
          var w = b.getAttribute("data-" + stufe);
          st[stufe] = st[stufe] === w ? null : w;
          if (stufe === "t1") { st.t2 = null; st.t3 = null; }
          if (stufe === "t2") { st.t3 = null; }
          render();
        });
      });
    });
  }

  /* ═══ Rubrik: Ratsmitglieder ═══════════════════════════════════════════ */
  function renderMembers(el) {
    if (st.mitglied) return renderMitgliedDetail(el);
    var alle = mitgliedStats();
    var frakList = {};
    alle.forEach(function (m) { frakList[m.f] = 1; });
    var liste = alle.filter(function (m) {
      if (st.frakFilter && m.f !== st.frakFilter) return false;
      if (!st.suche) return true;
      return (m.name + " " + m.f + " " + m.p).toLowerCase().indexOf(st.suche.toLowerCase()) !== -1;
    });
    var key = st.sortKey;
    liste.sort(function (a, b) {
      var A = key === "name" ? a.nach : a[key], B = key === "name" ? b.nach : b[key];
      if (typeof A === "string") return A.localeCompare(B, "de") * st.sortDir;
      return (A - B) * st.sortDir;
    });
    var s0 = scopeSessions()[0];
    var pfeil = function (k) { return st.sortKey === k ? '<span class="pfeil">' + (st.sortDir > 0 ? "▲" : "▼") + "</span>" : ""; };

    el.innerHTML =
      '<header class="hero"><div class="eyebrow">' + esc(scopeLabel()) + "</div>" +
      "<h1>Ratsmitglieder</h1>" +
      '<p class="subline">Zustimmungsquote, Präsenz und Stimmverhalten. Ein Klick auf einen ' +
      "Namen öffnet das Profil mit allen Einzelstimmen.</p></header>" +
      '<div class="hinweis"><b>Zur Zustimmungsquote:</b> Sie zählt Ja-Stimmen im Verhältnis zu ' +
      "allen abgegebenen Stimmen, Abwesenheiten bleiben draussen. Bei Umkehrabstimmungen sind " +
      "Ja und Nein vorher getauscht, damit ein Ja überall dasselbe bedeutet.</div>" +
      '<div class="filter"><select id="fFrak"><option value="">Alle Fraktionen</option>' +
      Object.keys(frakList).sort().map(function (f) {
        return '<option value="' + esc(f) + '"' + (st.frakFilter === f ? " selected" : "") + ">" + esc(f) + "</option>";
      }).join("") + "</select>" +
      '<span class="zaehler">' + liste.length + " Ratsmitglieder</span></div>" +
      '<table class="mtab"><thead><tr>' +
      '<th data-sort="name">Name' + pfeil("name") + "</th>" +
      '<th data-sort="f" class="weg">Fraktion' + pfeil("f") + "</th>" +
      '<th data-sort="quote" style="text-align:right">Zustimmung' + pfeil("quote") + "</th>" +
      '<th data-sort="praesenz" style="text-align:right" class="weg">Präsenz' + pfeil("praesenz") + "</th>" +
      '<th class="weg">Stimmen</th></tr></thead><tbody>' +
      liste.map(function (m) {
        return "<tr>" +
          '<td class="nm' + (wegSeit(m.k) ? " istweg" : "") + '">' +
          '<button type="button" data-member="' + esc(m.k) + '">' +
          avatar(PERS[m.k], m.p, 30, m.name) + esc(m.name) + wegChip(m.k) + "</button></td>" +
          '<td class="weg" style="font-size:12.5px;color:var(--ink-2)">' + esc(m.f) + "</td>" +
          '<td class="zahl"><span class="quote"><span class="qbar"><i style="width:' +
          m.quote.toFixed(1) + '%"></i></span>' + pz(m.quote) + " %</span></td>" +
          '<td class="zahl weg">' + pz(m.praesenz) + " %</td>" +
          '<td class="weg"><span style="font-size:12px;color:var(--ink-3)">' +
          m.J + " Ja · " + m.N + " Nein · " + m.E + " Enth. · " + m.A + " abw.</span></td></tr>";
      }).join("") + "</tbody></table>" + fussHtml(s0);

    var sel = $("#fFrak", el);
    if (sel) sel.addEventListener("change", function () { st.frakFilter = sel.value; render(); });
    $$("th[data-sort]", el).forEach(function (th) {
      th.addEventListener("click", function () {
        var k = th.getAttribute("data-sort");
        if (st.sortKey === k) st.sortDir *= -1; else { st.sortKey = k; st.sortDir = k === "name" || k === "f" ? 1 : -1; }
        render();
      });
    });
  }

  function renderMitgliedDetail(el) {
    var k = st.mitglied;
    var stats = mitgliedStats().filter(function (m) { return m.k === k; })[0];
    if (!stats) { st.mitglied = null; return renderMembers(el); }
    var teile = k.split("|");
    var sessions = scopeSessions();
    var themen = {};
    var zeilen = [];
    sessions.forEach(function (s) {
      var m = s.m.filter(function (x) { return x.n === k; })[0];
      if (!m) return;
      var proSitzung = [];
      s.v.forEach(function (v, i) {
        var c = roh(m, i), kk = korr(m, i, istUmkehr(v));
        if (v.th) {
          themen[v.th] = themen[v.th] || { J: 0, N: 0, E: 0, A: 0 };
          themen[v.th][kk]++;
        }
        proSitzung.push({ v: v, i: i, c: c });
      });
      if (proSitzung.length) zeilen.push({ s: s, liste: proSitzung });
    });

    var pr = (D.personen && D.personen.liste || []).filter(function (p) { return p.k === k; })[0];
    var raus = wegSeit(k);
    var profil = "";
    if (pr) {
      var felder = [];
      if (pr.be) felder.push(["Beruf", pr.be]);
      if (pr.se) felder.push(["Im Rat seit", pr.se]);
      if (pr.ge) felder.push(["Gemeinde", pr.ge]);
      if (raus) felder.push(["Letzte Sitzung", raus]);
      profil =
        (felder.length ? '<div class="profilzeile">' + felder.map(function (f) {
          return "<span><b>" + f[0] + "</b>" + esc(f[1]) + "</span>";
        }).join("") + "</div>" : "") +
        ibBlock(pr);
    }
    if (ohneProfil(k)) {
      profil += '<p class="quellluecke"><b>Kein Profil auf sh.ch.</b> Zu dieser Person ' +
        "führt die Mitgliederseite des Kantons keinen Personenkasten. Darum fehlen hier " +
        "Porträt, Beruf und die Selbstdeklaration der Interessenbindungen. Die " +
        "Abstimmungsdaten sind davon nicht betroffen, sie stammen aus den " +
        "Abstimmungsprotokollen.</p>";
    }

    el.innerHTML =
      '<div class="mkopf">' + avatar(pr, stats.p, 58, teile[1] + " " + teile[0]) +
      "<div><h2>" + esc(teile[1] + " " + teile[0]) + wegChip(k) + "</h2>" +
      '<div class="msub">' + esc(stats.f) + " · " + esc(stats.p) + " · " +
      stats.sitzungen + " Sitzungen im Zeitraum" +
      (raus ? ". Nicht mehr im Rat: die Mitgliederliste auf sh.ch führt diese Person " +
        "nicht mehr. Belegt ist nur die letzte Sitzung, an der sie teilgenommen hat, " +
        "das Rücktrittsdatum steht in keiner der Quellen." : "") +
      "</div></div>" +
      '<button type="button" class="zurueck" id="zurueck">← Alle Ratsmitglieder</button></div>' +
      profil +
      '<div class="mgrid">' +
      mstat(pz(stats.quote) + " %", "Zustimmungsquote", "der abgegebenen Stimmen") +
      mstat(pz(stats.praesenz) + " %", "Präsenz", stats.abgegeben + " von " + stats.total) +
      mstat(stats.J, "Ja", "richtungskorrigiert") +
      mstat(stats.N, "Nein", "richtungskorrigiert") +
      mstat(stats.E, "Enthaltungen", "") +
      "</div>" +
      (Object.keys(themen).length
        ? '<div class="sec"><h2>Nach Thema</h2><p>richtungskorrigiert</p></div>' +
          '<div class="tbars">' + Object.keys(themen).sort().map(function (t) {
            var x = themen[t], ab = x.J + x.N + x.E;
            return '<div class="tbar"><div class="l"><span>' + esc(t) + "</span></div>" +
              '<div class="b">' + ["J", "N", "E", "A"].map(function (c) {
                var ges = x.J + x.N + x.E + x.A;
                return x[c] ? '<i class="seg-' + KLASSE[c] + '" style="width:' + (x[c] / ges * 100) + '%"></i>' : "";
              }).join("") + "</div>" +
              '<div class="v">' + (ab ? pz(x.J / ab * 100, 0) + " % Ja" : "–") + "</div></div>";
          }).join("") + "</div>"
        : "") +
      '<div class="sec"><h2>Jede einzelne Stimme</h2><p>neueste Sitzung zuerst</p></div>' +
      zeilen.map(function (g) {
        return '<section class="gruppe"><div class="ghead"><div>' +
          '<span class="glabel">Sitzung</span><h3>' + esc(g.s.n) + "</h3></div>" +
          '<span class="gcount">' + esc(g.s.dt) + "</span></div>" +
          '<div class="tbars" style="margin-top:14px">' + g.liste.map(function (x) {
            return '<div class="tbar" style="grid-template-columns:74px 1fr">' +
              '<div class="l"><span class="badge b-' + (x.c === "J" ? "ja" : x.c === "N" ? "nein" : "enth") +
              '" style="margin:0;font-size:10px">' + LABEL[x.c] + "</span></div>" +
              '<div style="font-size:13.5px;line-height:1.4">' +
              '<button type="button" class="lnk" data-goto="' + esc(g.s.s) + "|" + x.i + '">' +
              esc(x.v.t) + "</button>" +
              (g.s.pu && !g.s.pf ? ' <a class="plink" href="' + esc(g.s.pu) + '" target="_blank" ' +
                'rel="noopener" title="Wortprotokoll der Sitzung öffnen">' +
                '<svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true">' +
                '<path d="M6 3h7v7M13 3L6.5 9.5M11 9.5V13H3V5h3.5" stroke="currentColor" ' +
                'stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>' +
                "</svg></a>" : "") +
              (x.v.inv === 1 ? '<span class="uquelle" style="margin-left:7px">Umkehr</span>' : "") +
              "</div></div>";
          }).join("") + "</div></section>";
      }).join("") + fussHtml(sessions[0]);

    var zur = $("#zurueck", el);
    if (zur) zur.addEventListener("click", function () { st.mitglied = null; render(); });
  }
  /* Personenverzeichnis nach Schlüssel «Nachname|Vorname» */
  var PERS = {};
  (D.personen && D.personen.liste || []).forEach(function (p) { PERS[p.k] = p; });

  /* Porträt mit Ring in der Parteifarbe. Der Ring ersetzt den früheren
     Farbpunkt, sonst ginge beim Wechsel auf Bilder die Parteizuordnung auf
     einen Blick verloren. Fehlt ein Bild, bleibt der gefüllte Kreis. */
  function avatar(p, partei, groesse, name) {
    var g = groesse || 30;
    var ring = "box-shadow:0 0 0 2px var(--surface),0 0 0 " + (g > 40 ? 4 : 3) +
      "px var(--p-" + pkey(partei) + ")";
    var mass = "width:" + g + "px;height:" + g + "px;";
    if (p && p.bi) {
      return '<img class="avatar" src="data:image/jpeg;base64,' + p.bi +
        '" alt="" loading="lazy" width="' + g + '" height="' + g +
        '" style="' + mass + ring + '">';
    }
    // Ohne Bild die Initialen. Das betrifft vor allem Ausgeschiedene: sh.ch
    // führt sie nicht mehr, also gibt es kein Porträt. Eine leere dunkle
    // Scheibe sähe nach Fehler aus, die Initialen nach Absicht.
    var voll = (p && p.n) || name || "";
    var ini = voll.split(/\s+/).filter(Boolean).slice(0, 2)
                  .map(function (x) { return x[0]; }).join("").toUpperCase();
    return '<span class="avatar leerbild p-' + pkey(partei) + '" style="' + mass + ring +
      ";font-size:" + Math.round(g * 0.38) + 'px">' + esc(ini) + "</span>";
  }

  function mstat(n, l, s) {
    return '<div class="mstat"><div class="n">' + n + '</div><div class="l">' + l +
      '</div><div class="s">' + (s || "") + "</div></div>";
  }

  /* ═══ Rubrik: Fraktionen ═══════════════════════════════════════════════ */
  var ACHSEN = [
    { k: "quote", l: "Zustimmung" },
    { k: "disziplin", l: "Geschlossenheit" },
    { k: "praesenz", l: "Präsenz" },
    { k: "enthQuote", l: "Enthaltung" },
    { k: "opposition", l: "Opposition" }
  ];
  function renderFrak(el) {
    var fs = frakStats();
    fs.forEach(function (f) { if (st.spider[f.f] === undefined) st.spider[f.f] = true; });
    el.innerHTML =
      '<header class="hero"><div class="eyebrow">' + esc(scopeLabel()) + "</div>" +
      "<h1>Fraktionen</h1>" +
      '<p class="subline">Zustimmungsquote, Präsenz und Geschlossenheit. Alle Quoten sind ' +
      "richtungskorrigiert, ein Ja bedeutet überall inhaltliche Zustimmung.</p></header>" +
      '<div class="hinweis"><b>Geschlossenheit</b> heisst hier: Wie gross ist im Schnitt der ' +
      "Anteil der Fraktion, der gleich stimmt? 100 % wären lauter einstimmige Entscheide. " +
      "Bewusst nicht gezählt wird, wie oft eine Fraktion vollständig einig war, denn kleine " +
      "Fraktionen sind das rein zufällig viel häufiger als grosse.</div>" +
      '<div class="fgrid">' + fs.map(function (f) {
        return '<div class="fcard" style="border-top-color:' + fvar(f.f) + '">' +
          "<h3>" + esc(f.f) + '</h3><div class="sitze">' + f.sitze + " Sitze</div>" +
          zeile("Zustimmung", pz(f.quote) + " %", f.quote, "var(--ja)") +
          zeile("Präsenz", pz(f.praesenz) + " %", f.praesenz, "var(--ink-3)") +
          zeile("Geschlossenheit", pz(f.disziplin) + " %", f.disziplin, fvar(f.f)) +
          zeile("Enthaltungen", pz(f.enthQuote) + " %", f.enthQuote, "var(--enth)") +
          "</div>";
      }).join("") + "</div>" +
      '<div class="sec"><h2>Profil im Vergleich</h2><p>fünf Kennzahlen, gemittelt</p></div>' +
      '<div class="hinweis"><b>Lesehinweis:</b> Diese Achsen beschreiben Verhaltensmuster, nicht ' +
      "die politische Ausrichtung. Eine Links-Rechts-Einordnung würde eine redaktionelle " +
      "Bewertung jeder Vorlage verlangen und ist bewusst nicht enthalten.</div>" +
      '<div class="spiderwrap"><div><svg id="spider" width="440" height="380" viewBox="-40 0 440 380"></svg></div>' +
      '<div class="spidersteuer">' + fs.map(function (f) {
        return '<label class="ftoggle"><input type="checkbox" data-frak="' + esc(f.f) + '"' +
          (st.spider[f.f] ? " checked" : "") + '><span class="sw" style="background:' + fvar(f.f) +
          '"></span>' + esc(f.f) + "</label>";
      }).join("") + "</div></div>" + fussHtml(scopeSessions()[0]);

    $$('input[data-frak]', el).forEach(function (cb) {
      cb.addEventListener("change", function () {
        st.spider[cb.getAttribute("data-frak")] = cb.checked;
        zeichneSpider(fs);
      });
    });
    zeichneSpider(fs);

    function zeile(l, w, pct, farbe) {
      return '<div class="frow2"><span>' + l + "</span>" +
        '<span class="mini"><i style="width:' + Math.max(0, Math.min(100, pct)) + "%;background:" + farbe + '"></i></span>' +
        "<b>" + w + "</b></div>";
    }
  }
  function zeichneSpider(fs) {
    var svg = $("#spider");
    if (!svg) return;
    var CX = 180, CY = 190, R = 128, N = ACHSEN.length, g = "";
    g += '<g stroke="var(--line)" fill="none">';
    [0.25, 0.5, 0.75, 1].forEach(function (f) {
      var pts = [];
      for (var i = 0; i < N; i++) {
        var a = Math.PI * 2 * i / N - Math.PI / 2;
        pts.push((CX + Math.cos(a) * R * f).toFixed(1) + "," + (CY + Math.sin(a) * R * f).toFixed(1));
      }
      g += '<polygon points="' + pts.join(" ") + '"/>';
    });
    g += "</g>";
    g += '<g font-size="11" fill="var(--ink-3)" font-weight="600">';
    ACHSEN.forEach(function (ax, i) {
      var a = Math.PI * 2 * i / N - Math.PI / 2;
      var x = CX + Math.cos(a) * (R + 26), y = CY + Math.sin(a) * (R + 20);
      var anchor = Math.abs(Math.cos(a)) < 0.3 ? "middle" : (Math.cos(a) > 0 ? "start" : "end");
      g += '<text x="' + x.toFixed(0) + '" y="' + y.toFixed(0) + '" text-anchor="' + anchor + '">' + ax.l + "</text>";
    });
    g += "</g>";
    fs.forEach(function (f) {
      if (!st.spider[f.f]) return;
      var pts = [];
      ACHSEN.forEach(function (ax, i) {
        var val = Math.max(0, Math.min(100, f[ax.k])) / 100;
        var a = Math.PI * 2 * i / N - Math.PI / 2;
        pts.push((CX + Math.cos(a) * R * val).toFixed(1) + "," + (CY + Math.sin(a) * R * val).toFixed(1));
      });
      g += '<polygon points="' + pts.join(" ") + '" fill="' + fvar(f.f) +
        '" fill-opacity=".14" stroke="' + fvar(f.f) + '" stroke-width="2"/>';
    });
    svg.innerHTML = g;
  }

  /* ═══ Rubrik: Themen ═══════════════════════════════════════════════════ */
  function renderThemen(el) {
    var liste = alleVotes().filter(function (x) { return x.v.th; });
    var zaehler = {};
    liste.forEach(function (x) { zaehler[x.v.th] = (zaehler[x.v.th] || 0) + 1; });
    var namen = Object.keys(zaehler).sort();
    if (!st.thema || namen.indexOf(st.thema) === -1) st.thema = namen[0] || null;
    var gewaehlt = liste.filter(function (x) { return x.v.th === st.thema; });

    var proFrak = {};
    gewaehlt.forEach(function (x) {
      var inv = istUmkehr(x.v);
      x.s.m.forEach(function (m) {
        proFrak[m.f] = proFrak[m.f] || { J: 0, N: 0, E: 0, A: 0 };
        proFrak[m.f][korr(m, x.i, inv)]++;
      });
    });

    el.innerHTML =
      '<header class="hero"><div class="eyebrow">' + esc(scopeLabel()) + "</div><h1>Themen</h1>" +
      '<p class="subline">Die Themen folgen den neun Hauptgruppen der Schaffhauser ' +
      "Rechtssammlung. Rein beschreibend, ohne Wertung.</p></header>" +
      '<div class="chips">' + namen.map(function (t) {
        return '<button type="button" class="tchip' + (t === st.thema ? " on" : "") +
          '" data-thema="' + esc(t) + '">' + esc(t) + '<span class="n">' + zaehler[t] + "</span></button>";
      }).join("") + "</div>" +
      (st.thema ? '<div class="sec"><h2>' + esc(st.thema) + "</h2><p>" + gewaehlt.length +
        " Abstimmungen im Zeitraum</p></div>" +
        '<div class="tbars">' + Object.keys(proFrak).sort(function (a, b) {
          var A = proFrak[a], B = proFrak[b];
          return (B.J + B.N + B.E) - (A.J + A.N + A.E);
        }).map(function (f) {
          var x = proFrak[f], ges = x.J + x.N + x.E + x.A, ab = x.J + x.N + x.E;
          return '<div class="tbar"><div class="l"><i class="pdot p-' + fkey(f) + '"></i>' +
            "<span>" + esc(f) + "</span></div>" +
            '<div class="b">' + ["J", "N", "E", "A"].map(function (c) {
              return x[c] ? '<i class="seg-' + KLASSE[c] + '" style="width:' + (x[c] / ges * 100) + '%"></i>' : "";
            }).join("") + "</div>" +
            '<div class="v">' + (ab ? pz(x.J / ab * 100, 0) + " % Ja" : "–") + "</div></div>";
        }).join("") + "</div>" +
        '<div class="sec"><h2>Abstimmungen zum Thema</h2><p>neueste zuerst</p></div>' +
        '<div class="cards">' + gewaehlt.slice(0, 40).map(function (x) {
          return voteCardHtml(x.s, x.v, x.i, { zeigeSitzung: true });
        }).join("") + "</div>"
        : '<p class="leer">Für diesen Zeitraum sind keine Themen zugeordnet.</p>') +
      fussHtml(scopeSessions()[0]);
  }

  /* ═══ Rubrik: Ranglisten ═══════════════════════════════════════════════ */
  function renderRang(el) {
    var mem = mitgliedStats().filter(function (m) { return m.total > 0; });
    var fs = frakStats();
    function box(titel, unter, daten, wert, format) {
      var top = daten.slice().sort(function (a, b) { return wert(b) - wert(a); }).slice(0, 8);
      return '<div class="rbox"><h3>' + titel + "<em>" + unter + "</em></h3><ul class=\"rlist\">" +
        top.map(function (it, i) {
          /* Personen führen ins Profil, Fraktionen bleiben Text */
          var inhalt = it.k
            ? '<button type="button" data-member="' + esc(it.k) + '">' +
              avatar(PERS[it.k], it.p, 26, it.name) + esc(it.name) +
              " <small>" + esc(it.f) + "</small></button>"
            : '<i class="pdot p-' + fkey(it.f) + '"></i>' + esc(it.f);
          return '<li><span class="r">' + (i + 1) + '</span><span class="nm">' + inhalt +
            '</span><span class="v">' + format(wert(it)) + "</span></li>";
        }).join("") + "</ul></div>";
    }
    var prozent = function (v) { return pz(v) + " %"; };
    el.innerHTML =
      '<header class="hero"><div class="eyebrow">' + esc(scopeLabel()) + "</div><h1>Ranglisten</h1>" +
      '<p class="subline">Jeweils die ersten acht. Die Bezeichnungen sind bewusst sachlich ' +
      "gehalten, die Zahlen beschreiben Verhalten und bewerten es nicht.</p></header>" +
      '<div class="hinweis"><b>Zur Einordnung:</b> Abwesenheiten können entschuldigt sein. ' +
      "Quoten beziehen sich auf die Sitzungen seit Amtsantritt der jeweiligen Person, " +
      "Zustimmungsquoten auf die abgegebenen Stimmen und sind richtungskorrigiert.</div>" +
      '<div class="sec"><h2>Ratsmitglieder</h2><p>' + mem.length + " Personen im Zeitraum</p></div>" +
      '<div class="rgrid">' +
      box("Höchste Präsenz", "abgegebene Stimmen", mem, function (m) { return m.praesenz; }, prozent) +
      box("Höchste Abwesenheitsquote", "nicht teilgenommen", mem, function (m) { return 100 - m.praesenz; }, prozent) +
      box("Höchste Zustimmungsquote", "der abgegebenen Stimmen", mem, function (m) { return m.quote; }, prozent) +
      box("Höchste Ablehnungsquote", "der abgegebenen Stimmen", mem, function (m) { return 100 - m.quote - m.enthQuote; }, prozent) +
      box("Häufigste Enthaltungen", "der abgegebenen Stimmen", mem, function (m) { return m.enthQuote; }, prozent) +
      "</div>" +
      '<div class="sec" style="margin-top:40px"><h2>Fraktionen</h2><p>' + fs.length + " Fraktionen</p></div>" +
      '<div class="rgrid">' +
      box("Höchste Präsenz", "abgegebene Stimmen", fs, function (f) { return f.praesenz; }, prozent) +
      box("Höchste Zustimmungsquote", "der abgegebenen Stimmen", fs, function (f) { return f.quote; }, prozent) +
      box("Höchste Geschlossenheit", "einstimmige Fraktionsentscheide", fs, function (f) { return f.disziplin; }, prozent) +
      box("Häufigste Enthaltungen", "der abgegebenen Stimmen", fs, function (f) { return f.enthQuote; }, prozent) +
      "</div>" + fussHtml(scopeSessions()[0]);
  }

  /* ═══ Rubrik: Wer stimmt wie ich ═══════════════════════════════════════ */
  function renderMatch(el) {
    var M = D.match;
    if (!M || !M.fragen.length) {
      el.innerHTML = '<header class="hero"><h1>Wer stimmt wie ich?</h1></header>' +
        '<p class="leer">Für die laufende Legislatur liegen noch zu wenige geprüfte ' +
        "Abstimmungen vor.</p>";
      return;
    }
    if (!st.modus || M.modi.indexOf(st.modus) === -1) st.modus = M.modi[0];
    var fragen = M.fragen.slice(0, st.modus);
    var beantwortet = 0;
    for (var q = 0; q < fragen.length; q++) {
      if (st.antworten[q] === "J" || st.antworten[q] === "N") beantwortet++;
    }

    el.innerHTML =
      '<header class="hero"><div class="eyebrow">' +
      esc((D.leg[String(M.leg)] || {}).label || "") + "</div>" +
      "<h1>Wer stimmt wie ich?</h1>" +
      '<p class="subline">Beantworten Sie Sachfragen, über die der Kantonsrat wirklich ' +
      "abgestimmt hat. Danach sehen Sie, welche Ratsmitglieder und Fraktionen am häufigsten " +
      "gleich gestimmt haben wie Sie. Mindestens " + M.min + " Antworten sind nötig.</p></header>" +
      '<div class="modi"><span class="modilabel">Umfang</span>' +
      M.modi.map(function (m) {
        return '<button type="button" class="tchip' + (m === st.modus ? " on" : "") +
          '" data-modus="' + m + '">' + m + " Fragen</button>";
      }).join("") +
      '<span class="modinote">Die Fragen sind nach Trennschärfe geordnet. Der kurze ' +
      "Modus ist der Anfang des langen, Antworten bleiben beim Wechsel erhalten.</span></div>" +
      '<div class="hinweis"><b>Wie die Fragen gewählt sind:</b> Aus der laufenden Legislatur, ' +
      "geordnet danach, wie stark eine Abstimmung die Fraktionen geteilt hat. Je Vorlage " +
      "steht zuerst die trennschärfste Abstimmung, in den längeren Modi kommen weitere " +
      "aus derselben Vorlage dazu. Insgesamt stehen " + M.fragen.length + " Fragen zur " +
      "Verfügung. Weggelassen sind Verfahrensfragen wie Ordnungsanträge und Rückweisungen " +
      "sowie Abstimmungen, bei denen die unterlegene Seite weniger als 15 Prozent hielt: " +
      "eine Vorlage, die einstimmig durchgeht, ordnet niemanden zu. Zugelassen sind nur " +
      "Abstimmungen aus Sitzungen mit publiziertem Wortprotokoll, deren Richtung geprüft " +
      "oder ausdrücklich festgelegt ist. Bei Umkehrabstimmungen sind Ja und Nein vorher " +
      "getauscht, damit ein Ja hier immer Zustimmung zur Sache bedeutet.</div>" +
      fragen.map(function (f, i) {
        var a = st.antworten[i];
        return '<article class="mfrage">' +
          '<div class="thema">' + esc(f.thema || "Ohne Thema") +
          (f.geprueft ? "" : ' <span class="roh">Frage noch nicht redigiert</span>') + "</div>" +
          (f.kontext ? '<p class="fkontext">' + esc(f.kontext) + "</p>" : "") +
          "<h3>" + esc(f.kurz) + "</h3>" +
          (f.zus ? '<p class="ktx">' + esc(f.zus) + "</p>" : "") +
          (f.pro || f.contra ? '<div class="procontra">' +
            (f.pro ? '<div class="pro"><b>Aus der Debatte, dafür</b>«' + esc(f.pro) + "»</div>" : "") +
            (f.contra ? '<div class="contra"><b>Aus der Debatte, dagegen</b>«' + esc(f.contra) + "»</div>" : "") +
            "</div>" : "") +
          '<details class="fold fquelle"><summary><span class="caret"></span>' +
          "Worüber genau abgestimmt wurde</summary>" +
          '<div class="foldbody"><p class="frohtext">' + esc(f.roh || "—") + "</p>" +
          (f.pu ? '<a class="plink" href="' + esc(f.pu) + '" target="_blank" rel="noopener">' +
            "Wortprotokoll der Sitzung</a>" : "") + "</div></details>" +
          '<div class="mopts">' +
          opt(i, "J", "Ja", a) + opt(i, "N", "Nein", a) + opt(i, "S", "Überspringen", a) +
          "</div></article>";
      }).join("") +
      '<div class="mleiste"><button type="button" class="btn" id="auswerten"' +
      (beantwortet >= M.min ? "" : " disabled") + ">Auswerten</button>" +
      '<button type="button" class="btn ghost" id="zuruecksetzen">Zurücksetzen</button>' +
      '<span class="mzaehler">' + beantwortet + " von " + fragen.length + " beantwortet" +
      (beantwortet < M.min ? ", mindestens " + M.min + " nötig" : "") + "</span></div>" +
      '<div id="mergebnis"></div>' + fussHtml(null);

    $$("[data-modus]", el).forEach(function (b) {
      b.addEventListener("click", function () {
        st.modus = parseInt(b.getAttribute("data-modus"), 10);
        render();
        window.scrollTo({ top: 0 });
      });
    });
    $$(".mopt", el).forEach(function (b) {
      b.addEventListener("click", function () {
        var i = b.getAttribute("data-i"), w = b.getAttribute("data-w");
        st.antworten[i] = st.antworten[i] === w ? undefined : w;
        render();
        var el2 = $("#p-match");
        var karte = $$(".mfrage", el2)[parseInt(i, 10)];
        if (karte) karte.scrollIntoView({ block: "center", behavior: "smooth" });
      });
    });
    var aus = $("#auswerten", el);
    if (aus) aus.addEventListener("click", function () { auswerten(); });
    var res = $("#zuruecksetzen", el);
    if (res) res.addEventListener("click", function () { st.antworten = {}; render(); });

    function opt(i, w, label, aktiv) {
      var kl = aktiv === w ? " on-" + (w === "J" ? "ja" : w === "N" ? "nein" : "skip") : "";
      return '<button type="button" class="mopt' + kl + '" data-i="' + i + '" data-w="' + w + '">' +
        label + "</button>";
    }
  }

  /* Die Auswertung steckte in auswerten() und war damit nur für die Anzeige
     verfügbar. Sie ist jetzt eine eigene Funktion, damit der Bilddownload
     dasselbe Ergebnis zeigt wie die Seite und nicht eine zweite Rechnung. */
  function matchRechnen() {
    var M = D.match;
    if (!M || !st.antworten) return null;
    var n = st.modus || M.modi[0];
    var eigene = M.fragen.slice(0, n).map(function (_, i) {
      var a = st.antworten[i];
      return a === "J" || a === "N" ? a : null;
    });
    function trefferquote(stimmen) {
      var gleich = 0, gemeinsam = 0;
      for (var i = 0; i < eigene.length; i++) {
        if (!eigene[i] || !stimmen[i]) continue;
        gemeinsam++;
        if (eigene[i] === stimmen[i]) gleich++;
      }
      return { gemeinsam: gemeinsam, p: gemeinsam ? gleich / gemeinsam * 100 : 0 };
    }
    var personen = M.mitglieder.map(function (m) {
      var r = trefferquote(m.s);
      return { name: m.n, f: m.f, p: m.p, quote: r.p, gemeinsam: r.gemeinsam };
    }).filter(function (x) { return x.gemeinsam >= M.min; })
      .sort(function (a, b) { return b.quote - a.quote; });

    var proFrak = {};
    M.mitglieder.forEach(function (m) {
      var r = trefferquote(m.s);
      if (r.gemeinsam < M.min) return;
      proFrak[m.f] = proFrak[m.f] || { summe: 0, n: 0 };
      proFrak[m.f].summe += r.p; proFrak[m.f].n++;
    });
    var fraktionen = Object.keys(proFrak).map(function (f) {
      return { f: f, quote: proFrak[f].summe / proFrak[f].n, n: proFrak[f].n };
    }).sort(function (a, b) { return b.quote - a.quote; });

    var beantwortet = eigene.filter(Boolean).length;
    if (beantwortet < M.min) return null;
    return {
      personen: personen, fraktionen: fraktionen,
      beantwortet: beantwortet, gesamt: n,
      /* für den Bilddownload vereinheitlicht */
      frak: fraktionen.map(function (f) {
        return { name: f.f, wert: f.quote, partei: f.f,
                 unter: f.n + (f.n === 1 ? " Ratsmitglied" : " Ratsmitglieder") };
      }),
      leute: personen.map(function (x) {
        return { name: x.name, wert: x.quote, partei: x.p, f: x.f, unter: x.f };
      })
    };
  }

  function auswerten() {
    var M = D.match;
    var erg = matchRechnen();
    if (!erg) return;
    var personen = erg.personen, fraktionen = erg.fraktionen;

    $("#mergebnis").innerHTML =
      '<div class="sec" style="margin-top:34px"><h2>Fraktionen</h2>' +
      "<p>gemittelte Übereinstimmung</p></div>" +
      '<div class="mtreffer">' + fraktionen.map(function (f, i) {
        return balken(i + 1, esc(f.f), f.n + " Mitglieder", f.quote, fkey(f.f));
      }).join("") + "</div>" +
      '<div class="sec" style="margin-top:34px"><h2>Ratsmitglieder</h2>' +
      "<p>die zwanzig höchsten Übereinstimmungen</p></div>" +
      '<div class="mtreffer">' + personen.slice(0, 20).map(function (p, i) {
        return balken(i + 1, esc(p.name), esc(p.f), p.quote, pkey(p.p));
      }).join("") + "</div>" +
      '<div class="hinweis" style="margin-top:26px"><b>Was die Zahl bedeutet:</b> Der Anteil ' +
      "der Fragen, bei denen Sie und die Person beide Stellung bezogen haben und gleich " +
      "gestimmt haben. Enthaltungen und Abwesenheiten zählen nicht mit. Das ist eine " +
      "Beschreibung des Stimmverhaltens, keine Wahlempfehlung.</div>";
    $("#mergebnis").scrollIntoView({ behavior: "smooth", block: "start" });

    function balken(rang, name, sub, quote, farbKey) {
      return '<div class="mt"><span class="r">' + rang + '</span>' +
        '<span class="nm"><i class="pdot p-' + farbKey + '"></i>' + name +
        " <small>" + sub + "</small></span>" +
        '<span class="bar"><i style="width:' + quote.toFixed(1) + '%"></i></span>' +
        '<span class="p">' + pz(quote, 0) + " %</span></div>";
    }
  }

  /* ═══ Bilddownload ═════════════════════════════════════════════════════ */
  /* Motive für den Bilddownload.
     gruppe  Überschrift im Auswahlfeld
     subjekt "mitglied" verlangt eine zweite Auswahl, wer gemeint ist
     nur     Bedingung, ob das Motiv überhaupt anwählbar ist
     Die Ranglisten teilen sich eine Zeichenfunktion und unterscheiden sich nur
     in Titel, Kennzahl und Formatierung; darum stehen sie als Daten hier und
     nicht als vier fast gleiche Funktionen. */
  var MOTIVE = [
    { k: "vote",    g: "Abstimmungen", l: "Neuste Abstimmung" },
    { k: "sitzung", g: "Abstimmungen", l: "Sitzungsüberblick" },

    { k: "rang:quote",    g: "Rangliste Ratsmitglieder", l: "Höchste Zustimmungsquote",
      w: "quote",    u: "der abgegebenen Stimmen" },
    { k: "rang:nein",     g: "Rangliste Ratsmitglieder", l: "Höchste Ablehnungsquote",
      w: "nein",     u: "der abgegebenen Stimmen" },
    { k: "rang:praesenz", g: "Rangliste Ratsmitglieder", l: "Höchste Präsenz",
      w: "praesenz", u: "abgegebene Stimmen" },
    { k: "rang:abw",      g: "Rangliste Ratsmitglieder", l: "Höchste Abwesenheitsquote",
      w: "abw",      u: "nicht teilgenommen" },
    { k: "rang:enth",     g: "Rangliste Ratsmitglieder", l: "Häufigste Enthaltungen",
      w: "enthQuote", u: "der abgegebenen Stimmen" },

    { k: "frang:quote",    g: "Rangliste Fraktionen", l: "Höchste Zustimmungsquote",
      w: "quote",    u: "der abgegebenen Stimmen", frak: true },
    { k: "frang:praesenz", g: "Rangliste Fraktionen", l: "Höchste Präsenz",
      w: "praesenz", u: "abgegebene Stimmen", frak: true },
    { k: "frang:geschl",   g: "Rangliste Fraktionen", l: "Höchste Geschlossenheit",
      w: "disziplin", u: "mittlerer Mehrheitsanteil", frak: true },
    { k: "frang:enth",     g: "Rangliste Fraktionen", l: "Häufigste Enthaltungen",
      w: "enthQuote", u: "der abgegebenen Stimmen", frak: true },

    { k: "frak", g: "Fraktionen", l: "Fraktionsvergleich" },

    { k: "person",     g: "Einzelnes Ratsmitglied", l: "Profilkarte", subjekt: "mitglied" },
    { k: "personIb",   g: "Einzelnes Ratsmitglied", l: "Interessenbindungen",
      subjekt: "mitglied" },

    { k: "matchFrak", g: "Wer stimmt wie ich?", l: "Mein Ergebnis: Fraktionen",
      nur: "match" },
    { k: "matchTop",  g: "Wer stimmt wie ich?", l: "Mein Ergebnis: Ratsmitglieder",
      nur: "match" }
  ];

  function motivVon(k) {
    for (var i = 0; i < MOTIVE.length; i++) if (MOTIVE[i].k === k) return MOTIVE[i];
    return MOTIVE[0];
  }

  /* Anwählbar ist ein Motiv nur, wenn es auch etwas zu zeigen gibt. Ein leeres
     Ergebnisbild wäre schlimmer als ein fehlendes Motiv. */
  function motivMoeglich(m) {
    if (m.nur === "match") return matchErgebnisDa();
    return true;
  }

  /* Ob ein Ergebnis vorliegt, entscheidet dieselbe Rechnung wie die Anzeige.
     Eine eigene Zählung war schon einmal falsch: st.antworten ist ein Objekt
     und hat kein length, die Schleife lief nie und die Motive fehlten. */
  function matchErgebnisDa() {
    return matchRechnen() !== null;
  }
  var W = 1080, H = 1350;

  function cssFarbe(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || "#888";
  }
  /* Das Porträt eines Ratsmitglieds ist ein base64-JPEG und muss vor dem
     Zeichnen geladen sein, sonst bliebe die Fläche leer und ein sofortiger
     Download zeigte ein halbfertiges Bild. Darum: erst laden, dann malen. */
  function zeichneBild(motiv) {
    var m = motivVon(motiv);
    if (m.subjekt === "mitglied") {
      var pr = PERS[bildSubjekt()];
      if (pr && pr.bi) {
        var im = new Image();
        im.onload = function () { malen(motiv, im); };
        im.onerror = function () { malen(motiv, null); };
        im.src = "data:image/jpeg;base64," + pr.bi;
        return;
      }
    }
    malen(motiv, null);
  }

  function malen(motiv, bild) {
    var c = $("#bildCanvas"), x = c.getContext("2d");
    var bg = cssFarbe("--surface"), ink = cssFarbe("--ink"),
        ink2 = cssFarbe("--ink-2"), ink3 = cssFarbe("--ink-3"), line = cssFarbe("--line");
    x.fillStyle = bg; x.fillRect(0, 0, W, H);

    /* Kopf */
    x.fillStyle = ink;
    x.font = "700 30px Archivo, sans-serif";
    x.fillText("KANTONSRAT SCHAFFHAUSEN", 72, 96);
    x.fillStyle = ink3;
    x.font = "600 21px 'Public Sans', sans-serif";
    x.fillText("KANTONSRATSSPIEGEL", 72, 130);
    x.strokeStyle = ink; x.lineWidth = 3;
    x.beginPath(); x.moveTo(72, 156); x.lineTo(W - 72, 156); x.stroke();

    var y = 240, m = motivVon(motiv);
    if (motiv === "vote") y = bildVote(x, y, ink, ink2, ink3, line);
    else if (motiv === "sitzung") y = bildSitzung(x, y, ink, ink2, ink3, line);
    else if (motiv === "frak") y = bildFrak(x, y, ink, ink2, ink3, line);
    else if (motiv === "person") y = bildPerson(x, y, ink, ink2, ink3, line, bild);
    else if (motiv === "personIb") y = bildPersonIb(x, y, ink, ink2, ink3, line, bild);
    else if (motiv === "matchFrak") y = bildMatch(x, y, ink, ink2, ink3, line, "frak");
    else if (motiv === "matchTop") y = bildMatch(x, y, ink, ink2, ink3, line, "top");
    else if (m.w) y = bildRangArt(x, y, ink, ink2, ink3, line, m);
    else y = bildRangArt(x, y, ink, ink2, ink3, line, motivVon("rang:quote"));

    /* Wasserzeichen */
    x.strokeStyle = line; x.lineWidth = 1;
    x.beginPath(); x.moveTo(72, H - 132); x.lineTo(W - 72, H - 132); x.stroke();
    x.fillStyle = ink2;
    x.font = "700 22px 'Public Sans', sans-serif";
    x.fillText("Kantonsrat Schaffhausen · Kantonsratsspiegel", 72, H - 92);
    x.fillStyle = ink3;
    x.font = "400 18px 'Public Sans', sans-serif";
    x.fillText("Daten: Parlamentsdienste Kanton Schaffhausen", 72, H - 62);
  }


  /* ── Bausteine für die neuen Motive ──────────────────────────────────── */

  function bildSubjekt() {
    var s = $("#bildSubjekt");
    return (s && s.value) || (mitgliedStats()[0] || {}).k || "";
  }

  /* Kennzahl eines Motivs. Zwei der fünf Mitgliederranglisten lassen sich nicht
     direkt ablesen und werden hier gerechnet. */
  function motivWert(m, e) {
    if (m.w === "nein") return e.abgegeben ? e.N / e.abgegeben * 100 : 0;
    if (m.w === "abw")  return e.total ? e.A / e.total * 100 : 0;
    return e[m.w] || 0;
  }

  function kopfzeile(x, ink, ink3, titel, unter, y) {
    x.fillStyle = ink;
    x.font = "700 52px Archivo, sans-serif";
    y = umbrechen(x, titel, 72, y, W - 144, 60, 2);
    x.fillStyle = ink3;
    x.font = "400 26px 'Public Sans', sans-serif";
    x.fillText(unter, 72, y + 12);
    return y + 60;
  }

  /* Eine Rangliste, für Mitglieder wie für Fraktionen. Zehn Zeilen mit Balken.
     Der Balken ist auf den höchsten Wert der Liste bezogen und nicht auf 100
     Prozent: bei Präsenzwerten zwischen 88 und 99 wären sonst alle Balken
     gleich lang und die Grafik sagte nichts. */
  function bildRangArt(x, y, ink, ink2, ink3, line, m) {
    var liste = (m.frak ? frakStats() : mitgliedStats())
      .filter(function (e) { return m.frak ? e.abgegeben > 0 : e.abgegeben > 0; })
      .map(function (e) {
        return { name: m.frak ? e.f : anzeigeName(e.k),
                 partei: m.frak ? null : e.p,
                 /* Unterzeile: bei Mitgliedern die Fraktion, bei Fraktionen die
                    Sitzzahl. Den Fraktionsnamen zu wiederholen sagt nichts. */
                 unter: m.frak ? (e.sitze + (e.sitze === 1 ? " Sitz" : " Sitze"))
                               : e.f,
                 wert: motivWert(m, e) };
      })
      .sort(function (a, b) { return b.wert - a.wert; })
      .slice(0, 10);
    if (!liste.length) return y;

    y = kopfzeile(x, ink, ink3, m.l, m.u + " · " + scopeLabel(), y);
    var hoch = liste[0].wert || 1;

    liste.forEach(function (e, i) {
      /* Fraktionen tragen ihre Fraktionsfarbe (fkey), Ratsmitglieder die ihrer
         Partei (pkey). Mit pkey auf einen Fraktionsnamen kommt nur Grau heraus. */
      var farbe = cssFarbe("--p-" + (m.frak ? fkey(e.name) : pkey(e.partei)));
      x.fillStyle = ink3;
      x.font = "700 26px 'Public Sans', sans-serif";
      x.fillText(String(i + 1), 72, y + 30);
      x.fillStyle = ink;
      x.font = "600 30px 'Public Sans', sans-serif";
      x.fillText(kuerzText(x, e.name, 470), 118, y + 30);
      if (e.unter) {
        x.fillStyle = ink3;
        x.font = "400 21px 'Public Sans', sans-serif";
        x.fillText(kuerzText(x, e.unter, 400), 118, y + 60);
      }

      var bx = 620, bw = W - 72 - bx - 130;
      x.fillStyle = line;
      x.fillRect(bx, y + 12, bw, 22);
      x.fillStyle = farbe;
      x.fillRect(bx, y + 12, Math.max(bw * (e.wert / hoch), 3), 22);
      x.fillStyle = ink;
      x.font = "700 30px 'Public Sans', sans-serif";
      x.textAlign = "right";
      x.fillText(pz(e.wert, 1) + " %", W - 72, y + 34);
      x.textAlign = "left";

      y += 86;
      if (i < liste.length - 1) {
        x.strokeStyle = line; x.lineWidth = 1;
        x.beginPath(); x.moveTo(72, y - 22); x.lineTo(W - 72, y - 22); x.stroke();
      }
    });
    return y;
  }

  function kuerzText(x, s, breite) {
    s = String(s || "");
    if (x.measureText(s).width <= breite) return s;
    while (s.length > 4 && x.measureText(s + "…").width > breite) s = s.slice(0, -1);
    return s + "…";
  }

  function rundesBild(x, bild, cx, cy, r, ringfarbe) {
    x.save();
    x.beginPath(); x.arc(cx, cy, r, 0, Math.PI * 2); x.closePath(); x.clip();
    if (bild) {
      var s = Math.max(2 * r / bild.width, 2 * r / bild.height);
      x.drawImage(bild, cx - bild.width * s / 2, cy - bild.height * s / 2,
                  bild.width * s, bild.height * s);
    } else {
      x.fillStyle = cssFarbe("--sunken");
      x.fillRect(cx - r, cy - r, 2 * r, 2 * r);
    }
    x.restore();
    x.strokeStyle = ringfarbe; x.lineWidth = 6;
    x.beginPath(); x.arc(cx, cy, r + 3, 0, Math.PI * 2); x.stroke();
  }

  /* Profilkarte eines Ratsmitglieds: Porträt, Fraktion, die drei Kennzahlen und
     die stärksten Themen. */
  function bildPerson(x, y, ink, ink2, ink3, line, bild) {
    var k = bildSubjekt();
    var e = mitgliedStats().filter(function (s) { return s.k === k; })[0];
    if (!e) return y;
    var pr = PERS[k] || {}, farbe = cssFarbe("--p-" + pkey(e.p));

    rundesBild(x, bild, 72 + 90, y + 80, 90, farbe);
    if (!bild) {
      x.fillStyle = ink3;
      x.font = "700 60px 'Public Sans', sans-serif";
      x.textAlign = "center";
      x.fillText(initialen(anzeigeName(k)), 72 + 90, y + 102);
      x.textAlign = "left";
    }

    x.fillStyle = ink;
    x.font = "700 50px Archivo, sans-serif";
    var yy = umbrechen(x, anzeigeName(k), 300, y + 52, W - 372, 56, 2);
    x.fillStyle = ink3;
    x.font = "600 25px 'Public Sans', sans-serif";
    x.fillText(kuerzText(x, e.f, W - 372), 300, yy + 10);
    if (wegSeit(k)) {
      x.fillStyle = ink3;
      x.font = "400 21px 'Public Sans', sans-serif";
      x.fillText("ausgeschieden, letzte Sitzung " + wegSeit(k).slice(0, 34), 300, yy + 44);
    }
    y += 210;

    [["Zustimmung", pz(e.quote, 1) + " %", "der abgegebenen Stimmen"],
     ["Präsenz", pz(e.praesenz, 1) + " %", e.abgegeben + " von " + e.total],
     ["Sitzungen", String(e.sitzungen), "im Zeitraum"]].forEach(function (s, i) {
      var bx = 72 + i * ((W - 144) / 3);
      x.fillStyle = ink;
      x.font = "700 46px Archivo, sans-serif";
      x.fillText(s[1], bx, y + 46);
      x.fillStyle = ink2;
      x.font = "600 22px 'Public Sans', sans-serif";
      x.fillText(s[0], bx, y + 78);
      x.fillStyle = ink3;
      x.font = "400 19px 'Public Sans', sans-serif";
      x.fillText(s[2], bx, y + 104);
    });
    y += 150;

    x.strokeStyle = line; x.lineWidth = 1;
    x.beginPath(); x.moveTo(72, y); x.lineTo(W - 72, y); x.stroke();
    y += 46;

    var t = themenFuer(k);
    if (t.length) {
      x.fillStyle = ink3;
      x.font = "600 22px 'Public Sans', sans-serif";
      x.fillText("ZUSTIMMUNG NACH THEMA", 72, y);
      y += 40;
      t.slice(0, 5).forEach(function (r) {
        x.fillStyle = ink;
        x.font = "600 26px 'Public Sans', sans-serif";
        x.fillText(kuerzText(x, r.t, 560), 72, y + 24);
        var bx = 660, bw = W - 72 - bx - 110;
        x.fillStyle = line; x.fillRect(bx, y + 6, bw, 20);
        x.fillStyle = farbe; x.fillRect(bx, y + 6, Math.max(bw * r.q / 100, 3), 20);
        x.fillStyle = ink;
        x.font = "700 26px 'Public Sans', sans-serif";
        x.textAlign = "right";
        x.fillText(pz(r.q, 0) + " %", W - 72, y + 26);
        x.textAlign = "left";
        y += 62;
      });
    }
    return y;
  }

  /* In der Tabelle steht «Nachname Vorname», weil danach sortiert wird. Auf
     einem Bild, das geteilt wird, liest sich «Vorname Nachname» natürlicher. */
  function anzeigeName(k) {
    var teile = String(k || "").split("|");
    return teile.length > 1 ? teile[1] + " " + teile[0] : (k || "");
  }

  function initialen(n) {
    return String(n || "").split(/\s+/).filter(Boolean).slice(0, 2)
      .map(function (w) { return w[0]; }).join("").toUpperCase();
  }

  function themenFuer(k) {
    var themen = {};
    scopeSessions().forEach(function (s) {
      var m = s.m.filter(function (q) { return q.n === k; })[0];
      if (!m) return;
      for (var i = 0; i < s.v.length; i++) {
        var th = s.v[i].th || "Ohne Thema";
        themen[th] = themen[th] || { J: 0, ab: 0 };
        var c = korr(m, i, istUmkehr(s.v[i]));
        if (c === "J") { themen[th].J++; themen[th].ab++; }
        else if (c === "N" || c === "E") themen[th].ab++;
      }
    });
    return Object.keys(themen).map(function (th) {
      return { t: th, q: themen[th].ab ? themen[th].J / themen[th].ab * 100 : 0,
               n: themen[th].ab };
    }).filter(function (r) { return r.n >= 5; })
      .sort(function (a, b) { return b.q - a.q; });
  }

  /* Interessenbindungen eines Ratsmitglieds, blau deklariert, gelb nur im
     Handelsregister. Dieselbe Unterscheidung wie im Dashboard, damit ein
     geteiltes Bild nicht anders aussagt als die Seite. */
  function bildPersonIb(x, y, ink, ink2, ink3, line, bild) {
    var k = bildSubjekt();
    var e = mitgliedStats().filter(function (s) { return s.k === k; })[0];
    var pr = PERS[k] || {};
    if (!e) return y;
    var farbe = cssFarbe("--p-" + pkey(e.p));

    rundesBild(x, bild, 72 + 62, y + 52, 62, farbe);
    if (!bild) {
      x.fillStyle = ink3;
      x.font = "700 42px 'Public Sans', sans-serif";
      x.textAlign = "center";
      x.fillText(initialen(anzeigeName(k)), 72 + 62, y + 68);
      x.textAlign = "left";
    }
    x.fillStyle = ink;
    x.font = "700 44px Archivo, sans-serif";
    x.fillText(kuerzText(x, anzeigeName(k), W - 300), 248, y + 44);
    x.fillStyle = ink3;
    x.font = "600 23px 'Public Sans', sans-serif";
    x.fillText(kuerzText(x, e.f, W - 300), 248, y + 78);
    y += 150;

    var dekl = pr.ib || [], hr = pr.hr || [];
    x.fillStyle = ink;
    x.font = "700 36px Archivo, sans-serif";
    x.fillText("Interessenbindungen", 72, y);
    x.fillStyle = ink3;
    x.font = "400 22px 'Public Sans', sans-serif";
    y = umbrechen(x, dekl.length + (dekl.length === 1 ? " deklariertes Mandat" :
      " deklarierte Mandate") + (hr.length ? ", " + hr.length + " nur im Handelsregister" : ""),
      72, y + 34, W - 144, 30, 2) + 18;

    if (!dekl.length && !hr.length) {
      x.fillStyle = ink3;
      x.font = "400 26px 'Public Sans', sans-serif";
      umbrechen(x, ohneProfil(k)
        ? "Zu dieser Person führt sh.ch keinen Personenkasten, darum liegt keine Deklaration vor."
        : "Keine Interessenbindungen deklariert.", 72, y + 20, W - 144, 34, 3);
      return y + 90;
    }

    /* Alle Einträge sollen aufs Bild. Peter Neukomm deklariert 16, eine feste
       Obergrenze hätte zehn davon stillschweigend verschluckt: ein Bild, das
       vollständig aussieht und es nicht ist, ist schlimmer als eines, das die
       Lücke benennt.

       Darum wird die Schriftgrösse an die Menge angepasst. Erst wird gemessen,
       wie hoch die Liste in einer Grösse würde; passt sie nicht, kommt die
       nächstkleinere. Reicht auch die kleinste nicht, wird abgeschnitten und
       die Zahl der übrigen ausdrücklich genannt. */
    var alle = dekl.map(function (s) { return { text: s, gelb: false }; })
      .concat(hr.map(function (s) {
        return { text: s.f + (s.o ? ", " + s.o : "") + (s.r ? " · " + s.r : ""),
                 gelb: true };
      }));
    var platz = H - 160 - y - 60;   /* 60 für die Fussnote reservieren */

    function zeilenZahl(text, groesse, bw) {
      x.font = "400 " + groesse + "px 'Public Sans', sans-serif";
      var w = String(text).split(/\s+/), zl = "", n = 1;
      for (var i = 0; i < w.length; i++) {
        var pr2 = zl ? zl + " " + w[i] : w[i];
        if (x.measureText(pr2).width > bw && zl) { n++; zl = w[i]; } else zl = pr2;
      }
      return n;
    }
    function hoeheFuer(g, liste) {
      var zh = Math.round(g * 1.32), h = 0;
      liste.forEach(function (e) {
        h += Math.round(g * 0.7) + zeilenZahl(e.text, g, W - 144 - 40) * zh + 10;
      });
      return h;
    }

    var groesse = 25, pass = null;
    [25, 23, 21, 19, 17, 15].forEach(function (g) {
      if (pass === null && hoeheFuer(g, alle) <= platz) pass = g;
    });
    var zeigen = alle, rest = 0;
    if (pass === null) {
      groesse = 15;
      /* So viele wie hineinpassen, der Rest wird gezählt und benannt. */
      var h = 0, i = 0;
      for (; i < alle.length; i++) {
        var hh = hoeheFuer(groesse, [alle[i]]);
        if (h + hh > platz - 40) break;
        h += hh;
      }
      zeigen = alle.slice(0, i);
      rest = alle.length - i;
    } else groesse = pass;

    var zh = Math.round(groesse * 1.32);
    zeigen.forEach(function (e) {
      var bx = 72, bw = W - 144;
      var n = zeilenZahl(e.text, groesse, bw - 40);
      var hoehe = Math.round(groesse * 0.7) + n * zh;
      x.fillStyle = e.gelb ? cssFarbe("--q-reg-flaeche") : cssFarbe("--q-dekl-flaeche");
      x.fillRect(bx, y, bw, hoehe);
      x.fillStyle = e.gelb ? cssFarbe("--q-reg") : cssFarbe("--q-dekl");
      x.fillRect(bx, y, 6, hoehe);
      x.fillStyle = ink;
      x.font = "400 " + groesse + "px 'Public Sans', sans-serif";
      umbrechen(x, e.text, bx + 22, y + Math.round(groesse * 1.15), bw - 40, zh, n);
      y += hoehe + 10;
    });

    if (rest) {
      x.fillStyle = ink3;
      x.font = "600 " + groesse + "px 'Public Sans', sans-serif";
      x.fillText("und " + rest + (rest === 1 ? " weitere Interessenbindung"
                                             : " weitere Interessenbindungen"), 72, y + 24);
      y += 44;
    }

    if (y + 70 < H - 160) {
      x.fillStyle = ink3;
      x.font = "400 20px 'Public Sans', sans-serif";
      y = umbrechen(x, hr.length
        ? "Blau: Selbstdeklaration auf sh.ch. Gelb: im Handelsregister eingetragen, in der Deklaration nicht gefunden."
        : "Quelle: Selbstdeklaration auf sh.ch.", 72, y + 24, W - 144, 28, 2);
    }
    return y;
  }

  /* Ergebnis des Matchings, entweder nach Fraktionen oder die stärksten
     Übereinstimmungen mit einzelnen Ratsmitgliedern. */
  function bildMatch(x, y, ink, ink2, ink3, line, art) {
    var erg = matchRechnen();
    if (!erg) {
      x.fillStyle = ink3;
      x.font = "400 28px 'Public Sans', sans-serif";
      umbrechen(x, "Noch kein Ergebnis. Zuerst im Reiter «Wer stimmt wie ich?» " +
        "genügend Fragen beantworten und auswerten.", 72, y + 20, W - 144, 38, 4);
      return y + 140;
    }
    var liste = art === "frak" ? erg.frak : erg.leute;
    y = kopfzeile(x, ink, ink3,
      art === "frak" ? "So nah stehe ich den Fraktionen" : "So nah stehe ich den Ratsmitgliedern",
      erg.beantwortet + " von " + erg.gesamt + " Fragen beantwortet", y);

    liste.slice(0, art === "frak" ? 6 : 10).forEach(function (e, i) {
      var farbe = cssFarbe("--p-" + (art === "frak" ? fkey(e.name) : pkey(e.partei)));
      x.fillStyle = ink3;
      x.font = "700 26px 'Public Sans', sans-serif";
      x.fillText(String(i + 1), 72, y + 30);
      x.fillStyle = ink;
      x.font = "600 30px 'Public Sans', sans-serif";
      x.fillText(kuerzText(x, e.name, 470), 118, y + 30);
      if (e.unter) {
        x.fillStyle = ink3;
        x.font = "400 21px 'Public Sans', sans-serif";
        x.fillText(kuerzText(x, e.unter, 400), 118, y + 60);
      }
      var bx = 620, bw = W - 72 - bx - 130;
      x.fillStyle = line; x.fillRect(bx, y + 12, bw, 22);
      x.fillStyle = farbe; x.fillRect(bx, y + 12, Math.max(bw * e.wert / 100, 3), 22);
      x.fillStyle = ink;
      x.font = "700 30px 'Public Sans', sans-serif";
      x.textAlign = "right";
      x.fillText(pz(e.wert, 0) + " %", W - 72, y + 34);
      x.textAlign = "left";
      y += art === "frak" ? 96 : 82;
    });

    /* Die Fussnote nur, wenn sie über dem Wasserzeichen Platz hat. Sonst
       überschreibt sie es, und das Bild sieht nach Fehler aus. */
    if (y + 70 < H - 160) {
      x.fillStyle = ink3;
      x.font = "400 20px 'Public Sans', sans-serif";
      umbrechen(x, "Übereinstimmung über die beantworteten Fragen. Bei Umkehrabstimmungen " +
        "ist die Richtung korrigiert, ein Ja bedeutet überall dasselbe.", 72, y + 24,
        W - 144, 28, 2);
    }
    return y + 90;
  }

  function umbrechen(x, text, links, oben, breite, zeilenhoehe, maxZeilen) {
    var worte = String(text).split(/\s+/), zeile = "", y = oben, n = 0;
    for (var i = 0; i < worte.length; i++) {
      var test = zeile ? zeile + " " + worte[i] : worte[i];
      if (x.measureText(test).width > breite && zeile) {
        x.fillText(zeile, links, y); y += zeilenhoehe; zeile = worte[i]; n++;
        if (maxZeilen && n >= maxZeilen) { zeile = ""; break; }
      } else zeile = test;
    }
    if (zeile) { x.fillText(zeile, links, y); y += zeilenhoehe; }
    return y;
  }
  function balkenZeichnen(x, links, oben, breite, hoehe, teile) {
    var ges = teile.reduce(function (a, t) { return a + t.wert; }, 0) || 1, cx = links;
    teile.forEach(function (t) {
      var w = t.wert / ges * breite;
      if (w <= 0) return;
      x.fillStyle = t.farbe;
      x.fillRect(cx, oben, Math.max(w - 3, 1), hoehe);
      if (w > 66) {
        x.fillStyle = t.text || "#fff";
        x.font = "700 24px 'Public Sans', sans-serif";
        x.textAlign = "center";
        x.fillText(String(t.wert), cx + w / 2 - 1, oben + hoehe / 2 + 9);
        x.textAlign = "left";
      }
      cx += w;
    });
  }

  function badge(x, text, links, oben, hg, fg) {
    x.font = "700 26px 'Public Sans', sans-serif";
    var b = x.measureText(text).width + 46;
    x.fillStyle = hg; x.fillRect(links, oben, b, 52);
    x.fillStyle = fg; x.fillText(text, links + 23, oben + 35);
    return b;
  }

  function bildVote(x, y, ink, ink2, ink3, line) {
    var s = D.sessions[0], i = 0, beste = 999;
    /* die knappste Abstimmung der neusten Sitzung ist die interessanteste */
    s.v.forEach(function (v, k) {
      var t = tally(s, k), d = Math.abs(t.J - t.N);
      if (t.J + t.N > 20 && d < beste) { beste = d; i = k; }
    });
    var v = s.v[i], e = ergebnis(s, i), t = e.t;

    x.fillStyle = ink3; x.font = "600 21px 'Public Sans', sans-serif";
    x.fillText(v.b ? kuerz(v.b, 54).toUpperCase() : "ABSTIMMUNG", 72, y);
    y += 52;
    x.fillStyle = ink; x.font = "700 52px Archivo, sans-serif";
    y = umbrechen(x, v.t, 72, y, W - 144, 64, 4) + 10;
    x.fillStyle = ink2; x.font = "400 24px 'Public Sans', sans-serif";
    y = umbrechen(x, s.n + " · " + s.dt, 72, y, W - 144, 34, 2) + 22;

    badge(x, e.text.toUpperCase(), 72, y,
          e.key === "ja" ? cssFarbe("--ja") : cssFarbe("--nein"),
          e.key === "ja" ? cssFarbe("--ja-on") : cssFarbe("--nein-on"));
    y += 100;

    balkenZeichnen(x, 72, y, W - 144, 78, [
      { wert: t.J, farbe: cssFarbe("--ja"), text: cssFarbe("--ja-on") },
      { wert: t.N, farbe: cssFarbe("--nein"), text: cssFarbe("--nein-on") },
      { wert: t.E, farbe: cssFarbe("--enth"), text: cssFarbe("--enth-on") },
      { wert: t.A, farbe: cssFarbe("--abw"), text: cssFarbe("--abw-on") }
    ]);
    y += 116;
    x.font = "600 23px 'Public Sans', sans-serif";
    [["Ja", t.J, "--ja"], ["Nein", t.N, "--nein"],
     ["Enthaltung", t.E, "--enth"], ["abwesend", t.A, "--abw"]].forEach(function (p, k) {
      var px = 72 + (k % 2) * 470, py = y + Math.floor(k / 2) * 44;
      x.fillStyle = cssFarbe(p[2]); x.beginPath(); x.arc(px + 9, py - 8, 9, 0, 7); x.fill();
      x.fillStyle = ink2; x.fillText(p[1] + "  " + p[0], px + 30, py);
    });
    y += 106;

    /* Fraktionsaufteilung füllt die Mitte und macht das Bild erst aussagekräftig */
    x.strokeStyle = line; x.lineWidth = 1;
    x.beginPath(); x.moveTo(72, y - 36); x.lineTo(W - 72, y - 36); x.stroke();
    x.fillStyle = ink3; x.font = "700 21px 'Public Sans', sans-serif";
    x.fillText("SO HABEN DIE FRAKTIONEN GESTIMMT", 72, y);
    y += 46;
    var proFrak = {};
    s.m.forEach(function (m) {
      proFrak[m.f] = proFrak[m.f] || { J: 0, N: 0, E: 0, A: 0 };
      proFrak[m.f][roh(m, i)]++;
    });
    Object.keys(proFrak).sort(function (a, b) {
      var A = proFrak[a], B = proFrak[b];
      return (B.J + B.N + B.E + B.A) - (A.J + A.N + A.E + A.A);
    }).forEach(function (f) {
      var q = proFrak[f];
      x.fillStyle = cssFarbe("--p-" + fkey(f));
      x.fillRect(72, y - 17, 8, 24);
      x.fillStyle = ink; x.font = "600 24px 'Public Sans', sans-serif";
      x.fillText(kuerz(f, 30), 96, y);
      balkenZeichnen(x, 520, y - 20, 400, 28, [
        { wert: q.J, farbe: cssFarbe("--ja"), text: cssFarbe("--ja-on") },
        { wert: q.N, farbe: cssFarbe("--nein"), text: cssFarbe("--nein-on") },
        { wert: q.E, farbe: cssFarbe("--enth"), text: cssFarbe("--enth-on") },
        { wert: q.A, farbe: cssFarbe("--abw"), text: cssFarbe("--abw-on") }
      ]);
      x.fillStyle = ink2; x.font = "600 22px 'Public Sans', sans-serif";
      x.textAlign = "right"; x.fillText(q.J + " : " + q.N, W - 72, y); x.textAlign = "left";
      y += 52;
    });
    return y;
  }

  function bildSitzung(x, y, ink, ink2, ink3, line) {
    var s = D.sessions[0];
    var ges = 0, ab = 0, ohne = 0;
    s.v.forEach(function (v, i) {
      var t = tally(s, i);
      ges += t.J + t.N + t.E + t.A; ab += t.J + t.N + t.E;
      if (t.N === 0 && t.E === 0) ohne++;
    });
    x.fillStyle = ink3; x.font = "600 21px 'Public Sans', sans-serif";
    x.fillText("SITZUNG VOM " + s.dt.toUpperCase(), 72, y); y += 54;
    x.fillStyle = ink; x.font = "700 54px Archivo, sans-serif";
    y = umbrechen(x, s.n, 72, y, W - 144, 66, 2) + 48;

    var kz = [[String(s.v.length), "namentliche Abstimmungen"],
              [String(s.m.length), "Ratsmitglieder"],
              [pz(ges ? ab / ges * 100 : 0) + " %", "Präsenz"],
              [String(ohne), "ohne Gegenstimme"]];
    kz.forEach(function (k, i) {
      var px = 72 + (i % 2) * 470, py = y + Math.floor(i / 2) * 176;
      x.fillStyle = ink; x.font = "600 82px Archivo, sans-serif";
      x.fillText(k[0], px, py + 66);
      x.fillStyle = ink2; x.font = "400 24px 'Public Sans', sans-serif";
      x.fillText(k[1], px, py + 108);
    });
    y += 372;

    x.strokeStyle = line; x.lineWidth = 1;
    x.beginPath(); x.moveTo(72, y - 40); x.lineTo(W - 72, y - 40); x.stroke();
    x.fillStyle = ink3; x.font = "700 21px 'Public Sans', sans-serif";
    x.fillText("DIE KNAPPSTEN ENTSCHEIDE", 72, y); y += 52;
    var knapp = s.v.map(function (v, i) {
      var t = tally(s, i);
      return { v: v, i: i, t: t, d: Math.abs(t.J - t.N) };
    }).filter(function (o) { return o.t.J + o.t.N > 20; })
      .sort(function (a, b) { return a.d - b.d; }).slice(0, 3);
    knapp.forEach(function (o) {
      x.fillStyle = ink; x.font = "600 29px 'Public Sans', sans-serif";
      y = umbrechen(x, kuerz(o.v.t, 76), 72, y, W - 260, 38, 2);
      x.fillStyle = cssFarbe("--ja"); x.beginPath(); x.arc(80, y - 5, 7, 0, 7); x.fill();
      x.fillStyle = ink3; x.font = "400 22px 'Public Sans', sans-serif";
      x.fillText(o.t.J + " Ja  zu  " + o.t.N + " Nein", 98, y + 2);
      y += 62;
    });
    return y;
  }

  function bildFrak(x, y, ink, ink2, ink3, line) {
    var fs = frakStats();
    x.fillStyle = ink3; x.font = "600 20px 'Public Sans', sans-serif";
    x.fillText(scopeLabel().toUpperCase(), 72, y); y += 48;
    x.fillStyle = ink; x.font = "700 48px Archivo, sans-serif";
    y = umbrechen(x, "Wie geschlossen stimmen die Fraktionen?", 72, y, W - 144, 60, 3) + 34;
    fs.forEach(function (f) {
      x.fillStyle = cssFarbe("--p-" + fkey(f.f));
      x.fillRect(72, y - 22, 10, 30);
      x.fillStyle = ink; x.font = "700 27px 'Public Sans', sans-serif";
      x.fillText(kuerz(f.f, 34), 100, y);
      x.fillStyle = ink3; x.font = "400 21px 'Public Sans', sans-serif";
      x.fillText(f.sitze + " Sitze", 100, y + 30);
      y += 56;
      [["Zustimmung", f.quote, "--ja"], ["Geschlossenheit", f.disziplin, "--p-" + fkey(f.f)],
       ["Präsenz", f.praesenz, "--ink-3"]].forEach(function (p) {
        x.fillStyle = ink2; x.font = "400 21px 'Public Sans', sans-serif";
        x.fillText(p[0], 100, y + 6);
        x.fillStyle = cssFarbe("--sunken"); x.fillRect(330, y - 10, 480, 14);
        x.fillStyle = cssFarbe(p[2]);
        x.fillRect(330, y - 10, Math.max(0, Math.min(100, p[1])) / 100 * 480, 14);
        x.fillStyle = ink; x.font = "700 21px 'Public Sans', sans-serif";
        x.textAlign = "right"; x.fillText(pz(p[1], 0) + " %", W - 72, y + 6); x.textAlign = "left";
        y += 32;
      });
      y += 28;
    });
    return y;
  }

  function bildRang(x, y, ink, ink2, ink3, line) {
    var mem = mitgliedStats().filter(function (m) { return m.total > 0; })
      .sort(function (a, b) { return b.quote - a.quote; }).slice(0, 8);
    x.fillStyle = ink3; x.font = "600 20px 'Public Sans', sans-serif";
    x.fillText(scopeLabel().toUpperCase(), 72, y); y += 48;
    x.fillStyle = ink; x.font = "700 48px Archivo, sans-serif";
    y = umbrechen(x, "Höchste Zustimmungsquote", 72, y, W - 144, 60, 2) + 12;
    x.fillStyle = ink2; x.font = "400 22px 'Public Sans', sans-serif";
    y = umbrechen(x, "Anteil Ja an den abgegebenen Stimmen, richtungskorrigiert.",
                  72, y, W - 144, 32, 2) + 34;
    mem.forEach(function (m, i) {
      x.fillStyle = ink3; x.font = "600 24px Archivo, sans-serif";
      x.fillText(String(i + 1), 72, y + 6);
      x.fillStyle = cssFarbe("--p-" + pkey(m.p));
      x.beginPath(); x.arc(126, y - 2, 9, 0, 7); x.fill();
      x.fillStyle = ink; x.font = "600 26px 'Public Sans', sans-serif";
      x.fillText(kuerz(m.name, 26), 150, y + 6);
      x.fillStyle = ink3; x.font = "400 19px 'Public Sans', sans-serif";
      x.fillText(kuerz(m.f, 30), 150, y + 34);
      x.fillStyle = cssFarbe("--sunken"); x.fillRect(620, y - 10, 300, 16);
      x.fillStyle = cssFarbe("--ja"); x.fillRect(620, y - 10, m.quote / 100 * 300, 16);
      x.fillStyle = ink; x.font = "700 24px Archivo, sans-serif";
      x.textAlign = "right"; x.fillText(pz(m.quote, 0) + " %", W - 72, y + 6); x.textAlign = "left";
      y += 76;
    });
    return y;
  }

  function bildModal(offen) {
    var m = $("#bildModal");
    m.hidden = !offen;
    if (offen) {
      bildMotivListe();
      zeichneBild($("#bildMotiv").value);
    }
  }

  function bildMotivListe() {
    var sel = $("#bildMotiv"), gruppen = [], nach = {};
    MOTIVE.filter(motivMoeglich).forEach(function (m) {
      if (!nach[m.g]) { nach[m.g] = []; gruppen.push(m.g); }
      nach[m.g].push(m);
    });
    var vorher = sel.value;
    sel.innerHTML = gruppen.map(function (g) {
      return '<optgroup label="' + esc(g) + '">' + nach[g].map(function (m) {
        return '<option value="' + m.k + '">' + esc(m.l) + "</option>";
      }).join("") + "</optgroup>";
    }).join("");
    if (vorher && sel.querySelector('option[value="' + vorher + '"]')) sel.value = vorher;
    subjektFeld();
  }

  /* Das zweite Auswahlfeld erscheint nur für Motive, die eine Person brauchen.
     Vorbelegt ist, wer gerade im Dashboard offen ist, sonst der erste Name. */
  function subjektFeld() {
    var sel = $("#bildMotiv"), wrap = $("#bildSubjektWrap"), sub = $("#bildSubjekt");
    var m = motivVon(sel.value);
    wrap.hidden = m.subjekt !== "mitglied";
    if (wrap.hidden) return;
    var leute = mitgliedStats().sort(function (a, b) {
      return a.nach.localeCompare(b.nach, "de");
    });
    var vorher = sub.value || st.mitglied;
    sub.innerHTML = leute.map(function (e) {
      return '<option value="' + esc(e.k) + '">' + esc(e.name) +
        (e.f ? " · " + esc(e.f) : "") + "</option>";
    }).join("");
    if (vorher && sub.querySelector('option[value="' + vorher + '"]')) sub.value = vorher;
  }

  function initBild() {
    var sel = $("#bildMotiv");
    bildMotivListe();
    sel.addEventListener("change", function () {
      subjektFeld();
      zeichneBild(sel.value);
    });
    $("#bildSubjekt").addEventListener("change", function () { zeichneBild(sel.value); });
    $("#bildZu").addEventListener("click", function () { bildModal(false); });
    $("#bildModal").addEventListener("click", function (e) {
      if (e.target === $("#bildModal")) bildModal(false);
    });
    $("#bildLaden").addEventListener("click", function () {
      var c = $("#bildCanvas");
      var a = document.createElement("a");
      var teil = sel.value.replace(/:/g, "-");
      if (motivVon(sel.value).subjekt === "mitglied") {
        teil += "-" + bildSubjekt().replace(/\|/g, "-").toLowerCase();
      }
      a.download = "kantonsrat-sh-" + teil + ".png";
      a.href = c.toDataURL("image/png");
      a.click();
    });
    var start = document.createElement("button");
    start.type = "button";
    start.className = "bildstart";
    start.innerHTML = '<svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true">' +
      '<rect x="2" y="3" width="12" height="10" rx="2" stroke="currentColor" stroke-width="1.6" fill="none"/>' +
      '<circle cx="6" cy="7" r="1.4" fill="currentColor"/>' +
      '<path d="M3 12l3.5-3.5 2.5 2.5 2-2L13 12" stroke="currentColor" stroke-width="1.6" fill="none" stroke-linejoin="round"/></svg>' +
      "Bild für Social Media";
    start.addEventListener("click", function () { bildModal(true); });
    document.body.appendChild(start);
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !$("#bildModal").hidden) bildModal(false);
    });
  }

  /* ═══ Rubrik: Interessenbindungen ══════════════════════════════════════ */
  /* Der folgende Block stammt aus build2.py und ist inhaltlich unverändert
     übernommen. Angepasst wurden nur die Farben: sie kommen jetzt aus den
     CSS-Token, damit das Netz dem Hell- und Dunkelmodus folgt. */
  var netzBereit = false;

  /* Angaben aus dem Handelsregister zu einer Organisation.
     Quelle: Zefix, abgefragt über lindas.admin.ch. Die Zuordnung erfolgt über
     einen Namensabgleich, ist also eine Aufbereitung und keine amtliche
     Auskunft. Darum steht auf jeder Karte, wie sicher der Treffer ist. */
  var HREG = D.hreg || {};
  var HREG_INDEX = {};
  ["eindeutig", "moeglich", "nicht_gefunden"].forEach(function (stufe) {
    (HREG[stufe] || []).forEach(function (e) {
      HREG_INDEX[e.organisation] = { e: e, stufe: stufe };
    });
  });

  function registerBlock(label) {
    var x = HREG_INDEX[label];
    if (!x) return "";
    var stand = HREG.stand ? " · Stand " + esc(HREG.stand) : "";
    if (x.stufe === "nicht_gefunden") {
      return '<div class="hreg offen"><b>Handelsregister</b> kein Eintrag gefunden. ' +
        "Das ist kein Beleg dafür, dass es die Organisation nicht gibt: Schreibweise, " +
        "Umbenennung oder Löschung sind die häufigsten Gründe." +
        "<small>Zefix" + stand + "</small></div>";
    }
    var t = (x.e.treffer || [])[0];
    if (!t) return "";
    var uid = t.uid
      ? " · " + esc(t.uid.replace(/^CHE(\d{3})(\d{3})(\d{3})$/, "CHE-$1.$2.$3")) : "";
    var weitere = (x.e.treffer.length > 1)
      ? "<br><small>" + (x.e.treffer.length - 1) + " weitere mögliche Treffer</small>" : "";
    return '<div class="hreg ' + x.stufe + '"><b>Handelsregister</b> ' +
      (x.stufe === "eindeutig" ? "" : "möglicher Treffer: ") +
      esc(t.name) + (t.ort ? ", " + esc(t.ort) : "") + uid + weitere +
      amtlichBlock(x.e.amtlich) +
      "<small>Zefix" + stand + ", über Namensabgleich zugeordnet. Verbindlich ist " +
      "allein der Registereintrag selbst.</small></div>";
  }

  // Angaben aus dem amtlichen Register selbst, sofern der Zefix-Zugang lief.
  // Sie sind mehr wert als der Namensabgleich: der Status sagt, ob es die
  // Firma überhaupt noch gibt, und der Link führt zum Eintrag.
  function amtlichBlock(a) {
    if (!a) return "";
    var zeilen = [];
    // status kommt aus zefix.py schon auf Deutsch: aktiv, gelöscht, in Löschung
    if (a.status === "gelöscht" || a.status === "in Löschung" || a.geloescht_am) {
      zeilen.push('<span class="hwarn">Im Register ' +
        esc(a.status === "in Löschung" ? "in Löschung" : "gelöscht") +
        (a.geloescht_am ? ", " + esc(a.geloescht_am) : "") + "</span>");
    }
    if (a.rechtsform) zeilen.push(esc(a.rechtsform));
    if (a.sitz) zeilen.push("Sitz " + esc(a.sitz));
    if (a.frueher && a.frueher.length) {
      zeilen.push("früher " + a.frueher.map(esc).join(", "));
    }
    if (!zeilen.length && !a.url && !a.zweck) return "";
    return '<div class="hamt">' + zeilen.join(" · ") +
      (a.zweck ? '<div class="hzweck">' + esc(a.zweck) + "</div>" : "") +
      (a.url ? ' <a class="plink" href="' + esc(a.url) + '" target="_blank" rel="noopener" ' +
        'title="Amtlichen Registereintrag auf zefix.ch öffnen">Registereintrag' +
        '<svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true">' +
        '<path d="M6 3h7v7M13 3L6.5 9.5M11 9.5V13H3V5h3.5" stroke="currentColor" ' +
        'fill="none" stroke-width="1.4"/></svg></a>' : "") + "</div>";
  }

  function regKanten(N) {
    return (N.kanten || []).filter(function (k) { return k.q === "r"; }).length;
  }

  /* Vollständige Legende: was ein Punkt ist, was seine Grösse sagt und was die
     beiden Linienarten bedeuten. Die Zeile zum Handelsregister erscheint nur,
     wenn es dort etwas zu sehen gibt, sonst erklärt sie eine Unterscheidung,
     die im Bild gar nicht vorkommt. */
  function netzLegende(N) {
    var reg = regKanten(N);
    var regOrg = (N.knoten || []).filter(function (k) {
      return k.typ === "organisation" && k.q === "r";
    }).length;

    var punkte =
      '<span class="qleg"><i class="pkt pkt-m"></i>Ratsmitglied</span>' +
      '<span class="qleg"><i class="pkt pkt-o"></i>Organisation</span>' +
      '<span class="qleg"><i class="pkt pkt-b"></i>Branche</span>' +
      (regOrg ? '<span class="qleg"><i class="pkt pkt-r"></i>Organisation nur im ' +
        "Handelsregister (" + regOrg + ")</span>" : "");

    var linien =
      '<span class="qleg qleg-d"><i></i>deklariert auf sh.ch</span>' +
      (reg ? '<span class="qleg qleg-r"><i></i>nur im Handelsregister (' + reg + ")</span>"
           : "");

    return '<div class="qlegende">' +
      '<div class="qzeile"><b>Punkte</b>' + punkte + "</div>" +
      '<div class="qzeile"><b>Linien</b>' + linien + "</div>" +
      '<div class="qzeile"><b>Grösse</b><span class="qleg qlegnote">Je mehr Verbindungen ' +
      "ein Punkt hat, desto grösser ist er. Beschriftet werden die grösseren, die " +
      "Schwelle lässt sich unter «Darstellung feinjustieren» ändern.</span></div>" +
      '<div class="qzeile"><b>Suche</b><span class="qleg qlegnote">Ein Treffer bekommt ' +
      "einen farbigen Ring, seine Füllung bleibt. Ein angeklickter Punkt bekommt einen " +
      "dunklen Ring, und der Rest tritt zurück.</span></div>" +
      (reg ? '<p class="qlegnote qfuss">Gestrichelt und gelb heisst: die Bindung steht im ' +
        "Handelsregister des Kantons Schaffhausen, nicht in der Selbstdeklaration. Das muss " +
        "nichts bedeuten, die Deklarationspflicht deckt nicht jedes Mandat, und der " +
        "Registerstand kann nachhinken. Jeder solche Eintrag ist einzeln am Registerauszug " +
        "geprüft; verbindlich ist allein der beglaubigte Auszug.</p>" : "") +
      "</div>";
  }

  function renderNetz(el) {
    var N = D.netz || {knoten: [], kanten: []};
    if (!N.knoten.length) {
      el.innerHTML = '<header class="hero"><h1>Interessenbindungen</h1></header>' +
        '<p class="leer">Es liegen keine Netzdaten vor. ' +
        '<code>data/interessen_netz.json</code> fehlt.</p>';
      return;
    }
    var branchen = {};
    N.knoten.forEach(function (k) { if (k.typ === "organisation" && k.branche) branchen[k.branche] = 1; });
    var mit = N.knoten.filter(function (k) { return k.typ === "mitglied"; }).length;
    var org = N.knoten.filter(function (k) { return k.typ === "organisation"; }).length;

    el.innerHTML =
      '<header class="hero"><div class="eyebrow">Selbstdeklarationen</div>' +
      "<h1>Interessenbindungen</h1>" +
      '<p class="subline">Wer sitzt wo? Jeder Punkt ist ein Ratsmitglied, eine Organisation ' +
      "oder eine Branche, jede Linie ein Mandat. Blaue Linien stehen in der " +
      "Selbstdeklaration, gelb gestrichelte nur im Handelsregister. Organisationen, die mehrere " +
      "Ratsmitglieder nennen, rücken zwischen diese.</p></header>" +
      '<div class="hinweis"><b>Quelle:</b> die Selbstdeklarationen auf sh.ch' +
      (D.personen && D.personen.stand ? ", Stand " + esc(D.personen.stand) : "") +
      (regKanten(N) ? ", ergänzt um Einträge aus dem Handelsregister des Kantons " +
        "Schaffhausen, die in keiner Deklaration stehen und einzeln am Registerauszug " +
        "geprüft sind" : "") +
      ". Keine eigenen Zuschreibungen, keine Bewertung. " + mit + " Ratsmitglieder, " + org +
      " Organisationen, " + (N.kanten || []).length + " Mandate.</div>" +
      netzLegende(N) +
      '<div class="netzleiste">' +
      '<select id="netzBranche"><option value="">Alle Branchen</option>' +
      Object.keys(branchen).sort().map(function (b) {
        return '<option value="' + esc(b) + '">' + esc(b) + "</option>";
      }).join("") + "</select>" +
      '<input type="text" id="netzSuche" placeholder="Person oder Organisation suchen…" autocomplete="off">' +
      '<label class="ftoggle" id="netzGeteiltWrap" style="padding:8px 12px">' +
      '<input type="checkbox" id="netzGeteilt"><span>Nur geteilte Organisationen</span></label>' +
      '<button type="button" class="tchip" id="netzReset">zurücksetzen</button>' +
      '<span class="netzzoom"><button type="button" id="zoomAus" title="kleiner">−</button>' +
      '<button type="button" id="zoomWert" title="auf 100 % zurücksetzen">100 %</button>' +
      '<button type="button" id="zoomEin" title="grösser">+</button></span></div>' +
      '<details class="fold netzregler"><summary><span class="caret"></span>Darstellung feinjustieren</summary>' +
      '<div class="foldbody"><div class="reglergrid">' +
      regler("rKnoten", "Knotengrösse", 4, 26, 1) +
      regler("rLaenge", "Verbindungslänge", 30, 240, 5) +
      regler("rZug", "Anziehung", 2, 60, 1) +
      regler("rAbstoss", "Abstossung", 200, 4000, 50) +
      regler("rBeschriftung", "Beschriftung", 0, 12, 1) +
      regler("rCluster", "Clusterstärke", 1, 8, 0.5) +
      regler("rTiefe", "Pfadtiefe", 1, 4, 1) +
      regler("rMandate", "Mandate je Person", 0, 10, 1) +
      '</div><button type="button" class="tchip" id="netzNeu">neu anordnen</button>' +
      "</div></details>" +
      '<div class="netzwrap"><canvas id="netz"></canvas><div class="netzinfo" id="netzInfo"></div></div>' +
      '<div class="netzlegende" id="netzLegende"></div>' + fussHtml(null);

    netzBereit = false;
    initNetz();
    netzBereit = true;

    function regler(id, label, min, max, step) {
      return '<label>' + label + '<input type="range" id="' + id + '" min="' + min +
        '" max="' + max + '" step="' + step + '"><output id="' + id + 'Wert"></output></label>';
    }
  }

/* ===== Netz der Interessenbindungen =====
   Kraftgerichtetes Layout auf Canvas, ohne Fremdbibliothek. Knoten stossen
   sich ab, Kanten ziehen zusammen, Organisationen hängen zusätzlich an ihrer
   Branche, dadurch bilden sich die Cluster. Alle Kräfte sind über Regler
   einstellbar, dazu Zoom, Verschieben und Ziehen einzelner Knoten: ohne das
   wird ein Netz mit zweihundert Knoten schnell unleserlich. */
function netzFarben(){ return {mitglied: cssFarbe("--p-al"), organisation: cssFarbe("--p-fdp"),
                              branche: cssFarbe("--ink-3"), treffer: cssFarbe("--p-evp")}; }
let netzKnoten=[], netzKanten=[], netzGewaehlt=null, netzGeteiltMenge=new Set();
let netzFilterBranche="", netzFilterText="", netzNurGeteilt=false;

/* Stellschrauben, von den Reglern gesetzt */
const NP = {knoten:10, laenge:70, zug:12, abstoss:900, beschriftung:4,
            cluster:3, tiefe:2, minMandate:0};
/* Ansicht */
let netzZoom=1, netzOffX=0, netzOffY=0;
/* Bewegung: alpha kühlt ab, bei Änderungen wird neu aufgeheizt */
let netzAlpha=0, netzLaeuft=false, netzZieht=null;

function netzHeizen(a=1){ netzAlpha=Math.max(netzAlpha,a); netzSchleife(); }

function netzSchleife(){
  if(netzLaeuft) return;
  netzLaeuft=true;
  const takt=()=>{
    if(netzAlpha>0.005 || netzZieht){
      netzSchritt();
      netzAlpha*=0.985;
      netzMalen();
      requestAnimationFrame(takt);
    } else {
      netzLaeuft=false;
      netzMalen();
    }
  };
  requestAnimationFrame(takt);
}

function netzAufbauen(behalten=true){
  const canvas=document.getElementById("netz");
  if(!canvas || !(D.netz.knoten||[]).length) return;
  const proOrg={};
  (D.netz.kanten||[]).filter(k=>k.art!=="branche").forEach(k=>{
    (proOrg[k.nach]=proOrg[k.nach]||new Set()).add(k.von);
  });
  netzGeteiltMenge=new Set(Object.entries(proOrg).filter(([,ms])=>ms.size>1).map(([oid])=>oid));

  const passtOrg=o=>{
    if(netzFilterBranche && o.branche!==netzFilterBranche) return false;
    if(netzNurGeteilt && !netzGeteiltMenge.has(o.id)) return false;
    return true;
  };
  // Personen nach Anzahl ihrer Mandate filtern. Danach bleiben nur die
  // Organisationen übrig, an denen noch mindestens eine sichtbare Person hängt,
  // sonst stünden lauter Organisationen ohne Anschluss im Bild.
  const passtMit=m=>(m.anzahl||0) >= NP.minMandate;
  const kandidatMit=new Set((D.netz.knoten||[]).filter(k=>k.typ==="mitglied"&&passtMit(k)).map(k=>k.id));
  const kandidatOrg=new Set((D.netz.knoten||[]).filter(k=>k.typ==="organisation"&&passtOrg(k)).map(k=>k.id));

  const sichtbarOrg=new Set(), sichtbarMit=new Set();
  (D.netz.kanten||[]).filter(k=>k.art!=="branche").forEach(k=>{
    if(kandidatOrg.has(k.nach) && kandidatMit.has(k.von)){
      sichtbarOrg.add(k.nach); sichtbarMit.add(k.von);
    }
  });
  const branchenVon={}; (D.netz.knoten||[]).forEach(k=>{ if(k.typ==="organisation") branchenVon[k.id]="b:"+k.branche; });
  const sichtbarBra=new Set([...sichtbarOrg].map(id=>branchenVon[id]));

  const alt={}; if(behalten) netzKnoten.forEach(n=>alt[n.id]=n);
  netzKnoten=(D.netz.knoten||[]).filter(k=>
      (k.typ==="organisation"&&sichtbarOrg.has(k.id)) ||
      (k.typ==="mitglied"&&sichtbarMit.has(k.id)) ||
      (k.typ==="branche"&&sichtbarBra.has(k.id)))
    .map(k=>{
      const v=alt[k.id];
      return {...k, x:v?v.x:(Math.random()*600-300), y:v?v.y:(Math.random()*400-200), vx:0, vy:0};
    });
  const id2=Object.fromEntries(netzKnoten.map(n=>[n.id,n]));
  netzKanten=(D.netz.kanten||[]).filter(k=>id2[k.von]&&id2[k.nach])
    .map(k=>({...k, a:id2[k.von], b:id2[k.nach]}));
  netzTreffer();
  netzInfoLeer();
  netzHeizen(1);
}

function netzRadius(n){
  const grund = n.typ==="branche" ? 1.4 : (n.typ==="mitglied" ? 1 : 0.75);
  return (NP.knoten*0.55)*grund + Math.min(n.anzahl,8)*(NP.knoten*0.055) + 2;
}

function netzTreffer(){
  const q=netzFilterText.trim().toLowerCase();
  netzKnoten.forEach(n=>{ n.treffer = q ? n.label.toLowerCase().includes(q) : false; });
}

function netzSchritt(){
  const N=netzKnoten.length; if(!N) return;
  const alpha=Math.max(netzAlpha,0.08);
  for(let i=0;i<N;i++){
    const a=netzKnoten[i];
    for(let j=i+1;j<N;j++){
      const b=netzKnoten[j];
      let dx=b.x-a.x, dy=b.y-a.y, d2=dx*dx+dy*dy;
      if(d2<1){ dx=Math.random()-0.5; dy=Math.random()-0.5; d2=1; }
      if(d2>250000) continue;
      // Branchen stossen sich untereinander viel stärker ab, damit die Cluster
      // auseinanderrücken statt sich zu überlagern
      const beide = a.typ==="branche" && b.typ==="branche";
      const staerke = NP.abstoss * (beide ? NP.cluster*NP.cluster : 1);
      const kraft=staerke/d2, d=Math.sqrt(d2);
      const fx=kraft*dx/d, fy=kraft*dy/d;
      a.vx-=fx; a.vy-=fy; b.vx+=fx; b.vy+=fy;
    }
  }
  netzKanten.forEach(k=>{
    // Kanten zur Branche sind kürzer und ziehen stärker: das hält eine Branche
    // mit ihren Organisationen zusammen
    const zurBranche = k.art==="branche";
    const soll = zurBranche ? NP.laenge*0.45 : NP.laenge;
    const dx=k.b.x-k.a.x, dy=k.b.y-k.a.y, d=Math.hypot(dx,dy)||1;
    const kraft=(d-soll)*(NP.zug/1000)*(zurBranche ? NP.cluster : 1);
    const fx=kraft*dx/d, fy=kraft*dy/d;
    k.a.vx+=fx; k.a.vy+=fy; k.b.vx-=fx; k.b.vy-=fy;
  });
  netzKnoten.forEach(n=>{
    if(netzZieht && netzZieht.knoten===n){ n.vx=0; n.vy=0; return; }
    n.vx-=n.x*0.0018; n.vy-=n.y*0.0018;
    n.vx*=0.86; n.vy*=0.86;
    n.x+=n.vx*alpha*2; n.y+=n.vy*alpha*2;
  });
}

/* Bildschirm- und Weltkoordinaten */
function netzMasse(){
  const c=document.getElementById("netz");
  const b=c.getBoundingClientRect();
  return {c,b};
}
function zuWelt(sx,sy){
  const {b}=netzMasse();
  return {x:(sx-b.width/2-netzOffX)/netzZoom, y:(sy-b.height/2-netzOffY)/netzZoom};
}

function netzMalen(){
  const c=document.getElementById("netz"); if(!c) return;
  const g=c.getContext && c.getContext("2d");
  if(!g) return;                      // Umgebungen ohne Canvas (z. B. Tests)
  const dpr=window.devicePixelRatio||1;
  const b=c.getBoundingClientRect();
  if(c.width!==Math.round(b.width*dpr)||c.height!==Math.round(b.height*dpr)){
    c.width=Math.round(b.width*dpr); c.height=Math.round(b.height*dpr);
  }
  g.setTransform(dpr,0,0,dpr,0,0);
  g.clearRect(0,0,b.width,b.height);
  g.save();
  g.translate(b.width/2+netzOffX, b.height/2+netzOffY);
  g.scale(netzZoom, netzZoom);

  const q=netzFilterText.trim().length>0;
  const hervor = netzGewaehlt ? pfadVon(netzGewaehlt, NP.tiefe) : null;

  netzKanten.forEach(k=>{
    const an = !hervor || (hervor.has(k.von)&&hervor.has(k.nach));
    // Herkunft der Bindung: blau deklariert, gelb nur im Handelsregister.
    // Die Farbe liegt bewusst auf der Kante und nicht auf dem Mitgliederknoten,
    // der die Parteifarbe trägt; FDP-Blau und EVP-Gelb liegen zu nah daran.
    if(k.art==="branche"){
      g.strokeStyle = an?cssFarbe("--line"):cssFarbe("--hair");
      g.lineWidth = 0.7/Math.max(netzZoom,0.6);
      g.setLineDash([]);
    } else if(k.q==="r"){
      g.strokeStyle = an?cssFarbe("--q-reg"):cssFarbe("--line");
      g.lineWidth = 1.6/Math.max(netzZoom,0.6);
      // Gestrichelt, damit die Unterscheidung nicht allein an der Farbe hängt
      g.setLineDash([4/Math.max(netzZoom,0.6), 3/Math.max(netzZoom,0.6)]);
    } else {
      g.strokeStyle = an?cssFarbe("--q-dekl"):cssFarbe("--line");
      g.lineWidth = 1/Math.max(netzZoom,0.6);
      g.setLineDash([]);
    }
    g.beginPath(); g.moveTo(k.a.x,k.a.y); g.lineTo(k.b.x,k.b.y); g.stroke();
  });
  g.setLineDash([]);
  netzKnoten.forEach(n=>{
    const an = !hervor || hervor.has(n.id);
    const treffer = q && n.treffer;
    const r=netzRadius(n);
    g.globalAlpha = an ? 1 : 0.16;
    // Die Füllung sagt, was der Knoten ist. Gelb ist Organisationen
    // vorbehalten, die nur im Handelsregister stehen; ein Suchtreffer bekommt
    // darum keine eigene Füllung mehr, sondern einen Ring. Sonst sähen ein
    // gesuchter Verein und ein Registerfund gleich aus.
    g.fillStyle = (n.typ==="organisation" && n.q==="r") ? cssFarbe("--q-reg")
                : netzFarben()[n.typ];
    g.beginPath(); g.arc(n.x,n.y,r,0,Math.PI*2); g.fill();
    if(n.typ==="organisation" && n.q==="r"){
      // Ring auch hier, damit die Unterscheidung nicht allein an der Farbe hängt
      g.strokeStyle=cssFarbe("--q-reg-ink"); g.lineWidth=1.6/netzZoom;
      g.beginPath(); g.arc(n.x,n.y,r+2.5/netzZoom,0,Math.PI*2); g.stroke();
    }
    if(treffer){
      g.strokeStyle=cssFarbe("--focus"); g.lineWidth=2.6/netzZoom;
      g.beginPath(); g.arc(n.x,n.y,r+4/netzZoom,0,Math.PI*2); g.stroke();
    }
    if(netzGewaehlt && n.id===netzGewaehlt.id){
      g.strokeStyle=cssFarbe("--ink"); g.lineWidth=2/netzZoom; g.stroke();
    }
    // Regler auf 0 heisst: alle beschriften
    const zeigen = n.typ==="branche" || treffer || (hervor&&hervor.has(n.id)) ||
                   NP.beschriftung===0 || n.anzahl>=NP.beschriftung;
    if(zeigen){
      g.globalAlpha = an ? 1 : 0.25;
      g.fillStyle=cssFarbe("--ink");
      const gr = (n.typ==="branche" ? 12 : 11)/Math.max(netzZoom,0.75);
      g.font = n.typ==="branche" ? `600 ${gr}px Georgia, serif` : `${gr}px sans-serif`;
      g.textAlign="center";
      g.fillText(n.label.slice(0,38), n.x, n.y - r - 4/netzZoom);
    }
  });
  g.globalAlpha=1;
  g.restore();
}

/* Alle Knoten, die vom gewählten aus in höchstens `tiefe` Schritten erreichbar
   sind. Ein Klick auf ein Ratsmitglied zeigt damit nicht nur seine Mandate,
   sondern auch deren Branchen und die übrigen Mitglieder derselben
   Organisation; von einer Branche aus geht es entsprechend abwärts. */
function pfadVon(start, tiefe){
  const nachbarn={};
  netzKanten.forEach(k=>{
    (nachbarn[k.von]=nachbarn[k.von]||[]).push(k.nach);
    (nachbarn[k.nach]=nachbarn[k.nach]||[]).push(k.von);
  });
  const gesehen=new Set([start.id]);
  let rand=[start.id];
  for(let i=0;i<Math.max(1,tiefe);i++){
    const naechste=[];
    rand.forEach(id=>(nachbarn[id]||[]).forEach(n=>{
      if(!gesehen.has(n)){ gesehen.add(n); naechste.push(n); }
    }));
    rand=naechste;
    if(!rand.length) break;
  }
  return gesehen;
}

function netzInfoLeer(){
  const box=document.getElementById("netzInfo"); if(!box) return;
  const m=netzKnoten.filter(n=>n.typ==="mitglied").length;
  const o=netzKnoten.filter(n=>n.typ==="organisation").length;
  box.innerHTML=`<div class="ni-typ">Übersicht</div>
    <h4>${o} Organisationen</h4>
    <p><small>${m} Ratsmitglieder, ${netzKanten.filter(k=>k.art!=="branche").length} Mandate.
    ${netzGeteiltMenge.size} Organisationen werden von mehr als einem Ratsmitglied genannt.</small></p>
    ${NP.minMandate>0?`<p><small>Gezeigt werden nur Ratsmitglieder mit mindestens
      ${NP.minMandate} Interessenbindungen.</small></p>`:""}
    <p style="margin-top:9px"><small>Punkt anklicken zeigt die Verbindungen, Punkt ziehen ordnet um,
    Mausrad zoomt, Ziehen im leeren Bereich verschiebt.</small></p>`;
}

function netzInfoZeigen(n){
  const box=document.getElementById("netzInfo"); if(!box) return;
  const eigene=netzKanten.filter(k=>k.von===n.id||k.nach===n.id);
  const zeilen=eigene.filter(k=>k.art!=="branche").map(k=>{
    const anderer = k.von===n.id ? k.b : k.a;
    const rolle = k.rolle ? ` <small>${esc(k.rolle)}</small>` : "";
    return `<li>${esc(anderer.label)}${rolle}</li>`;
  }).join("");
  const typ={mitglied:"Ratsmitglied", organisation:"Organisation", branche:"Branche"}[n.typ];
  const zusatz = n.typ==="mitglied" ? `<p><small>${esc(n.partei||"")}${n.fraktion?" · "+esc(n.fraktion):""}</small></p>`
               : n.typ==="organisation" ? `<p><small>${esc(n.branche||"")}${n.ort?" · "+esc(n.ort):""}</small></p>` : "";
  const pfad=pfadVon(n, NP.tiefe);
  const nach={}; netzKnoten.forEach(k=>nach[k.id]=k);
  const zaehlung=[...pfad].filter(id=>id!==n.id).map(id=>nach[id]).filter(Boolean);
  const stat=["mitglied","organisation","branche"].map(tp=>{
    const c=zaehlung.filter(k=>k.typ===tp).length;
    return c ? `${c} ${({mitglied:"Ratsmitglieder", organisation:"Organisationen", branche:"Branchen"})[tp]}` : null;
  }).filter(Boolean).join(", ");
  const hreg = n.typ==="organisation" ? registerBlock(n.label) : "";
  box.innerHTML=`<div class="ni-typ">${typ}</div><h4>${esc(n.label)}</h4>${zusatz}
    ${zeilen?`<ul>${zeilen}</ul>`:"<p><small>Keine Mandate erfasst.</small></p>"}
    ${stat?`<p style="margin-top:9px"><small>Im Pfad über ${NP.tiefe} Schritte: ${stat}.</small></p>`:""}
    ${hreg}`;
}

function knotenBei(sx,sy){
  const w=zuWelt(sx,sy);
  let beste=null, dist=1e9;
  netzKnoten.forEach(n=>{
    const d=Math.hypot(n.x-w.x,n.y-w.y);
    const grenze=Math.max(netzRadius(n)+6, 12/netzZoom);
    if(d<grenze && d<dist){ dist=d; beste=n; }
  });
  return beste;
}

function zoomSetzen(faktor, sx, sy){
  const {b}=netzMasse();
  const mx = sx!==undefined ? sx : b.width/2;
  const my = sy!==undefined ? sy : b.height/2;
  const vor=zuWelt(mx,my);
  netzZoom=Math.min(4, Math.max(0.25, netzZoom*faktor));
  const nach=zuWelt(mx,my);
  netzOffX += (nach.x-vor.x)*netzZoom;
  netzOffY += (nach.y-vor.y)*netzZoom;
  const a=document.getElementById("zoomWert");
  if(a) a.textContent=Math.round(netzZoom*100)+" %";
  netzMalen();
}

function initNetz(){
  const c=document.getElementById("netz"); if(!c) return;

  const sel=document.getElementById("netzBranche");
  [...new Set((D.netz.knoten||[]).filter(k=>k.typ==="branche").map(k=>k.label))].sort()
    .forEach(b=>{ const o=document.createElement("option"); o.value=b; o.textContent=b; sel.appendChild(o); });
  sel.onchange=()=>{ netzFilterBranche=sel.value; netzGewaehlt=null; netzAufbauen(); };

  const feld=document.getElementById("netzSuche");
  let t=null;
  feld.oninput=()=>{ clearTimeout(t); t=setTimeout(()=>{ netzFilterText=feld.value; netzTreffer(); netzMalen(); },180); };

  const gt=document.getElementById("netzGeteilt");
  gt.onchange=()=>{ netzNurGeteilt=gt.checked;
    document.getElementById("netzGeteiltWrap").classList.toggle("an", gt.checked);
    netzGewaehlt=null; netzAufbauen(); };

  document.getElementById("netzReset").onclick=()=>{
    netzFilterBranche=""; netzFilterText=""; netzNurGeteilt=false; netzGewaehlt=null;
    NP.minMandate=0;
    const rmm=document.getElementById("rMandate");
    if(rmm){ rmm.value=0; const w=document.getElementById("rMandateWert"); if(w) w.textContent="alle"; }
    sel.value=""; feld.value=""; gt.checked=false;
    document.getElementById("netzGeteiltWrap").classList.remove("an");
    netzZoom=1; netzOffX=0; netzOffY=0; zoomSetzen(1);
    netzAufbauen(false);
  };

  /* Regler */
  const rm=document.getElementById("rMandate");
  if(rm){
    const maxMandate=Math.max(...(D.netz.knoten||[]).filter(k=>k.typ==="mitglied").map(k=>k.anzahl||0), 1);
    rm.max=maxMandate;
  }
  const regler=[
    ["rKnoten","knoten", v=>v+" px"],
    ["rLaenge","laenge", v=>v+" px"],
    ["rZug","zug", v=>v],
    ["rAbstoss","abstoss", v=>v],
    ["rBeschriftung","beschriftung", v=>v==0?"alle":"ab "+v+" Verb."],
    ["rCluster","cluster", v=>v+"x"],
    ["rTiefe","tiefe", v=>v+" Schritte"],
    ["rMandate","minMandate", v=>v==0?"alle":"ab "+v],
  ];
  regler.forEach(([id,feldname,fmt])=>{
    const el=document.getElementById(id); if(!el) return;
    el.value=NP[feldname];
    const aus=document.getElementById(id+"Wert");
    const zeigen=()=>{ if(aus) aus.textContent=fmt(el.value); };
    zeigen();
    el.oninput=()=>{
      NP[feldname]=+el.value; zeigen();
      if(feldname==="knoten"||feldname==="beschriftung"){ netzMalen(); }
      else if(feldname==="tiefe"){
        if(netzGewaehlt) netzInfoZeigen(netzGewaehlt);
        netzMalen();
      } else if(feldname==="minMandate"){
        netzGewaehlt=null; netzAufbauen();
      } else { netzHeizen(0.6); }
    };
  });
  const neu=document.getElementById("netzNeu");
  if(neu) neu.onclick=()=>netzAufbauen(false);

  /* Zoom */
  document.getElementById("zoomEin").onclick=()=>zoomSetzen(1.25);
  document.getElementById("zoomAus").onclick=()=>zoomSetzen(0.8);
  document.getElementById("zoomWert").onclick=()=>{ netzZoom=1; netzOffX=0; netzOffY=0; zoomSetzen(1); };
  c.addEventListener("wheel",(e)=>{
    e.preventDefault();
    const b=c.getBoundingClientRect();
    zoomSetzen(e.deltaY<0?1.12:0.89, e.clientX-b.left, e.clientY-b.top);
  }, {passive:false});

  /* Ziehen: Knoten verschieben, im leeren Bereich die ganze Ansicht.
     Zwei Finger: Zoom um die Fingermitte und Verschieben mit der Mitte
     (Pinch). Pointer Events liefern jeden Finger als eigenen Zeiger; die
     aktiven Zeiger stehen in «finger». Sobald ein zweiter Finger liegt,
     endet das Ziehen eines Knotens und das Bild folgt den zwei Fingern. */
  let schieben=null, bewegt=false;
  const finger=new Map();
  let pinch=null;
  const pinchStart=()=>{
    const [p1,p2]=[...finger.values()];
    const b=c.getBoundingClientRect();
    pinch={dist:Math.hypot(p1.x-p2.x,p1.y-p2.y), mx:(p1.x+p2.x)/2-b.left, my:(p1.y+p2.y)/2-b.top, zoom:netzZoom, ox:netzOffX, oy:netzOffY};
    if(netzZieht){ netzZieht=null; netzHeizen(0.3); }
    schieben=null; bewegt=true;
  };
  c.addEventListener("pointerdown",(e)=>{
    finger.set(e.pointerId,{x:e.clientX,y:e.clientY});
    try{ c.setPointerCapture(e.pointerId); }catch(_e){}
    if(finger.size===2){ pinchStart(); return; }
    if(finger.size>2) return;
    const b=c.getBoundingClientRect();
    const sx=e.clientX-b.left, sy=e.clientY-b.top;
    const n=knotenBei(sx,sy);
    bewegt=false;
    if(n){ netzZieht={knoten:n}; netzHeizen(0.5); }
    else { schieben={x:e.clientX, y:e.clientY, ox:netzOffX, oy:netzOffY}; }
  });
  c.addEventListener("pointermove",(e)=>{
    if(finger.has(e.pointerId)) finger.set(e.pointerId,{x:e.clientX,y:e.clientY});
    const b=c.getBoundingClientRect();
    if(pinch && finger.size>=2){
      const [p1,p2]=[...finger.values()];
      const dist=Math.hypot(p1.x-p2.x,p1.y-p2.y);
      const mx=(p1.x+p2.x)/2-b.left, my=(p1.y+p2.y)/2-b.top;
      // Weltpunkt unter der Fingermitte beim Start soll unter der Mitte bleiben
      const wx=(pinch.mx-b.width/2-pinch.ox)/pinch.zoom, wy=(pinch.my-b.height/2-pinch.oy)/pinch.zoom;
      netzZoom=Math.min(4, Math.max(0.25, pinch.zoom*(dist/Math.max(pinch.dist,1))));
      netzOffX = mx-b.width/2-wx*netzZoom;
      netzOffY = my-b.height/2-wy*netzZoom;
      const a=document.getElementById("zoomWert");
      if(a) a.textContent=Math.round(netzZoom*100)+" %";
      netzMalen();
      return;
    }
    if(netzZieht){
      bewegt=true;
      const w=zuWelt(e.clientX-b.left, e.clientY-b.top);
      netzZieht.knoten.x=w.x; netzZieht.knoten.y=w.y;
      netzMalen();
    } else if(schieben){
      const dx=e.clientX-schieben.x, dy=e.clientY-schieben.y;
      if(Math.abs(dx)+Math.abs(dy)>3) bewegt=true;
      netzOffX=schieben.ox+dx; netzOffY=schieben.oy+dy;
      netzMalen();
    }
  });
  const loslassen=(e)=>{
    finger.delete(e.pointerId);
    if(finger.size<2) pinch=null;
    if(netzZieht){ netzZieht=null; netzHeizen(0.3); }
    schieben=null;
    try{ c.releasePointerCapture(e.pointerId); }catch(_e){}
  };
  c.addEventListener("pointerup",(e)=>{
    const b=c.getBoundingClientRect();
    if(!bewegt && finger.size===1){
      const n=knotenBei(e.clientX-b.left, e.clientY-b.top);
      netzGewaehlt = (n && netzGewaehlt && n.id===netzGewaehlt.id) ? null : n;
      if(netzGewaehlt) netzInfoZeigen(netzGewaehlt); else netzInfoLeer();
    }
    loslassen(e);
    netzMalen();
  });
  c.addEventListener("pointercancel", loslassen);
  // Safari iOS: Gestenereignisse abfangen, sonst zoomt die ganze Seite
  ["gesturestart","gesturechange","gestureend"].forEach(n=>c.addEventListener(n,e=>e.preventDefault()));

  const leg=document.getElementById("netzLegende");
  leg.innerHTML=Object.entries({Ratsmitglied:netzFarben().mitglied, Organisation:netzFarben().organisation, Branche:netzFarben().branche})
    .map(([k,v])=>`<span><i style="background:${v}"></i>${k}</span>`).join("")
    + `<span><i style="background:${cssFarbe("--p-evp")}"></i>Suchtreffer</span>`;
  netzAufbauen(false);
}

  /* ═══ Rahmen: Navigation, Bereich, Thema ═══════════════════════════════ */
  var RENDER = {
    neu: renderNeu, votes: renderVotes, members: renderMembers,
    frak: renderFrak, themen: renderThemen, rang: renderRang,
    netz: renderNetz, match: renderMatch
  };

  function render() {
    $$(".panel").forEach(function (p) { p.classList.remove("on"); });
    $$("#nav button").forEach(function (b) {
      b.classList.toggle("on", b.getAttribute("data-tab") === st.tab);
    });
    var el = $("#p-" + st.tab);
    el.classList.add("on");
    RENDER[st.tab](el);
    verdrahten(el);
    $("#scope").disabled = (st.tab === "neu" || st.tab === "match");
  }

  function verdrahten(el) {
    $$("[data-member]", el).forEach(function (b) {
      b.addEventListener("click", function () {
        st.mitglied = b.getAttribute("data-member");
        st.tab = "members";
        render();
        window.scrollTo({ top: 0 });
      });
    });
    $$("[data-thema]", el).forEach(function (b) {
      b.addEventListener("click", function () { st.thema = b.getAttribute("data-thema"); render(); });
    });
    $$("[data-goto-sess]", el).forEach(function (b) {
      b.addEventListener("click", function () {
        st.scope = { typ: "sess", wert: b.getAttribute("data-goto-sess") };
        st.tab = "votes";
        fuelleScope();
        render();
        window.scrollTo({ top: 0 });
      });
    });
    $$("[data-goto]", el).forEach(function (b) {
      b.addEventListener("click", function () {
        var teile = b.getAttribute("data-goto").split("|");
        springeZu(teile[0], null, parseInt(teile[1], 10));
      });
    });
  }

  /* Zu einer Abstimmung springen: Sitzung als Bereich, Rubrik Abstimmungen,
     Karte in die Mitte und kurz aufblitzen. Angesprochen entweder ueber den
     Index der Karte (interne Verweise) oder ueber die Nummer der Abstimmung
     (Sprungadresse von aussen, siehe leseAdresse). */
  function springeZu(sitzung, nr, idx) {
    if (!D.sessions.some(function (s) { return s.s === sitzung; })) return false;
    st.scope = { typ: "sess", wert: sitzung };
    st.tab = "votes";
    st.mitglied = null;
    st.suche = "";
    fuelleScope();
    render();
    var karte = null;
    if (nr != null) karte = document.getElementById("v-" + sitzung.replace(/[^a-z0-9]/gi, "") + "-" + nr);
    if (!karte && idx != null) karte = $$(".vcard", $("#p-votes"))[idx];
    if (karte) {
      karte.scrollIntoView({ behavior: "smooth", block: "center" });
      karte.classList.add("blitz");
      setTimeout(function () { karte.classList.remove("blitz"); }, 2200);
    }
    return true;
  }

  /* Sprungadresse: kantonsrat/#s=<Sitzung>&nr=<Nummer>. So verweist der
     Abstimmungsspiegel auf die einzelne namentliche Abstimmung im Rat. Die
     Sitzung steht in der Adresse so, wie sie in den Daten heisst, kodiert
     mit encodeURIComponent. Ohne Treffer bleibt die Startrubrik. */
  function leseAdresse() {
    var h = (location.hash || "").replace(/^#/, "");
    if (!h) return false;
    var q = new URLSearchParams(h);
    var s = q.get("s"), nr = q.get("nr");
    if (!s) return false;
    return springeZu(s, nr, null);
  }

  function fuelleScope() {
    var sel = $("#scope");
    var gruppen = [];
    var legs = Object.keys(D.leg).sort(function (a, b) { return D.leg[b].nummer - D.leg[a].nummer; });
    gruppen.push('<optgroup label="Legislatur">' + legs.map(function (n) {
      var L = D.leg[n];
      var aktiv = st.scope && st.scope.typ === "leg" && String(st.scope.wert) === String(L.nummer);
      return '<option value="leg:' + L.nummer + '"' + (aktiv ? " selected" : "") + ">" +
        esc(L.label) + (String(L.nummer) === String(D.aktLeg) ? " (aktuell)" : "") +
        " · " + L.n_sitzungen + " Sitzungen</option>";
    }).join("") + "</optgroup>");
    gruppen.push('<optgroup label="Einzelne Sitzung">' + D.sessions.map(function (s) {
      var aktiv = st.scope && st.scope.typ === "sess" && st.scope.wert === s.s;
      return '<option value="sess:' + esc(s.s) + '"' + (aktiv ? " selected" : "") + ">" +
        esc(s.s) + "</option>";
    }).join("") + "</optgroup>");
    sel.innerHTML = gruppen.join("");
  }

  function initRahmen() {
    var body = document.body;
    var mq = window.matchMedia("(max-width: 960px)");
    var navToggle = $("#navToggle"), burger = $("#burger"), scrim = $("#scrim");

    function setNav(state) {
      body.setAttribute("data-nav", state);
      var offen = state !== "min";
      navToggle.setAttribute("aria-expanded", String(offen));
      navToggle.setAttribute("aria-label", offen ? "Seitenleiste einklappen" : "Seitenleiste ausklappen");
      if (!mq.matches) { try { localStorage.setItem("krsh-nav", state); } catch (e) {} }
      burger.setAttribute("aria-expanded", String(state === "open"));
      scrim.hidden = state !== "open";
    }
    navToggle.addEventListener("click", function () {
      if (mq.matches) { setNav("closed"); return; }
      setNav(body.getAttribute("data-nav") === "min" ? "closed" : "min");
    });
    burger.addEventListener("click", function () { setNav("open"); });
    scrim.addEventListener("click", function () { setNav("closed"); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && body.getAttribute("data-nav") === "open") setNav("closed");
    });
    mq.addEventListener("change", function () { setNav("closed"); });
    try {
      var g = localStorage.getItem("krsh-nav");
      setNav(g === "min" && !mq.matches ? "min" : "closed");
    } catch (e) { setNav("closed"); }

    /* Hell und Dunkel */
    var tT = $("#themeToggle"), tL = $("#themeLabel"), tI = $("#themeIcon");
    var SONNE = '<circle cx="8" cy="8" r="3.2" fill="currentColor"/>' +
      '<path d="M8 .8v2M8 13.2v2M.8 8h2M13.2 8h2M2.9 2.9l1.4 1.4M11.7 11.7l1.4 1.4' +
      'M13.1 2.9l-1.4 1.4M4.3 11.7l-1.4 1.4" stroke="currentColor" stroke-width="1.5"' +
      ' stroke-linecap="round" fill="none"/>';
    var MOND = '<path d="M13 9.6A5.4 5.4 0 0 1 6.4 3a5.6 5.6 0 1 0 6.6 6.6z" fill="currentColor"/>';
    function dunkel() {
      var t = document.documentElement.getAttribute("data-theme");
      return t ? t === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
    }
    function themeAnzeigen() {
      var d = dunkel();
      tL.textContent = d ? "Hellmodus" : "Dunkelmodus";
      tI.innerHTML = d ? SONNE : MOND;
      tT.setAttribute("aria-pressed", String(d));
    }
    tT.addEventListener("click", function () {
      document.documentElement.setAttribute("data-theme", dunkel() ? "light" : "dark");
      try { localStorage.setItem("krsh-theme", dunkel() ? "dark" : "light"); } catch (e) {}
      themeAnzeigen();
      if (!$("#bildModal").hidden) zeichneBild($("#bildMotiv").value);
    });
    try {
      var gt = localStorage.getItem("krsh-theme");
      if (gt === "dark" || gt === "light") document.documentElement.setAttribute("data-theme", gt);
    } catch (e) {}
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", themeAnzeigen);
    themeAnzeigen();

    /* Rubriken */
    $$("#nav button").forEach(function (b) {
      b.addEventListener("click", function () {
        st.tab = b.getAttribute("data-tab");
        st.mitglied = null;
        if (mq.matches) setNav("closed");
        render();
        window.scrollTo({ top: 0 });
      });
    });

    /* Bereich */
    $("#scope").addEventListener("change", function () {
      var w = this.value.split(":");
      st.scope = { typ: w[0], wert: w.slice(1).join(":") };
      st.mitglied = null;
      render();
    });

    /* Suche */
    var suche = $("#suche"), timer = null;
    suche.addEventListener("input", function () {
      clearTimeout(timer);
      timer = setTimeout(function () {
        st.suche = suche.value.trim();
        if (st.tab !== "votes" && st.tab !== "members" && st.suche) st.tab = "votes";
        render();
      }, 220);
    });

    /* Datenstand */
    var s0 = D.sessions[0];
    $("#stand").innerHTML = "Datenstand<br>" + esc(s0 ? s0.dt : "");
  }

  /* ═══ Start ════════════════════════════════════════════════════════════ */
  st.scope = { typ: "leg", wert: D.aktLeg };
  fuelleScope();
  initRahmen();
  initBild();
  if (!leseAdresse()) render();
  window.addEventListener("hashchange", leseAdresse);
})();
