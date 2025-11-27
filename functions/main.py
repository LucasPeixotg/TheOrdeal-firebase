# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import firestore_fn
from firebase_functions.options import set_global_options
from google.cloud import firestore
from firebase_admin import initialize_app, messaging

# For cost control, you can set the maximum number of containers that can be
# running at the same time. This helps mitigate the impact of unexpected
# traffic spikes by instead downgrading performance. This limit is a per-function
# limit. You can override the limit for each function using the max_instances
# parameter in the decorator, e.g. @https_fn.on_request(max_instances=5).
set_global_options(max_instances=10)

initialize_app()
#
#
# @https_fn.on_request()
# def on_request_example(req: https_fn.Request) -> https_fn.Response:
#     return https_fn.Response("Hello world!")

db = firestore.Client()

@firestore_fn.on_document_created(document="campaigns/{campaignId}/quests/{questId}")
def notify_new_quest(event: firestore_fn.Event[firestore_fn.DocumentSnapshot]) -> None:
    campaign_id = event.params['campaignId']
    quest_id = event.params['questId']
    # Add your notification logic here

    quest_snapshot = event.data  # DocumentSnapshot
    quest_data = quest_snapshot.to_dict()
    print("Quest data:", quest_data)

    members_ref = db.collection("campaigns").document(campaign_id).collection("members")
    members = members_ref.stream()


    member_docs = []
    fcm_tokens = []

    for m in members:
        data = m.to_dict()
        member_docs.append(data)

        user_id = data.get("userId")
        user_doc = db.collection("users").document(user_id).get()

        if user_doc.exists:
            user_data = user_doc.to_dict()

            # 3. Extract the token from user doc
            token = user_data.get("fcmToken") or user_data.get("notificationToken")

            if token:
                fcm_tokens.append(token)
        else:
            print(f"User {user_id} not found in /users")


    print("Members:", member_docs)
    print("Tokens:", fcm_tokens)

    if fcm_tokens:
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title="Nova missão!",
                body=f"{quest_data.get('title', '')} foi adicionada!",
            ),
            tokens=fcm_tokens,
        )

        response = messaging.send_each_for_multicast(message)

        if response.failure_count > 0:
            failed_tokens = [
                fcm_tokens[idx]
                for idx, resp in enumerate(response.responses)
                if not resp.success
            ]
            print("Tokens that caused failure:", failed_tokens)

    print(f"New quest created in campaign {campaign_id} with ID {quest_id}")
