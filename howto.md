# JugiAI Command Deck – Käyttöönotto-opas

Tervetuloa AnomFINin JugiAI-komentokeskukseen! Tämä dokumentti johdattaa sinut alusta loppuun – ympäristön valmistelusta aina ensimmäiseen keskusteluun ja syvällisiin optimointeihin asti.

## 1. Vaatimukset
- **Käyttöjärjestelmä:** Windows 10/11 (64-bit suositeltu).
- **Python:** Versio 3.9 tai uudempi. Asennuksen voi automatisoida Microsoft Storessa tai osoitteesta [python.org](https://www.python.org/downloads/windows/).
- **OpenAI API -avain:** Luo tai hallinnoi avaimiasi [OpenAI:n hallintapaneelista](https://platform.openai.com/account/api-keys).
- **Valinnaisesti:** GPU ja gguf-mallit, jos haluat hyödyntää paikallista LLM-ajoa `llama-cpp-python`-kirjaston avulla.

## 2. Nopea asennus `install.bat`-skriptillä
1. **Pura** projekti haluamaasi kansioon (esim. `C:\AnomFIN\JugiAI`).
2. **Kaksoisnapsauta** `install.bat`-tiedostoa.
3. **Vahvista Python** – skripti etsii automaattisesti tulkin (`py -3`, `python`, `python3`). Tarvittaessa voit syöttää oman polun.
4. **Valitse virtuaaliympäristö** – suosittelemme hyväksymään oletuksen ja luomaan `venv`-hakemiston projektin juureen.
5. **(Valinnainen)** Asenna paikallisen mallin tuki (`llama-cpp-python`) valitsemalla `K` asennuksen aikana.
6. **Syötä API-avain ja malliasetukset**. Voit antaa mukautetun system-promptin, säätää lämpötilaa, asettaa `max_tokens`-rajan ja päättää käytetäänkö AnomFINin visuaalista taustaa.
7. **Valmis!** Skripti generoi `config.json`-tiedoston, alustaa tyhjän `history.json`:n ja muistuttaa, että sovellus käynnistetään `start_jugiai.bat`-tiedostolla.

> 💡 **Vinkki:** Asennusohjelma käyttää `jugiai.py`:n oletusprofiileja. Voit muokata asetuksia myöhemmin sovelluksen käyttöliittymästä ilman, että asennus skriptiä tarvitsee ajaa uudelleen.

## 3. Ensimmäinen käynnistys
1. Käynnistä `start_jugiai.bat`. Skripti priorisoi `venv\\Scripts\\pythonw.exe`:n, jolloin käyttöliittymä avautuu ilman taustakonsolia. Tarvittaessa se käyttää `py -3`- tai `python`-komentoa.
2. Mikäli API-avainta ei ole tallennettu, sovellus avaa asetuspaneelin automaattisesti.
3. Aktivoi haluamasi profiili ja varmista, että mallivalitsin näyttää oikean mallin ja taustajärjestelmän.

## 4. Uudistettu käyttöliittymä pähkinänkuoressa
- **Komento-yläpalkki:** Näet reaaliaikaisen API-pingin, mallivalitsimen sekä pikanapit profiilien hallintaan, asetuksiin ja keskustelun tyhjentämiseen.
- **Tilakortit:** Ammattimaiset kortit tiivistävät aktiivisen profiilin, mallimoottorin, viestien kokonaismäärän sekä viimeisimmän vastausajan.
- **Reaaliaikainen keskustelualue:** Premium-tyylinen tekstialue korostaa käyttäjän ja avustajan panokset selkeästi erotetuilla väreillä ja erottimilla.
- **Tilabadge:** Yläreunassa sijaitseva badge vaihtaa väriä sen mukaan, onko JugiAI työn touhussa vai valmiustilassa.
- **Liitetiedostopaneeli:** Liitetyt tiedostot näkyvät moderneina chipeinä, jotka voit poistaa yhdellä klikkauksella.

## 5. Profiilit ja asetukset
- **Profiilit (Profiilit-nappi):** Luo erillisiä mallikokoonpanoja eri käyttötarkoituksiin. Voit tallentaa lämpötilan, `top_p`-arvon, rangaistukset ja jopa taustajärjestelmän (OpenAI vs. paikallinen).
- **Asetukset (Asetukset ⚙):**
  - **Yleiset:** System-prompt, luovuussäätimet, maksimimääritys.
  - **OpenAI:** API-avain ja mallivalinnat.
  - **Paikallinen:** Lataa gguf-malli ja määritä säikeiden lukumäärä paikallista ajoa varten.
  - **Ulkoasu:** Hallitse taustakuvaa, läpinäkyvyyttä, fonttikokoa ja taustan alasnäytteen parametreja.
- Muista painaa **“Tallenna muutokset”**, jotta päivitykset kirjautuvat `config.json`-tiedostoon ja näkyvät käyttöliittymässä.

## 6. Liitteet ja historian hallinta
- **Liitteiden lisääminen:** Paina `📎 Liitä tiedosto` ja valitse yksi tai useampi tiedosto. Suuret liitteet (>4 Mt) varmistetaan ennen lisäämistä.
- **Poistaminen:** Sulje liite-chip painikkeesta ✕.
- **Historia:** `Tyhjennä`-pikanappi pyyhkii keskustelun ja päivittää mittarit. Historia tallentuu `history.json`-tiedostoon automaattisesti jokaisen viestin jälkeen.

## 7. Paikallinen LLM (valinnainen)
1. Aja `install.bat` uudelleen tai asenna manuaalisesti `llama-cpp-python` samaan Python-ympäristöön.
2. Avaa Asetukset → *Paikallinen* ja valitse `.gguf`-malli.
3. Vaihda taustajärjestelmäksi **local** ja määritä tarvittaessa säikeiden lukumäärä.
4. Tallenna ja testaa keskustelu – tilakortti päivittää mallimoottori-tekstin esimerkiksi muotoon `Paikallinen · llama-7b.gguf`.

## 8. Vianmääritys
| Ongelma | Ratkaisu |
| --- | --- |
| `Python 3 ei löytynyt` | Asenna Python ja varmista, että se löytyy `PATH`-ympäristömuuttujasta tai syötä polku asennusohjelman pyytäessä. |
| `API-avain puuttuu` | Syötä avain `install.bat`-skriptiin tai JugiAI:n asetuksissa. Ilman avainta OpenAI-taustajärjestelmä ei toimi. |
| `llama-cpp-python`-asennus epäonnistuu | Varmista, että Visual C++ -ajonaikaiset kirjastot ovat asennettuna ja että käytät 64-bittistä Pythonia. |
| Käyttöliittymä näyttää vääriltä | Poista mahdolliset mukautetut taustakuvat asetuksista tai palauta oletus (`install.bat` → asetus `K` taustalle). |

## 9. Päivitysstrategia
- **Konfiguraatiot:** Voit ajaa `install.bat`-skriptin uudelleen turvallisesti – se kysyy uudet arvot ja korvaa `config.json`:n.
- **Sovelluskoodi:** Vedä uusin versio Gitistä ja suorita `install.bat`, jos konfiguraatiot muuttuvat.
- **Varmuuskopiot:** Tallenna `config.json` ja `history.json` ennen isompia päivityksiä, jotta voit palata aiempaan tilaan tarvittaessa.

## 10. Usein kysytyt kysymykset
- **Voinko käyttää useita API-avaimia?** Voit luoda erillisiä profiileja ja vaihtaa avainta profiilien välillä.
- **Missä logot sijaitsevat?** `logo.png` toimii työpöytäkuvakkeena – voit luoda pikakuvakkeita osoittamaan `start_jugiai.bat`-skriptiin.
- **Miten päivitän mallilistat?** Lisää uusia arvoja `config.json`-tiedoston `model_options`-taulukkoon tai hallitse profiilien kautta.

---

**AnomFIN | JugiAI Command Deck** – Luo kilpailuetua hallitulla, visuaalisesti viimeistellyllä tekoälykeskuksella.

— AnomFIN
