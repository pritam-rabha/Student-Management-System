**# Student Management System**



A web-based administration system for a small educational institution, built with Flask and JSON file storage. It was written for an MCA Python Programming assignment.

**Author:** Pritam Rabha  
**Programme:** MCA, 3rd Semester  
**University:** Dr. Hari Singh Gour Vishwavidyalaya, Sagar, Madhya Pradesh
**Project Guide:** Dr. Pangambam Sendash Singh

> **Academic Project Disclaimer:** This Student Management System was developed independently by a student as part of an academic programming assignment.




An administrator signs in and can manage student records, search and filter the directory, view a dashboard with charts, and run reports on enrolment and marks.



**## Contents**



1\. [Features]\(#features)

2\. [Technology]\(#technology)

3\. [Project structure]\(#project-structure)

4\. [Run locally]\(#run-locally)

5\. [Administrator account setup]\(#administrator-account-setup)

6\. [Environment variables]\(#environment-variables)

7\. [Data storage]\(#data-storage)

8\. [Important: storage on Render's free plan]\(#important-storage-on-renders-free-plan)

9\. [Application routes]\(#application-routes)

10\. [Validation rules]\(#validation-rules)

11\. [Security]\(#security)

12\. [Testing]\(#testing)

13\. [Upload to GitHub]\(#upload-to-github)

14\. [Deploy to Render]\(#deploy-to-render)

15\. [Troubleshooting]\(#troubleshooting)

16\. [Known limitations]\(#known-limitations)



**## Features**



\- Administrator login and logout with hashed passwords, Flask sessions, CSRF protection and login throttling.

\- Student create, view, edit and delete. Deletion requires confirmation in a dialog.

\- Student fields: unique student ID, full name, email, phone, course, department, semester, admission date, date of birth (optional), marks (optional), address (optional).

\- Search by student ID, name, email or course. Filter by course, department and semester. Sort by name, student ID or marks, ascending or descending. Pagination with 10, 25 or 50 rows per page.

\- Dashboard: total students, average, highest and lowest marks, course and department statistics, recently added students, and four Chart.js charts (by course, by department, by semester, marks distribution). All values are calculated from the stored data.

\- Reports: totals, per-course, per-department and per-semester counts with averages, topper(s), lowest scorer(s), and a ranked list that can be filtered by course, department and semester. Equal marks share a rank. Students without marks are listed but not ranked.

\- Server-side validation of every field, plus HTML5 client-side validation for quick feedback.

\- Responsive layout (desktop, tablet, mobile), keyboard-accessible controls, skip link, labelled forms, and friendly error pages.



There is no attendance module, by design.



**## Technology**



Python 3.11 or newer, Flask 3, Jinja2, Bootstrap 5.3, Chart.js 4, vanilla JavaScript, JSON file storage, pytest, Gunicorn.



Bootstrap and Chart.js are bundled under \`app/static/vendor/\` (with their MIT licences), so the application needs no CDN access and runs under a strict Content Security Policy.



**## Project structure**



\`\`\`

Student_Management_System/

&#x20;   run.py                  Local development entry point

&#x20;   wsgi.py                 Production entry point (gunicorn wsgi:app)

&#x20;   config.py               Configuration read from environment variables

&#x20;   requirements.txt        Runtime dependencies

&#x20;   requirements-dev.txt    Runtime plus pytest

&#x20;   render.yaml             Render blueprint

&#x20;   pytest.ini

&#x20;   .env.example            Variable names with placeholder values

&#x20;   .gitignore

&#x20;   README.md

&#x20;   app/

&#x20;       \_\_init\_\_.py         Application factory, hooks, error handlers

&#x20;       exceptions.py       Domain exceptions

&#x20;       routes/             Flask blueprints: auth, dashboard, students, reports

&#x20;       services/           Business logic: students, reports, authentication

&#x20;       storage/            Repository interface, JSON store, demo-data seeding

&#x20;       utils/              Validators, CSRF, pagination, rate limiting, formatting

&#x20;       templates/          Jinja2 templates

&#x20;       static/             css/, js/, images/, vendor/

&#x20;   data/

&#x20;       sample_data/        students_sample.json (demonstration data)

&#x20;   scripts/

&#x20;       create_admin_hash.py     Generate ADMIN_PASSWORD_HASH

&#x20;       seed_sample_data.py      Load demo data on request

&#x20;       generate_sample_data.py  Rebuild the demo data file

&#x20;   tests/                  pytest suite

\`\`\`



The entry point is \`wsgi.py\` rather than \`app.py\` because a module named \`app.py\` cannot coexist with the \`app/\` package: Python would import the package and Gunicorn could not find the application object.



Layering: routes handle HTTP only; services hold validation and business rules; storage is hidden behind the \`StudentRepository\` interface in \`app/storage/base.py\`. Routes never touch files directly.



**## Run locally**



Requires Python 3.11 or newer.



\`\`\`bash

\# 1. Create and activate a virtual environment

python -m venv .venv

source .venv/bin/activate          # Windows: .venv\Scripts\activate



\# 2. Install dependencies

pip install -r requirements-dev.txt



\# 3. Create your local configuration

cp .env.example .env               # Windows: copy .env.example .env



\# 4. Create the administrator password hash (see next section) and paste it into .env

python scripts/create_admin_hash.py



\# 5. Start the development server

python run.py

\`\`\`



Open http\://localhost:5000 and sign in. On first start the application creates \`data/students.json\` from the bundled demonstration data (30 students). If \`data/students.json\` already exists it is never modified at startup.



Use \`APP_ENV=development\` locally. In \`production\` mode session cookies are marked Secure and are only sent over HTTPS.



To run the production server locally (Linux or macOS):



\`\`\`bash

gunicorn --workers 1 --threads 4 --bind 0.0.0.0:5000 wsgi:app

\`\`\`



Gunicorn does not run on Windows; use \`python run.py\` there.



**## Administrator account setup**



No credentials are stored in the source code. The administrator is defined by two environment variables:



\- \`ADMIN_USERNAME\` (default \`admin\`)

\- \`ADMIN_PASSWORD_HASH\`, a password hash



Generate the hash with the helper script. The password is typed without echo and is not saved anywhere:



\`\`\`bash

python scripts/create_admin_hash.py

\`\`\`



Copy the printed \`ADMIN_PASSWORD_HASH=...\` line into your \`.env\` file (keep the single quotes) or into the Render dashboard (paste only the value, without quotes).



For quick local trials only, you may set \`ADMIN_PASSWORD\` instead. It is hashed in memory at startup. \`ADMIN_PASSWORD_HASH\` takes priority when both are set. If neither is set, the login page reports that sign-in is unavailable and no one can sign in.



**## Environment variables**



\| Variable | Required | Default | Purpose |

\|---|---|---|---|

\| \`APP_ENV\` | No | \`development\` | \`production\` enforces \`SECRET_KEY\` and Secure cookies |

\| \`SECRET_KEY\` | Yes in production | random per start in development | Signs session cookies |

\| \`ADMIN_USERNAME\` | No | \`admin\` | Administrator username |

\| \`ADMIN_PASSWORD_HASH\` | Yes (or \`ADMIN_PASSWORD\`) | none | Hash from \`create_admin_hash.py\` |

\| \`ADMIN_PASSWORD\` | No | none | Local trials only; hashed in memory |

\| \`DATA_DIR\` | No | \`./data\` | Directory holding \`students.json\` |

\| \`SEED_SAMPLE_DATA\` | No | \`true\` | Create demo data only when no data file exists |

\| \`TRUST_PROXY\` | No | \`false\` | Set \`true\` behind Render so client IPs and HTTPS are detected |

\| \`SESSION_COOKIE_SECURE\` | No | \`true\` in production | Override cookie Secure flag |

\| \`LOGIN_MAX_ATTEMPTS\` | No | \`5\` | Failed logins allowed per window |

\| \`LOGIN_LOCKOUT_SECONDS\` | No | \`300\` | Length of the throttle window |

\| \`PORT\` | No | \`5000\` | Local port for \`run.py\`; Render sets this itself |



Generate a secret key with:



\`\`\`bash

python -c "import secrets; print(secrets.token_hex(32))"

\`\`\`



**## Data storage**



Records are stored in \`data/students.json\` (or \`$DATA_DIR/students.json\`):



\`\`\`json

{

&#x20; "version": 1,

&#x20; "students": [

&#x20;   {

&#x20;     "student_id": "MCA26001",

&#x20;     "full_name": "Aarav Sharma",

&#x20;     "email": "aarav.sharma\@students.example.edu",

&#x20;     "phone": "+91 70962 74343",

&#x20;     "course": "MCA",

&#x20;     "department": "Computer Applications",

&#x20;     "semester": 1,

&#x20;     "admission_date": "2026-07-08",

&#x20;     "date_of_birth": "2005-10-18",

&#x20;     "marks": null,

&#x20;     "address": "160, MG Road, Indore, Madhya Pradesh",

&#x20;     "created_at": "2026-07-08T09:30:00+00:00",

&#x20;     "updated_at": "2026-07-08T09:30:00+00:00"

&#x20;   }

&#x20; ]

}

\`\`\`



Field notes: \`student_id\` is stored in upper case and is unique. \`marks\` is a number from 0 to 100 or \`null\`. \`date_of_birth\` and \`address\` may be empty strings. Dates are ISO \`YYYY-MM-DD\`; timestamps are ISO 8601 in UTC.



How the storage layer protects the data:



\- **\*\*Atomic writes.\*\*** Each save writes a temporary file in the same directory, flushes and fsyncs it, then replaces the real file with \`os.replace\`. A crash mid-write cannot leave a half-written file.

\- **\*\*Serialised writers.\*\*** Read-modify-write operations run under a thread lock and, on Linux and macOS, an \`flock\` on \`students.json.lock\`.

\- **\*\*Missing file.\*\*** Treated as an empty data set.

\- **\*\*Malformed or corrupted file.\*\*** The file is renamed to \`students.json.corrupt-\<timestamp>\` (nothing is lost) and the application starts with an empty set instead of crashing. The event is logged.

\- **\*\*Demo data never overwrites.\*\*** At startup, sample data is loaded only when \`students.json\` does not exist at all. An existing file, even an empty list, is left alone. \`python scripts/seed_sample_data.py --force\` replaces the file on request and keeps a timestamped \`.bak\` copy.

\- **\*\*No user-controlled paths.\*\*** The file location comes only from configuration. Student IDs are only used as lookup keys, never as file names.



To move to a database later, implement the \`StudentRepository\` interface (\`all\`, \`get\`, \`add\`, \`update\`, \`delete\`) and construct that class in \`app/\_\_init\_\_.py\` in place of \`JsonStudentRepository\`. Services, routes and templates do not change.



**## Important: storage on Render's free plan**



Render's free web service has an **\*\*ephemeral filesystem\*\***. Files written while the service runs, including \`students.json\`, can be lost when the service restarts, is redeployed, or spins down after inactivity. **\*\*JSON files on the free plan are not permanent storage.\*\***



What this means in practice:



\- Records added on a free Render instance may disappear. After a reset, the application starts again from the demonstration data (or empty, if \`SEED_SAMPLE_DATA=false\`).

\- This is acceptable for a demonstration or assignment submission. It is not acceptable for real institutional records.



Options for real persistence:



1\. Use a Render paid plan with a persistent disk, mount it (for example at \`/var/data\`), and set \`DATA_DIR=/var/data\`. No code change is needed.

2\. Implement a database-backed \`StudentRepository\` (see above).

3\. Host the application on a server with a normal persistent filesystem.



Because the file lock only coordinates processes on one machine, run a single Gunicorn worker (as configured) with JSON storage.



**## Application routes**



All routes except \`/login\`, \`/healthz\` and static files require an authenticated administrator; anonymous users are redirected to the login page. Every POST requires a valid CSRF token.



\| Method | Path | Purpose |

\|---|---|---|

\| GET, POST | \`/login\` | Sign in |

\| POST | \`/logout\` | Sign out |

\| GET | \`/\` | Dashboard |

\| GET | \`/students/\` | Directory with \`q\`, \`course\`, \`department\`, \`semester\`, \`sort\`, \`order\`, \`page\`, \`per_page\` |

\| GET, POST | \`/students/new\` | Add a student |

\| GET | \`/students/\<id>\` | Student details |

\| GET, POST | \`/students/\<id>/edit\` | Edit a student (ID cannot change) |

\| POST | \`/students/\<id>/delete\` | Delete a student |

\| GET | \`/reports/\` | Reports, with \`course\`, \`department\`, \`semester\`, \`page\` |

\| GET | \`/healthz\` | Health check for Render (public, returns \`{"status": "ok"}\`) |



Status codes: 400 for validation failures and CSRF errors, 401 for wrong credentials, 404 for missing records or pages, 405 for unsupported methods, 409 for duplicate student IDs, 413 for oversized requests, 429 when login is throttled, 503 when the data file cannot be read or written, 500 for unexpected errors.



**## Validation rules**



\| Field | Rule |

\|---|---|

\| Student ID | Required, unique (case-insensitive), 2 to 20 characters: letters, digits, \`-\`, \`\_\`; must start with a letter or digit |

\| Full name | Required, 2 to 100 characters |

\| Email | Required, valid format, up to 254 characters |

\| Phone | Required, digits with optional \`+\`, spaces, brackets, dots and hyphens; 7 to 15 digits |

\| Course, department | Required, 2 to 80 characters |

\| Semester | Required, whole number 1 to 10 |

\| Admission date | Required, valid date, not in the future |

\| Date of birth | Optional, valid past date, before the admission date |

\| Marks | Optional, number from 0 to 100 with at most two decimals; NaN and infinity are rejected |

\| Address | Optional, up to 300 characters |



**## Security**



\- Passwords are verified against a PBKDF2-SHA256 hash. Username and password are checked in a way that does not reveal which one was wrong.

\- Sessions are signed with \`SECRET_KEY\`. Cookies are HttpOnly and SameSite=Lax, and Secure in production. The session is replaced on login to prevent fixation. Sessions expire after 8 hours.

\- CSRF tokens are required on every POST (forms and logout).

\- After 5 failed logins from one address, further attempts are blocked for 5 minutes. The counter is held in memory and resets when the application restarts.

\- The \`next\` parameter after login only accepts local paths, preventing open redirects.

\- Jinja2 auto-escaping protects against script injection from stored data. Responses carry \`X-Content-Type-Options\`, \`X-Frame-Options\`, \`Referrer-Policy\` and a Content Security Policy that only allows resources from the same origin. Authenticated pages are sent with \`Cache-Control: no-store\`.

\- Unexpected errors are logged on the server and shown to users as a generic message. No stack traces or configuration values are displayed.

\- Request bodies are limited to 64 KB.

\- \`.env\` and runtime data files are excluded by \`.gitignore\`.



**## Testing**



\`\`\`bash

pip install -r requirements-dev.txt

python -m pytest

\`\`\`



Result of the last run: **\*\*163 passed\*\***.



The tests build the application against a fresh temporary directory for every test, so they never read or modify \`data/\`. They cover:



\- Login, logout, wrong credentials, throttling, CSRF rejection, open-redirect protection, unconfigured administrator.

\- Anonymous access to every page and every state-changing request.

\- Student creation, listing, viewing, editing, deletion, missing records, duplicate IDs (including different letter case), invalid marks and other invalid fields, escaping of script input, persistence across an application restart.

\- Search, filters, sorting (including missing marks), natural ordering of IDs, pagination and its edge cases, empty states.

\- Report calculations (averages, highest, lowest, toppers, counts, rankings with ties, empty data set, data set without marks) and the dashboard and reports pages.

\- JSON storage: missing, empty, malformed, binary and structurally invalid files, atomic write failure handling, concurrent writers, seeding rules, and validity of the bundled sample data.



**## Upload to GitHub**



1\. Create an empty repository on GitHub (no README, licence or .gitignore, since the project already has them).

2\. From the project folder:



\`\`\`bash

git init

git add .

git status                     # confirm .env and data/students.json are NOT listed

git commit -m "Student Management System"

git branch -M main

git remote add origin https\://github.com/\<your-username>/\<your-repository>.git

git push -u origin main

\`\`\`



Never commit \`.env\` or a real password hash. If one is committed by mistake, generate a new hash and a new \`SECRET_KEY\`, because the old values remain in the repository history.



**## Deploy to Render**



The repository includes \`render.yaml\`, so you can deploy as a Blueprint.



**\*\*Option A: Blueprint\*\***



1\. Push the project to GitHub.

2\. In the Render dashboard choose New, then Blueprint, and select the repository.

3\. Render reads \`render.yaml\`. When prompted, enter a value for \`ADMIN_PASSWORD_HASH\` (output of \`python scripts/create_admin_hash.py\`, pasted without quotes). \`SECRET_KEY\` is generated automatically.

4\. Apply the Blueprint and wait for the build to finish.



**\*\*Option B: manual web service\*\***



1\. In Render choose New, then Web Service, and connect the repository.

2\. Settings: Runtime Python 3, Build Command \`pip install -r requirements.txt\`, Start Command:



\`\`\`

gunicorn --workers 1 --threads 4 --timeout 60 --bind 0.0.0.0:$PORT wsgi:app

\`\`\`



3\. Instance type: Free. Health Check Path: \`/healthz\`.

4\. Add environment variables: \`PYTHON_VERSION=3.11.9\`, \`APP_ENV=production\`, \`TRUST_PROXY=true\`, \`SECRET_KEY\` (random value), \`ADMIN_USERNAME\`, \`ADMIN_PASSWORD_HASH\`, and optionally \`SEED_SAMPLE_DATA=false\` for an empty start.



Render provides the \`PORT\` variable and the HTTPS certificate. Gunicorn binds to \`0.0.0.0:$PORT\` as required. Read the [storage limitation]\(#important-storage-on-renders-free-plan) before relying on the deployed data. A free service also sleeps after a period of inactivity, so the first request afterwards is slow.



**## Troubleshooting**



\- **\*\*"Sign-in is not available because the administrator account has not been set up."\*\*** \`ADMIN_PASSWORD_HASH\` is missing. Generate it and set it.

\- **\*\*Cannot stay signed in locally.\*\*** \`APP_ENV=production\` makes cookies Secure, so they are dropped over plain HTTP. Use \`APP_ENV=development\` locally.

\- **\*\*Application refuses to start with \`SECRET_KEY must be set\`.\*\*** Set \`SECRET_KEY\` when \`APP_ENV=production\`.

\- **\*\*Records vanished on Render.\*\*** Expected on the free plan; see the storage section.

\- **\*\*A \`students.json.corrupt-\<timestamp>\` file appeared.\*\*** The data file was unreadable and was set aside. Inspect or repair that file and copy valid records back.

\- **\*\*\`$\` characters in the hash are altered in a \`.env\` file.\*\*** Keep the value inside single quotes.



**## Known limitations**



\- JSON storage is meant for small data sets: each request reads the whole file. It also limits deployment to a single worker process.

\- The login throttle is in memory and per process.

\- Single administrator account; there are no per-user roles or audit log.

\- Email addresses are not required to be unique, because the assignment only requires unique student IDs.

\- The interface was tested through automated requests against a running Gunicorn server. It has not been checked in a real browser on different screen sizes, and the deployment files have not been run on Render itself.
