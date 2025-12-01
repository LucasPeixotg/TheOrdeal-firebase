# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import firestore_fn
from firebase_functions.options import set_global_options
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

@firestore_fn.on_document_created(document="campaigns/{campaignId}/quests/{questId}")
def notify_new_quest(event: firestore_fn.Event[firestore_fn.DocumentSnapshot]) -> None:
    quest_id = event.params['questId']
    
    quest_snapshot = event.data  # DocumentSnapshot
    quest_data = quest_snapshot.to_dict()

    fcm_tokens = quest_data.get('targetNotificationTokens', [])

    if fcm_tokens:
        print(f"NOTIFYING_NEW_QUEST | ({quest_id}) TOKENS: {fcm_tokens}")
        title = f"{quest_data.get('title','Uma missão te espera!')}"
        quest_type = quest_data.get('type', None)
        if quest_type == 'dice':
            body = "🎲 Rolagem"
        elif quest_type == 'choice':
            body = "✅ Opção"
        elif quest_type == 'textOnly':
            body = "📕 Texto"
        else:
            body = "❓ Surpresa"

        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound="default"
                    )
                )
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
            print("NOTIFYING_NEW_QUEST_FAILURE | TOKENS:", failed_tokens)
