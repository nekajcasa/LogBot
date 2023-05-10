from datetime import date
from datetime import time
import datetime
import GSDB
import secret


def handle_response(message, debug=False):
    """Funkcija vzame sporočilo in ga pretvori v male tiskane... pretvorba sporočila se izpiše ti"""
    p_message = message.lower()

    if debug:
        # izpis za namene analize kode
        print(f"Prejteo sporocilo: {message} => {p_message}")

    return p_message


def sestevanje_ure(ura1, dodatek):
    """funkcija sešteje uro v pričakovanem formatu ##:##+##:##"""
    # delitev na ure in minute
    ura0 = int(ura1.split(":")[0])
    min0 = int(ura1.split(":")[1])

    ura1 = int(dodatek.split(":")[0])
    min1 = int(dodatek.split(":")[1])

    # prevrjanje če je pravilen zapis minut, za ure se mi ne zdi potrebno
    if min0 >= 60 or min1 >= 60:
        print("Napaka! v uri je 60 min")
        return

    # seštevanje
    res_min = min0 + min1

    if res_min / 60 >= 1:
        res_ura = ura0 + ura1 + 1
        res_min = res_min % 60
    else:
        res_ura = ura0 + ura1
        res_min = res_min % 60

    # vračanje v pričakovanem formatu
    if res_min == 0:
        ura_res = str(res_ura) + ":00"
    else:
        ura_res = str(res_ura) + ":" + str(res_min)

    return ura_res


def prpravi_format_ure(ura, minute=False):
    """funkcija popravi format ure #### v ##:##, če minute=True se popravi ##->00:##,
    drugače ##->##:00"""

    if len(ura) < 3:
        if minute:
            ura = "00:" + ura
        else:
            ura += ":00"
    else:
        ura = ura[:-2] + ":" + ura[-2:]
    return ura


def prevajalnik(message):
    """V prevajlnik pride string iz katerega se prebere začetek in konec treninga"""
    # odstranjevanje znakov
    message = message[1:]
    message = message.replace(" ", "")
    message = message.replace(".", ":")

    # preverjanje načina zapira in standardizacija
    if "-" not in message:
        if "za" not in message:
            if ":" not in message:
                message = prpravi_format_ure(message)
            message = message + "-" + sestevanje_ure(message, "2:00")
        else:
            ms = message.split("za")
            ura_prihoda = ms[0]
            trajanje = ms[1]
            if ":" not in ura_prihoda:
                ura_prihoda = prpravi_format_ure(ura_prihoda)
            if ":" not in trajanje:
                trajanje = prpravi_format_ure(trajanje, minute=True)
            message = ura_prihoda + "-" + sestevanje_ure(ura_prihoda, trajanje)
    else:
        ms = message.split("-")
        prihod = ms[0]
        oddhod = ms[1]

        if ":" not in prihod:
            prihod = prpravi_format_ure(prihod)
        if ":" not in oddhod:
            oddhod = prpravi_format_ure(oddhod)
        message = prihod + "-" + oddhod

    return message


def preveri_format_termina(termin):
    """funkcija preveri če je termin pravilnega formata ##:##-##:##, kjer nobena
    ura ne presega 23 in nobene minute ne presegajo 59, prihod mora biti za odhodom"""
    ts = termin.split("-")
    prihod = ts[0]
    odhod = ts[1]

    ura_prihod = int(prihod.split(":")[0])
    min_prihod = int(prihod.split(":")[1])
    ura_odhod = int(odhod.split(":")[0])
    min_odhod = int(odhod.split(":")[0])

    ure = ura_prihod < 23 and ura_odhod < 23
    minute = min_prihod < 59 and min_odhod < 59
    sledenje = ura_prihod < ura_odhod or (ura_prihod == ura_odhod and min_prihod < min_odhod)

    if ure and minute and sledenje:
        return True
    else:
        return False


