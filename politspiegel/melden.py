"""Meldewerkzeug «Fehler melden», einmal fuer alle Seiten des Politspiegels.

Die Seiten liegen statisch bei GitHub Pages; einen eigenen Server gibt es
nicht. Die Meldung geht darum ueber den Formulardienst Web3Forms
(api.web3forms.com) als Mail an die Adresse, die beim Anlegen des Schluessels
hinterlegt wurde. Das Captcha (hCaptcha) ist Pflicht: ohne geloestes Captcha
schickt der Browser nichts ab, und Web3Forms prueft die Antwort ein zweites
Mal auf dem Server.

Einrichten (einmal, Michael):
1. https://web3forms.com, Mailadresse politspiegel.sh@gmail.com eintragen,
   den zugeschickten Zugangsschluessel kopieren.
2. In politspiegel/politspiegel.json unter "melden" eintragen:
     "melden": {"schluessel": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}
3. Alle Seiten neu bauen (bauen.py, argumente.py je Abstimmung, publish.py).

Der Schluessel steht danach im Seitenquelltext. Das ist bei diesem Dienst so
vorgesehen: er legt nur den Empfaenger fest, nicht mehr; wer ihn missbraucht,
schickt Mails an denselben Empfaenger und scheitert am Captcha.

Solange kein Schluessel eingetragen ist, erscheint kein Knopf.
"""

from __future__ import annotations

import json
from html import escape as e
from pathlib import Path

QUELLE = Path(__file__).resolve().parent / "politspiegel.json"
ZIEL = "https://api.web3forms.com/submit"
# hCaptcha-Seitenschluessel von Web3Forms (fuer alle Nutzer des Dienstes gleich)
HCAPTCHA = "50b2fe65-b00b-4b9e-ad62-3ba471098be2"


def schluessel() -> str:
    try:
        return str(json.loads(QUELLE.read_text(encoding="utf-8")).get("melden", {}).get("schluessel") or "")
    except Exception:
        return ""


def melden_html(seite: str = "") -> str:
    """Knopf und Dialog. «seite» ist eine Bezeichnung der Seite fuer die Mail;
    die Adresse traegt der Browser selbst ein."""
    k = schluessel()
    if not k:
        return ""
    return f'''
<button type="button" class="melden-knopf" id="meldenKnopf" title="Einen Fehler auf dieser Seite melden">
  <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M8 2.5l6 11H2z" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linejoin="round"/><path d="M8 6.5v3.2M8 11.6v.6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>Fehler melden</button>
<dialog class="melden" id="meldenDialog" aria-labelledby="meldenTitel">
  <form id="meldenForm" method="dialog" novalidate>
    <h2 id="meldenTitel">Fehler melden</h2>
    <p class="melden-hinweis">Was stimmt nicht? Eine Zahl, ein Name, ein toter Verweis, ein Satz, der so nicht haltbar ist. Die Meldung geht als Mail an den Herausgeber; Korrekturen werden sichtbar protokolliert.</p>
    <input type="hidden" name="access_key" value="{e(k)}">
    <input type="hidden" name="subject" value="Politspiegel: Fehlermeldung{(' · ' + e(seite)) if seite else ''}">
    <input type="hidden" name="from_name" value="Politspiegel Schaffhausen">
    <input type="hidden" name="seite" id="meldenSeite" value="">
    <input type="checkbox" name="botcheck" class="melden-falle" tabindex="-1" autocomplete="off" aria-hidden="true">
    <label>Was ist falsch, und wo?<textarea name="meldung" id="meldenText" rows="5" required maxlength="3000" placeholder="Zum Beispiel: Im Ratsblock steht 35:20, im Abstimmungsmagazin 36:19."></textarea></label>
    <label>Mailadresse für Rückfragen, freiwillig<input type="email" name="email" autocomplete="email" placeholder="name@beispiel.ch"></label>
    <div class="h-captcha" data-captcha="true" data-sitekey="{HCAPTCHA}"></div>
    <p class="melden-status" id="meldenStatus" aria-live="polite"></p>
    <div class="melden-zeile">
      <button type="button" class="melden-ab" id="meldenAb">Abbrechen</button>
      <button type="submit" class="melden-los" id="meldenLos">Meldung senden</button>
    </div>
    <p class="melden-klein">Übermittlung über Web3Forms (Formulardienst) und hCaptcha (Spam-Schutz). Beide erhalten dabei Ihre IP-Adresse; die Meldung selbst wird als Mail an den Herausgeber weitergeleitet und nicht anderweitig gespeichert.</p>
  </form>
</dialog>
<script src="https://web3forms.com/client/script.js" async defer></script>
<script>
(function(){{
  var k=document.getElementById("meldenKnopf"), d=document.getElementById("meldenDialog"), f=document.getElementById("meldenForm");
  if(!k||!d||!f) return;
  var st=document.getElementById("meldenStatus"), los=document.getElementById("meldenLos");
  k.addEventListener("click",function(){{
    document.getElementById("meldenSeite").value=location.href;
    st.textContent=""; f.reset();
    if(typeof d.showModal==="function") d.showModal(); else d.setAttribute("open","");
    document.getElementById("meldenText").focus();
  }});
  document.getElementById("meldenAb").addEventListener("click",function(){{ d.close(); }});
  d.addEventListener("click",function(ev){{ if(ev.target===d) d.close(); }});
  f.addEventListener("submit",function(ev){{
    ev.preventDefault();
    var text=document.getElementById("meldenText").value.trim();
    if(text.length<10){{ st.textContent="Bitte beschreiben Sie den Fehler in einem Satz."; return; }}
    var cap=f.querySelector('[name="h-captcha-response"]');
    if(!cap||!cap.value){{ st.textContent="Bitte zuerst das Captcha lösen."; return; }}
    los.disabled=true; st.textContent="Wird gesendet …";
    var fd=new FormData(f);
    fetch("{ZIEL}",{{method:"POST",body:fd,headers:{{Accept:"application/json"}}}})
      .then(function(r){{ return r.json(); }})
      .then(function(j){{
        if(j&&j.success){{ st.textContent="Danke, die Meldung ist angekommen."; setTimeout(function(){{ d.close(); }},1600); }}
        else {{ st.textContent="Das hat nicht geklappt: "+((j&&j.message)||"unbekannter Fehler")+". Alternativ per Mail an die Adresse im Impressum."; }}
      }})
      .catch(function(){{ st.textContent="Keine Verbindung zum Formulardienst. Alternativ per Mail an die Adresse im Impressum."; }})
      .finally(function(){{ los.disabled=false; if(window.hcaptcha){{ try{{ hcaptcha.reset(); }}catch(_e){{}} }} }});
  }});
}})();
</script>'''


