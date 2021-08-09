#! /usr/bin/env python
# -*- coding: latin-1 -*-

#########################
# TSpoofer------------------------------------
# Programmed by: Dante Signal31
# dante.signal31@gmail.com
#
# This program stores file timestamps under
# a file tree in order to restore them after file 
# modification.
#
# THIS PROGRAM HAS BEEN DEVELOPED FOR LAB TESTS
# IN CONTROLLED ENVIRONMENTS. 
# USE THIS PROGRAM AT YOUR OWN RISK AND LIABILITY.
#########################

#############
# LIBRARIES
#############
import sys
import getopt
import pickle   # As far as I know I could have used cPickle instead of Pickle to get speer enhacements but I don't know
                        # if it's so portable.
import os
import stat
import subprocess

#############
# CONSTANTS
#############
TRUE = 1
FALSE = 0
OK = 1
ERROR = -1
TEMPFILE_EXTENSION = "tsp"

###############
# GLOBAL VARIABLES
###############
target_directory = None
data_directory = "/tmp/tspoofer"
restoration = FALSE
backup = FALSE
cleaning = FALSE
ctime_change_error = FALSE
file_systems = {}
file_list = []

###############
# CLASSES
###############
class FileTimeStamps:
    path = ""
    filename = ""
    mtime = ""
    atime = ""
    ctime = ""
    def __init__(self,  path="",  filename="",  mtime="",  atime="",  ctime="",  inode_number=None, device=None):
        self.path = path
        self.filename = filename
        self.inode = inode_number
        self.device = device
        self.mtime = mtime
        self.atime = atime
        self.ctime = ctime

#############
# FUNCTIONS
#############
#
# Print help text.
def printHelp():
    print("TSpoofer")
    print("========")
    print("Programmed by: Dante Signal31 (dante.signal31@gmail.com)")
    print("\n This program stores file timestamps under a file tree")
    print("\n in order to restore them after file modification.")
    print("\n   Format " + sys.argv[0] + " <arguments>")
    print("          -b <directory to backup> --------> Directory to backup its file timestamps.")
    print("          -r <directory to restore> -------> Directory to restore its timestamps.")
    print("          -d <directory to use> -----------> Directory where data gathered by TSpoofer is stored. (OPTIONAL) ")
    print("          -c <directory> ------------------> Clean " + sys.argv[
        0] + " footprint about directory. '*' means every footprint.")
    print("          -h | --help --------------> Print this text.")
    print("\n\nExamples:")
    print(" Storing directory timestamps:" + sys.argv[0] + " -b /directory/sudirectory -d /tmpdir/tmpsubdir")
    print("         Restoring timestamps:" + sys.argv[0] + " -r /directory/sudirectory -d /tmpdir/tmpsubdir")
    print(" Deleting " + sys.argv[0] + " temporary files: " + sys.argv[0] + " -c '*' -d /tmpdir/tmpsubdir")


#
# This function stores our file timestamps list in a file.
def save_filelist(file, file_list):
    #We'll use object serialization, which is called in python pickling.
    print("Storing timestamps in " + file + "...")
    file_object = open(file, 'wb')
    for file_times in file_list:
        pickle.dump(file_times, file_object)
    file_object.close()
    print("     done...")


#
#  This function gets our file timestamps from a file.
def get_filelist(file):
    print("Retrieving timestamps from " + file + "...")
    files = []
    file_object = open(file, 'rb') # Docs recomend using binary mode in reading instead of ASCII one.
    file_times = None
    file_times = pickle.load(file_object)
    while (file_times != None):
        files.append(file_times)
        file_times = None
        try:
            file_times = pickle.load(file_object)
        except EOFError:
            break
    print("     done...")
    file_object.close()
    return files

#
# This function performs filetree timestamps backup.
def backup_directory_timestamps(target_dir,  data_dir):
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if (os.path.islink(file_path)): # In this version of tspoofer I won't deal with symbolic links. 
                continue
            file_times = FileTimeStamps(path=root, filename=file)
            file_times.mtime = (os.stat(file_path))[stat.ST_MTIME]
            file_times.atime = (os.stat(file_path))[stat.ST_ATIME]
            file_times.ctime = (os.stat(file_path))[stat.ST_CTIME]
            file_times.inode = (os.stat(file_path))[stat.ST_INO]
            file_times.device = getFilesSystem(file_path)
            file_list.append(file_times)
    #I could have used tmpnam function from os module to get a temp filename, but I wanted to give
    #user freedom to select where to place temp files.
    print("Calculating hash for: " + os.path.abspath(target_dir) + "...")
    temp_file_name = str(hash(os.path.abspath(target_dir))) + "." + TEMPFILE_EXTENSION
    data_path = os.path.join(data_dir, temp_file_name)
    save_filelist(data_path, file_list)

