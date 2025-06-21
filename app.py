import requests, datetime, json

people = {}
conversations = {}
unknownIds = []

def addUnknownId(uid):
    if uid and not uid in unknownIds:
        unknownIds.append(uid)

print("Enter the value of your .ROBLOSECURITY cookie")
print("Get this from your browser -- look up online how to if you don't know how")
cookie = input("> ")

session = requests.Session()
session.cookies.set(".ROBLOSECURITY", cookie)

print("fetching conversations...", flush=True, end="")

next_cursor = ""
while True:
    resp_json = session.get(f"https://apis.roblox.com/platform-chat-api/v1/get-user-conversations?cursor={next_cursor}").json()
    next_cursor = resp_json['next_cursor']

    if not next_cursor:
        break
    
    for convo in resp_json['conversations']:
        if not convo['id']:
            continue

        conversations[convo['id']] = convo

# print(conversations)

# conversations = dict(sorted(conversations.items())) #sorted(conversations)

print(f" done! (got {len(conversations)} conversations)", flush=True)

for convoId in conversations.copy():
    convo = conversations[convoId]
    print(f"fetching chat history for conversation {convoId} ({convo['name']})...", flush=True, end="")

    messages = []

    next_cursor = ""
    while True:
        resp_json = session.get(f"https://apis.roblox.com/platform-chat-api/v1/get-conversation-messages?conversation_id={convo['id']}&cursor={next_cursor}").json()
        next_cursor = resp_json['next_cursor']

        if not next_cursor:
            break

        messages += resp_json['messages']

    count = len(messages)
    if count == 0:
        del conversations[convoId]
    else:
        convo['messages'] = messages

        addUnknownId(convo['created_by'])

        for uid in convo['participant_user_ids']:
            addUnknownId(uid)

        for message in messages:
            addUnknownId(message['sender_user_id'])


    print(f" done! (got {count} messages)", flush=True)    

print("resolving people...", flush=True, end="")
for unknownId in unknownIds:
    if not unknownId in people:
        resp_json = session.get(f"https://users.roblox.com/v1/users/{unknownId}").json()
        people[unknownId] = resp_json

resp_json = session.get("https://users.roblox.com/v1/users/authenticated").json()
print(" done!", flush=True)

# correct data -- this was all originally written in 2023 but 
# some things have changed since then

for userId in people:
    people[userId]['targetId'] = people[userId]['id']

    del people[userId]['description']
    del people[userId]['created']
    del people[userId]['isBanned']
    del people[userId]['externalAppDisplayName']
    del people[userId]['id']

for convoId in conversations:
    conversations[convoId]['title'] = conversations[convoId]['name']

    del conversations[convoId]['name']

    for message in conversations[convoId]['messages']:
        message['senderTargetId'] = message['sender_user_id']
        message['sent'] = message['created_at']

        if not message['senderTargetId']:
            message['senderTargetId'] = 0

        del message['sender_user_id']
        del message['created_at']

people["0"] = {
    "hasVerifiedBadge": False,
    "name": "Roblox", 
    "displayName": "Roblox", 
    "targetId": 0
}

filename = f"roblox-chat-archive-{resp_json['id']}-{resp_json['name']}-{datetime.datetime.now().strftime('%d-%m-%Y-%H-%M-%S')}.json"

with open(filename, "w") as file:
    json.dump({
        "userId": resp_json['id'],
        "people": people,
        "conversations": conversations
    }, file, indent=4)

print(f"saved to {filename}")