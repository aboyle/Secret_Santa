import os
from os import path
import random
import datetime
import time
import re
from slackclient import SlackClient

# Instantiate Slack Client
slack_client = SlackClient("**********")

# Assign bot user name
BOT_NAME = None
starterbot_id = None

# Family user name mapping
userName = {
}

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "generate"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"], event["user"]
    return None, None, None


def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)


def handle_command(command, cmd_channel, cmd_user):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*.".format(EXAMPLE_COMMAND)

    # Finds and executes the given command, filling in response
    response = None

    # This is where you start to implement more commands!
    if command.startswith("commands"):
        response = "SClaus commands: commands, generate (generates a new list), santee (messages a reminder of your santee)";
    elif command.startswith("generate"):
        response = generate_secret_santa()
    elif command.startswith("santee"):
        response = message_santee(cmd_channel, cmd_user)
    elif command.startswith("reannounce"):
        response = reannounce_secret_santa()

    # Sends the response back to the channel
    if (response):
        slack_client.api_call(
            "chat.postMessage",
            channel=cmd_channel,
            text=response or default_response
        )


def generate_secret_santa():
    #get the year
    now = datetime.datetime.now()
    lastYearFile = "SS_" + str(now.year-1) + ".txt"
    thisYearFile = "SS_" + str(now.year) + ".txt"

    # Check to see if the file already exists for this year
    # indicating that the list has already been generated
    if(path.exists(thisYearFile)):
        slack_client.api_call(
            "chat.postMessage",
            channel="C0HM2MJ3C",
            username="sclaus",
            icon_emoji=":santa:",
            text="Secret Santa list for " + str(now.year) + " has already been generated"
        )
        return

    #Announce to slack channel that we are generating a list
    slack_client.api_call(
        "chat.postMessage",
        channel="C0HM2MJ3C",
        username="sclaus",
        icon_emoji=":santa:",
        text="Generating the Secret Santa list for " + str(now.year) + "!!!"
    )

    slack_client.api_call(
        "chat.postMessage",
        channel="C0HM2MJ3C",
        username="sclaus",
        icon_emoji=":santa:",
        text="I am building a list that prevents you from matching with your spouse or your giftee from last year..."
    )

    # Get ordered list
    f = {}
    for i, line in enumerate(open("SS_people", "r").readlines()):
        family = line.strip().split(" ")
        f.update({p: i for p in family})

    santas = f.keys()

    #prevent same match as last year
    ly = {}
    for i, line in enumerate(open(lastYearFile, "r").readlines()):
        lastSS = line.strip().split(" ")
        ly.update({lastSS[0]: lastSS[1]})

    while True:
        random.shuffle(santas)
        assignments = {a: b for a,b in zip(santas, santas[1:] + [santas[0]])}
        if all([f[a] != f[b] for a,b in assignments.iteritems()]):
            if all([b != ly[a] for a,b in assignments.iteritems()]):
                break

    #save this for next year
    out = open(thisYearFile, "w")
    for a, b in assignments.iteritems():
        out.write("{} {}\n".format(a, b))

    #Now talk to slack
    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        # retrieve all users so we can find our bot
        users = api_call.get('members')
        for user in users:
            send_user_santee(user.get('id'), thisYearFile)

    slack_client.api_call(
        "chat.postMessage",
        channel="C0HM2MJ3C",
        username="sclaus",
        icon_emoji=":santa:",
        text="DONE! Please check your private messages from me to get your new Santee!"
    )

    slack_client.api_call(
        "chat.postMessage",
        channel="C0HM2MJ3C",
        username="sclaus",
        icon_emoji=":santa:",
        text="If you don't get a message, please let me know here!"
    )


def reannounce_secret_santa():
    #get the year
    now = datetime.datetime.now()
    thisYearFile = "SS_" + str(now.year) + ".txt"

    # Check to see if the file already exists for this year
    # indicating that the list has already been generated
    if(not path.exists(thisYearFile)):
        slack_client.api_call(
            "chat.postMessage",
            channel="C0HM2MJ3C",
            username="sclaus",
            icon_emoji=":santa:",
            text="Secret Santa list for " + str(now.year) + " has not yet been generated"
        )
        return

    #Announce to slack channel that we are generating a list
    slack_client.api_call(
        "chat.postMessage",
        channel="C0HM2MJ3C",
        username="sclaus",
        icon_emoji=":santa:",
        text="Re-announcing the Secret Santa list for " + str(now.year) + "!!!"
    )

    slack_client.api_call(
        "chat.postMessage",
        channel="C0HM2MJ3C",
        username="sclaus",
        icon_emoji=":santa:",
        text="At any point you can send the command @sclaus santee to have me pm you your match."
    )

    #Now talk to slack
    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        # retrieve all users so we can find our bot
        users = api_call.get('members')
        for user in users:
            send_user_santee(user.get('id'), thisYearFile)

    slack_client.api_call(
        "chat.postMessage",
        channel="C0HM2MJ3C",
        username="sclaus",
        icon_emoji=":santa:",
        text="DONE! Please check your private messages from me to get your new Santee!"
    )

    slack_client.api_call(
        "chat.postMessage",
        channel="C0HM2MJ3C",
        username="sclaus",
        icon_emoji=":santa:",
        text="If you don't get a message, please let me know here!"
    )



def message_santee(cmd_channel, cmd_user):
    #get the year
    now = datetime.datetime.now()
    thisYearFile = "SS_" + str(now.year) + ".txt"
    # Check to see if the file already exists for this year
    # indicating that the list has already been generated
    if(not path.exists(thisYearFile)):
        slack_client.api_call(
            "chat.postMessage",
            channel=cmd_channel,
            username="sclaus",
            icon_emoji=":santa:",
            text="Secret Santa list for " + str(now.year) + " has not yet been generated"
        )
        return

    return send_user_santee(cmd_user, thisYearFile)


def send_user_santee(cmd_user, file):
    assignments = {}
    with open(file) as f:
        for line in f:
            (key, val) = line.split()
            assignments[userName[key]] = val

    print("Request: ", cmd_user)

    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        # retrieve all users so we can find our bot
        users = api_call.get('members')
        for user in users:
#            print(user.get('name'), user.get('id'))
            if 'name' in user and user.get('id') == cmd_user and user.get('name') in assignments:
                print("Bot ID for '" + user.get('name') + "' is " + user.get('id'))
                print("Selection for " + user.get('name') + " is " + assignments[user.get('name')])

                giftee = assignments[user.get('name')]

                slack_client.api_call(
                    "chat.postMessage",
                    channel=user.get('id'),
                    username="sclaus",
                    icon_emoji=":santa:",
                    as_user="U2U1F7M8C",
                    text="This year you will be getting a gift for: " + giftee
                )

    else:
        print("could not find bot user with the name " + cmd_user)


# Main function
if __name__ == "__main__":
    if slack_client.rtm_connect():
        print("Secret Santa connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel, user = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel, user)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
