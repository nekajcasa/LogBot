from discord.ext import tasks
import secret
import discord
import responses
from datetime import date
from datetime import time


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # dan vsebuje vse dogodke dneva
        self.danes = responses.Dan(date.today())  # za testiranje date(2023, 4, 26)

    async def setup_hook(self) -> None:
        # start the task to run in the background
        self.my_background_task.start()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    # to se dogaja v ozadju na vskih  600 sekund
    @tasks.loop(seconds=600)
    async def my_background_task(self):
        if self.danes.datum == date.today():
            print("Isti dan")
        else:
            if len(self.danes.events) > 0:
                zdruzeni_dogodki = responses.združevanje_terminov(self.danes.events)
                print("Nov dan-dogodki združeni")
                # če ni isti dan se zpaišejo podatki
            else:
                zdruzeni_dogodki = []
                print("Nov dan-ni bolo dogodkov")

            # zaključek dneva -> zapis v tabelo, če je konec meseca nova tabela in poročilo
            self.danes.zaključi_dan(zdruzeni_dogodki)
            self.danes = responses.Dan(date.today())

    @my_background_task.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in

    # to se zgodi ko se prejeme sporoćilo
    async def on_message(self, message):

        if message.author == client.user:
            return

        username = str(message.author)
        user_message = str(message.content)
        channel = str(message.channel)[:-1]
        ima_kluc = False

        print(f"{username} said: {user_message} ({channel})")

        # preverjanje če je DM
        if isinstance(message.channel, discord.channel.DMChannel):
            sporocilo = responses.handle_response(user_message)
            if sporocilo == "!help":
                resp = responses.help()
            else:
                resp = "Napačen vnos, napiši '!help' za pomoč ali kontaktiraj admina."
            await message.author.send(resp)

        else:
            # preverjanje uporabnikovih "roles"
            for i in message.author.roles:
                # preverjanje če ima avtor sporočila ključ
                if str(i) == "🔑":
                    ima_kluc = True
                    print("Ima kljuc")

            if ima_kluc:
                if channel == "treningi":
                    sporocilo = responses.handle_response(user_message)
                    zacetek = sporocilo[0]

                    # dodajanje termina
                    if zacetek == "+":
                        self.danes, resp = responses.rezerviraj_termin(sporocilo, username, self.danes)
                        if resp[0] == "N":
                            await message.author.send(resp)
                        else:
                            await message.channel.send(resp)

                    # brisanje termina
                    if sporocilo.replace(" ", "") == "!menebo":
                        self.danes, resp = responses.odstrani_termin(sporocilo, username, self.danes)
                        if resp[0] == "N":
                            await message.author.send(resp)
                        else:
                            await message.channel.send(resp)

                    if sporocilo == "data":
                        print()
                        print(f"Poročilo za {self.danes.datum}:")
                        for i in range(len(self.danes.events)):
                            print(f"ZT {i+1}: {self.danes.events[i].prihod} do {self.danes.events[i].odhod}")
                else:
                    resp = "Ukaze za termine se sprejema samo v kanalu 'treningi' !."
                    await message.author.send(resp)


if __name__ == '__main__':

    intents = discord.Intents.default()
    intents.message_content = True
    client = MyClient(intents=intents)
    client.run(secret.TOKEN())
