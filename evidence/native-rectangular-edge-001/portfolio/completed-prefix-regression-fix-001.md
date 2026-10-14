Completed-prefix regression correction

Full040 exposed a genuine regression missed by the earlier targeted set, which omitted test_portfolio_completed_resume. Existing completed-prefix metadata reused the new allocation parameter name, replacing the remaining policy string with a dict. The exact pre-fix invalidated status, returned reason, Low64-only call and dictionary are preserved in completed-prefix-regression-before-fix.json.

Renamed that metadata local to prefix_allocation; its original dictionary/protocol/accounting payload remains unchanged. Added a direct policy/metadata separation control using the existing completed-prefix fixture. Targeted portfolio/resume/completed-resume/allocation now passes50 checks; Low64 and High54 and full prior+new41wall/43CPU accounting are restored. Full integration and Native are lead-owned.
