import requests, datetime, json

people = {}
conversations = {}
unknownIds = []

session = requests.Session()
session.cookies.set(".ROBLOSECURITY", input("enter the value of your .roblosecurity cookie: "))

print("fetching conversations...", flush=True, end="")

page = 1
while True:
    resp_json = session.get(f"https://chat.roblox.com/v2/get-user-conversations?pageNumber={page}&pageSize=30").json()

    if len(resp_json) == 0:
        break
    
    for convo in resp_json:
        conversations[convo['id']] = convo
        
    page += 1

conversations = dict(sorted(conversations.items())) #sorted(conversations)

print(f" done! (got {len(conversations)} conversations)", flush=True)

for convoId in conversations.copy():
    convo = conversations[convoId]
    print(f"fetching chat history for conversation {convoId} ({convo['title']})...", flush=True, end="")

    messages = []

    lastMessageId = ""
    while True:
        resp_json = session.get(f"https://chat.roblox.com/v2/get-messages?conversationId={convo['id']}&pageSize=30&exclusiveStartMessageId={lastMessageId}").json()

        if len(resp_json) == 0:
            break

        messages += resp_json

        lastMessageId = resp_json[len(resp_json)-1]['id']

    count = len(messages)
    if count == 0:
        del conversations[convoId]
    else:
        convo['messages'] = messages

        for message in messages:
            if not message['senderTargetId'] in unknownIds:
                unknownIds.append(message['senderTargetId'])

        initiatorId = convo['initiator']['targetId']
        if not initiatorId in people:
            people[initiatorId] = convo['initiator']

        convo['initiator'] = initiatorId

        participants = convo['participants']
        for person in participants:
            personId = person['targetId']
            if not personId in people:
                people[personId] = person

        for person in participants.copy():
            participants.append(person['targetId'])
            participants.remove(person)


    print(f" done! (got {count} messages)", flush=True)    

for unknownId in unknownIds:
    if not unknownId in people:
        resp_json = session.get(f"https://users.roblox.com/v1/users/{unknownId}").json()
        people[unknownId] = resp_json

resp_json = session.get("https://users.roblox.com/v1/users/authenticated").json()

filename = f"roblox-chat-archive-{resp_json['id']}-{resp_json['name']}-{datetime.datetime.now().strftime('%d-%m-%Y-%H-%M-%S')}.json"

with open(filename, "w") as file:
    json.dump({
        "userId": resp_json['id'],
        "people": people,
        "conversations": conversations
    }, file, indent=4)

print(f"saved to {filename}")