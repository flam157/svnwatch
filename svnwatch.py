#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 29 14:38:58 2012

Script to notify the user for changes in a subversion repository.

this script is based on the program svnnotify

@author: remi.flamary àt gmail.com
"""

try:
    import pysvn, pynotify, configobj
except:
    print "Error while loading external depencencies."
    print "Make sure 'pysvn' and 'pynotify' is installed."
    exit()
    
import datetime, os, time

cfile_init=""" # svnwatch configuration file


# in second 
sleep=1

#print 
log=True
notify=True


[repos]


"""

conf_dir=os.path.expanduser("~/.config/")

nblog0=5

conf_file='svnwatch.ini'

class svnrepo():
    """
    class handling the link between local and server repository
    """
    config = None
    local_revision=0
    server_revision=0
    server_revision_old=0
    changed=False
    client=None
    url=''
    log=''  
    authors_changed=[]
    messages_changed=[]
    files_changed=[]
    
    def __init__(self,config=None,opts=None):
        """
        initialisation function, loads and prepare everything
        """
        
        
        if not config:       
            print 'config dictionnary is necessary'
        else:
            self.config=config
            self.client=pysvn.Client(config['local'])
            self.client.set_auth_cache(True)
            self.client.set_store_passwords(True)
            self.client.callback_get_login=self.credentials
            self.url=self.client.info(config['local']).url
            self.local_revision=self.client.info(self.config['local']).revision.number
            self.server_revision=self.local_revision
            self.update()
            
    def credentials(self,realm, username, may_save):
        """Return the default login credentials"""
        return True, self.config['username'],self.config['password'], False
        
    def update(self):
        
        self.server_revision_old=self.server_revision
        
        self.local_revision=self.client.info(self.config['local']).revision.number
        #print 'Local',self.local_revision
        #temp=self.client.log(self.config['local'],limit=1,discover_changed_paths=True,revision_end=pysvn.Revision( pysvn.opt_revision_kind.working ) )[0].revision.number
        #print temp        
        #self.log= self.client.log(self.config['local'],limit=nblog0,discover_changed_paths=True,revision_end=pysvn.Revision( pysvn.opt_revision_kind.number,self.local_revision ) )
        self.log= self.client.log(self.config['local'],limit=nblog0,discover_changed_paths=True )
        
        if len(self.log):
            self.server_revision=self.log[0].revision.number
        else:
            self.server_revision=self.local_revision

        
            
        self.authors_changed=[]
        self.messages_changed=[]
        self.files_changed=[]            
        for entry in self.log:
            if entry.author not in self.authors_changed:
                self.authors_changed.append(entry.author)
            #print entry
            #self.message.append(entry.message)
            for change in entry.changed_paths:
                path = change.path.split('/')[-1]
                if path not in self.files_changed:
                    self.files_changed.append(path)
            


            

class svnwatch():
    
    def __init__(self,config_file=''):
        
        self.config=read_config(config_file='')
        self.nbrepo=len(self.config['repos'])
        self.countrepo=list()
        for i in range(self.nbrepo) :
            self.countrepo.append(0)
        
        self.repos=list()
        self.reponames=list()
        
        #print len(self.config['repos'])
        for reponame in self.config['repos']:
            self.repos.append(svnrepo(self.config['repos'][reponame]))
            self.reponames.append(reponame)
            
    def update(self):
        
        for repo in self.repos:
            repo.update()
            
    def check_changed(self):

        for i,repo in enumerate(self.repos):
            #print repo.server_revision
            #print repo.server_revision_old
            if repo.server_revision >repo.server_revision_old:
                
                if self.config['log']:
                    log_message(self.reponames[i],repo.local_revision, repo.server_revision,repo.files_changed,repo.authors_changed)

                if self.config['notify']:
                    notify(self.reponames[i],repo.local_revision, repo.server_revision,repo.files_changed,repo.authors_changed)
       
    def loop(self):
        
        while True:
            
            self.check_changed()            
            
            self.update()
            
                        
            time.sleep(int(self.config['sleep']))
            
            print 'end loop'
        
        


def read_config(config_file=''):
    """Read the configuration file"""
    if config_file=='':
        config_file = conf_dir+conf_file
        
    try:
        conf = configobj.ConfigObj(config_file)
        #print conf
        #print conf['servers']
    except BaseException as e:
        print "Error while parsing file '%s':" % config_file
        print e
        exit()
    return conf

def notify(repo,rev0,rev1,paths, authors):
    """Display the changed paths using libnotify"""
    title_string = 'New Commits:'+repo
    path_string = ', '.join(paths)
    author_string = ', '.join(authors)
    message_string = 'Authors: ' + author_string + '\nFiles: ' + path_string
    
    if pynotify.init("SVN Monitor"):
        n = pynotify.Notification(title_string, message_string, "emblem-shared")
        n.show()

def log_message(repo,rev0,rev1,paths, authors):
    """Print a log message containing the time, authors and paths"""
    now = datetime.datetime.now()
    now = now.strftime("%c")
    path_string = ', '.join(paths)
    author_string = ', '.join(authors)
    print "[{reponame}] -- Rev {rev0} -> {rev1}, {now} \nAuthors: {authors}\nFiles: {files}".format(now=now,reponame=repo,rev0=rev0,rev1=rev1,authors=author_string,files=path_string)
    


def check_install():
    
    if not os.path.exists(conf_dir):
        print("Creating config files")
        os.mkdir(conf_dir)  
        f = open(conf_dir+ conf_file, 'w')
        f.write(cfile_init)
        f.close()    
    


if __name__ == '__main__':
    #conf=read_config()
    #repo=svnrepo(conf['repos']['ICML2012'])
    watch=svnwatch()
    watch.check_changed()
    
    pass
#    read_config()
#    print '- Press %s to quit -' % '^C'
#    last_revision = None
#    while True:
#        last_revision, authors, paths = discover_changes(last_revision)
#        if paths is not None:
#            log_message(paths, authors)
#            #notify(paths, authors)
#        time.sleep(2*60)
