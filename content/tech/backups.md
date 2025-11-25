---
title: "Backups"
date: 2023-03-12
draft: true
---
# My Backup Strategy

Over the years I've learned how important a personal data backup strategy can be. Photos are probably the most cherished piece of data to me, but there are plenty of other things that are important to keep around for many years. The conventional wisdom says that you should keep 3 copies of your data, 2 on site, and 1 somewhere else. I agree with this philosohpy, it seems like a solid way to keep things long term. As a regular home user though, this can seem a bit daunting. However these days with the advent of cloud storage, its really not that hard to achieve. In this article I'm going to explain the strategy I devloped for keeping photo backups, and how to apply it to just about anything.



## 2 At Home Replicas

To achieve the 2 at home replicas, I have tried various file server solutions including Unraid, and Truenas. These are both great, but I ultimately landed on a vanilla Ubuntu server. Its rock solid, and just about any question you could have about Ubuntu has been asked and answered on the internet. ZFS is prefectly stable on Linux now, so I saw no reason not to use it. I chose ZFS for a few reasons, native snapshots and protections against corruption being the biggest for me. With the [Sanoid]() and [Syncoid]() projects, backups are easy to manage. 

ZFS allows you to create multiple datasets per pool. I have all of my datasets broken up by category, photos, music, videos, documents, etc. With Sanoid, I can create snapshots on custom schedules per dataset, depending on how important they are to me. I have a separate backup ZFS pool that I synchronize my snapshots to using Syncoid every hour. This gives me my 2 copies of data at home with relatively minimal effort. I run a cron job daily to check the health of my pools with the `zpool status` command. If anything is amiss, the healtcheck will fail, and I'll get an email notifying me. The service I use to monitor the cronjob is called [healthchecks.io](https://healthchecks.io)

The script below runs in a cron job nightly to verify that my zfs pools are healthy.
#### Backup Script
```shell
#!/bin/bash
status="$(sudo zpool status -x)"

if [ "$status" != "all pools are healthy" ]; then
    echo "Error detected"
    echo "$status" && exit 1
fi
curl -m 10 --retry 5 <my healthcheck URL>
```

## Geting Files from my Phone to the Server

The first step in my backup flow is getting the photos off my phone and to the server. I have looked high and low for something better, but [Syncthing]() has been the best thing I can find. I hoestly have a pretty love hate relationship with Syncthing. It has its really annoying quirks, and I have sworn I'd never use it again more than once. At the end of the day though, all of my issues have been due to not fully undestanding how it works. When properly configured, it syncs my pictures for years at a time without any interaction. My setup is pretty simple, I set up a folder from my phone's storage in Syncthing to sync to a folder within a particular dataset on my ZFS pool. I personally only have these files sync while my phone is plugged into AC power to save battery. 

## Off Site Backup

The harder part is figuring out where to send the third copy. Its definitely possible to colocate with a friend or family memmber, but I don't want to deal with the complexity of running a backup server at someone else's house. It could be cheaper that way, but its an added burden, and never going to be as reliable as a cloud provider. S3 buckets are a great place to store backups, and there are some pretty cheap providers these days. I settled on [Wasabi](), but wouldn't mind switching to [Backblaze]() sometime as their prices seem a bit cheaper. I set up buckets in Wasabi that more or less match up with the datasets on my ZFS pool. 

To keep the data in my ZFS pool synced with my s3 bucket, I ended up creating a custom docker image. I wanted these to be scheduled with Cron so that I can avoid using up a ton of bandwidth during times we are streaming or using the internet. So I run all of my backups at night after I go to bed. I also wanted to have the ability to use my Hashicorp Vault to store the s3 credentials. 
