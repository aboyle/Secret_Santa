import os
from os import path
import random
import datetime
import time
import re
from slack import RTMClient
from slack.errors import SlackApiError

# Assign bot user name
BOT_NAME = 'sclaus'
BOT_ID = ''
BOT_CHANNEL = ''

# Family user name mapping
userName = {
}

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "commands"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

@RTMClient.run_on(event='message')
def parse_bot_commands(**payload):
    data = payload['data']
    web_client = payload['web_client']
    rtm_client = payload['rtm_client']

    if 'text' in data:
      mention, text = parse_direct_mention(data['text'])
      if mention == BOT_ID:
        print(mention, text)
        handle_command(web_client, text, data['channel'], data['user'])



def send_direct_message(web_client, channel_id, message_text):
    try:
      response = web_client.chat_postMessage(
        channel = channel_id,
        username="sclaus",
        icon_emoji=":santa:",
        text=message_text
#        thread_ts = thread_ts
      )
    except SlackApiError as e:
      assert e.response["ok"] is False
      assert e.response["error"]
      print(f"Got an error: {e.response['error']}")
    return



def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)



def handle_command(web_client, command, cmd_channel, cmd_user):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*.".format(EXAMPLE_COMMAND)

    # Finds and executes the given command, filling in response
    response = default_response

    # This is where you start to implement more commands!
    if command.startswith("commands"):
        response = "SClaus commands: commands, generate (generates a new list), santee (messages a reminder of your santee)";
    elif command.startswith("generate"):
        response = generate_secret_santa(web_client)
    elif command.startswith("santee"):
        response = message_santee(web_client, cmd_channel, cmd_user)
    elif command.startswith("reannounce"):
        response = reannounce_secret_santa(web_client)

    # Sends the response back to the channel
    send_direct_message(web_client, cmd_channel, response)



def generate_secret_santa(web_client):
    #get the year
    now = datetime.datetime.now()
    lastYearFile = "SS_" + str(now.year-1) + ".txt"
    thisYearFile = "SS_" + str(now.year) + ".txt"

    # Check to see if the file already exists for this year
    # indicating that the list has already been generated
    if(path.exists(thisYearFile)):
        text="Secret Santa list for " + str(now.year) + " has already been generated"
        send_direct_message(web_client, BOT_CHANNEL, text)
        return

    #Announce to slack channel that we are generating a list
    text="Generating the Secret Santa list for " + str(now.year) + "!!!"
    send_direct_message(web_client, BOT_CHANNEL, text)

    text="I am building a list that prevents you from matching with your spouse or your giftee from last year..."
    send_direct_message(web_client, BOT_CHANNEL, text)

    # Get ordered list
    f = {}
    for i, line in enumerate(open("SS_people", "r").readlines()):
        family = line.strip().split(" ")
        f.update({p: i for p in family})

    santas = list(f.keys())

    #prevent same match as last year
    ly = {}
    for i, line in enumerate(open(lastYearFile, "r").readlines()):
        lastSS = line.strip().split(" ")
        ly.update({lastSS[0]: lastSS[1]})

    while True:
        random.shuffle(santas)
        assignments = {a: b for a,b in zip(santas, santas[1:] + [santas[0]])}
        if all([f[a] != f[b] for a,b in assignments.items()]):
            if all([b != ly[a] for a,b in assignments.items()]):
                break


    #save this for next year
    out = open(thisYearFile, "w")
    for a, b in assignments.items():
        out.write("{} {}\n".format(a, b))
    out.close()

    announce_all(web_client, thisYearFile)
    text="DONE! Please check your private messages from me to get your new Santee!"
    send_direct_message(web_client, BOT_CHANNEL, text)
    text="If you don't get a message, please let me know here!"
    send_direct_message(web_client, BOT_CHANNEL, text)



def announce_all(web_client, thisYearFile):
    api_call = web_client.users_list()
    users = api_call["members"]
    user_names = list(map(lambda u: u["name"], users))
    user_map = {user["name"]:user["id"] for user in users}
    for user in user_names:
        send_user_santee(web_client, user_map[user], thisYearFile)
    return


def reannounce_secret_santa(web_client):
    #get the year
    now = datetime.datetime.now()
    thisYearFile = "SS_" + str(now.year) + ".txt"

    # Check to see if the file already exists for this year
    # indicating that the list has already been generated
    if(not path.exists(thisYearFile)):
        text="Secret Santa list for " + str(now.year) + " has not yet been generated"
        send_direct_message(web_client, BOT_CHANNEL, text)
        return

    #Announce to slack channel that we are generating a list
    text="Re-announcing the Secret Santa list for " + str(now.year) + "!!!"
    send_direct_message(web_client, BOT_CHANNEL, text)
    text="At any point you can send the command @sclaus santee to have me pm you your match."
    send_direct_message(web_client, BOT_CHANNEL, text)

    announce_all(web_client, thisYearFile)
    text="DONE! Please check your private messages from me to get your new Santee!"
    send_direct_message(web_client, BOT_CHANNEL, text)
    text="If you don't get a message, please let me know here!"
    send_direct_message(web_client, BOT_CHANNEL, text)



def message_santee(web_client, cmd_channel, cmd_user):
    #get the year
    now = datetime.datetime.now()
    thisYearFile = "SS_" + str(now.year) + ".txt"
    # Check to see if the file already exists for this year
    # indicating that the list has already been generated
    if(not path.exists(thisYearFile)):
        text="Secret Santa list for " + str(now.year) + " has not yet been generated"
        send_direct_message(web_client, cmd_channel, text)
        return

    return send_user_santee(web_client, cmd_user, thisYearFile)



def send_user_santee(web_client, cmd_user, file):
    assignments = {}
    with open(file) as f:
        for line in f:
            (key, val) = line.split()
            assignments[userName[key]] = val
    f.close()

    print("Request:", cmd_user)

    api_call = web_client.users_list()
    users = api_call["members"]
    user_map = {user["id"]:user["name"] for user in users}

    # retrieve all users so we can find our bot
    user = user_map[cmd_user]
    if user in assignments.keys():
        print("Bot ID for '" + user + "' is " + cmd_user)
        print("Selection for " + user + " is " + assignments[user])

        giftee = assignments[user]

        text="This year you will be getting a gift for: " + giftee
        response = web_client.conversations_open(users=[cmd_user])
        conversation_id = response['channel']['id']
        send_direct_message(web_client, conversation_id, text)
    time.sleep(5)
    return



# Instantiate Slack Client
rtm_client = RTMClient(token="******************")
rtm_client.start()
