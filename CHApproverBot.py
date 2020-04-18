import logging
import praw
import json
import os

logging.basicConfig( 
    format = "[%(asctime)s] %(message)s", 
    level = logging.INFO,
    handlers=[
        logging.FileHandler("approval_log.log"),
        logging.StreamHandler()
    ])

CONFIG_FILE = "config.json"
BLACKLIST_FILE = "approver_blacklist.csv"

with open(CONFIG_FILE, "r") as f:
    CONFIG = json.load(f)

REDDIT = praw.Reddit(**CONFIG["redditapi"])
SUBREDDIT = REDDIT.subreddit(CONFIG["subreddit"])

def blacklist(action_id):
    with open(BLACKLIST_FILE, "a") as f:
        f.write(action_id + "\n")

def action_blacklisted(action_id):
    if not os.path.exists(BLACKLIST_FILE):
        return False

    with open(BLACKLIST_FILE, "r") as f:
        links = f.read().splitlines()
    return action_id in links

def get_mods():
    return [str(i) for i in SUBREDDIT.moderator()] + ["AutoModerator"]

def main():
    while True:
        for log in praw.models.util.stream_generator(SUBREDDIT.mod.log, attribute_name = "id", pause_after=-1):
            if log is None:
                break

            if log.action == "approvelink" and not action_blacklisted(log.id):
                if str(log.mod) != "AutoModerator":
                    blacklist(log.id)
                
                subj = CONFIG["subject"].replace("<>", str(SUBREDDIT))
                submission = REDDIT.submission(url = "https://reddit.com" + log.target_permalink)
                SUBREDDIT.contributor.add(submission.author)

                if str(submission.author) not in get_mods():
                    submission.author.message(
                        subj, 
                        CONFIG["message"].replace("<>", "https://redd.it/" + submission.id), 
                        from_subreddit = SUBREDDIT
                    )

                    for conv in SUBREDDIT.modmail.conversations():
                       if conv.subject.startswith(subj[:23]) or conv.subject == "you are an approved user":
                           conv.archive()

                    SUBREDDIT.flair.set(submission.author, text = ":approved: Approved user", flair_template_id="2b56a12c-7c2f-11ea-9666-0e72ae1d5f77")

                logging.info("Added user /u/%s for the submission https://redd.it/%s" % (submission.author, submission.id))
        
        for comment in SUBREDDIT.stream.comments(pause_after=-1):
            if comment is None:
                break
            
            if "!removeapproved" in comment.body.lower() and comment.author in get_mods() and not action_blacklisted(comment.id):
                blacklist(comment.id)

                try:
                    next(SUBREDDIT.contributor(redditor = comment.submission.author))
                except StopIteration:
                    continue

                SUBREDDIT.contributor.remove(comment.submission.author)
                reply = comment.reply("/u/%s has been removed as an approved submitter from /r/%s for posting '[%s](%s)'. \n\n%s" % (
                    comment.submission.author, str(SUBREDDIT), comment.submission.title, "https://redd.it/" + comment.submission.title, CONFIG["tail"].replace("<>", str(SUBREDDIT))
                ))
                reply.mod.distinguish()
                reply.mod.approve()

                SUBREDDIT.flair.delete(comment.submission.author)

                logging.info("Removed user /u/%s for the submission https://redd.it/%s" % (comment.submission.author, comment.submission.id))


if __name__ == "__main__":
    with open("pid.json", "w") as f:
        json.dump(os.getpid(), f)
    
    logging.info("=== RESTARTED ===")
    main()
