import CHApproverBot

for log in CHApproverBot.praw.models.util.stream_generator(CHApproverBot.SUBREDDIT.mod.log, attribute_name = "id"):
    print(log.id)
    CHApproverBot.blacklist(log.id)

# for comment in CHApproverBot.SUBREDDIT.comments():
#     print(comment.id)
#     CHApproverBot.blacklist(comment.id)

# for submission in CHApproverBot.SUBREDDIT.new():
#     print(submission.id)
#     CHApproverBot.blacklist(submission.id)

# for flair in CHApproverBot.REDDIT.subreddit("comedyheaven").flair(limit = None):
#     if flair["flair_text"] == ':approved: Approved user':
#         redditor = str(flair["user"])
#         print(redditor)
#         CHApproverBot.append_approved(redditor)

