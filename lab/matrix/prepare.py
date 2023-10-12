# def fetch_from_matrix():
#     client = AsyncClient("https://matrix.org", os.environ["MATRIXUSER"])

#     async def iterate():
#         await client.login(os.environ["MATRIXPASSWORD"])

#         room_id = "!apmkrFyPwFRRvQgtEw:gitter.im"

#         # Initialize pagination
#         start_token = "$NQ04ubhtjsFD-pKKa4EX3uHm63K1afauqWpbTes_F0w"
#         while True:
#             try:
#                 response = await client.room_messages(
#                     room_id, limit=10, start=start_token
#                 )
#                 print(response)
#                 if not response or not response.get("chunk"):
#                     break

#                 for event in response["chunk"]:
#                     if event["type"] == "m.room.message":
#                         content = event["content"]
#                         sender = event["sender"]
#                         message_body = content["body"]

#                         print(f"Message from {sender}: {message_body}")

#                 # Get the token for the next page of events
#                 start_token = response.get("end")
#                 if not start_token:
#                     break

#             except Exception as e:
#                 logging.error(e)
#                 break

#         await client.sync_forever(timeout=30000, full_state=True)

#     asyncio.run(iterate())