#
# This function restores filetree timestamps.
def restore_directory_timestamps(data_dir,  target_dir):
    print("Calculating hash for: " + os.path.abspath(target_dir) + "...")
    temp_file_name = str(hash(os.path.abspath(target_dir))) + "." + TEMPFILE_EXTENSION
    data_path = os.path.join(data_dir, temp_file_name)
    file_list = get_filelist(data_path)
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            file_found = FALSE
            # We search this file in our stored timestamps list in order to recover its times.
            for file_times in file_list:
                file_path = os.path.join(file_times.path, file_times.filename)
                if (os.path.islink(file_path)):
                    continue
                if (file_times.path == root):
                    if (file_times.filename == file):
                        if (((os.stat(file_path))[stat.ST_MTIME] != file_times.mtime) or ((os.stat(file_path))[stat.ST_ATIME] != file_times.atime) or ((os.stat(file_path))[stat.ST_CTIME] != file_times.ctime)):
                            print("Setting time of " + file_path + " from atime " + str(
                                (os.stat(file_path))[stat.ST_ATIME]) + ", atime " + str(
                                (os.stat(file_path))[stat.ST_MTIME]) + " and ctime " + str(
                                (os.stat(file_path))[stat.ST_CTIME]))
                            print("                                   to atime " + str(
                                file_times.atime) + ", mtime " + str(file_times.mtime) + " and ctime " + str(
                                file_times.ctime))
                            os.utime(file_path,(file_times.atime, file_times.mtime))
                            changeCTime(file_times)
                        file_list.remove(file_times) # We remove object to make searches faster.
                        file_found = TRUE
                    else:
                        continue
                else:
                    continue
                break # If we get here it means we have found file in our list.
            if (not file_found):
                if not (os.path.islink(os.path.join(root, file))):
                    print("ALERT:   The file " + os.path.join(root,
                                                              file) + " was not in our backup list, maybe it was created after,")
                    print("         you'll have to change its timestamps manually.")


#In order to use debugfs we need a table with all filesystems devices.
def getFileSystems():
    global file_systems
    df = subprocess.Popen("df",  stdout = subprocess.PIPE)
    grep = subprocess.Popen(["grep","/dev"], stdin=df.stdout)
    devices = grep.communicate()[0]
    for line in grep.stdout:
        devices.append(line)
    grep.wait()
    for device in devices:
        device_tokens = devices.split()
        file_systems[device_tokens[5]] = device_tokens[0]

#This function identifies wich filesystems corresponds to each file.
def getFilesSystem(path):    
    winner_length = 0
    winner = None
    for file_system in file_systems.keys():
        if ((path.find(file_system) == 0) and (len(file_system)>winner_length)):
            winner = file_system
            winner_length = len(file_system)
    return winner
    
#This functions deals with low-level stuff in order to change CTime. 
def changeCTime(filetimes):
    global ctime_change_error
    #We'll use debugfs to change inode's timestamps. If we are in a Windows system or in a Linux without a ext2/ext3 filesystem this call will end in an error.
    if not(ctime_change_error):
        print("sudo debugfs -w " + str(filetimes.device) + " -R \'set_inode_field <" + str(
            filetimes.inode) + "> ctime " + str(filetimes.ctime) + "\'")
        try:
            debugfs = subprocess.Popen("sudo debugfs -w " + str(filetimes.device) + " -R \'set_inode_field <"+ str(filetimes.inode) + "> ctime " + str(filetimes.ctime) +"\'")
#            print debugfs.communicate()
        except:
            ctime_change_error = TRUE

#Argument parsing.
def parse_arguments():
    global target_directory
    global data_directory
    global restoration
    global backup
    global cleaning
    
    try:
        arguments, args = getopt.getopt(sys.argv[1:],"b:d:r:c:h",["help"])
    except getopt.error as msg:
        print("Argument parsing error.")
        print(msg)
        sys.exit(2)
    #Empty string of arguments means user has no idea about how to use our program, so we display help.
    if (len(arguments) == 0):
        printHelp()
        sys.exit(0)
    for token, value in arguments:
        if (token in ["-h", "--help"]):
            printHelp()
            sys.exit(0)
        elif token == "-b":
            target_directory = value
            backup = TRUE
            print("Directory to backup: " + target_directory + "...")
        elif token == "-d":
            data_directory = value
            print("Directory to store temp files: " + data_directory + "...")
        elif token == "-c":
            cleaning = TRUE
            target_directory = value
            print("Cleaning " + target_directory + " footprint...")
        elif token == "-r":
            target_directory = value
            restoration = TRUE
            print("Restoring timestamps in: " + target_directory)
        else:
            print("Unexpected argument " + token + ", please read help (" + sys.argv[0] + " --help )")
            sys.exit(2)

#
#############
# MAIN PROGRAM
#############
#We get arguments provided by user.
parse_arguments()
print("Identifying local filesystems...")
getFileSystems()
if (restoration): # We replace timestamps with older timestamps.
    print("Restoration requested ...")
    restore_directory_timestamps(data_directory,  target_directory)
    print("Restoration done.")
    if (ctime_change_error):
        print(" CAUTION: Errors happened while restoring ctime values. Change them manually.")
if (backup): # We're doing a filetree backup..
    print("Backup requested ...")
    backup_directory_timestamps(target_directory, data_directory)
    print("Backup done.")
if (cleaning):
    if (target_directory == '*'):
        for file in os.listdir(data_directory):
            if ((file.split('.'))[1] == TEMPFILE_EXTENSION):
                os.remove(os.path.join(data_directory, file))
        print("Cleaning: " + os.path.join(data_directory, "*." + TEMPFILE_EXTENSION))
    else:
        print("Cleaning temporary files...")
        temp_file_name = str(hash(os.path.abspath(target_directory))) + "." + TEMPFILE_EXTENSION
        data_path = os.path.join(data_directory, temp_file_name)
        os.remove(data_path)
        print("Cleaning: " + data_path)
        print("Cleaning done.")
print("Have a nice day!")




