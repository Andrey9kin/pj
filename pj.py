"""Getting Started Example for Python 2.7+/3.3+"""
from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import os
import sys
import subprocess
import jenkins
import logging
from tempfile import gettempdir
import json
import requests

logging.basicConfig(level=logging.INFO)

jenkins_url = "http://192.168.99.100:8080"
job_name = "polly-test"

logging.info("Connect to Jenkins at {}".format(jenkins_url))

server = jenkins.Jenkins(jenkins_url)

logging.info("Get latest build for the job {}".format(job_name))
last_build_number = server.get_job_info(job_name)['lastCompletedBuild']['number']
build_info = server.get_job_info(job_name, last_build_number)

repo = ""
sha1 = ""

for action in build_info['lastCompletedBuild']['actions']:
    if 'remoteUrls' in action:
        repo = action['remoteUrls'][0]
        sha1 = action['lastBuiltRevision']['SHA1']

if repo == "" and sha1 == "":
    logging.error("Can not get repo and sha1 info for job {}".format(job_name))

logging.info("Jenkins job {} with the build number {} built repo {} sha1 {}".format(job_name, last_build_number, repo, sha1))

github_user = repo.split('/')[-2]
github_repo = (repo.split('/')[-1]).replace('.git','')

logging.info("Extracted github user name - {}".format(github_user))
logging.info("Extracted github repo name - {}".format(github_repo))

r = requests.get("https://api.github.com/repos/{}/{}/git/commits/{}".format(github_user, github_repo, sha1))
response = json.loads(r.text)

github_username = response['author']['name']
github_commit_message = response['message'].split('\n', 1)[0]

logging.info("Extracted github users name - {}".format(github_username))
logging.info("Extracted github commit message - {}".format(github_commit_message))

text = "Message for user {}! Message for user {}! Your commit with sha1 {} and commit message {} broke the build number {} for the job {}. Go and fix it! God dammit!".format(github_username, github_username, sha1[:10], github_commit_message, last_build_number, job_name)

# Create a client using the credentials and region defined in the [adminuser]
# section of the AWS credentials file (~/.aws/credentials).
logging.info("Login...")
session = Session(profile_name="default")
polly = session.client("polly")

try:
    # Request speech synthesis
    logging.info("Request audio for {}".format(text))
    response = polly.synthesize_speech(Text=text,
                                       OutputFormat="mp3",
                                       VoiceId="Joanna")
except (BotoCoreError, ClientError) as error:
    # The service returned an error, exit gracefully
    logging.error(error)
    sys.exit(-1)

# Access the audio stream from the response
if "AudioStream" in response:
    # Note: Closing the stream is important as the service throttles on the
    # number of parallel connections. Here we are using contextlib.closing to
    # ensure the close method of the stream object will be called automatically
    # at the end of the with statement's scope.
    with closing(response["AudioStream"]) as stream:
        output = os.path.join(gettempdir(), "speech.mp3")
        try:
            # Open a file for writing the output as a binary stream
            logging.info("Write received audio to {}".format(output))
            with open(output, "wb") as file:
                file.write(stream.read())
        except IOError as error:
            # Could not write to file, exit gracefully
            logging.error(error)
            sys.exit(-1)
        else:
            # The response didn't contain audio data, exit gracefully
            logging.error("Could not stream audio")
            sys.exit(-1)

# Play the audio using the platform's default player
if sys.platform == "win32":
    os.startfile(output)
else:
    # the following works on Mac and Linux. (Darwin = mac, xdg-open = linux).
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.call([opener, output])