def overlap(E1, E2):
    """Funkcija preveri ali pride do prekrivanja treminov, če pride do prekrivanja vrne tudi vrsto,
    glej komentarje E1 in E2 predstavljata čas zasedenosti skupin 1 in 2. Čas kdaj je zasedeno je
    simboliziran z -- """
    if E1.odhod == E2.prihod:
        # E1  ----
        # E2      ----
        # R   --------
        return "T0"
    elif E1.prihod == E2.odhod:
        # E1      ----
        # E2  ----
        # R   --------
        return "T1"
    elif E1.prihod < E2.prihod and E1.odhod > E2.odhod:
        # E1  -------
        # E2   ----
        # R   -------
        return "T2"
    elif E2.prihod < E1.prihod and E2.odhod > E1.odhod:
        # E1    ---
        # E2  -------
        # R   -------
        return "T3"
    else:
        if E1.prihod < E2.prihod:
            # skupina 1 pred s2
            if E1.odhod > E2.prihod:
                # E1    ----
                # E2      ----
                # R     ------
                return "T4"
            else:
                # E1  ---
                # E2       ----
                # R   ---  ----
                return "F"
        else:
            # s2 pred s1
            if E2.odhod > E1.prihod:
                # skupina 2 je odšla za prihodom S1
                # E1       ----
                # E2    ----
                # R     -------
                return "T5"
            else:
                # skupina 1 je prišla za odhodom S2
                # E1        ---
                # E2   ---
                # R    ---  ---
                return "F"


def sort_events(events):
    """funkcija razvrsti dogodke od tistega ki se je pričel najprej do tistega ki se je
    pričel najkasneje"""
    začetki = []
    for i in events:
        začetki.append(i.prihod)
    events_sorted = [x for _, x in sorted(zip(začetki, events))]

    return events_sorted


def združevanje_terminov(events, debug=False):
    """funkcija kot argument vzame events, ki je seznam dogodkov razreda Event za pretekli dan"""
    over = "T"

    stev = 0
    while over[0] == "T":
        stev += 1
        overlap_najden = False
        if len(events)==1:
            break
        for i in range(len(events)):
            for j in range(len(events)):
                if j > i:
                    T1 = events[i]
                    T2 = events[j]
                    over = overlap(T1, T2)

                    if debug:
                        # izpis za namene analize kode
                        print(f"T{i}: {T1.prihod}-{T1.odhod}")
                        print(f"T{j}: {T2.prihod}-{T2.odhod}")
                        print(over)

                    # če se dogodka prkrivata ju združi
                    if over[0] == "T":
                        if over[1] == "0":
                            zdruzen_termin = Event(T1.prihod, T2.odhod, "Skupinsko")
                        elif over[1] == "1":
                            zdruzen_termin = Event(T2.prihod, T1.odhod, "Skupinsko")
                        elif over[1] == "2":
                            zdruzen_termin = Event(T1.prihod, T1.odhod, "Skupinsko")
                        elif over[1] == "3":
                            zdruzen_termin = Event(T2.prihod, T2.odhod, "Skupinsko")
                        elif over[1] == "4":
                            zdruzen_termin = Event(T1.prihod, T2.odhod, "Skupinsko")
                        else:
                            zdruzen_termin = Event(T2.prihod, T1.odhod, "Skupinsko")

                        if debug:
                            # izpis za namene analize kode
                            print(zdruzen_termin.prihod, zdruzen_termin.odhod)
                            print()

                        # Odstranjevanje uporabljenih
                        events.remove(T1)
                        events.remove(T2)
                        # dodajanje združenega array
                        events.append(zdruzen_termin)
                        overlap_najden = True

                if overlap_najden:
                    break
            if overlap_najden:
                break

    if debug:
        # izpis za namene analize kode
        print(f"Problem rešen v {stev} korakih.")

    events_sorted = sort_events(events)

    return events_sorted


def help():
    """Funkcija vrne string z navodili za uporabo robota"""
    navodila = """ `Navodila za uporabo:
    Veljavni zapisi:
    -> '+15' - rezervira se termin ob 15 za 2h
    -> '+1500' ali '+15:00' ali '+15.00' - rezervira se termin ob 15:00 za 2h
    -> '+15-16' - rezervira se termin  od 15 do 16
    -> '+1500-1600' (lahko tudi s : ali .) - rezervira se termin  od 15 do 16
    -> '+15za45' ali '+15za145' ob 15 za 45min ali 1h45min
    -> '+1500za130' - (lahko tudi s : ali .) od 15 do 16:30
    -> '!Me ne bo' - odstrani se zadnji dodani termin (v dnevu)

    Če imaš težave kontaktiraj admina.`"""
    return navodila


