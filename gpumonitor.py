#!/usr/bin/python3

import os
import pwd
import subprocess
import time
import json
import requests

# fill in slack webhook api address below
mattermostIncomingWebhook=""
nvidiaLogoLink=""

# Saves all known and already published jobs, so that they get not published again
saveKnownPIDS = []

# Dictionary contains in addition username and job info to notify user
saveKnownDic = dict()

# Bool used to show status update if new job started
showStatusUpdate = False

while (True):
  showStatusUpdate = False
  # List contains jobs seen at this time, so that one can find and show finished jobs
  seenPIDS = []
  pidfinding=subprocess.Popen(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  pidProcessMemorystring=pidfinding.stdout.read()
  pidProcessMemorys=pidProcessMemorystring.decode('utf-8').split('\n')

  for info in pidProcessMemorys:
    infodetail=info.split(',')
    if(len(infodetail) == 3):
      pid=infodetail[0]
      processName=infodetail[1]
      processMemory=infodetail[2]

      if pid.isdigit() and pid not in saveKnownPIDS:
        # the /proc/PID is owned by process creator
        proc_stat_file = os.stat("/proc/%d" % int(pid))
        # get UID via stat call
        uid = proc_stat_file.st_uid
        # look up the username from uid
        username = pwd.getpwuid(uid)[0]

        # Save job info in dictionary to notify user later  about finished job
        tempList=[username, processName]
        if pid not in saveKnownDic:
            saveKnownDic[pid] = list()
            saveKnownDic[pid] = tempList

	      # Create string
        postProcessName=""
        if len(processName.split('/')) > 5:
          #postProcessName = processName
          print(saveKnownDic.items())
          postProcessName = str([f"{k}:{v[1]}" for k,v in saveKnownDic.items()])
        else:
          postProcessName = processName
        #messageString = "```[NEW] [Running: " + str(list(saveKnownDic.keys())) + "] \n + **@" +  username + "** has created a job named **" + postProcessName + "** on GPU with pid **" + pid + ".```"
        messageString = "```[🔥] [GPU: " + str(len(list(saveKnownDic.keys())))  + "] \n" + postProcessName + "```"

        print(messageString)
        messageData={'text': messageString, 'icon_url': nvidiaLogoLink}
        #print(messageData)

        response = requests.post(mattermostIncomingWebhook, data=json.dumps(messageData), headers={'Content-Type': 'application/json'})
        if (response.status_code != 200):
          print('Request error ', response.status_code, ' the response is:\n', response.text)

        # Activate statusUpdate
        showStatusUpdate = True
        saveKnownPIDS.append(pid)

      if pid.isdigit():
        seenPIDS.append(pid)

  # Show status update after last new job is published
  # if showStatusUpdate:
  #   statusFinding=subprocess.Popen(['nvidia-smi'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  #   currentStatus=statusFinding.stdout.read()
  #   currentStatusString='### Status after starting new jobs\n ``` \n' + currentStatus.decode('utf-8') + '\n ```'
  #   print(currentStatusString)
  #   statusData={'text': currentStatusString, 'icon_url': nvidiaLogoLink}
  #   print(statusData)
  #   response = requests.post(mattermostIncomingWebhook, data=json.dumps(statusData), headers={'Content-Type': 'application/json'})
  #   if response.status_code != 200:
  #     print('Request error ', response.status_code, ' the response is:\n', response.text)

  # Compare seenPIDS with knownPIDS and notify user if job is finished
  finishedPIDS = list(set(saveKnownPIDS) - set(seenPIDS))
  for pid in finishedPIDS:
    username, processName = saveKnownDic.get(pid)
    saveKnownPIDS.remove(pid)
    del saveKnownDic[pid]

    if username != None and processName != None: 
      postProcessName=""
      if len(processName.split('/')) > 5:
        #postProcessName = processName
        postProcessName = str([f"{k}:{v[1]}" for k,v in saveKnownDic.items()])
      else:
        postProcessName = processName
      # Create string
      #messageString = "```[FIN] [Running: " + str(list(saveKnownDic.keys())) +  "]\n - **@" +  username + "** your job named **" + postProcessName + "** with pid **" + pid + "** has finished.```"
      messageString = "```[💧] [GPU: " + str(len(list(saveKnownDic.keys())))  + "] \n" + postProcessName + "```"
      print(messageString)

      messageData={'text': messageString, 'icon_url': nvidiaLogoLink}
      print(messageData)
      response = requests.post(mattermostIncomingWebhook, data=json.dumps(messageData), headers={'Content-Type': 'application/json'})
      if response.status_code != 200:
        print('Request error ', response.status_code, ' the response is:\n', response.text)

  time.sleep(1)