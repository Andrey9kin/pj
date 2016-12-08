from github import Github

usr = 'Andrey9kin'
repo_name = 'pj'

g = Github()

r = g.get_repo("{0}/{1}".format(usr,repo_name))
print(r.clone_url)

c = r.get_git_commit('64991d9b81ff30476b7e48ec3ac94502ca1024e8')
print(c.message)