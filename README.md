# Jenkins voice message generator (p - polly, j - jenkins)

This tool reads info from Jenkins job (sha1, result, repo url), gets info about commit author and commit message from GitHub and then generated voice message using Amazon Polly

```
python pj.py -a default -o ~/Downloads -u http://192.168.99.100:8080 -j polly-test
INFO:root:Connect to Jenkins at http://192.168.99.100:8080
INFO:root:Get latest build for the job polly-test from Jenkins server http://192.168.99.100:8080
INFO:root:Jenkins job polly-test with the build number 4 built repo https://github.com/Andrey9kin/pj.git sha1 0fe984f70f51a3a99ec1a2cb838dbf9963197ceb
INFO:root:Extracted github user name - Andrey9kin
INFO:root:Extracted github repo name - pj
INFO:root:Extracted name - Andrius Ordojan
INFO:root:Extracted commit message - pygithub code to get repo and commit
INFO:root:Login to AWS
INFO:botocore.credentials:Found credentials in shared credentials file: ~/.aws/credentials
INFO:root:Request audio for Message for user Andrius Ordojan! Message for user Andrius Ordojan! Your commit with sha1 - 0fe984f70f, and commit message - pygithub code to get repo and commit, broke the build number - 4 for the job - polly-test. Go and fix it! God dammit!
INFO:botocore.vendored.requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): polly.us-west-2.amazonaws.com
INFO:root:Message saved to file /Users/andrey9kin/Downloads/message.mp3
```