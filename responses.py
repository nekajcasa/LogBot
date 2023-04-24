def handle_response(message):
  p_message = message.lower()

  print(f"Prejteo sporocilo: {message} => {p_message}")

  if p_message == "!help":
    return " `YOUR MESSAGE IN HERE`"
  else:
    return p_message


def rezerviraj_termin(message):

  return "Označen termin !"