MELDEN_CSS = """
.melden-knopf{position:fixed;z-index:850;right:18px;bottom:64px;display:inline-flex;align-items:center;gap:7px;
  padding:8px 12px;border-radius:999px;border:1px solid rgba(17,24,32,.18);background:#FFFFFF;color:#2A3441;
  font:600 12.5px/1 Archivo,"Public Sans","Helvetica Neue",Arial,sans-serif;cursor:pointer;box-shadow:0 2px 10px rgba(17,24,32,.14)}
.melden-knopf:hover{color:#111820;border-color:rgba(17,24,32,.4)}
.melden{border:0;border-radius:14px;padding:0;max-width:min(560px,92vw);width:100%;box-shadow:0 20px 60px rgba(17,24,32,.3);background:#FFFFFF;color:#111820}
.melden::backdrop{background:rgba(17,24,32,.45)}
.melden form{padding:24px 26px 20px;display:flex;flex-direction:column;gap:12px;font-family:"Public Sans","Helvetica Neue",Arial,sans-serif}
.melden h2{margin:0;font-size:20px;font-family:Archivo,"Public Sans",Arial,sans-serif}
.melden-hinweis{margin:0;font-size:14px;line-height:1.5;color:#4A5563}
.melden label{display:flex;flex-direction:column;gap:5px;font-size:13px;font-weight:600;color:#2A3441}
.melden textarea,.melden input[type=email]{font:400 14.5px/1.45 "Public Sans","Helvetica Neue",Arial,sans-serif;padding:9px 11px;border:1px solid rgba(17,24,32,.25);border-radius:8px;background:#FFFFFF;color:#111820;resize:vertical}
.melden-falle{position:absolute;left:-9999px;opacity:0}
.melden-status{margin:0;min-height:1.3em;font-size:13.5px;color:#7A2E2E}
.melden-zeile{display:flex;justify-content:flex-end;gap:10px}
.melden-ab,.melden-los{font:600 13.5px/1 Archivo,"Public Sans",Arial,sans-serif;padding:10px 16px;border-radius:999px;cursor:pointer;border:1px solid rgba(17,24,32,.25);background:#FFFFFF;color:#2A3441}
.melden-los{background:#1F4E9C;border-color:#1F4E9C;color:#FFFFFF}
.melden-los[disabled]{opacity:.6;cursor:wait}
.melden-klein{margin:4px 0 0;font-size:11.5px;line-height:1.45;color:#6B7684}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .melden-knopf,:root:not([data-theme="light"]) .melden{background:#1A2230;color:#E6EAF0;border-color:rgba(230,234,240,.2)}
  :root:not([data-theme="light"]) .melden-hinweis,:root:not([data-theme="light"]) .melden label{color:#B9C2CE}
  :root:not([data-theme="light"]) .melden textarea,:root:not([data-theme="light"]) .melden input[type=email],:root:not([data-theme="light"]) .melden-ab{background:#111820;color:#E6EAF0;border-color:rgba(230,234,240,.25)}}
:root[data-theme="dark"] .melden-knopf,:root[data-theme="dark"] .melden{background:#1A2230;color:#E6EAF0;border-color:rgba(230,234,240,.2)}
:root[data-theme="dark"] .melden-hinweis,:root[data-theme="dark"] .melden label{color:#B9C2CE}
:root[data-theme="dark"] .melden textarea,:root[data-theme="dark"] .melden input[type=email],:root[data-theme="dark"] .melden-ab{background:#111820;color:#E6EAF0;border-color:rgba(230,234,240,.25)}
@media (max-width:640px){.melden-knopf{bottom:70px;right:12px;padding:8px 10px;font-size:12px}}
@media print{.melden-knopf,.melden{display:none}}
"""
