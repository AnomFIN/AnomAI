# AnomFIN · JugiAI – käyttöönotto ja käyttöopas

Tämä asiakirja kokoaa yhteen kaikki vaiheet, joilla AnomAI/JugiAI puretaan, asennetaan ja otetaan käyttöön Windows-ympäristössä. Paketti sisältää ohjatun asennuksen (`install.bat`), sovelluksen lähdekoodin (`jugiai.py`) sekä automaattisen EXE-rakentajan. Kun noudatat alla olevia vaiheita järjestyksessä, sovellus toimii heti purkamisen jälkeen – aivan kuin junan vessa.

> **Allekirjoitus:** AnomFIN · Älykkyyden käyttöönotto

---

## 1. Valmistelut

1. **Lataa uusin jakopaketti** GitHubista tai toimittamastasi lähteestä ja pura se haluamaasi kansioon (esim. `C:\AnomAI`).
2. **Varmista Python 3.9+** on asennettuna. Jos sitä ei löydy, hae uusin versio osoitteesta [python.org](https://www.python.org/downloads/windows/).
3. (Valinnainen) **Poista aiempien versioiden jäännökset** – esimerkiksi vanhat `venv`-kansiot tai `dist`-kansiot.

---

## 2. Ohjattu asennus (`install.bat`)

Asennusohjelma käy läpi seuraavat vaiheet ja pitää ikkunan auki myös virhetilanteissa, jotta näet selkeät korjausohjeet:

1. **Käynnistä asennus** kaksoisklikkaamalla `install.bat`. Konsolin koodisivu vaihtuu automaattisesti UTF-8-muotoon, joten ääkköset näkyvät oikein.
2. **Pythonin tunnistus ja tarkistus.** Skripti etsii asennetun Pythonin (`py -3`, `python`, `python3`) ja varmistaa, että versio on vähintään 3.9. Halutessasi voit syöttää oman polun.
3. **Virtuaaliympäristö (valinnainen).** Voit luoda automaattisesti `venv`-kansion. Jos luonti epäonnistuu, jatketaan suoraan järjestelmän Pythonilla.
4. **Pip ja riippuvuudet.** Pip päivitetään (valinnainen) ja sinulta kysytään, haluatko asentaa paikallisen LLM-tuen (`llama-cpp-python --prefer-binary`). Kaikki asennuskomennot on suojattu uudelleenyritysluopeilla – epäonnistuminen ei kaada ikkunaa, vaan tarjoaa mahdollisuuden yrittää uudelleen tai ohittaa valinnaisen vaiheen.
5. **JugiAI:n konfigurointi.** Vastaa ohjattuun lomakkeeseen (API-avain, malli, lämpötila, taustakuva-asetukset jne.). Tiedot tallennetaan `config.json`-tiedostoon, ja tyhjä `history.json` luodaan automaattisesti.
6. **AnomAI.exe:n generointi.** Skripti asentaa PyInstaller-riippuvuudet, muuntaa `logo.png` → `logo.ico`, koostaa `AnomAI.exe`-tiedoston ja kopioi sen projektin juureen. Samalla tuotetaan `dist\AnomAI`-hakemisto ja jakopaketti `AnomAI_Windows.zip`.
7. **Pikakuvake työpöydälle.** Powershell-komento luo `AnomAI.lnk`-pikakuvakkeen työpöydällesi ja käyttää automaattisesti `logo.ico`-ikonia. Mahdolliset virheet (esim. jos työpöytää ei löydy) raportoidaan.
8. **Yhteenveto.** Lopuksi näet listan luoduista tiedostoista ja ohjeen seuraaviin askeliin. Ikkuna pysyy auki, kunnes suljet sen (tai painat Enteriä `pause`-kehotteessa).

---

## 3. Ensimmäinen käynnistys

1. **Käytä työpöydän `AnomAI`-pikakuvaketta** tai kaksoisklikkaa projektin juureen kopioitua `AnomAI.exe` -tiedostoa.
2. Vaihtoehtoisesti voit käynnistää `start_jugiai.bat`-tiedoston. Se yrittää ensin avata `AnomAI.exe`-tiedoston ja palaa tarvittaessa Python-versioon (virtuaaliympäristö → `pythonw` → `py -3` → `python`).
3. Kun sovellus avautuu, ⚙️-kuvakkeen takaa löytyy Asetukset-paneeli, jossa voit hienosäätää profiilia sekä valita paikallisen mallin, jos `llama-cpp-python` asennettiin.

---

## 4. Päivitys tai uudelleenrakennus

* **Asennuksen uudelleenkäyttö:** Aja `install.bat` uudelleen. Skripti tunnistaa olemassa olevan `venv`-kansion, konfiguraatiot ja EXE:n ja päivittää ne turvallisesti.
* **Pelkkä EXE-rakennus:** Käytä `build_exe.bat`-tiedostoa. Se luo tai päivittää `.venv_build`-ympäristön, tarjoaa samat virheenkäsittelyt kuin asennin ja tuottaa:
  - `dist\AnomAI\AnomAI.exe`
  - projektin juureen kopioidun `AnomAI.exe`
  - `AnomAI_Windows.zip`
* **Lähdekoodin ajaminen:** Voit aina suorittaa `jugiai.py` suoraan (esim. `python jugiai.py`), mikäli Python-riippuvuudet ovat kunnossa.

---

## 5. Vianetsintä

| Ongelma | Syy | Ratkaisu |
| --- | --- | --- |
| `llama-cpp-python` asennus epäonnistuu (CMake-virheet) | Windowsilta puuttuu rakennustyökalut tai sopiva pyörä | Asenna [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/), valitse `Retry` asennusohjelmassa tai kirjoita `E` ohittaaksesi paikallisen mallin tuen. Etä-API toimii silti. |
| Pikakuvaketta ei synny | Työpöydän polku ei ollut PowerShellin saatavilla | Luo pikakuvake manuaalisesti: hiiren oikea `AnomAI.exe` → **Lähetä** → **Työpöytä (luo pikakuvake)**. |
| `start_jugiai.bat` ei löydä Pythonia | Python puuttuu tai PATH-ympäristömuuttuja ei sisällä sitä | Asenna Python 3.9+ ja varmista, että asennuksen lopussa valitset “Add python.exe to PATH”, tai käynnistä `AnomAI.exe` suoraan. |
| Sovellus ei yhdistä OpenAI:hin | Virheellinen API-avain tai malli | Avaa ⚙️ Asetukset → OpenAI-välilehti, syötä toimiva avain ja malli (esim. `gpt-4o-mini`). |

---

## 6. Projektiin sisältyvät työkalut

| Tiedosto | Kuvaus |
| --- | --- |
| `install.bat` | Täydellinen käyttöönottoskripti: virtuaaliympäristö, riippuvuudet, konfigurointi, EXE, pikakuvake. |
| `start_jugiai.bat` | Älykäs käynnistin, joka suosii `AnomAI.exe`:tä ja käyttää Pythonia vain tarvittaessa. |
| `build_exe.bat` | Erillinen EXE-pakettien rakennus (samat virheenkäsittelyt kuin asennuksessa). |
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

**© 2024 AnomFIN · Intelligent Experiences**
