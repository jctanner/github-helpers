#!/usr/bin/env python

import os
import sys
import shlex
import subprocess

def run_command(cmd, cwd=None):
    #print "running: %s" % cmd
    if type(cmd) is not list:
        cmd = shlex.split(cmd)

    if not cwd:
         p = subprocess.Popen(cmd, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
    else:
         p = subprocess.Popen(cmd, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd)

    out, err = p.communicate() 
    #assert p.returncode == 0, "failed to run: %s" % cmd
    #print "running: %s succeeded" % cmd

    #import epdb; epdb.st()
    return p.returncode, out, err

    

class PRTest(object):
    def __init__(self, repo_url, branch='devel', tmp_path='/tmp'):
        self.repo_url = repo_url
        #self.patch_url = patch_url
        self.tmp_path = tmp_path
        self.branch = branch

        self.git = subprocess.check_output(['which', 'git'])
        self.git = self.git.strip()

        parts = repo_url.split('/')        
        self.repo_user = parts[-2]
        self.repo_name = parts[-1]
        self.repo_dir = self.repo_user + "_" + self.repo_name
        self.repo_path = os.path.join(self.tmp_path, self.repo_dir)

    def makecheckout(self):

        if not os.path.isdir(self.repo_path):
            cmd = "git clone %s %s" % (self.repo_url, self.repo_path)
            run_command(cmd, cwd=self.temp_path)
        else:
            cmd = "git reset --hard"                
            run_command(cmd, cwd=self.repo_path)
            cmd = "git checkout %s" % self.branch                
            run_command(cmd, cwd=self.repo_path)
            cmd = "git reset --hard"                
            run_command(cmd, cwd=self.repo_path)
            cmd = "git pull --rebase"                
            run_command(cmd, cwd=self.repo_path)
            cmd = "git clean -f"                
            run_command(cmd, cwd=self.repo_path)

    def trypatch(self, patch):
        this_branch = "test__" 

        #cmd = "git branch -d %s" % this_branch
        #rc, so, se = run_command(cmd, cwd=self.repo_path)

        #cmd = "git checkout -b %s" % this_branch
        #rc, so, se = run_command(cmd, cwd=self.repo_path)

        patch_file = os.path.join(self.tmp_path, "patch1")

        """
        cmd = "wget %s -O %s" % (patch_url, patch_file)         
        rc, so, se = run_command(cmd, cwd=self.tmp_path)
        """

        f = open(patch_file, "wb")
        f.write(patch)
        f.close()

        cmd = "git apply %s" % patch_file
        this_rc, this_so, this_se = run_command(cmd, cwd=self.repo_path) 
        #print "PATCH_RESULT: %s %s %s" % (this_rc, so, se)

        #cmd = "git checkout %s" % self.branch
        #rc, so, se = run_command(cmd, cwd=self.repo_path)

        #cmd = "git branch -d %s" % this_branch
        #rc, so, se = run_command(cmd, cwd=self.repo_path)

        if this_rc == 0:
            return True
        else:
            #import epdb; epdb.st()
            return False

    def trymerge(self, url, branch):
        this_branch = "test__" + branch

        cmd = "git branch -d %s" % this_branch
        rc, so, se = run_command(cmd, cwd=self.repo_path)

        cmd = "git checkout -b %s" % this_branch
        rc, so, se = run_command(cmd, cwd=self.repo_path)
        if rc != 0:
            import epdb; epdb.st()
            return rc

        cmd = "git pull %s %s" % (url, branch)
        rc, so, se = run_command(cmd, cwd=self.repo_path)
        if rc != 0:
            import epdb; epdb.st()
            return rc

        cmd = "git checkout %s" % self.branch
        rc, so, se = run_command(cmd, cwd=self.repo_path)

        cmd = "git merge %s" % this_branch
        this_rc, so, se = run_command(cmd, cwd=self.repo_path)
        if rc != 0:
            import epdb; epdb.st()
            return rc

        cmd = "git branch -d %s" % this_branch
        rc, so, se = run_command(cmd, cwd=self.repo_path)
        
        return True
        

def main():
    this_repo = "https://github.com/ansible/ansible"
    this_patch = "https://github.com/ansible/ansible/pull/6097.diff"
    x = PRTest(this_repo)
    x.makecheckout()
    #res = x.trymerge('git://github.com/iiordanov/ansible.git', 'devel')
    #print "res: %s" % res
    res = x.trypatch(this_patch)
    print "res: %s" % res
    

if __name__ == "__main__":
    main()        
