import discord
import responses
from discord.ext import commands

# py datokteka v kateri je definiran token
import keys


async def send_message(message):
  try:
    response = responses.handle_response(str(message.content))
    await message.channel.send(response)
  except Exception as e:
    print(e)


def run_discord_bot():
  intents = discord.Intents.default()
  intents.message_content = True

  client = discord.Client(intents=intents)

  @client.event
  async def on_ready():
    print(f'We have logged in as {client.user}')

  @client.event
  async def on_message(message):
    if message.author == client.user:
      return

    username = str(message.author)
    user_message = str(message.content)
    channel = str(message.channel)
    ima_kluc = False

    print(f"{username} said: {user_message} ({channel})")
    # preverjanje uporabnikovih "roles"
    for i in message.author.roles:
      # preverjanje če ima avtor sporočila ključ
      if str(i) == "🔑":
        ima_kluc = True
        print("Ima kljuc")

    if message.content.startswith("+") and ima_kluc:
      await message.channel.send(responses.rezerviraj_termin(user_message))
    else:
      print("Nima kljuca/napačen poziv")

  client.run(keys.TOKEN())
