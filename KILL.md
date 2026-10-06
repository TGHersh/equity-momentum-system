# Kill criteria - decided 6 Oct 2026, before the account ran unattended

- Paper drawdown beyond 15% -> stop, revisit the signal 
- Two consecutive weeks where real fills differ from assumed opens by more
than 20bp -> the cost model is wrong; fix that before anything else
- Any day the ledger and portfolio.json disagree -> stop trading
immediately. This is a correctness bug, not a performance one.
- Six weeks with no bug found in the loop -> plumbing is trusted; start 
Phase D
