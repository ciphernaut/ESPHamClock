---
description: Managing the HamClock service stack (backend, proxy, client)
---
// turbo-all
To manage HamClock services, ALWAYS use the `run_stack.sh` script from the project root.

### Start all services
```bash
./run_stack.sh start all
```

### Restart specific component (backend|proxy|client)
```bash
./run_stack.sh restart [component]
```

### Check service status
```bash
./run_stack.sh status all
```

### Stop all services
```bash
./run_stack.sh stop all
```

> [!IMPORTANT]
> Do NOT use manual `python3` or `fuser` commands if `run_stack.sh` covers the use case.
