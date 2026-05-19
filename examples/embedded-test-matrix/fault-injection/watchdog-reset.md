# Watchdog Fault Injection

- fault: stop kicking watchdog from control task
- expected:
  - watchdog reset occurs within configured timeout
  - boot reason is recorded
  - persistent state is not corrupted
  - recovery path enters normal service or safe mode
- evidence:
  - serial log
  - reset reason register
  - health-check result
- status: template
