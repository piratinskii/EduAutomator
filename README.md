# EDU AUTOMATOR

#### This software is designed to automate the registration and enrollment of students in Moodle courses for my previous job place. But if you manage a student registry in Google Sheets, you can use it to automate certain processes within your company.

#### This program will:
- Check your Google Sheets for new students 
- Create new users in Moodle 
- Create new courses in Moodle (if they don't exist)
- Enroll new users in Moodle courses 
- Send a welcome email to new users (or email to admin if the new course is empty)

## Requirements
- You must have a Google Cloud account (for working with Google Sheets)
- You must have your own Moodle server (for working with Moodle API)
- You must have a Gmail account (for sending emails)
- Python 3.11 and PIP

## Preparation
1. Google Cloud project's settings
   - Authorize your Google Cloud account here - https://console.cloud.google.com/
   - Create a new project
   - Fill the project name and click "Create" (you can leave location field by default)
   - After creation (it may take a few minutes) - select your project here:
   - Press side menu button and select "APIs & Services" > "Enable APIs & Services"
   - Press "+ Enable APIs and Services" button
   - In the search field type "Google Sheets API" and select it
   - Press "Enable" button
   - Repeat the same steps for "Google Drive" and "Gmail API"
2. Google service-account credentials
   - Press side menu button and select "APIs & Services" > "Credentials"
   - Press "+ Create Credentials" > "Service account"
   - Enter the service account ID (for example "service-account"). Other fields can be left blank.
   Then press "Create and continue" button
   - Select a role - Owner (or Editor) and press "Continue" button
   - Press "Done" button
   - After redirect to "Credentials" page - press on the name of your service account (below the "Service Accounts" section)
   - Select "Keys" tab and press "Add Key" > "Create new key" > "JSON" > "Create"
   - Save the downloaded JSON file to the root of the project and rename it to "service-account.json" (just for your convenience)
3. Google OAuth credentials (GMail)
   - Press side menu button and select "APIs & Services" > "Credentials"
   - Press "+ Create Credentials" > "OAuth client ID"
     - For  the first time you will need to configure the consent screen. Press "Configure consent screen" button
     - Select "External"
     - Fill the "App name", "User support email" and "Email addresses" (Developer contact information) fields and press "Save and continue" button
     - Press "Save and continue" button again
     - Now you must add "Test users" for your app. Press "+ Add users" button and just add your email address (for email sending)
     - Press "Save and continue" button and return to "Credentials" > "+ Create Credentials" > "OAuth client ID" page
   - Select "Desktop app", fill in name field and press "Create" button
   - Now press "Download JSON" and save it also to the root of the project and rename it to "oauth.json" (for your convenience)
4. Moodle settings
   - Install and configure Moodle on your server if you haven't already done so
   - Go to the "Site administration" > "Server" > "Web services" > Overview
   - 1. Enable web services - just press this link, click on the checkbox and press "Save changes" button
     2. Enable protocols - just press this link, click on the "eye" button opposite to REST protocol and press "Save changes" button
     3. Create a specific user - press this link, fill in fields "Username", chose "Web service authentication" (also if it marked disabled), "First name", "Last name", "Email address" and press "Create user" button
     4. Check user capability - You must create new role with some additional functions.
        - Site Administration, Users, Define roles, press "Add a new role" button. Select "template" for the role (Use role or archetype). For example - "manager". Press "continue" button.
        - Fill in Short name of new role (for example API) and in the bottom of page fill in "Filter" field with "webservice/rest:use" and press checkbox "Allow" for this function. Press "Create this role" button.
        - Now we should link this role to our user. Go to Site Administration, Users, Permissions, Assign system roles. 
        - Press on your role link and select your "api" users in the list on the right. Press "Add" button.
     5. Select a service - press this link, press Add button, fill in the name field (for example "Edu Automator"), click on the checkboxes "Enabled" and "Authorised users only" and press "Add service" button
	 6. Add functions - press this link, click on the "Functions" link on line with your service, press "Add functions" button, select the following functions and press "Add functions" button:
        - core_course_create_courses
        - core_course_get_courses_by_field
        - core_user_create_users
        - core_user_get_users_by_field
        - enrol_manual_enrol_users
     7. Select a specific user - press this link, click on the "Authorised users" link on line with your service, select your user in the field on the right and press "Add" button
     8. Create a token for a user - press this link, select your user in the "search" field, select your service in the field below, press "Add" button and press "Save changes". Here you can also use "IP Restriction" and valid util for your security.
        - Now you was redirected to the "Manage tokens" page. Here you can see your token. Please, save it for future use in safe place.
     9. It's all. 
5. Google Sheets
   - Create or open your Google Sheets document.
   - Press "Share" button in the top right corner and add your service account email address (from the "Service accounts" section of the "Credentials" page in the Google Cloud) as editor.
   - Now you must make sure that all required fields are present in the table:
     - Full name of the student
     - Course name to enroll
     - Student's email address
     - Empty column for the login of the student (will be filled in automatically)/for error's information
     - Confirmation column. You must press "Insert" from the top menu, select "Checkbox" and insert it in the whole column. This column will be used to confirm the enrollment of the student in the course.
6. Edu Automator.
   - Now you have all the necessary data to configure the Edu Automator. In first time program will install all necessary packages from "requirements.txt". After that you can start the program.
   - You can start the program with the following command:
     - `sudo py main.py` for Linux
     - 'python main.py' for Windows (please, run command line as Administrator) 
   - Complete all configure questions of the program. It's required process.
   - Also you should change templates in the "letters" folder. There is 3 templates:
     - "registration.html" - for registration email letter to the new student
     - "enrollment.html" - if student already was registered in the system, and you want to enroll him in the new course
     - "system.html" - for system email letters (if system will create new empty course)
   - Now you can use the program.

## How to use?
1. Run the program
2. In the Google Sheets document, fill in the required fields for the student (full name, course name, email address) and after that select confirmation checkbox. 
The program will automatically enroll the student in the course and fill in the login field. You can check all information about the process in the console or in logs file (logs folder in the root)
3. It's all. In the cases, when program will create a new course, you will receive an email on the administration mailbox, that you should fill the course with content.

## Author:
- Evgenii Piratinskii
