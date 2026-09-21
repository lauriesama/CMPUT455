# Assignments

## Overview

- Limited AI usage for code testing and improvement, no full-solution generation. See SyllabusDownload Syllabus for details, and the Glossary for items in italic.
- Each assignment is worth 5 marks, which is 5% of course marks. Assignments 2, 3 and 4 allow for bonus marks for exceptional programs. See syllabus for details.
- You need to test your submission file on a lab machine before submitting it. If you are not working in a lab, see connect via SSH.

## Team Submissions

    See Assignment Group Instructions
    One submission per team from group leader
    Setup your group in Canvas under People, button Assignment-groups near the top. We use automatic mode - the first student becomes group leader. See the Canvas manual entryLinks to an external site.

## Assignment marks

### Marking breakdown

- 20% for proper submission format:
  - Submission is named assignmentX.tgz, where X is 1, 2, 3 or 4, and is a valid tgz file - a gzipped tarball.
  - Note added Sep 11, 2026: Canvas may modify the file name that you used: In case of re-submissions it seems to add a version number. We will deal with that on our end. You should always submit using the regular name above, even if you re-submit.
  - Decompresses without issue on lab machine
  - All specified files are included and file names are identical to those provided - our marking scripts have those hard-coded
  - No extra directory levels for tested files. Extra files is fine
  - Be very careful as formatting issues could lead to a mark of zero.
- 20% for passing public tests
  - Public tests are not comprehensive, just examples for tested functions
  - You will need to create your own test cases if you want to pass all of the private tests
  - Make sure to test on the undergrad lab machines, not your own computer
- 20% for code quality. How does the submitted code reflect the assignment spec? Is it simple and direct, or does it contain strange AI-like artifacts, or leftovers from failed directions, or unhelpful comments, or other markers of bad code quality?
- 40% for private tests
  - Far more private tests than public
  - You need to follow output specification exactly, even extra whitespace will fail the tests
  - Edge cases will be tested - large, small, special values. However, nothing outside the specification will be tested.
  - Depending on the assignment, your program might be partially evaluated on efficiency - how long it takes to run the private tests. This will be especially important for consideration for bonus marks.
- No late submissions are accepted.
- All submitted assignments are marked.
- A maximum of one excused absence can be taken across all assignments - see syllabus
  - To take your excused absence, don’t submit anything. The weight will be transferred to the final.
  - Excused absences are applied to a whole group. You cannot absent yourself from your other group members.

We will test all programs on undergraduate lab machines running Linux which are using python3 version 3.8.10 3.9.4 at the moment. We will support a higher version in case the undergraduate lab machines are automatically updated.

You can use command python3 --version to confirm your current python version.

You cannot use tools that (partially) compile the code into faster formats, beyond what the standard python3 command does.


## SSH connection guide

Connect to undergraduate lab machine in UCOMM through SSH

(Disclaimer: these suggestions have been tested but are provided as-is without guarantees. Things do change. Post to forum or ask a TA or colleague if you have trouble connecting.) 

    List of available machines: https://www.ualberta.ca/en/computing-science/resources/technical-support/computing-resources/index.html
    Almost all of these machines (all except ucomm-2030-w01 - see below) share the standard setup for this term. As of now, this is based on python 3.8.10. Your code will be tested on one of these. Make sure it works there.
    Of course, you can just go to a lab and work there directly.
    Added Sep 5: do not use ucomm-2030-w01 - it is different from all the other lab machines. It is a testing machine for Ubuntu 24.
    Added Sep 5: make sure to use python3, not just python, as your command.

### First connection method: directly with VPN

    Use the university VPN (https://universityofalberta.freshservice.com/support/solutions/articles/19000109142Links to an external site.)

### Second method: connect through public machine such as ohaton

    In a terminal / command prompt enter:

ssh your_ccid@ohaton.cs.ualberta.ca

    Replace your_ccid with your actual CCID.
    If asked whether you want to add a connection fingerprint, type yes to this prompt.
    To enter your password, use your CCID password - the same one you use for all your ualberta account log-ins like bear tracks.
    Ohaton is a shared resource, for many users. Do NOT test your program directly on ohaton.
    Now connect from ohaton to a specific undergrad machine which will not be as contested.

### Connect to a specific machine

    Choose the machine, named ucomm-XXXX-wYY.cs.ualberta.ca for some XXXX and YY
        XXXX is the room number and YY is the machine number in that room
    Connect to this specific machine with the command:

ssh your_ccid@ucomm-XXXX-wYY.cs.ualberta.ca

### Other Tips

    If you are using VSCode, you can easily set up an automatic SSH connection that is nearly indistinguishable from accessing it locally.
    Install the “Remote - SSH” extension, and set up your ssh config file. 
    You will need a proxyjump connection through ohaton in order to connect straight to an undergrad machine.
    You’ll also need to generate ssh keys if you haven’t already, use the “ssh-keygen” command (google for details).

Example ~/.ssh/config file:

Host * 

  User *your CCID* 

  IdentityFile *path to your key* 

Host ohaton 

  HostName ohaton.cs.ualberta.ca 

Host ugrad_machine 

  HostName *undergrad machine of your choosing* 

  ProxyJump ohaton

Leave “Host *” as is, don’t change that asterisk.
