import os
import random
import datetime
from slackclient import SlackClient

BOT_NAME = 'primaryuser'

slack_client = SlackClient("apikeyhere")

userName = {
	#users
}

startYear = 2018

if __name__ == "__main__":
    #get the year
    now = datetime.datetime.now()
    lastYearFile = "SS_" + str(now.year-1) + ".txt"
    thisYearFile = "SS_" + str(now.year) + ".txt"

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

    #prevent same match as last eyar
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

    #Now talk to slack
    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        # retrieve all users so we can find our bot
        users = api_call.get('members')
        for user in users:
            for BOT_NAME in assignments:
                if 'name' in user and user.get('name') == userName[BOT_NAME]:
                    print("Bot ID for '" + user['name'] + "' is " + user.get('id'))
#                    print("Selection for " + BOT_NAME + " is " + assignments[BOT_NAME])
                    giftee = assignments[BOT_NAME]

                    slack_client.api_call(
                        "chat.postMessage",
                        channel=user.get('id'),
                        username="sclaus",
                        icon_emoji=":santa:",
                        as_user="U2U1F7M8C",
                        text="Welcome to Secret Santa! I have generated a match for you!"
                    )

                    slack_client.api_call(
                        "chat.postMessage",
                        channel=user.get('id'),
                        username="sclaus",
                        icon_emoji=":santa:",
                        as_user="U2U1F7M8C",
                        text="This year you will be getting a gift for: " + giftee
                    )

    else:
        print("could not find bot user with the name " + BOT_NAME)
