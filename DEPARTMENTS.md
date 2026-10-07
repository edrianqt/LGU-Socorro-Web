# Department Directory

The original site's 20 executive offices and two legislative offices are available at `/departments/`, on the homepage, and on the About page. Office names and inquiry topics are maintained in `data/departments.json`.

Each office has its own page and inquiry form. Inquiries are saved in the local database and receive a reference number. Citizens can check their status at `/departments/track/`. Appointment requests are requests for staff review, not confirmed reservations.

Staff sign in at `/staff/login/` with the credentials in `instance/staff-access.json`. That local file is generated on first startup and is not served by the website. The staff inbox at `/submissions/` includes department inquiries, existing service requests, and contact messages. Staff can set department inquiries to New, In review, or Resolved. Changes appear on the citizen's tracking page.

To override the generated password, set `SOCORRO_STAFF_PASSWORD` before starting Flask. `SOCORRO_SECRET_KEY` can override the persistent local session key. The entire `instance/` directory is excluded from Git.

Inquiry delivery currently means saving it for staff review within this application. No email or external municipal system is connected. Office-specific telephone numbers, hours, fees, and document requirements are not supplied by the original homepage and have not been invented.

Run backend workflow checks with `python -m unittest discover -s tests -p 'test_*.py'`. The Playwright checks in `tests/interactions.cjs` cover directory filtering, expanded office details, profile navigation, and responsive layouts, alongside the other public interactions.