def odstrani_termin(message, user, dan):
    """Funkcija vrne napis da je termin uspešno odstranjen"""
    #!odstranjevanje termina
    termin_odstranjen = False

    for i in dan.events[::-1]:
        if i.oseba == user:
            dan.events.remove(i)
            termin_odstranjen = True
            break

    if termin_odstranjen:
        response = f"Termin od {str(i.prihod)[:-3]} do {str(i.odhod)[:-3]} je odstranjen!"
        return dan, response
    else:
        response = f"Napaka: {user} danes nima zabeleženega nobenega termina!"
        return dan, response


def rezerviraj_termin(message, user, dan, debug=False):
    """Funkcija poiskuša rezervirati termin in vrne poročilo """
    try:
        # prevajanje termina v splošno kodo
        termin = prevajalnik(message)
        if debug:
            # izpis za namene analize kode
            print(termin)

        # preverjanje zapisa termina
        if (termin):
            termin = termin.split("-")

            ps = termin[0].split(":")
            os = termin[1].split(":")

            prihod = time(int(ps[0]), int(ps[1]), 0, 0)
            odhod = time(int(os[0]), int(os[1]), 0, 0)

            # dodanjanje termina dnevu
            dan.events.append(Event(prihod, odhod, user))

            response = f"Dodan termin od {termin[0]} do {termin[1]}."
        else:
            response = "Napačen vnos, napiši '!help' za pomoč ali kontaktiraj admina."
    except:
        response = "Napačen vnos, napiši '!help' za pomoč ali kontaktiraj admina."

    return dan, response


def test():
    ukazi = ["+15",
             "+8",
             "+6:20",
             "+1500",
             "+15:00",
             "+15.00",
             "+15-16",
             "+1500-1600",
             "+15.00-16.00",
             "+15:00-16:00",
             "+15za45",
             "+15za145",
             "+1500za30",
             "+15:20za20",
             "+15:15za1:30"]

    for i in ukazi:
        termin = prevajalnik(i)
        print(f"{i} \t--> {termin}, \t {preveri_format_termina(termin)}")


