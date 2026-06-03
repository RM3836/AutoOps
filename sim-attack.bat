@echo off
chcp 65001 >nul 2>&1
title AutoOps - Intrusion Simulator
color 0A

set "LOGDIR=%~dp0logs"
set "LOGFILE=%LOGDIR%\auth.log"

if not exist "%LOGDIR%" mkdir "%LOGDIR%"

echo ============================================================
echo   AutoOps Intrusion Log Simulator v1.0
echo   Generates simulated attack logs for security module demo
echo   Output: %LOGFILE%
echo ============================================================
echo.

echo # Simulated intrusion log - AutoOps demo > "%LOGFILE%"
echo. >> "%LOGFILE%"

echo [1/6] Normal logins ...
echo Jun  1 09:00:01 server sshd[1000]: Accepted password for ops from 192.168.1.50 port 49123 ssh2 >> "%LOGFILE%"
echo Jun  1 09:05:12 server sshd[1001]: Accepted publickey for deploy from 192.168.1.51 port 49200 ssh2 >> "%LOGFILE%"
echo Jun  1 09:10:33 server sshd[1002]: Accepted password for root from 192.168.1.10 port 49300 ssh2 >> "%LOGFILE%"
echo   - 3 normal login records
ping -n 2 127.0.0.1 >nul

echo [2/6] Brute force attack from 192.168.1.100 (admin/root/test) ...
echo Jun  1 10:23:45 server sshd[1234]: Failed password for invalid user admin from 192.168.1.100 port 55443 ssh2 >> "%LOGFILE%"
echo Jun  1 10:23:52 server sshd[1235]: Failed password for root from 192.168.1.100 port 55445 ssh2 >> "%LOGFILE%"
echo Jun  1 10:24:01 server sshd[1236]: Failed password for admin from 192.168.1.100 port 55446 ssh2 >> "%LOGFILE%"
echo Jun  1 10:28:15 server sshd[1240]: Failed password for invalid user test from 192.168.1.100 port 55501 ssh2 >> "%LOGFILE%"
echo Jun  1 10:32:22 server sshd[1245]: Failed password for invalid user guest from 192.168.1.100 port 55510 ssh2 >> "%LOGFILE%"
echo Jun  1 10:36:18 server sshd[1250]: Failed password for root from 192.168.1.100 port 55520 ssh2 >> "%LOGFILE%"
echo Jun  1 10:38:12 server sshd[1260]: Failed password for root from 192.168.1.100 port 55450 ssh2 >> "%LOGFILE%"
echo Jun  1 10:42:05 server sshd[1270]: Failed password for invalid user admin from 192.168.1.100 port 55530 ssh2 >> "%LOGFILE%"
echo Jun  1 10:45:33 server sshd[1280]: Failed password for invalid user user from 192.168.1.100 port 55540 ssh2 >> "%LOGFILE%"
echo Jun  1 10:48:50 server sshd[1290]: Failed password for invalid user admin from 192.168.1.100 port 55550 ssh2 >> "%LOGFILE%"
echo   - 10 failed attempts (should trigger CRITICAL brute-force alert)
ping -n 2 127.0.0.1 >nul

echo [3/6] Distributed scan from multiple IPs ...
echo Jun  1 10:50:01 server sshd[1301]: Failed password for invalid user admin from 192.168.1.101 port 45123 ssh2 >> "%LOGFILE%"
echo Jun  1 10:50:08 server sshd[1302]: Failed password for invalid user test from 192.168.1.101 port 45124 ssh2 >> "%LOGFILE%"
echo Jun  1 10:51:15 server sshd[1303]: Invalid user operator from 192.168.1.102 port 45234 ssh2 >> "%LOGFILE%"
echo Jun  1 10:52:20 server sshd[1304]: Failed password for root from 192.168.1.103 port 46001 ssh2 >> "%LOGFILE%"
echo Jun  1 10:53:25 server sshd[1305]: Failed password for invalid user guest from 192.168.1.104 port 34521 ssh2 >> "%LOGFILE%"
echo Jun  1 10:54:30 server sshd[1306]: Failed password for invalid user admin from 192.168.1.105 port 54321 ssh2 >> "%LOGFILE%"
echo Jun  1 10:55:35 server sshd[1307]: Failed password for invalid user test from 192.168.1.105 port 54322 ssh2 >> "%LOGFILE%"
echo Jun  1 10:56:40 server sshd[1308]: authentication failure; logname= uid=0 euid=0 tty=ssh ruser= rhost=192.168.1.106 user=root >> "%LOGFILE%"
echo   - 8 entries from 6 different IPs
ping -n 2 127.0.0.1 >nul

echo [4/6] Sudo privilege escalation attempts ...
echo Jun  1 11:00:01 server sudo: pam_unix(sudo:auth): authentication failure; logname=ops uid=1001 euid=0 tty=/dev/pts/0 ruser=ops rhost=localhost user=root >> "%LOGFILE%"
echo Jun  1 11:05:15 server sudo: pam_unix(sudo:auth): conversation failed; logname=web uid=1002 euid=0 tty=/dev/pts/1 ruser=web rhost=localhost user=root >> "%LOGFILE%"
echo Jun  1 11:10:22 server sudo:   web : 3 incorrect password attempts ; TTY=pts/1 ; PWD=/var/www ; USER=root ; COMMAND=/bin/bash >> "%LOGFILE%"
echo   - 3 sudo escalation attempts
ping -n 2 127.0.0.1 >nul

echo [5/6] System kernel anomalies ...
echo Jun  1 11:15:00 server kernel: Out of memory: Kill process 5234 (java) score 567 or sacrifice child >> "%LOGFILE%"
echo Jun  1 11:15:05 server kernel: Killed process 5234 (java) total-vm:2048000kB, anon-rss:1024000kB >> "%LOGFILE%"
echo Jun  1 11:20:30 server kernel: segfault at 7f1234567890 ip 00007f1111111111 sp 00007ffd12345678 error 4 in libc-2.31.so >> "%LOGFILE%"
echo Jun  1 11:25:00 server kernel: EXT4-fs error (device sda1): ext4_lookup:1590: inode #262147: comm nginx: deleted inode referenced >> "%LOGFILE%"
echo   - 4 kernel anomalies (OOM / segfault / filesystem error)
ping -n 2 127.0.0.1 >nul

echo [6/6] Attacker finally succeeds ...
echo Jun  1 11:30:00 server sshd[1400]: Accepted password for root from 192.168.1.100 port 55600 ssh2 >> "%LOGFILE%"
echo Jun  1 11:30:05 server sshd[1401]: pam_unix(sshd:session): session opened for user root by (uid=0) >> "%LOGFILE%"
echo Jun  1 11:35:00 server sshd[1401]: pam_unix(sshd:session): session closed for user root >> "%LOGFILE%"
echo   - Attacker logged in as root via brute force!
ping -n 2 127.0.0.1 >nul

echo.
echo ============================================================
echo   Simulation complete!
echo.
echo   Log summary:
echo     Normal logins:        3
echo     Brute force attempts: 18 (10 concentrated)
echo     Sudo escalation:      3
echo     Kernel anomalies:     4
echo     Successful breach:    3
echo.
echo   Next: Start AutoOps, visit /logs, click Analyze
echo ============================================================
echo.
pause
