# AnomFIN · JugiAI – käyttöönotto ja käyttöopas

Tämä asiakirja kokoaa yhteen kaikki vaiheet, joilla AnomAI/JugiAI puretaan, asennetaan ja otetaan käyttöön Windows-ympäristössä. Paketti sisältää ohjatun asennuksen (`install.bat`), sovelluksen lähdekoodin (`jugiai.py`) sekä automaattisen EXE-rakentajan. Kun noudatat alla olevia vaiheita järjestyksessä, sovellus toimii heti purkamisen jälkeen – aivan kuin junan vessa.

> **Allekirjoitus:** AnomFIN · Älykkyyden käyttöönotto

---

## 1. Valmistelut

1. **Lataa uusin jakopaketti** GitHubista tai toimittamastasi lähteestä ja pura se haluamaasi kansioon (esim. `C:\AnomAI`).
2. **Varmista Python 3.10+ (64-bittinen)** on asennettuna. Jos sitä ei löydy, hae uusin versio osoitteesta [python.org](https://www.python.org/downloads/windows/).
3. (Valinnainen) **Poista aiempien versioiden jäännökset** – esimerkiksi vanhat `venv`-kansiot tai `dist`-kansiot.

---

## 2. Ohjattu asennus (`install.bat`)

Asennusohjelma käy läpi seuraavat vaiheet ja pitää ikkunan auki myös virhetilanteissa, jotta näet selkeät korjausohjeet:

### UTF-8-käynnistin (`install_utf8.bat`)

* **Turvallinen koodisivun vaihto.** `install_utf8.bat` tunnistaa konsolin nykyisen koodisivun, yrittää vaihtaa UTF-8:aan ja palauttaa alkuperäisen tilan, vaikka `install.bat` epäonnistuisi.
* **Rakenteinen lokitus.** Kaikki ilmoitukset tulostuvat JSON-muodossa (`{"component":"install_utf8", ...}`), joten ne on helppo ohjata lokityökaluun tai liittää tukipyyntöön.
* **Virhesieto.** Jos koodisivun vaihto tai `install.bat`-haku epäonnistuu, skripti raportoi tilanteen, pitää prosessin käynnissä ja antaa yksiselitteiset jatko-ohjeet.

1. **Käynnistä asennus** kaksoisklikkaamalla `install.bat`. Konsolin koodisivu vaihtuu automaattisesti UTF-8-muotoon, joten ääkköset näkyvät oikein.
2. **Pythonin tunnistus ja tarkistus.** Skripti etsii asennetun Pythonin (`py -3`, `python`, `python3`) ja varmistaa, että käytössä on vähintään 64-bittinen Python 3.10. Halutessasi voit syöttää oman polun.
3. **Virtuaaliympäristö `.venv`.** Projektiin luodaan automaattisesti `.venv`-kansio. Jos luonti epäonnistuu, jatketaan suoraan järjestelmän Pythonilla, mutta suosittelemme käyttämään virtuaaliympäristöä.
4. **Pip ja riippuvuudet.** Pip päivitetään ja `requirements.txt` asennetaan. Tämän jälkeen skripti kysyy, haluatko asentaa paikallisen LLM-tuen (`llama-cpp-python --prefer-binary`). Kaikki asennuskomennot jatkavat virhetilanteissa, jotta voit yrittää uudelleen tai ohittaa vaiheen hallitusti.
5. **JugiAI:n konfigurointi.** Vastaa ohjattuun lomakkeeseen (API-avain, malli, lämpötila, taustakuva-asetukset jne.). Tiedot tallennetaan `config.json`-tiedostoon, ja tyhjä `history.json` luodaan automaattisesti.
6. **AnomAI.exe:n generointi.** Skripti asentaa PyInstaller-riippuvuudet, muuntaa `logo.png` → `logo.ico`, koostaa `AnomAI.exe`-tiedoston ja kopioi sen projektin juureen. Samalla tuotetaan `dist\AnomAI`-hakemisto ja jakopaketti `AnomAI_Windows.zip`.
7. **Pikakuvake työpöydälle.** Powershell-komento luo `AnomAI.lnk`-pikakuvakkeen työpöydällesi ja käyttää automaattisesti `logo.ico`-ikonia. Mahdolliset virheet (esim. jos työpöytää ei löydy) raportoidaan.
8. **Yhteenveto.** Lopuksi näet listan luoduista tiedostoista ja ohjeen seuraaviin askeliin. Ikkuna pysyy auki, kunnes suljet sen (tai painat Enteriä `pause`-kehotteessa).

---

## 3. Ensimmäinen käynnistys

1. **Käytä työpöydän `AnomAI`-pikakuvaketta** tai kaksoisklikkaa projektin juureen kopioitua `AnomAI.exe` -tiedostoa.
2. Vaihtoehtoisesti voit käynnistää `start_jugiai.bat`-tiedoston. Se yrittää ensin avata `AnomAI.exe`-tiedoston ja palaa tarvittaessa Python-versioon (virtuaaliympäristö `.venv` → `pythonw` → `py -3` → `python`).
3. Kun sovellus avautuu, ⚙️-kuvakkeen takaa löytyy Asetukset-paneeli, jossa voit hienosäätää profiilia sekä valita paikallisen mallin, jos `llama-cpp-python` asennettiin.

### Virtuaaliympäristön aktivointi käsin

Jos haluat käyttää komentoriviä suoraan (esimerkiksi asentaaksesi lisäkirjastoja), aktivoi sama virtuaaliympäristö, jonka `install.bat` loi:

```powershell
cd C:\Polku\AnomAI
Set-ExecutionPolicy -Scope Process RemoteSigned  # tarvittaessa
\.venv\Scripts\Activate.ps1   # PowerShell
```

Komentokehotteessa (`cmd.exe`) vastaava komento on:

```cmd
cd C:\Polku\AnomAI
\.venv\Scripts\activate
```

Aktivoinnin jälkeen `python` ja `pip` viittaavat automaattisesti oikeaan ympäristöön, joten paikallisen mallin tuki ja Pillow pysyvät käytettävissä.

---

## 4. Päivitys tai uudelleenrakennus

* **Asennuksen uudelleenkäyttö:** Aja `install.bat` uudelleen. Skripti tunnistaa olemassa olevan `venv`-kansion, konfiguraatiot ja EXE:n ja päivittää ne turvallisesti.
* **Pelkkä EXE-rakennus:** Käytä `build_exe.bat`-tiedostoa. Se luo tai päivittää `.venv_build`-ympäristön, tarkistaa Python-version (vähintään 3.10, 64-bit) ja kirjoittaa kaiken lokiin `build_exe.log`. Skripti tuottaa:
  - `dist\AnomAI\AnomAI.exe`
  - projektin juureen kopioidun `AnomAI.exe`
  - `AnomAI_Windows.zip`
* **Lähdekoodin ajaminen:** Voit aina suorittaa `jugiai.py` suoraan (esim. `python jugiai.py`), mikäli Python-riippuvuudet ovat kunnossa.

---

## 5. Vianetsintä

| Ongelma | Syy | Ratkaisu |
| --- | --- | --- |
| `llama-cpp-python` asennus epäonnistuu (CMake-virheet) | Windowsilta puuttuu rakennustyökalut tai sopiva pyörä | Asenna [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) ja yritä `install.bat`:in ehdottamaa komentoa uudelleen. Vaihtoehtoisesti hae valmis binääripyörä osoitteesta [abetlen/llama-cpp-python releases](https://github.com/abetlen/llama-cpp-python/releases). Etä-API toimii silti ilman paikallista mallia. |
| `build_exe.bat` pysähtyy heti | Python ei ole 64-bittinen 3.10+ tai sitä ei löydy | Asenna [Python 3.10 64-bit](https://www.python.org/downloads/windows/) ja varmista, että `py -3` tai `python` osoittaa siihen. Tarkista lisätiedot `build_exe.log`-tiedostosta. |
| Pikakuvaketta ei synny | Työpöydän polku ei ollut PowerShellin saatavilla | Luo pikakuvake manuaalisesti: hiiren oikea `AnomAI.exe` → **Lähetä** → **Työpöytä (luo pikakuvake)**. |
| `start_jugiai.bat` ei löydä Pythonia | Python puuttuu tai PATH-ympäristömuuttuja ei sisällä sitä | Asenna Python 3.10+ (64-bit) ja varmista, että asennuksen lopussa valitset “Add python.exe to PATH”, tai käynnistä `AnomAI.exe` suoraan. |
| Sovellus ei yhdistä OpenAI:hin | Virheellinen API-avain tai malli | Avaa ⚙️ Asetukset → OpenAI-välilehti, syötä toimiva avain ja malli (esim. `gpt-4o-mini`). |
| `AnomAI.exe` sulkeutuu heti | Taustalla tapahtui poikkeus (esim. `llama-cpp-python` puuttuu nykyisestä ympäristöstä) | Katso virheilmoituksen kertoma polku `jugiai_error.log`-tiedostoon. Lokissa näkyy tarkka traceback ja käytetty Python-polku. Korjaa syy (esim. suorita `"%CD%\.venv\Scripts\python.exe" -m pip install --upgrade --prefer-binary llama-cpp-python`) ja käynnistä uudelleen. |
| `python jugiai.py` → "Moduulia llama_cpp ei löydy" | Komento käyttää Windows Storen python-stubia, jossa ei ole kirjastoja | Uusin versio yrittää automaattisesti käynnistää `py -3 jugiai.py` -komennon puolestasi. Jos näet virheilmoituksen, avaa `start_jugiai.bat` tai aja `py -3 jugiai.py` käsin. Aktivoi `.venv` komennolla `\.venv\Scripts\activate`, jos sellainen on luotu. |

---

## 6. Projektiin sisältyvät työkalut

| Tiedosto | Kuvaus |
| --- | --- |
| `install.bat` | Täydellinen käyttöönottoskripti: virtuaaliympäristö, riippuvuudet, konfigurointi, EXE, pikakuvake. |
| `start_jugiai.bat` | Älykäs käynnistin, joka suosii `AnomAI.exe`:tä ja käyttää Pythonia vain tarvittaessa. |
| `build_exe.bat` | Erillinen EXE-pakettien rakennus (samat virheenkäsittelyt kuin asennuksessa) ja kattava loki `build_exe.log`-tiedostoon. |
| `make_ico.py` | Muuntaa `logo.png` → `logo.ico` useissa resoluutioissa (vaatii Pillow-kirjaston). |
| `jugiai.py` | Tkinter-pohjainen pääsovellus: OpenAI- ja paikallinen GGUF-tuki, profiilit, taustakuvat ja historia. |
| `config.json` / `history.json` | Luodaan automaattisesti. Konfiguraatio kirjoitetaan UTF-8-muodossa, jotta ääkköset säilyvät oikein. |
| `logo.png` | AnomFINin vesileima ja ikoni. Asennus tuottaa tästä `logo.ico`-version. |

---

## 7. Parhaat käytännöt ja ideat jatkokehitykseen

* **Moniprofiilit:** Aktivoi useita profiileja lisäämällä niitä `config.json`-tiedostoon. Asennusohjelma varmistaa, että `DEFAULT_PROFILE` on ajan tasalla.
* **Yrityskäyttö:** Voit kopioida `AnomAI_Windows.zip` -paketin sellaisenaan loppukäyttäjille. Paketti sisältää kaiken tarvittavan, kunhan `config.json` on valmiiksi täytetty.
* **Paikallinen mallikirjasto:** Sijoita `.gguf`-mallit esimerkiksi `models`-hakemistoon ja viittaa niihin sovelluksen asetuksissa, kun `llama-cpp-python` on asennettu.
* **Automaattipäivitys:** Lisäkehitysideana voidaan tehdä skripti, joka tarkistaa GitHub-releaset ja päivittää sovelluksen yhdellä komennolla.

---

## 8. 2024-ulkoasupäivitys ja uudet toiminnot

* **Cyber-neon -teema:** Sovellus hyödyntää nyt anomfin-website -sivuston kaltaista tummaa taustaa, turkooseja korostuksia ja selkeitä kortteja.
* **Tallenteiden katselu:** Uusi *Tallenteet*-näkymä näyttää koko keskusteluhistorian listana. Valitse viesti selataksesi tai käytä toistonappeja (▶, ⏸, ⏹, 🐢, ⚖, ⚡) simuloituun uusintatoistoon.
* **Zoom-napit:** Yläpalkista löytyvät zoom-napit (＋/−) muuttavat chatti- ja editorifontin kokoa turvallisissa rajoissa. Muutos tallentuu `config.json`-tiedostoon.
* **Varmempi tallennus:** Keskusteluhistoria tallentuu nyt riippumatta siitä selaatko tallenteita tai toistatko vanhoja viestejä. Tallennus ja toistonäkymän päivitykset on eriytetty toisistaan.

---

## 9. Käyttö- ja testikomennot

```bash
python -m venv .venv            # (valinnainen) erillinen ympäristö
.venv/Scripts/activate          # Windows PowerShell
pip install -r requirements.txt
python jugiai.py                                # Käynnistä käyttöliittymä
python -m unittest discover -s tests            # Aja yksikkötestit
python -m unittest tests.test_install_utf8_script  # Varmista asennuskääreen eheys
```

### Vianetsintä ja varmistus

1. Käynnistä `python jugiai.py` ja varmista, että uusi tumma teema sekä zoom-painikkeet näkyvät.
2. Lähetä viesti → avaa *Tallenteet* → varmista, että viesti ilmestyy listaan ja toistopainikkeet toimivat.
3. Säädä zoomia ± ja tarkista, että fonttikoko muuttuu myös kirjoitusalueella.
4. Aja `install_utf8.bat` → varmista, että lokirivit ovat JSON-muotoisia ja että koodisivu palautuu, kun ikkuna suljetaan.

---

## 10. Miksi tämä design

* **Teema yhtenäistää brändin:** Käytetyt värit ja typografia seuraavat anomfin-website -sivuston kontrastia ja neon-korostuksia.
* **Tallenteiden toisto on sivuvaikutukseton:** Historiatoistin käyttää vain muistissa olevaa listaa eikä estä `history.json`-tiedoston kirjoitusta.
* **Zoom on saavutettava:** Fonttikoon rajaaminen varmistaa luettavuuden eikä riko layouttia.
* **Testattava ydin:** Zoom- ja toistonopeuslogiikka kapseloitiin `playback_utils.py`-tiedostoon, jota yksikkötestit kattavat.
* **UTF-8-kääre on idempotentti:** `install_utf8.bat` palauttaa alkuperäisen koodisivun ja raportoi JSON-lokeilla, joten se on turvallista ajaa myös skriptien sisältä.

---

## 11. Seuraavat iteroinnit

1. **Äänitallenteet:** Mahdollista ääni- ja videoliitteiden esikatselu Tallenteet-näkymässä.
2. **Haku tallenteista:** Lisää hakukenttä, joka suodattaa historiaa roolin, avainsanan tai aikaleiman perusteella.
3. **Export to PDF/Markdown:** Tarjoa pikatoiminto keskusteluhistorian vientiin yhdeksi tiedostoksi.

---

**© 2024 AnomFIN · Intelligent Experiences**