class Dan:
    def __init__(self, datum):
        self.datum = datum
        self.events = []
        self.uporaba = []

    def zaključi_dan(self, zdruzeni_dogodki):
        """Funkcija zaključi dan tako da zapiše dogodke v tabeleo, če je konec meseca naredi
        novo tabelo in pošlje staro tabelo mail_listi"""

        db = GSDB.DB("gs_credentials.json")

        if self.datum.day == 1:
            print("pošiljanje stare tabele")
            zadnji_ID = db.get_values(secret.Main_sheet_ID(), "B1:B1000")["values"][-1][0]

            for mail in secret.mail_list():
                print(f"Mail poslan na {mail}.")
                db.add_premission(zadnji_ID, mail)

            print("nov mesec")
            # kreiranje nove tebele
            date_new_month = str(self.datum.year) + "-" + str(self.datum.month)
            id_new_month, link_new_month = db.create(date_new_month)

            #Za normaln delovoanje
            db.append_values(secret.Main_sheet_ID(), "A1:A1000", "USER_ENTERED", [[date_new_month, id_new_month, link_new_month]])
            # Samo za testiranje
            #id_new_month = secret.test_sheet_ID()
            
            # Urejanje tebele
            db.update_values(id_new_month, "A1", "USER_ENTERED",
                             [['Vsa uporaba']])
            db.mrge_cells(id_new_month, 0, 4, 0, 1)
            db.update_values(id_new_month, "E1", "USER_ENTERED",
                             [['Po dnevih']])
            db.mrge_cells(id_new_month, 4, 6, 0, 1)
            db.update_values(id_new_month, "A2:F2", "USER_ENTERED",
                             [['Dan', 'do', 'do', 'Čas', 'Dan', 'Čas']])          
            db.update_values(id_new_month, "G1", "USER_ENTERED",
                             [['Skupno']])
            db.update_values(id_new_month, "G2", "USER_ENTERED",
                             [['=sum(F3:F100)']])
            db.format_cell_time(id_new_month,  6, 7, 1, 2)            
            
            

        zadnji_ID = db.get_values(secret.Main_sheet_ID(), "B1:B1000")["values"][-1][0]

        print()
        if len(zdruzeni_dogodki) > 0:
            print(f"Poročilo za {self.datum}:")

            skupni_cas = datetime.timedelta(0)
            i = 0
            for dogodek in zdruzeni_dogodki:
                i += 1
                prihod = dogodek.prihod
                odhod = dogodek.odhod
                t1 = datetime.datetime(self.datum.year, self.datum.month, self.datum.day, prihod.hour, prihod.minute)
                t2 = datetime.datetime(self.datum.year, self.datum.month, self.datum.day, odhod.hour, odhod.minute)

                cas = t2 - t1
                skupni_cas += cas
                print(f"ZT {i+1}: {prihod} do {odhod}")

                zadnja_vrstica_A = len(db.get_values(zadnji_ID, "A1:A1000")["values"])
                db.update_values(zadnji_ID, f"A{zadnja_vrstica_A+1}:D{zadnja_vrstica_A+1}", "USER_ENTERED", [[str(self.datum), str(prihod), str(odhod), str(cas)]])

            zadnja_vrstica_E = len(db.get_values(zadnji_ID, "E1:E1000")["values"])
            db.append_values(zadnji_ID, f"E{zadnja_vrstica_E+1}:F{zadnja_vrstica_E+1}", "USER_ENTERED", [[str(self.datum), str(skupni_cas)]])


class Event:
    def __init__(self, prihod, odhod, oseba):
        self.prihod = prihod
        self.odhod = odhod
        self.oseba = oseba
        #difference = self.prihod - self.odhod
        #self.cas = difference


# simulacija
def simulacija_disc(inputi, dnevi, user="User1"):
    """Funkcija namenja testiranju kode v terminalu... kjer se izpise BOT:, pomeni da se to vrne v discord,
    drugače je izpis v terminal"""

    for d in range(len(dnevi)):
        danes = Dan(dnevi[d])
        print(f"DAN  {danes.datum}")
        for sporočilo in inputi[d]:
            if sporočilo != "d":
                print(f"{user}: {sporočilo}")
            sporočilo = handle_response(sporočilo)
            začetek = sporočilo[0]

            if sporočilo == "d":
                # konec dneva, v pravi kodi se proži preko preverjanja ure
                # združevanje terminov ki se prekviajo
                zdruzeni_dogodki = združevanje_terminov(danes.events,debug=True)

                danes.zaključi_dan(zdruzeni_dogodki)

                break

            if začetek == "+":
                danes, resp = rezerviraj_termin(sporočilo, user, danes)
                print("BOT: " + resp)

            if sporočilo.replace(" ", "") == "!menebo":
                danes, resp = odstrani_termin(sporočilo, user, danes)
                print("BOT: " + resp)

            elif sporočilo == "!help":
                print(help())
        print("___________________________________________")


if __name__ == "__main__":
    print(secret.mail_list())
    leto = 2023
    mesec = 6

    # vnosi po simuliranih dnevih
    inputi = [["+15", "+16:15", "+13:45-15", "+16", "d"],
              ["+10", "+8", "+15:00", "+16za30", "d"],
              ["+10", "+8", "!Me ne bo", "+15.00", "+16-17", "d"],
              ["+15za30", "+16:00-18", "d"],
              ["+15za145", "+9za30", "+16za30", "d"],
              ["+10", "+10-10:33", "+15:00", "+16za90", "d"]]
    # simulirani dnevi
    dnevi = [date(leto, mesec, 27),
             date(leto, mesec, 28),
             date(leto, mesec, 29),
             date(leto, mesec, 30),
             date(leto, mesec + 1, 1),
             date(leto, mesec + 1, 2)]

    simulacija_disc(inputi, dnevi)
